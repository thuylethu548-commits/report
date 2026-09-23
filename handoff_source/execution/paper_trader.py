import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any, Set
from config.settings import settings
from core.constants import OrderSide
from core.events import OrderEvent, FillEvent, MarketEvent, TrailingStopEvent
from core.event_bus import EventBus
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
from ai_advisory.vyce_client import VyceClient
from execution.trailing_stop import TrailingStopManager

logger = logging.getLogger("PaperTrader")


class PaperTrader:
    def __init__(
        self,
        event_bus: EventBus,
        db: Database,
        circuit_breaker: CircuitBreaker,
        vyce_client: Optional[VyceClient] = None,
        audit_logs: Optional[List[Dict[str, Any]]] = None,
        enabled: Optional[bool] = None
    ):
        self.event_bus = event_bus
        self.db = db
        self.circuit_breaker = circuit_breaker
        self.vyce_client = vyce_client or VyceClient()
        self.audit_logs = audit_logs
        self.enabled = enabled if enabled is not None else (settings.TRADING_MODE == "paper")
        self.balance_usdt = settings.STARTING_BALANCE_USDT
        self.base_asset_balance = 0.0  # e.g. BTC
        self.open_positions: Dict[str, dict] = {}
        self.fee_rate = 0.001  # 0.1% Binance spot fee
        self.last_price = 0.0
        self.last_prices: Dict[str, float] = {}
        self._background_tasks: Set[asyncio.Task] = set()
        self.trailing_manager = TrailingStopManager()

        # Subscribe to approved Orders and Market ticks
        self.event_bus.subscribe(OrderEvent, self.handle_order)
        self.event_bus.subscribe(MarketEvent, self.handle_market_tick)

    async def sync_open_positions_from_db(self) -> None:
        """Synchronize in-memory open positions with active OPEN trades in SQLite database on startup."""
        if not self.db:
            return
        try:
            trades = await self.db.get_recent_trades(limit=100)
            count = 0
            for t in trades:
                if t.get("status") == "OPEN":
                    pos_key = f"{t.get('strategy_name')}_{t.get('symbol')}"
                    side_raw = t.get("side", "BUY")
                    side = OrderSide.BUY if side_raw.upper() == "BUY" else OrderSide.SELL
                    entry_p = float(t.get("entry_price") or 0.0)
                    qty = float(t.get("quantity") or 0.0)
                    self.open_positions[pos_key] = {
                        "order_id": t.get("order_id"),
                        "strategy_name": t.get("strategy_name"),
                        "symbol": t.get("symbol"),
                        "side": side,
                        "entry_price": entry_p,
                        "quantity": qty,
                        "stop_loss": 0.0,
                        "take_profit": 0.0,
                        "entry_time": t.get("entry_time"),
                        "fee": float(t.get("fee") or 0.0)
                    }
                    self.trailing_manager.register_position(
                        order_id=t.get("order_id"),
                        symbol=t.get("symbol"),
                        side=side,
                        entry_price=entry_p,
                        initial_stop_loss=0.0,
                        initial_take_profit=0.0,
                        quantity=qty
                    )
                    count += 1
            logger.info(f"[PaperTrader] Synced {count} active open position(s) from database into memory.")
        except Exception as e:
            logger.warning(f"[PaperTrader] Could not sync open positions from database: {e}")

    async def handle_market_tick(self, event: MarketEvent) -> None:
        self.last_prices[event.symbol] = event.close
        if event.symbol == "BTC/USDT":
            self.last_price = event.close

        # Update equity & check Take-Profit / Stop-Loss ONLY for positions matching this event's symbol
        positions_to_close = []

        for pos_id, pos in list(self.open_positions.items()):
            if pos.get("symbol") != event.symbol:
                continue

            symbol_price = event.close
            pos_side = pos.get("side", OrderSide.BUY)

            if pos_side == OrderSide.BUY:
                # Dynamic Trailing Stop & Break-Even Evaluation
                ts_adj = self.trailing_manager.update_price(
                    order_id=pos["order_id"],
                    current_price=symbol_price
                )
                if ts_adj:
                    pos["stop_loss"] = ts_adj["new_sl"]
                    action_name = ts_adj["action"]
                    logger.info(f"[Trailing Stop BUY] {action_name} for {pos['order_id']}: SL moved to ${ts_adj['new_sl']:,.2f}")
                    if self.audit_logs is not None:
                        self.audit_logs.append({
                            "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                            "level": "SUCCESS",
                            "msg": f"🔒 {action_name} ({pos['symbol']}): Dời SL lên ${ts_adj['new_sl']:,.2f} ({ts_adj['reason']})"
                        })
                    ts_event = TrailingStopEvent(
                        order_id=pos["order_id"],
                        symbol=pos["symbol"],
                        action=action_name,
                        old_sl=ts_adj["old_sl"],
                        new_sl=ts_adj["new_sl"],
                        current_price=symbol_price,
                        pnl_pct=ts_adj["pnl_pct"],
                        reason=ts_adj["reason"],
                        timestamp=datetime.now(timezone.utc)
                    )
                    await self.event_bus.publish(ts_event)

                # Check Stop Loss trigger
                if pos["stop_loss"] > 0 and symbol_price <= pos["stop_loss"]:
                    logger.warning(f"[Paper Stop Loss Hit BUY] Order {pos_id} at price {symbol_price}")
                    positions_to_close.append((pos_id, "STOP_LOSS"))

                # Check Take Profit trigger
                elif pos["take_profit"] > 0 and symbol_price >= pos["take_profit"]:
                    logger.info(f"[Paper Take Profit Hit BUY] Order {pos_id} at price {symbol_price}")
                    positions_to_close.append((pos_id, "TAKE_PROFIT"))

            elif pos_side == OrderSide.SELL:
                # Dynamic Trailing Stop & Break-Even Evaluation for SHORT
                ts_adj = self.trailing_manager.update_price(
                    order_id=pos["order_id"],
                    current_price=symbol_price
                )
                if ts_adj:
                    pos["stop_loss"] = ts_adj["new_sl"]
                    action_name = ts_adj["action"]
                    logger.info(f"[Trailing Stop SHORT] {action_name} for {pos['order_id']}: SL moved to ${ts_adj['new_sl']:,.2f}")
                    if self.audit_logs is not None:
                        self.audit_logs.append({
                            "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                            "level": "SUCCESS",
                            "msg": f"🔒 {action_name} ({pos['symbol']}): Hạ SL xuống ${ts_adj['new_sl']:,.2f} ({ts_adj['reason']})"
                        })
                    ts_event = TrailingStopEvent(
                        order_id=pos["order_id"],
                        symbol=pos["symbol"],
                        action=action_name,
                        old_sl=ts_adj["old_sl"],
                        new_sl=ts_adj["new_sl"],
                        current_price=symbol_price,
                        pnl_pct=ts_adj["pnl_pct"],
                        reason=ts_adj["reason"],
                        timestamp=datetime.now(timezone.utc)
                    )
                    await self.event_bus.publish(ts_event)

                # Check Stop Loss trigger (for SHORT: price rises above SL)
                if pos["stop_loss"] > 0 and symbol_price >= pos["stop_loss"]:
                    logger.warning(f"[Paper Stop Loss Hit SHORT] Order {pos_id} at price {symbol_price}")
                    positions_to_close.append((pos_id, "STOP_LOSS"))

                # Check Take Profit trigger (for SHORT: price falls below TP)
                elif pos["take_profit"] > 0 and symbol_price <= pos["take_profit"]:
                    logger.info(f"[Paper Take Profit Hit SHORT] Order {pos_id} at price {symbol_price}")
                    positions_to_close.append((pos_id, "TAKE_PROFIT"))

        # Calculate portfolio unrealized PnL across all active positions
        total_unrealized_pnl = 0.0
        for p in self.open_positions.values():
            sym = p.get("symbol")
            if sym in self.last_prices:
                cur_p = self.last_prices[sym]
                if p.get("side") == OrderSide.BUY:
                    total_unrealized_pnl += (cur_p - p.get("entry_price", cur_p)) * p.get("quantity", 0.0)
                else:
                    total_unrealized_pnl += (p.get("entry_price", cur_p) - cur_p) * p.get("quantity", 0.0)

        if settings.TRADING_MODE == "paper":
            current_equity = self.balance_usdt + total_unrealized_pnl
            self.circuit_breaker.update_equity(self.balance_usdt, current_equity)

        # Close any TP/SL positions
        for pos_id, reason in positions_to_close:
            pos_info = self.open_positions.get(pos_id, {})
            sym_price = self.last_prices.get(pos_info.get("symbol", ""), event.close)
            await self._close_position(pos_id, sym_price, reason)

    @staticmethod
    def _calc_fill_price(price: float, slippage_multiplier: float) -> float:
        raw = price * slippage_multiplier
        if price >= 100:
            return round(raw, 2)
        elif price >= 1:
            return round(raw, 4)
        elif price >= 0.001:
            return round(raw, 6)
        else:
            return round(raw, 8)

    async def handle_order(self, order: OrderEvent) -> None:
        if settings.TRADING_MODE != "paper":
            return

        # Simulate small random slippage (0.01% - 0.03%)
        slippage_pct = random.uniform(0.0001, 0.0003)
        if order.side == OrderSide.BUY:
            fill_price = self._calc_fill_price(order.price, 1.0 + slippage_pct)
            cost = fill_price * order.quantity
            fee = cost * self.fee_rate
            leverage = getattr(settings, "FUTURES_LEVERAGE", 1) if getattr(settings, "MARKET_TYPE", "spot") == "futures" else 1
            margin_required = cost / max(leverage, 1)

            if self.balance_usdt < (margin_required + fee):
                logger.warning(f"[Paper Reject] Insufficient USDT balance (${self.balance_usdt:.2f}) for cost (${margin_required + fee:.2f})")
                return

            self.balance_usdt -= (margin_required + fee)
            self.base_asset_balance += order.quantity

            pos_key = f"{order.strategy_name}_{order.symbol}"
            self.open_positions[pos_key] = {
                "order_id": order.order_id,
                "strategy_name": order.strategy_name,
                "symbol": order.symbol,
                "side": order.side,
                "entry_price": fill_price,
                "quantity": order.quantity,
                "stop_loss": order.stop_loss,
                "take_profit": order.take_profit,
                "entry_time": datetime.now(timezone.utc),
                "fee": fee,
                "margin": margin_required,
                "leverage": leverage
            }

            self.trailing_manager.register_position(
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                entry_price=fill_price,
                initial_stop_loss=order.stop_loss,
                initial_take_profit=order.take_profit,
                quantity=order.quantity
            )

            await self.db.record_trade_open(
                order_id=order.order_id,
                strategy_name=order.strategy_name,
                symbol=order.symbol,
                side=order.side.value,
                price=fill_price,
                quantity=order.quantity,
                fee=fee,
                dt=datetime.now(timezone.utc),
                is_paper=True
            )

            fill_event = FillEvent(
                order_id=order.order_id,
                strategy_name=order.strategy_name,
                symbol=order.symbol,
                side=order.side,
                fill_price=fill_price,
                quantity=order.quantity,
                fee=fee,
                timestamp=datetime.now(timezone.utc),
                is_paper=True
            )
            logger.info(f"[Paper Fill BUY] {order.quantity} {order.symbol} @ {fill_price} | Fee: ${fee:.4f} | Remaining USDT: ${self.balance_usdt:.2f}")
            await self.event_bus.publish(fill_event)

        elif order.side == OrderSide.SELL:
            pos_key = f"{order.strategy_name}_{order.symbol}"
            if pos_key in self.open_positions and self.open_positions[pos_key].get("side") == OrderSide.BUY:
                await self._close_position(pos_key, order.price, "STRATEGY_EXIT")
            else:
                # Open a SHORT position (Futures 2-way mode)
                fill_price = self._calc_fill_price(order.price, 1.0 - slippage_pct)
                leverage = getattr(settings, "FUTURES_LEVERAGE", 3)
                notional = fill_price * order.quantity
                margin_required = round(notional / leverage, 4)
                fee = round(notional * self.fee_rate, 4)

                if self.balance_usdt < (margin_required + fee):
                    logger.warning(f"[Paper Reject SHORT] Insufficient USDT margin (${self.balance_usdt:.2f}) for margin (${margin_required + fee:.2f})")
                    return

                self.balance_usdt -= (margin_required + fee)

                self.open_positions[pos_key] = {
                    "order_id": order.order_id,
                    "strategy_name": order.strategy_name,
                    "symbol": order.symbol,
                    "side": OrderSide.SELL,
                    "entry_price": fill_price,
                    "quantity": order.quantity,
                    "stop_loss": order.stop_loss,
                    "take_profit": order.take_profit,
                    "entry_time": datetime.now(timezone.utc),
                    "fee": fee,
                    "margin": margin_required,
                    "leverage": leverage
                }

                self.trailing_manager.register_position(
                    order_id=order.order_id,
                    symbol=order.symbol,
                    side=OrderSide.SELL,
                    entry_price=fill_price,
                    initial_stop_loss=order.stop_loss,
                    initial_take_profit=order.take_profit,
                    quantity=order.quantity
                )

                await self.db.record_trade_open(
                    order_id=order.order_id,
                    strategy_name=order.strategy_name,
                    symbol=order.symbol,
                    side=OrderSide.SELL.value,
                    price=fill_price,
                    quantity=order.quantity,
                    fee=fee,
                    dt=datetime.now(timezone.utc),
                    is_paper=True
                )

                fill_event = FillEvent(
                    order_id=order.order_id,
                    strategy_name=order.strategy_name,
                    symbol=order.symbol,
                    side=OrderSide.SELL,
                    fill_price=fill_price,
                    quantity=order.quantity,
                    fee=fee,
                    timestamp=datetime.now(timezone.utc),
                    is_paper=True
                )
                logger.info(f"[Paper Fill SHORT] {order.quantity} {order.symbol} @ {fill_price} (Lev {leverage}x) | Fee: ${fee:.4f} | Remaining USDT: ${self.balance_usdt:.2f}")
                await self.event_bus.publish(fill_event)

    async def _close_position(self, pos_key: str, exit_price: float, reason: str) -> None:
        if pos_key not in self.open_positions:
            return

        pos = self.open_positions.pop(pos_key)
        self.trailing_manager.remove_position(pos.get("order_id", ""))
        pos_copy = dict(pos)
        pos_side = pos.get("side", OrderSide.BUY)

        if pos_side == OrderSide.BUY:
            # Apply exit slippage (sell lower) with multi-decimal precision
            fill_price = self._calc_fill_price(exit_price, 1.0 - random.uniform(0.0001, 0.0003))
            gross_return = fill_price * pos["quantity"]
            exit_fee = gross_return * self.fee_rate
            net_return = gross_return - exit_fee
            self.base_asset_balance = max(0.0, self.base_asset_balance - pos["quantity"])

            if "margin" in pos:
                margin = pos["margin"]
                gross_pnl = (fill_price - pos["entry_price"]) * pos["quantity"]
                pnl_usdt = round(gross_pnl - pos.get("fee", 0.0) - exit_fee, 4)
                self.balance_usdt += max(0.0, margin + pnl_usdt)
                cost_basis = margin
            else:
                self.balance_usdt += net_return
                pnl_usdt = round(net_return - (pos["entry_price"] * pos["quantity"]) - pos.get("fee", 0.0), 4)
                cost_basis = pos["entry_price"] * pos["quantity"]

            total_fees = pos["fee"] + exit_fee
            pnl_pct = round((pnl_usdt / cost_basis) * 100.0, 2) if cost_basis > 0 else 0.0
            close_side = OrderSide.SELL
        else:
            # Closing SHORT (buy back to cover) with multi-decimal precision
            fill_price = self._calc_fill_price(exit_price, 1.0 + random.uniform(0.0001, 0.0003))
            notional = fill_price * pos["quantity"]
            exit_fee = notional * self.fee_rate
            gross_pnl = (pos["entry_price"] - fill_price) * pos["quantity"]
            pnl_usdt = round(gross_pnl - pos.get("fee", 0.0) - exit_fee, 4)
            margin = pos.get("margin", (pos["entry_price"] * pos["quantity"]) / pos.get("leverage", 1))
            self.balance_usdt += max(0.0, margin + pnl_usdt)
            cost_basis = margin
            pnl_pct = round((pnl_usdt / cost_basis) * 100.0, 2) if cost_basis > 0 else 0.0
            close_side = OrderSide.BUY

        await self.db.record_trade_close(
            order_id=pos["order_id"],
            exit_price=fill_price,
            fee=exit_fee,
            exit_time=datetime.now(timezone.utc),
            pnl_usdt=pnl_usdt,
            pnl_percent=pnl_pct
        )

        if hasattr(self.db, "update_golden_audit_outcome"):
            outcome_msg = (
                f"Chốt lệnh tại ${fill_price:,.2f} với PnL {pnl_usdt:+.4f} USDT ({pnl_pct:+.2f}%). "
                f"Trailing Stop / TP khớp thành công."
            )
            try:
                await self.db.update_golden_audit_outcome(pos["order_id"], outcome_msg)
            except Exception:
                pass

        fill_event = FillEvent(
            order_id=pos["order_id"],
            strategy_name=pos["strategy_name"],
            symbol=pos["symbol"],
            side=close_side,
            fill_price=fill_price,
            quantity=pos["quantity"],
            fee=exit_fee,
            timestamp=datetime.now(timezone.utc),
            is_paper=True
        )

        logger.info(f"[Paper Close {reason}] {pos['symbol']} @ {fill_price} | PnL: ${pnl_usdt:.4f} ({pnl_pct:+.2f}%) | Total USDT: ${self.balance_usdt:.2f}")
        await self.event_bus.publish(fill_event)

        # Trigger auto post-mortem on Stop-Loss, severe drawdown, or severe slippage
        sl_threshold = -abs(settings.STOP_LOSS_PERCENT * 100)
        is_sl_reason = reason == "STOP_LOSS"
        is_severe_drawdown = pnl_pct <= sl_threshold
        is_severe_slippage = reason in ("SLIPPAGE", "SEVERE_SLIPPAGE") or (
            exit_price > 0 and ((exit_price - fill_price) / exit_price) >= 0.005
        )

        if is_sl_reason or is_severe_drawdown or is_severe_slippage:
            task = asyncio.create_task(
                self._trigger_auto_post_mortem(pos_copy, fill_price, pnl_usdt, pnl_pct, reason)
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    async def _trigger_auto_post_mortem(
        self,
        pos: dict,
        exit_price: float,
        pnl_usdt: float,
        pnl_pct: float,
        reason: str
    ) -> Optional[int]:
        """
        Non-blocking background task: queries Claude-3.5-Sonnet (via Vyce AI)
        for forensic analysis and persists lesson into SQLite trading_lessons.
        """
        try:
            entry_time = pos.get("entry_time")
            if isinstance(entry_time, datetime):
                hold_duration = (datetime.now(timezone.utc) - entry_time).total_seconds()
            else:
                hold_duration = 0.0

            trade_info = {
                "order_id": pos.get("order_id", ""),
                "symbol": pos.get("symbol", settings.SYMBOL),
                "strategy_name": pos.get("strategy_name", "Unknown"),
                "entry_price": float(pos.get("entry_price", 0.0)),
                "exit_price": float(exit_price),
                "quantity": float(pos.get("quantity", 0.0)),
                "pnl_usdt": float(pnl_usdt),
                "pnl_percent": float(pnl_pct),
                "hold_duration_seconds": round(max(0.0, hold_duration), 1),
                "reason": reason
            }

            post_mortem = await self.vyce_client.generate_post_mortem(trade_info)

            category = post_mortem.get("category") or ("SLIPPAGE" if reason in ("SLIPPAGE", "SEVERE_SLIPPAGE") else "STOP_LOSS")
            title = post_mortem.get("title") or f"Dừng lỗ {trade_info['symbol']} bảo toàn vốn"
            details = post_mortem.get("details") or f"Vị thế {trade_info['symbol']} đóng tại {exit_price:.2f} do chạm {reason}."
            capital_impact = float(post_mortem.get("capital_impact") if post_mortem.get("capital_impact") is not None else abs(pnl_usdt))
            lesson_learned = post_mortem.get("lesson_learned") or "Tuân thủ kỷ luật cắt lỗ tự động để bảo vệ an toàn vốn."
            operator = post_mortem.get("operator") or "Claude-3.5-Sonnet"

            lesson_id = await self.db.add_lesson(
                category=category,
                title=title,
                details=details,
                capital_impact=capital_impact,
                lesson_learned=lesson_learned,
                operator=operator
            )

            logger.info(
                f"[Auto Post-Mortem] Generated lesson #{lesson_id} for order {trade_info['order_id']}: '{title}'"
            )

            if self.audit_logs is not None:
                self.audit_logs.append({
                    "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    "level": "CRITICAL" if abs(pnl_usdt) > 5.0 else "WARNING",
                    "msg": f"Auto Post-Mortem đúc kết bài học #{lesson_id} ({category}): '{title}'"
                })

            return lesson_id
        except Exception as e:
            logger.error(
                f"[Auto Post-Mortem Error] Failed to generate/record lesson for order {pos.get('order_id')}: {e}",
                exc_info=True
            )
            return None

    async def close(self, timeout: float = 5.0) -> None:
        """Gracefully awaits any in-flight background post-mortem tasks before shutdown."""
        if self._background_tasks:
            logger.info(f"Waiting for {len(self._background_tasks)} background post-mortem task(s) to finish...")
            done, pending = await asyncio.wait(self._background_tasks, timeout=timeout)
            for t in pending:
                t.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
