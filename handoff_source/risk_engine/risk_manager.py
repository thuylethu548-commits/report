import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from config.settings import settings
from core.constants import OrderSide, OrderType, OrderStatus, MarketRegime
from core.events import SignalEvent, OrderEvent, AIAdvisoryEvent, FillEvent
from core.event_bus import EventBus
from data.storage import Database
from ai_advisory.vyce_client import VyceClient
from .circuit_breaker import CircuitBreaker
from .time_window_guard import TimeWindowRiskGuard
from .funding_sentinel import FundingSentinel

logger = logging.getLogger("RiskManager")


class RiskManager:
    def __init__(
        self,
        event_bus: EventBus,
        db: Database,
        circuit_breaker: CircuitBreaker,
        vyce_client: Optional[VyceClient] = None,
        audit_logs: Optional[List[Dict[str, Any]]] = None,
        mtf_filter: Optional[Any] = None,
        time_guard: Optional[TimeWindowRiskGuard] = None,
        macro_scanner: Optional[Any] = None,
        funding_sentinel: Optional[FundingSentinel] = None
    ):
        self.event_bus = event_bus
        self.db = db
        self.circuit_breaker = circuit_breaker
        self.vyce_client = vyce_client or VyceClient()
        self.audit_logs = audit_logs
        self.mtf_filter = mtf_filter
        self.time_guard = time_guard or TimeWindowRiskGuard()
        self.macro_scanner = macro_scanner
        self.funding_sentinel = funding_sentinel or FundingSentinel()
        self.open_positions: Dict[str, dict] = {}
        self.latest_ai_advisory: Optional[AIAdvisoryEvent] = None
        self.last_order_times: Dict[str, datetime] = {}

        # Subscribe to signals, AI advisory, and execution fills
        self.event_bus.subscribe(SignalEvent, self.handle_signal)
        self.event_bus.subscribe(AIAdvisoryEvent, self.handle_ai_advisory)
        self.event_bus.subscribe(FillEvent, self.handle_fill)

    async def handle_ai_advisory(self, event: AIAdvisoryEvent) -> None:
        """Cache incoming AI advisory events from other background sources."""
        self.latest_ai_advisory = event

    async def handle_fill(self, event: FillEvent) -> None:
        """Synchronize open positions tracking from execution fills."""
        pos_key = f"{event.strategy_name}_{event.symbol}"
        if not event.is_paper and event.reduce_only:
            existing = self.open_positions.get(pos_key)
            if existing:
                # Track realized PnL
                if existing.get("fill_price") and event.fill_price:
                    entry_p = float(existing["fill_price"])
                    exit_p = float(event.fill_price)
                    qty = float(event.quantity)
                    trade_pnl = (exit_p - entry_p) * qty if existing.get("side") == OrderSide.BUY else (entry_p - exit_p) * qty
                    self.circuit_breaker.add_realized_pnl(trade_pnl)
                existing["quantity"] = max(0.0, existing["quantity"] - event.quantity)
                if existing["quantity"] <= 1e-10:
                    self.open_positions.pop(pos_key, None)
            return
        if event.side == OrderSide.BUY or (not event.is_paper and not event.reduce_only):
            self.open_positions[pos_key] = {
                "order_id": event.order_id,
                "strategy_name": event.strategy_name,
                "symbol": event.symbol,
                "side": event.position_side or event.side,
                "quantity": event.quantity,
                "fill_price": event.fill_price,
                "timestamp": event.timestamp
            }
        elif event.side == OrderSide.SELL:
            self.open_positions.pop(pos_key, None)

    async def sync_open_positions_from_db(self) -> None:
        """Synchronize in-memory open positions with active OPEN trades in SQLite database on startup."""
        if not self.db:
            return
        try:
            trades = await self.db.get_recent_trades(limit=100)
            count = 0
            is_paper_mode = (settings.TRADING_MODE == "paper")
            for t in trades:
                t_is_paper = bool(t.get("is_paper"))
                if t.get("status") == "OPEN" and t_is_paper == is_paper_mode:
                    pos_key = f"{t.get('strategy_name')}_{t.get('symbol')}"
                    side_raw = t.get("side", "BUY")
                    side = OrderSide.BUY if side_raw.upper() == "BUY" else OrderSide.SELL
                    self.open_positions[pos_key] = {
                        "order_id": t.get("order_id"),
                        "strategy_name": t.get("strategy_name"),
                        "symbol": t.get("symbol"),
                        "side": side,
                        "quantity": float(t.get("quantity") or 0.0),
                        "fill_price": float(t.get("entry_price") or 0.0),
                        "timestamp": t.get("entry_time")
                    }
                    count += 1
            logger.info(f"[RiskManager] Synced {count} active open position(s) from database (mode={settings.TRADING_MODE}): {list(self.open_positions.keys())}")

            # Sync today's realized PnL into Circuit Breaker (only matching current trading mode)
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            today_pnl = 0.0
            for t in trades:
                t_is_paper = bool(t.get("is_paper"))
                if t.get("status") == "CLOSED" and t_is_paper == is_paper_mode:
                    exit_time = str(t.get("exit_time") or "")
                    if exit_time.startswith(today_str):
                        today_pnl += float(t.get("pnl_usdt") or 0.0)
            if today_pnl != 0.0:
                self.circuit_breaker.add_realized_pnl(today_pnl)
                logger.info(f"[RiskManager] Synced today's realized PnL into Circuit Breaker: {today_pnl:+.4f} USDT")
        except Exception as e:
            logger.warning(f"[RiskManager] Could not sync open positions from database: {e}")

    async def handle_signal(self, signal: SignalEvent) -> Optional[OrderEvent]:
        """
        Gated Risk Processing Pipeline:
        Phase 1: Deterministic Hard Risk Rules (Circuit Breaker, Position Limit, Stop-Loss Bounds)
        Phase 2: Active AI Advisory Veto (Claude-3.5-Sonnet via Vyce AI with < 3.0s Timeout Fallback)
        Phase 3: Position Sizing & Allocation Multiplier
        Phase 4: Order Creation, Dual SQLite Persistence & OrderEvent Emission
        """
        # Explicitly reduce an existing opposite position before entry-only gates.
        position = self.open_positions.get(f"{signal.strategy_name}_{signal.symbol}")
        if position and signal.side != position.get("side", OrderSide.BUY) and signal.stop_loss <= 0:
            exit_order = OrderEvent(
                order_id="exit_" + str(uuid.uuid4()), strategy_name=signal.strategy_name,
                symbol=signal.symbol, side=signal.side, order_type=OrderType.MARKET,
                quantity=position["quantity"], price=signal.price, stop_loss=0,
                take_profit=0, timestamp=datetime.now(timezone.utc), reduce_only=True)
            await self.event_bus.publish(exit_order)
            return exit_order
        elif signal.stop_loss <= 0:
            # Exit signal without an active position tracked in risk manager; ignore gracefully
            logger.info(f"[Risk Manager] Ignored exit signal for {signal.symbol} (no active position tracked in risk manager)")
            return None
        # =====================================================================
        # Phase 1: Deterministic Hard Risk Checks (0ms)
        # =====================================================================
        # Check 1.0: Auto-Trade Master Switch Check
        if not getattr(settings, "AUTO_TRADE_ENABLED", True) and not getattr(signal, "force", False):
            reason = "Auto-Trade is currently PAUSED by master switch"
            logger.info(f"[Risk Standby] {reason} for {signal.symbol}")
            await self._record_rejection(signal, reason)
            return None

        # Check 1.0b: Cooldown Check between orders of the same symbol
        if getattr(settings, "ENABLE_COOLDOWN", False) and not getattr(signal, "force", False) and signal.symbol in self.last_order_times:
            elapsed = (datetime.now(timezone.utc) - self.last_order_times[signal.symbol]).total_seconds()
            cooldown_sec = getattr(settings, "COOLDOWN_MINUTES", 15) * 60
            if elapsed < cooldown_sec:
                rem_m = int((cooldown_sec - elapsed) // 60) + 1
                reason = f"Cooldown active for {signal.symbol}: {rem_m}m remaining"
                logger.info(f"[Risk Cooldown] {reason}")
                await self._record_rejection(signal, reason)
                return None

        # Check 1.0c: Red Flag Time Window Check (Vietnam & Global Market Storms)
        if getattr(settings, "ENABLE_TIME_WINDOW_GUARD", True) and not getattr(signal, "force", False) and settings.TRADING_MODE == "live":
            is_rf, rf_reason = self.time_guard.is_red_flag_window(getattr(signal, "timestamp", None))
            if is_rf:
                reason = f"Time Window Veto: {rf_reason}"
                logger.warning(f"[Risk Rejection] {reason}")
                if self.audit_logs is not None:
                    self.audit_logs.append({
                        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                        "level": "WARNING",
                        "msg": f"⏳ Time Window Veto [{signal.symbol}]: {rf_reason}"
                    })
                await self._record_rejection(signal, reason)
                return None

        # Check 1.0d: Geopolitical & War Emergency Defense Check
        if self.macro_scanner and not getattr(signal, "force", False):
            macro_status = getattr(self.macro_scanner, "cached_status", {})
            if macro_status.get("emergency_defense", False):
                state = macro_status.get("state", "WAR_RISK_DEFENSIVE")
                summary = macro_status.get("summary", "Tình báo vĩ mô khẩn cấp kích hoạt")
                reason = f"Macro Emergency Defense [{state}]: {summary}"
                logger.warning(f"[Risk Rejection] {reason}")
                if self.audit_logs is not None:
                    self.audit_logs.append({
                        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                        "level": "DANGER",
                        "msg": f"🚨 Macro Emergency Defense [{signal.symbol}]: {summary}"
                    })
                await self._record_rejection(signal, reason)
                return None

        # Check 1.0e: Funding Rate & Liquidation Squeeze Sentinel Check
        if self.funding_sentinel and not getattr(signal, "force", False) and settings.TRADING_MODE == "live":
            side_str = signal.side.value if hasattr(signal.side, "value") else str(signal.side)
            squeeze_res = await self.funding_sentinel.evaluate_squeeze_risk(signal.symbol, side_str)
            if not squeeze_res.get("safe", True):
                reason = squeeze_res.get("reason", "Funding Rate Squeeze Danger")
                logger.warning(f"[Funding Sentinel Veto] {reason}")
                if self.audit_logs is not None:
                    self.audit_logs.append({
                        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                        "level": "WARNING",
                        "msg": f"🦈 Funding Sentinel Veto [{signal.symbol}]: {reason}"
                    })
                await self._record_rejection(signal, reason)
                return None

        # Check 1.1: Circuit Breaker Check (Daily Drawdown & Max Loss -3.5u)
        if self.circuit_breaker.is_tripped:
            reason = f"Circuit breaker tripped: {self.circuit_breaker.trip_reason}"
            logger.warning(f"[Risk Rejection] {reason}")
            await self._record_rejection(signal, reason)
            return None

        # Check 1.1b: Daily Profit Target Lock & House Money Check (+10.0u Target)
        if getattr(self.circuit_breaker, "is_profit_locked", False):
            if not getattr(self.circuit_breaker, "house_money_mode", False):
                reason = f"Daily profit target reached: {self.circuit_breaker.trip_reason}"
                logger.info(f"[Profit Target Lock] {reason}")
                await self._record_rejection(signal, reason)
                return None
            else:
                logger.info(
                    f"[House Money Active] Daily profit +${self.circuit_breaker.daily_realized_pnl:.2f} reached +${self.circuit_breaker.target_daily_profit_usd:.2f} target. "
                    f"Allowing trade in conservative House Money mode (0.2x size multiplier)."
                )

        # Check 1.2: Max Open Positions Check (For new position entries)
        pos_key = f"{signal.strategy_name}_{signal.symbol}"
        existing_pos = self.open_positions.get(pos_key)

        # An order is an exit if we have an active position and this signal is an opposite close or SL=0.0
        is_exit = False
        if existing_pos:
            existing_side = existing_pos.get("side")
            if (existing_side in (OrderSide.BUY, "BUY") and signal.side == OrderSide.SELL) or \
               (existing_side in (OrderSide.SELL, "SELL") and signal.side == OrderSide.BUY) or \
               (signal.stop_loss == 0.0):
                is_exit = True

        is_new_entry = not is_exit and (
            (signal.side == OrderSide.BUY and pos_key not in self.open_positions) or
            (signal.side == OrderSide.SELL and pos_key not in self.open_positions and signal.stop_loss > 0)
        )

        if is_new_entry and len(self.open_positions) >= settings.MAX_OPEN_POSITIONS:
            reason = f"Maximum open positions reached ({len(self.open_positions)}/{settings.MAX_OPEN_POSITIONS})"
            logger.warning(f"[Risk Rejection] {reason}")
            await self._record_rejection(signal, reason)
            return None

        # Check 1.2b: Anti-Duplicate Single Position Per Symbol Gate (Khóa 1 vị thế / 1 đồng coin)
        max_per_symbol = getattr(settings, "MAX_POSITIONS_PER_SYMBOL", 1)
        if is_new_entry and max_per_symbol > 0 and not getattr(signal, "force", False):
            active_count = sum(1 for p in self.open_positions.values() if p.get("symbol") == signal.symbol)
            if active_count >= max_per_symbol:
                reason = f"Duplicate Position Veto: {signal.symbol} already has {active_count} active position(s) (Limit: {max_per_symbol}). Anti-duplicate protection active."
                logger.warning(f"[Anti-Duplicate Gate] {reason}")
                if self.audit_logs is not None:
                    self.audit_logs.append({
                        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                        "level": "WARNING",
                        "msg": f"🚫 Anti-Duplicate Veto [{signal.symbol}]: Đã có {active_count} lệnh mở, từ chối vào trùng lặp."
                    })
                await self._record_rejection(signal, reason)
                return None

        # Check 1.3: Mandatory Stop Loss Check (Only for NEW entries)
        if is_new_entry:
            if signal.side == OrderSide.BUY:
                if signal.stop_loss <= 0 or signal.stop_loss >= signal.price:
                    reason = f"Invalid stop loss level: SL={signal.stop_loss}, Price={signal.price}"
                    logger.warning(f"[Risk Rejection] {reason}")
                    await self._record_rejection(signal, reason)
                    return None
            elif signal.side == OrderSide.SELL and signal.stop_loss > 0:
                if signal.stop_loss <= signal.price:
                    reason = f"Invalid stop loss level for SHORT: SL={signal.stop_loss}, Price={signal.price}"
                    logger.warning(f"[Risk Rejection] {reason}")
                    await self._record_rejection(signal, reason)
                    return None

        # Check 1.4: Multi-Timeframe Trend Confluence Check (BUY & SHORT orders)
        if is_new_entry and getattr(settings, "ENABLE_MULTI_TIMEFRAME", True) and self.mtf_filter and not getattr(signal, "force", False):
            side_str = "BUY" if signal.side == OrderSide.BUY else "SELL"
            mtf_res = self.mtf_filter.check_confluence(signal.symbol, signal.price, side=side_str)
            if not mtf_res.get("approved", True):
                reason = f"Multi-Timeframe Veto: {mtf_res.get('reason')}"
                logger.warning(f"[Risk Rejection] {reason}")
                if self.audit_logs is not None:
                    self.audit_logs.append({
                        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                        "level": "DANGER",
                        "msg": f"🚫 MTF Veto [{signal.symbol} {side_str}]: {mtf_res.get('reason')}"
                    })
                await self._record_rejection(signal, reason)
                return None

        # =====================================================================
        # Phase 2: Active AI Advisory Veto Gatekeeper (< 3.0s Timeout Fallback)
        # =====================================================================
        ai_mult = 1.0

        if settings.ENABLE_AI_ADVISORY and not getattr(signal, "force", False):
            # Gather recent market context and hard-earned lessons for AI
            recent_candles = []
            recent_lessons = []
            if self.db:
                try:
                    recent_candles = await self.db.get_recent_candles(signal.symbol, limit=10)
                except Exception as e:
                    logger.debug(f"Could not retrieve recent candles for AI context: {e}")
                try:
                    lessons_data = await self.db.get_lessons(limit=10)
                    recent_lessons = [f"[{l['category']}] {l['title']}: {l['lesson_learned']}" for l in lessons_data]
                except Exception as e:
                    logger.debug(f"Could not retrieve recent lessons: {e}")

            market_context: Dict[str, Any] = {
                "symbol": signal.symbol,
                "price": signal.price,
                "strategy_name": signal.strategy_name,
                "side": signal.side.value if hasattr(signal.side, "value") else str(signal.side),
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "confidence": signal.confidence,
                "recent_candles": recent_candles,
                "hard_earned_lessons_to_respect": recent_lessons,
                "account_equity": self.circuit_breaker.current_equity or settings.STARTING_BALANCE_USDT,
                "open_positions": len(self.open_positions)
            }

            timeout_sec = getattr(settings, "AI_TIMEOUT_SECONDS", 3.0)
            if getattr(self.vyce_client, "council_mode", "") == "adversarial":
                timeout_sec = max(timeout_sec, 32.0)
            try:
                ai_decision = await asyncio.wait_for(
                    self.vyce_client.evaluate_signal_veto(signal, market_context),
                    timeout=timeout_sec
                )
            except asyncio.TimeoutError:
                logger.warning(f"[AI Fallback Engaged] Timeout after {timeout_sec:.1f}s. Engaging quantitative fallback.")
                ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Timeout (> {timeout_sec:.1f}s)")
            except Exception as e:
                logger.warning(f"[AI Fallback Engaged] Error during signal evaluation: {e}. Engaging quantitative fallback.")
                ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Error ({e})")

            # Enforce RiskManager quantitative fallback rules if AI provider engaged fallback or returned invalid payload
            if not isinstance(ai_decision, dict):
                logger.warning(f"[AI Fallback Engaged] Invalid non-dict AI decision payload ({type(ai_decision)}). Engaging quantitative fallback.")
                ai_decision = self._execute_quantitative_fallback(signal, reason="Invalid AI Decision Payload")
            elif ai_decision.get("fallback_used") and ai_decision.get("approved", True):
                if ai_decision.get("model") != "quantitative-fallback":
                    fb_reason = ai_decision.get("reasoning") or "AI provider fallback engaged"
                    logger.warning(f"[AI Fallback Engaged] Fallback flagged by AI provider; enforcing RiskManager quantitative rules: {fb_reason}")
                    ai_decision = self._execute_quantitative_fallback(signal, reason=fb_reason)

            # Parse AI decision
            approved = bool(ai_decision.get("approved", True))
            regime_raw = str(ai_decision.get("regime", "ranging")).lower()
            regime = MarketRegime(regime_raw) if regime_raw in MarketRegime._value2member_map_ else MarketRegime.RANGING
            risk_score = int(ai_decision.get("risk_score", 3))
            ai_mult = float(ai_decision.get("size_multiplier", 1.0))
            reasoning = str(ai_decision.get("reasoning", ""))
            confidence = float(ai_decision.get("confidence", 1.0))

            # Update latest AI advisory state
            advisory_event = AIAdvisoryEvent(
                symbol=signal.symbol,
                timestamp=datetime.now(timezone.utc),
                regime=regime,
                risk_score=risk_score,
                trade_allowed=approved,
                size_multiplier=ai_mult,
                reasoning=reasoning,
                confidence=confidence
            )
            self.latest_ai_advisory = advisory_event

            # Persist to SQLite ai_advisory_logs table
            if self.db:
                try:
                    await self.db.save_ai_advisory(
                        symbol=signal.symbol,
                        regime=advisory_event.regime.value,
                        risk_score=advisory_event.risk_score,
                        trade_allowed=advisory_event.trade_allowed,
                        size_multiplier=advisory_event.size_multiplier,
                        reasoning=advisory_event.reasoning,
                        dt=advisory_event.timestamp,
                        confidence=confidence
                    )
                except Exception as e:
                    logger.warning(f"Failed to persist AI advisory log to SQLite (lock/concurrency): {e}")

            # Record in-memory audit logs for live web terminal if configured
            if self.audit_logs is not None:
                level = "WARNING" if ai_decision.get("fallback_used") else ("SUCCESS" if approved else "DANGER")
                self.audit_logs.append({
                    "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    "level": level,
                    "msg": f"AI Advisory [{signal.symbol} {signal.side.value}]: {reasoning}"
                })

            # Publish AI advisory to bus for monitoring & dashboard feeds
            await self.event_bus.publish(advisory_event)

            # Evaluate Veto Condition
            if not approved:
                rejection_reason = f"AI Advisory Veto: {reasoning}"
                logger.warning(f"[Risk Rejection] {rejection_reason}")
                await self._record_rejection(signal, rejection_reason)
                return None

            if regime == MarketRegime.EXTREME_VOLATILITY:
                rejection_reason = f"AI Advisory flagged Extreme Market Volatility: {reasoning}"
                logger.warning(f"[Risk Rejection] {rejection_reason}")
                await self._record_rejection(signal, rejection_reason)
                return None

        # =====================================================================
        # Phase 3: Position Sizing & Allocation
        # =====================================================================
        pos_key = f"{signal.strategy_name}_{signal.symbol}"
        is_new_entry = (signal.side == OrderSide.BUY) or (signal.side == OrderSide.SELL and pos_key not in self.open_positions and signal.stop_loss > 0)

        if is_new_entry:
            current_equity = self.circuit_breaker.current_equity or settings.STARTING_BALANCE_USDT
            max_alloc = current_equity * settings.MAX_POSITION_PERCENT
            # If in House Money mode (+10u target already secured), cap size multiplier to 0.2x
            if getattr(self.circuit_breaker, "house_money_mode", False):
                ai_mult = min(ai_mult, 0.2)
                logger.info("[House Money Sizing] Capping position allocation multiplier to 0.2x to safeguard +10u daily profit.")
            allocated_usdt = max_alloc * max(0.2, min(1.0, ai_mult))

            quantity = round(allocated_usdt / signal.price, 6)
            if quantity <= 0:
                reason = f"Calculated order quantity too small: {quantity}"
                logger.warning(f"[Risk Rejection] {reason}")
                await self._record_rejection(signal, reason)
                return None
        else:
            # SELL / Exit: Close existing position
            if pos_key in self.open_positions:
                quantity = self.open_positions[pos_key]["quantity"]
            else:
                quantity = 0.001  # Nominal fallback

        self.last_order_times[signal.symbol] = datetime.now(timezone.utc)

        # =====================================================================
        # Phase 4: Order Construction, Approval Recording & OrderEvent Emission
        # =====================================================================
        order_event = OrderEvent(
            order_id=str(uuid.uuid4())[:12],
            strategy_name=signal.strategy_name,
            symbol=signal.symbol,
            side=signal.side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=signal.price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            timestamp=datetime.now(timezone.utc),
            status=OrderStatus.PENDING
        )

        # Record approved signal in SQLite signals table with transient lock guard
        if self.db:
            try:
                await self.db.save_signal(
                    strategy_name=signal.strategy_name,
                    symbol=signal.symbol,
                    side=signal.side.value if hasattr(signal.side, "value") else str(signal.side),
                    price=signal.price,
                    sl=signal.stop_loss,
                    tp=signal.take_profit,
                    confidence=signal.confidence,
                    dt=signal.timestamp,
                    approved=True,
                    rejection_reason=""
                )

                # Record 10 Golden Questions Audit Trail (7-Day Adaptive Trading Test Doctrine)
                if hasattr(self.db, "save_golden_audit"):
                    max_risk = round(quantity * abs(signal.price - signal.stop_loss), 4)
                    side_val = signal.side.value if hasattr(signal.side, "value") else str(signal.side)
                    regime_val = ai_decision.get("regime", "TREND")
                    ai_reason = ai_decision.get("reasoning", "")
                    await self.db.save_golden_audit(
                        order_id=order_event.order_id,
                        symbol=signal.symbol,
                        side=side_val,
                        strategy_name=signal.strategy_name,
                        why_trade=f"Chiến lược {signal.strategy_name} kích hoạt {side_val} tại {signal.price}. Hội đồng phê duyệt với Conf={ai_decision.get('confidence', signal.confidence):.2f}. {ai_reason}",
                        why_asset=f"{signal.symbol} thỏa mãn cấu trúc xu hướng và xung lực thanh khoản trong rổ 8 tài sản theo dõi.",
                        why_direction=f"Vị thế {side_val} phù hợp với chế độ thị trường {regime_val} và xác nhận đa khung thời gian MTF.",
                        why_now=f"Điểm vào lệnh chuẩn xác tại giá ${signal.price:,.2f} với SL=${signal.stop_loss:,.2f} và TP=${signal.take_profit:,.2f}.",
                        evidence=f"Signal Conf: {signal.confidence:.2f} | AI Model: {ai_decision.get('model', 'Vyce AI')} | Regime: {regime_val}",
                        what_could_go_wrong=f"Thị trường quét thanh khoản hoặc đảo chiều vĩ mô vượt quá khoảng cách dừng lỗ {abs(signal.price - signal.stop_loss)/signal.price*100:.2f}%.",
                        opposing_argument=ai_decision.get("opposing_argument") or "Cảnh báo biến động ngược xu hướng hoặc rủi ro bẫy thanh khoản ngắn hạn.",
                        opposing_verdict_reason=ai_decision.get("opposing_verdict_reason") or "Tỷ lệ R:R hợp lệ và hành lang Stop Loss kỷ luật bảo vệ an toàn vốn.",
                        max_risk_usdt=max_risk,
                        what_actually_happened="Lệnh vừa được mở trên sàn, chịu sự giám sát tự động của Trailing Stop & Risk Gate.",
                        dt=signal.timestamp
                    )
            except Exception as e:
                logger.warning(f"Failed to persist approved signal or golden audit to SQLite (lock/concurrency): {e}")

        logger.info(
            f"[Risk Approved] Order {order_event.order_id}: {order_event.side.value} "
            f"{order_event.quantity} {order_event.symbol} @ {order_event.price} (AI Multiplier: {ai_mult})"
        )
        await self.event_bus.publish(order_event)
        return order_event

    def _execute_quantitative_fallback(self, signal: SignalEvent, reason: str) -> Dict[str, Any]:
        """
        Deterministic quantitative fallback executed in < 0.1ms when AI times out (> 3.0s) or fails.
        - SELL/Exit: Always approve (risk reduction).
        - BUY: Validate stop loss corridor and signal confidence, then de-rate position size to 50%.
        """
        if signal.side == OrderSide.SELL:
            return {
                "approved": True,
                "regime": "ranging",
                "risk_score": 2,
                "confidence": signal.confidence,
                "size_multiplier": 1.0,
                "reasoning": f"[AI Fallback Engaged: {reason}] Exit signal approved unconditionally to protect capital.",
                "model": "quantitative-fallback",
                "fallback_used": True
            }

        # BUY Signal Validation:
        # 1. Stop loss distance check: must be between 0.5% and 5.0% of entry price
        if signal.stop_loss <= 0 or signal.stop_loss >= signal.price:
            return {
                "approved": False,
                "regime": "ranging",
                "risk_score": 4,
                "confidence": signal.confidence,
                "size_multiplier": 0.0,
                "reasoning": f"[AI Fallback Engaged: {reason}] Rejection: Invalid Stop Loss ({signal.stop_loss} vs Price {signal.price}).",
                "model": "quantitative-fallback",
                "fallback_used": True
            }

        sl_dist_pct = (signal.price - signal.stop_loss) / signal.price
        if sl_dist_pct < 0.005 or sl_dist_pct > 0.05:
            return {
                "approved": False,
                "regime": "ranging",
                "risk_score": 4,
                "confidence": signal.confidence,
                "size_multiplier": 0.0,
                "reasoning": f"[AI Fallback Engaged: {reason}] Rejection: Stop Loss distance {sl_dist_pct*100:.2f}% outside safe corridor [0.5%, 5.0%].",
                "model": "quantitative-fallback",
                "fallback_used": True
            }

        # 2. Confidence threshold check: minimum 0.70 for fallback acceptance
        if signal.confidence < 0.70:
            return {
                "approved": False,
                "regime": "ranging",
                "risk_score": 3,
                "confidence": signal.confidence,
                "size_multiplier": 0.0,
                "reasoning": f"[AI Fallback Engaged: {reason}] Rejection: Signal confidence ({signal.confidence:.2f}) below safe threshold 0.70.",
                "model": "quantitative-fallback",
                "fallback_used": True
            }

        # 3. Approved with conservative 50% sizing de-rating
        return {
            "approved": True,
            "regime": "ranging",
            "risk_score": 3,
            "confidence": signal.confidence,
            "size_multiplier": 0.5,
            "reasoning": f"[AI Fallback Engaged: {reason}] Approved via Quantitative Baseline (SL corridor valid, Conf={signal.confidence:.2f}, Size=0.50x).",
            "model": "quantitative-fallback",
            "fallback_used": True
        }

    async def _record_rejection(self, signal: SignalEvent, reason: str) -> None:
        """Persist rejected signal and reason into SQLite signals table with transient lock guard."""
        if self.db:
            try:
                await self.db.save_signal(
                    strategy_name=signal.strategy_name,
                    symbol=signal.symbol,
                    side=signal.side.value if hasattr(signal.side, "value") else str(signal.side),
                    price=signal.price,
                    sl=signal.stop_loss,
                    tp=signal.take_profit,
                    confidence=signal.confidence,
                    dt=signal.timestamp,
                    approved=False,
                    rejection_reason=reason
                )
            except Exception as e:
                logger.warning(f"Failed to persist rejected signal to SQLite (lock/concurrency): {e}")
