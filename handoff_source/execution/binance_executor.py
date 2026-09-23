import asyncio
import hashlib
import math
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any, Set
from config.settings import settings
from core.constants import OrderSide, OrderType, OrderStatus, round_price
from core.events import OrderEvent, FillEvent, MarketEvent, TrailingStopEvent
from core.event_bus import EventBus
from data.binance_client import BinanceClient
from data.storage import Database
from ai_advisory.vyce_client import VyceClient
from execution.trailing_stop import TrailingStopManager

logger = logging.getLogger("BinanceExecutor")


class BinanceExecutor:
    def __init__(
        self,
        event_bus: EventBus,
        binance_client: BinanceClient,
        db: Database,
        vyce_client: Optional[VyceClient] = None,
        audit_logs: Optional[List[Dict[str, Any]]] = None
    ):
        self.event_bus = event_bus
        self.client = binance_client
        self.db = db
        self.vyce_client = vyce_client or VyceClient()
        self.audit_logs = audit_logs
        self.open_positions: Dict[str, dict] = {}
        self._symbol_locks = {}
        self._submitted_ids = set()
        self._uncertain_symbols = set()
        self.entries_blocked = False
        self._closing = set()
        self._state_loaded = False
        self._reconciled = False
        self._state_lock = asyncio.Lock()
        self._execution_lock = asyncio.Lock()
        self._pending = {}
        self._background_tasks: Set[asyncio.Task] = set()
        self.trailing_manager = TrailingStopManager()
        self._candle_history: Dict[str, List[tuple]] = {}
        self._sync_task: Optional[asyncio.Task] = None

        if settings.TRADING_MODE in ("live", "testnet"):
            self._sync_task = asyncio.create_task(self._periodic_sync_worker())

        # Subscribe to approved Orders and Market ticks
        self.event_bus.subscribe(OrderEvent, self.handle_order)
        self.event_bus.subscribe(MarketEvent, self.handle_market_tick)

    async def _periodic_sync_worker(self) -> None:
        """Periodic background task to sync open and closed positions from Binance."""
        while True:
            try:
                await asyncio.sleep(20)
                await self.sync_open_positions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.entries_blocked = True
                logger.debug(f"[Periodic Sync Worker Error] {e}")
                await asyncio.sleep(5)

    @staticmethod
    def _symbol(symbol: str) -> str:
        symbol = symbol.split(":")[0].upper()
        if "/" not in symbol:
            for quote in ("USDT", "USDC"):
                if symbol.endswith(quote):
                    return symbol[:-len(quote)] + "/" + quote
        return symbol

    def _find_position(self, symbol: str):
        symbol = self._symbol(symbol)
        return next(((k, p) for k, p in self.open_positions.items()
                     if self._symbol(p["symbol"]) == symbol), (None, None))

    async def _persist(self):
        async with self._state_lock:
            positions = {}
            for key, pos in self.open_positions.items():
                value = dict(pos)
                value["side"] = pos["side"].value
                value["entry_time"] = pos["entry_time"].isoformat()
                state = self.trailing_manager.positions.get(pos["order_id"])
                if state:
                    value["trailing"] = {name: getattr(state, name) for name in (
                        "current_stop_loss", "highest_price", "lowest_price",
                        "break_even_triggered", "trailing_triggered")}
                positions[key] = value
            await self.db.save_execution_state({
                "positions": positions, "pending": self._pending,
                "entries_blocked": self.entries_blocked,
                "uncertain_symbols": sorted(self._uncertain_symbols),
                "submitted_ids": sorted(self._submitted_ids)})

    async def _restore(self):
        if self._state_loaded:
            return
        saved = await self.db.load_execution_state()
        self._pending = saved.get("pending", {})
        self._submitted_ids.update(saved.get("submitted_ids", []))
        self._uncertain_symbols.update(saved.get("uncertain_symbols", []))
        self._uncertain_symbols.update(item["symbol"] for item in self._pending.values())
        self.entries_blocked = bool(saved.get("entries_blocked") or self._pending)
        for key, value in saved.get("positions", {}).items():
            pos = dict(value)
            trailing = pos.pop("trailing", {})
            pos["side"] = OrderSide(pos["side"])
            pos["entry_time"] = datetime.fromisoformat(pos["entry_time"])
            self.open_positions[key] = pos
            state = self.trailing_manager.register_position(
                order_id=pos["order_id"], symbol=pos["symbol"], side=pos["side"],
                entry_price=pos["entry_price"], initial_stop_loss=pos["stop_loss"],
                initial_take_profit=pos["take_profit"], quantity=pos["quantity"],
                entry_time=pos["entry_time"])
            for name, field_value in trailing.items():
                setattr(state, name, field_value)
        self._state_loaded = True

    async def _protect(self, pos: dict) -> None:
        """Create the replacement before retiring the old reduce-only stop."""
        if settings.MARKET_TYPE != "futures":
            raise RuntimeError("This executor safety revision requires one-way futures")
        stop = float(pos["stop_loss"])
        if not math.isfinite(stop) or stop <= 0:
            raise RuntimeError("Position has no protective stop")
        old_id = pos.get("protective_order_id")
        if old_id and pos.get("protected_stop") == stop and pos.get("protected_quantity") == pos["quantity"]:
            return
        response = await self.client.create_order(
            symbol=pos["symbol"], order_type="STOP_MARKET",
            side="sell" if pos["side"] == OrderSide.BUY else "buy",
            amount=pos["quantity"],
            params={"stopPrice": stop, "reduceOnly": True, "workingType": "MARK_PRICE"})
        if not response.get("id") or response.get("status") != "open":
            raise RuntimeError("Exchange did not acknowledge protective stop")
        pos["protective_order_id"] = str(response["id"])
        pos["protected_stop"] = stop
        pos["protected_quantity"] = pos["quantity"]
        if old_id:
            try:
                await self.client.cancel_protective_order(old_id, pos["symbol"])
            except Exception:
                self.entries_blocked = True
                logger.warning("Old reduce-only stop cancellation requires reconciliation", exc_info=True)

    async def _fill_fee(self, result, symbol):
        fee = result.get("fee") or {}
        quote = self._symbol(symbol).split("/")[-1]
        if fee.get("cost") is not None and fee.get("currency") == quote:
            cost = float(fee["cost"])
        else:
            cost = await self.client.fetch_order_fee(result, self._symbol(symbol))
        if not math.isfinite(cost):
            raise RuntimeError("Invalid commission")
        return cost

    async def handle_order(self, order: OrderEvent) -> Optional[dict]:
        async with self._execution_lock:
            return await self._handle_order(order)

    async def _handle_order(self, order: OrderEvent) -> Optional[dict]:
        if settings.TRADING_MODE == "paper":
            return None
        if not self._reconciled:
            raise RuntimeError("Startup reconciliation required before execution")
        symbol = self._symbol(order.symbol)
        if not math.isfinite(float(order.quantity)) or order.quantity <= 0:
            raise ValueError("Invalid order quantity")
        lock = self._symbol_locks.setdefault(symbol, asyncio.Lock())
        async with lock:
            if order.order_id in self._submitted_ids:
                return None
            key, pos = self._find_position(symbol)
            closing = order.reduce_only or order.order_id.startswith("exit_")
            # Legacy strategy exits have no SL. Never infer a short entry from those.
            if not closing and pos and order.side != pos["side"] and order.stop_loss <= 0:
                closing = True
            if symbol in self._uncertain_symbols:
                raise RuntimeError(f"Execution outcome unresolved for {symbol}; reconcile before retry")
            if closing:
                if pos is None:
                    return None
                expected_side = OrderSide.SELL if pos["side"] == OrderSide.BUY else OrderSide.BUY
                if order.side != expected_side:
                    raise ValueError("Exit side does not reduce the tracked position")
                quantity = min(float(order.quantity), float(pos["quantity"]))
            else:
                if self.entries_blocked:
                    raise RuntimeError("New entries blocked pending operator reconciliation")
                if pos:
                    raise ValueError("One-way executor allows only one position per symbol")
                if len(self.open_positions) >= settings.MAX_OPEN_POSITIONS:
                    raise ValueError("Maximum open positions reached")
                if not all(math.isfinite(float(v)) for v in (order.price, order.quantity, order.stop_loss)):
                    raise ValueError("Non-finite order input")
                if order.price <= 0 or order.quantity <= 0:
                    raise ValueError("Invalid entry price or quantity")
                valid_sl = (0 < order.stop_loss < order.price if order.side == OrderSide.BUY
                            else order.stop_loss > order.price)
                if not valid_sl or abs(order.price - order.stop_loss) / order.price > settings.STOP_LOSS_PERCENT + 1e-9:
                    raise ValueError("Entry violates mandatory hard stop distance")
                quantity = min(order.quantity, settings.LIVE_MAX_USDT_PER_ORDER / order.price)

            # Exchange filters are authoritative. Do not round a small order UP past its risk budget.
            await self.client.load_markets()
            ex = self.client.exchange
            market_symbol = self.client.market_symbol(order.symbol)
            quantity = float(ex.amount_to_precision(market_symbol, quantity))
            market = ex.market(market_symbol)
            limits = market.get("limits", {})
            if quantity <= 0 or (not closing and (
                    quantity < (limits.get("amount", {}).get("min") or 0) or
                    quantity * order.price < (limits.get("cost", {}).get("min") or 0))):
                raise ValueError("Order is below exchange minimum; entry not enlarged")
            params = {"newOrderRespType": "RESULT", "newClientOrderId": "astra-" + hashlib.sha256(
                order.order_id.encode()).hexdigest()[:24]}
            if closing:
                params["reduceOnly"] = True
            self._submitted_ids.add(order.order_id)
            self._pending[order.order_id] = {"symbol": symbol, "client_order_id": params["newClientOrderId"]}
            await self._persist()
            try:
                result = await self.client.create_order(
                    symbol=order.symbol, order_type="market", side=order.side.value.lower(),
                    amount=quantity, params=params)
            except Exception:
                # Timeout does not prove rejection. Never submit another order blindly.
                self._uncertain_symbols.add(symbol)
                self.entries_blocked = True
                await self._persist()
                raise
            try:
                filled = float(result.get("filled") or 0)
                price = float(result.get("average") or result.get("price") or 0)
                if not all(math.isfinite(v) for v in (filled, price)) or filled <= 0 or price <= 0 or filled > quantity + 1e-10 or result.get("status") not in ("closed", "canceled", "expired"):
                    self._uncertain_symbols.add(symbol)
                    self.entries_blocked = True
                    raise RuntimeError("Fill incomplete or unconfirmed; exchange reconciliation required")
                fee_data = result.get("fee") or {}
                fee = float(fee_data.get("cost") or 0)
                if closing:
                    fee = await self._fill_fee(result, symbol)
                    pos_copy = dict(pos)
                    original_quantity = pos["quantity"]
                    if filled > original_quantity + 1e-10:
                        raise RuntimeError("Exit fill exceeds tracked exposure")
                    allocation = pos["fee"] * filled / original_quantity
                    direction = 1 if pos["side"] == OrderSide.BUY else -1
                    pnl = direction * (price - pos["entry_price"]) * filled - fee - allocation
                    remaining = max(0.0, original_quantity - filled)
                    result["realized_pnl"] = pnl
                    result["remaining_quantity"] = remaining
                    await self.db.record_trade_reduction(
                        position_id=pos["order_id"], exit_order_id=str(result["id"]),
                        exit_price=price, quantity=filled, remaining=remaining,
                        fee=fee, pnl_usdt=pnl, dt=datetime.now(timezone.utc))
                    position_id, position_side = pos["order_id"], pos["side"]
                    pos["quantity"] = remaining
                    pos["fee"] -= allocation
                    if remaining <= 1e-10:
                        self.open_positions.pop(key, None)
                        self.trailing_manager.remove_position(position_id)
                        if pos.get("protective_order_id"):
                            try:
                                await self.client.cancel_protective_order(pos["protective_order_id"], pos["symbol"])
                            except Exception:
                                self.entries_blocked = True
                                logger.warning("Closed position stop cancellation failed", exc_info=True)
                    else:
                        self.trailing_manager.positions[position_id].quantity = remaining
                        await self._protect(pos)
                    if remaining <= 1e-10 and pnl >= 0:
                        if hasattr(self.db, "update_golden_audit_outcome"):
                            outcome_msg = f"Chốt lời thành công tại ${price:,.2f} với PnL +${pnl:.4f} USDT (+{100 * pnl / (pos_copy['entry_price'] * filled):.2f}%). Trailing Stop / TP bảo toàn lợi nhuận."
                            asyncio.create_task(self.db.update_golden_audit_outcome(pos_copy["order_id"], outcome_msg))

                    if pnl < 0:
                        task = asyncio.create_task(self._trigger_auto_post_mortem(
                            pos_copy, price, pnl, 100 * pnl / (pos_copy["entry_price"] * filled), "STOP_LOSS"))
                        self._background_tasks.add(task)
                        task.add_done_callback(self._background_tasks.discard)
                else:
                    position_id, position_side = str(result["id"]), order.side
                    pos = {
                        "order_id": position_id, "strategy_name": order.strategy_name,
                        "symbol": symbol, "side": order.side, "entry_price": price,
                        "quantity": filled, "stop_loss": (
                            max(order.stop_loss, price * (1 - settings.STOP_LOSS_PERCENT))
                            if order.side == OrderSide.BUY else
                            min(order.stop_loss, price * (1 + settings.STOP_LOSS_PERCENT))),
                        "take_profit": order.take_profit,
                        "entry_time": datetime.now(timezone.utc), "fee": fee}
                    self.open_positions[symbol] = pos
                    self.trailing_manager.register_position(
                        order_id=position_id, symbol=symbol, side=order.side,
                        entry_price=price, initial_stop_loss=pos["stop_loss"],
                        initial_take_profit=order.take_profit, quantity=filled,
                        entry_time=pos["entry_time"])
                    await self.db.record_trade_open(
                        order_id=position_id, strategy_name=order.strategy_name,
                        symbol=symbol, side=order.side.value, price=price, quantity=filled,
                        fee=fee, dt=pos["entry_time"], is_paper=False)
                    await self._persist()
                    try:
                        await self._protect(pos)
                    except Exception:
                        # A stop timeout may have succeeded; a reduce-only rescue cannot reverse exposure.
                        self.entries_blocked = True
                        await self._flatten_unprotected(pos)
                        raise
                    fee = await self._fill_fee(result, symbol)
                    pos["fee"] = fee
                    await self.db.set_open_trade_fee(position_id, fee)
                self._pending.pop(order.order_id, None)
                await self._persist()
                await self.event_bus.publish(FillEvent(
                    order_id=str(result["id"]), strategy_name=order.strategy_name,
                    symbol=symbol, side=order.side, fill_price=price, quantity=filled,
                    fee=fee, timestamp=datetime.now(timezone.utc), is_paper=False,
                    reduce_only=closing, position_id=position_id, position_side=position_side))
                return result
            except Exception:
                self.entries_blocked = True
                self._uncertain_symbols.add(symbol)
                await self._persist()
                logger.critical("Execution/protection/accounting requires reconciliation", exc_info=True)
                raise

    async def _flatten_unprotected(self, pos):
        result = await self.client.create_order(
            symbol=pos["symbol"], order_type="market",
            side="sell" if pos["side"] == OrderSide.BUY else "buy",
            amount=pos["quantity"], params={"reduceOnly": True, "newOrderRespType": "RESULT",
                "newClientOrderId": "astra-rescue-" + hashlib.sha256(pos["order_id"].encode()).hexdigest()[:20]})
        filled = float(result.get("filled") or 0)
        price = float(result.get("average") or result.get("price") or 0)
        if result.get("status") != "closed" or filled <= 0 or price <= 0:
            raise RuntimeError("Unprotected rescue close is unconfirmed; manual reconciliation required")
        remaining = max(0.0, pos["quantity"] - filled)
        fee = await self._fill_fee(result, pos["symbol"])
        allocated = pos["fee"] * min(1.0, filled / pos["quantity"])
        direction = 1 if pos["side"] == OrderSide.BUY else -1
        await self.db.record_trade_reduction(
            position_id=pos["order_id"], exit_order_id=str(result["id"]),
            exit_price=price, quantity=filled, remaining=remaining, fee=fee,
            pnl_usdt=direction * (price - pos["entry_price"]) * filled - fee - allocated,
            dt=datetime.now(timezone.utc))
        pos["quantity"] = remaining
        pos["fee"] -= allocated
        if remaining <= 1e-10:
            key, _ = self._find_position(pos["symbol"])
            self.open_positions.pop(key, None)
            self.trailing_manager.remove_position(pos["order_id"])
        await self._persist()

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
            title = post_mortem.get("title") or f"Dừng lỗ Live {trade_info['symbol']} bảo toàn vốn"
            details = post_mortem.get("details") or f"Vị thế {trade_info['symbol']} đóng tại {exit_price:.2f} do chạm {reason}."
            capital_impact = float(post_mortem.get("capital_impact") if post_mortem.get("capital_impact") is not None else abs(pnl_usdt))
            lesson_learned = post_mortem.get("lesson_learned") or "Bảo toàn vốn và tuân thủ kỷ luật dừng lỗ trong giao dịch thực tế."
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
                f"[Auto Post-Mortem Live] Generated lesson #{lesson_id} for order {trade_info['order_id']}: '{title}'"
            )

            if self.audit_logs is not None:
                self.audit_logs.append({
                    "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    "level": "CRITICAL" if abs(pnl_usdt) > 5.0 else "WARNING",
                    "msg": f"Auto Post-Mortem Live đúc kết bài học #{lesson_id} ({category}): '{title}'"
                })

            return lesson_id
        except Exception as e:
            logger.error(
                f"[Auto Post-Mortem Live Error] Failed to record lesson for order {pos.get('order_id')}: {e}",
                exc_info=True
            )
            return None

    def _calculate_atr(self, symbol: str, event: MarketEvent, period: int = 14) -> float:
        symbol = self._symbol(symbol)
        history = self._candle_history.setdefault(symbol, [])
        h = float(getattr(event, "high", event.close))
        l = float(getattr(event, "low", event.close))
        c = float(event.close)
        
        if getattr(event, "is_candle_closed", True):
            history.append((h, l, c))
            if len(history) > period + 10:
                history.pop(0)

        if len(history) < 3:
            return c * 0.008

        trs = []
        for i in range(1, len(history)):
            prev_close = history[i - 1][2]
            cur_h, cur_l, _ = history[i]
            tr = max(cur_h - cur_l, abs(cur_h - prev_close), abs(cur_l - prev_close))
            trs.append(tr)

        recent_trs = trs[-period:]
        return sum(recent_trs) / len(recent_trs) if recent_trs else c * 0.008

    async def handle_market_tick(self, event: MarketEvent) -> None:
        if settings.TRADING_MODE == "paper" or not self._reconciled:
            return
        price = float(event.close)
        if not math.isfinite(price) or price <= 0:
            return
        close_request = None
        async with self._execution_lock:
            _, pos = self._find_position(event.symbol)
            if not pos:
                return
            state = self.trailing_manager.positions.get(pos["order_id"])
            if not state:
                self.entries_blocked = True
                await self._persist()
                return
            previous = dict(vars(state))
            # Compute live 14-period ATR for dynamic trailing stop
            atr = self._calculate_atr(event.symbol, event)
            adjustment = self.trailing_manager.update_price(pos["order_id"], price, current_atr=atr)
            if not adjustment:
                adjustment = self.trailing_manager.check_dead_trade_timer(
                    pos["order_id"], price, current_time=datetime.now(timezone.utc))
            if adjustment:
                old_stop = pos["stop_loss"]
                pos["stop_loss"] = adjustment["new_sl"]
                try:
                    await self._protect(pos)
                except Exception:
                    # Keep the last acknowledged stop. Do not announce an unconfirmed improvement.
                    pos["stop_loss"] = old_stop
                    for name, value in previous.items():
                        setattr(state, name, value)
                    self.entries_blocked = True
                    logger.critical("Protective stop replacement unconfirmed", exc_info=True)
                else:
                    await self.event_bus.publish(TrailingStopEvent(
                        order_id=pos["order_id"], symbol=pos["symbol"],
                        action=adjustment["action"], old_sl=adjustment["old_sl"],
                        new_sl=adjustment["new_sl"], current_price=price,
                        pnl_pct=adjustment["pnl_pct"], reason=adjustment["reason"],
                        timestamp=datetime.now(timezone.utc)))
            long = pos["side"] == OrderSide.BUY
            sl_hit = pos["stop_loss"] > 0 and (price <= pos["stop_loss"] if long else price >= pos["stop_loss"])
            tp_hit = pos.get("take_profit", 0) > 0 and (price >= pos["take_profit"] if long else price <= pos["take_profit"])
            if sl_hit or tp_hit:
                close_request = (pos, price, "STOP_LOSS" if sl_hit else "TAKE_PROFIT")
            # Save peaks and entry clock even when the stop did not change.
            await self._persist()
        if close_request:
            await self._emergency_market_close(*close_request)

    async def _emergency_market_close(self, pos: dict, current_price: float, reason: str) -> Optional[dict]:
        identity = pos["order_id"]
        if identity in self._closing:
            return None
        self._closing.add(identity)
        try:
            return await self.handle_order(OrderEvent(
                order_id=f"exit_{identity}_{pos['quantity']}",
                strategy_name=pos["strategy_name"], symbol=pos["symbol"],
                side=OrderSide.SELL if pos["side"] == OrderSide.BUY else OrderSide.BUY,
                order_type=OrderType.MARKET, quantity=pos["quantity"],
                price=current_price, stop_loss=0.0, take_profit=0.0,
                timestamp=datetime.now(timezone.utc), reduce_only=True))
        finally:
            self._closing.discard(identity)

    async def sync_open_positions(self) -> None:
        async with self._execution_lock:
            await self._sync_open_positions()

    async def _sync_open_positions(self) -> None:
        """Reconcile quantity without resetting stops, peak price, or entry time."""
        await self._restore()
        mode = await self.client.fetch_position_mode()
        if mode.get("hedged") is not False:
            self.entries_blocked = True
            raise RuntimeError("Confirmed one-way position mode required")
        positions = await self.client.fetch_positions()
        active = {}
        for p in positions:
            if p.get("hedged") or p.get("info", {}).get("positionSide", "BOTH") != "BOTH":
                self.entries_blocked = True
                raise RuntimeError("Hedge mode is not supported by this executor")
            qty = abs(float(p.get("contracts") or 0))
            if qty > 0:
                symbol = self._symbol(p["symbol"])
                if symbol in active:
                    self.entries_blocked = True
                    raise RuntimeError("Multiple exchange positions for the same symbol")
                active[symbol] = p
        for symbol in set(active) | {self._symbol(p["symbol"]) for p in self.open_positions.values()}:
            async with self._symbol_locks.setdefault(symbol, asyncio.Lock()):
                key, pos = self._find_position(symbol)
                remote = active.get(symbol)
                if not remote:
                    if pos:
                        # Position closed externally on Binance (e.g. TP/SL triggered on exchange)
                        self.open_positions.pop(key, None)
                        self.trailing_manager.remove_position(pos["order_id"])
                        try:
                            market_sym = self.client.market_symbol(symbol)
                            recent_trades = await self.client.exchange.fetch_my_trades(market_sym, limit=5)
                            exit_price = pos["entry_price"]
                            pnl_usdt = 0.0
                            exit_time = datetime.now(timezone.utc)
                            if recent_trades:
                                last_t = recent_trades[-1]
                                exit_price = float(last_t.get("price") or exit_price)
                                pnl_usdt = float(last_t.get("info", {}).get("realizedPnl") or 0.0)
                                if last_t.get("datetime"):
                                    exit_time = datetime.fromisoformat(last_t["datetime"].replace("Z", "+00:00"))
                            pnl_pct = ((exit_price - pos["entry_price"]) / pos["entry_price"] * 100) if pos["entry_price"] > 0 else 0.0
                            if pos["side"] == OrderSide.SELL:
                                pnl_pct = -pnl_pct
                            await self.db.record_trade_close(
                                order_id=pos["order_id"],
                                exit_price=exit_price,
                                fee=0.0,
                                exit_time=exit_time,
                                pnl_usdt=pnl_usdt,
                                pnl_percent=pnl_pct
                            )
                            logger.info("Auto-reconciled external close for %s in DB ledger: exit=%s, pnl=%s", symbol, exit_price, pnl_usdt)
                        except Exception as close_err:
                            logger.warning("Could not auto-close trade record for %s: %s", symbol, close_err)
                        self.entries_blocked = False
                    continue
                qty = abs(float(remote["contracts"]))
                side = OrderSide.BUY if remote["side"] == "long" else OrderSide.SELL
                entry = float(remote["entryPrice"])
                if pos:
                    if pos["side"] != side or abs(pos["entry_price"] - entry) > max(1e-8, entry * 1e-8):
                        self.entries_blocked = True
                        raise RuntimeError(f"External position change for {symbol}; reconciliation required")
                    if abs(pos["quantity"] - qty) > 1e-10:
                        self.entries_blocked = True
                        logger.warning("External quantity change for %s; ledger reconciliation required", symbol)
                    pos["quantity"] = qty
                    state = self.trailing_manager.positions.get(pos["order_id"])
                    if state:
                        state.quantity = qty
                    if pos.get("protective_order_id"):
                        protective = await self.client.fetch_protective_order(pos["protective_order_id"], symbol)
                        if protective.get("status") != "open":
                            self.entries_blocked = True
                            raise RuntimeError("Protective stop not confirmed open; reconciliation required")
                    await self._protect(pos)
                else:
                    # Check if this position matches a known OPEN trade in the database ledger
                    open_trade = None
                    try:
                        async with self.db._conn.cursor() as cur:
                            await cur.execute("SELECT * FROM trades WHERE symbol = ? AND status = 'OPEN' AND is_paper = 0 ORDER BY entry_time DESC LIMIT 1", (symbol,))
                            row = await cur.fetchone()
                            if row:
                                open_trade = dict(row)
                    except Exception as e:
                        logger.warning("Failed to query open trade for %s: %s", symbol, e)

                    if open_trade and abs(float(open_trade.get("quantity") or 0) - qty) <= 1e-6:
                        logger.info("Auto-adopting known open trade %s for %s (%s contracts at %s)", open_trade["order_id"], symbol, qty, entry)
                        sl = round_price(entry * (1 - settings.STOP_LOSS_PERCENT), 2) if side == OrderSide.BUY else round_price(entry * (1 + settings.STOP_LOSS_PERCENT), 2)
                        tp = round_price(entry * 1.03, 2) if side == OrderSide.BUY else round_price(entry * 0.97, 2)
                        entry_dt = datetime.fromisoformat(open_trade["entry_time"]) if open_trade.get("entry_time") else datetime.now(timezone.utc)
                        pos = {
                            "order_id": open_trade["order_id"],
                            "symbol": symbol,
                            "side": side,
                            "quantity": qty,
                            "entry_price": entry,
                            "stop_loss": sl,
                            "take_profit": tp,
                            "entry_time": entry_dt,
                            "fee": float(open_trade.get("fee") or 0.0)
                        }
                        self.open_positions[symbol] = pos
                        self.trailing_manager.register_position(
                            order_id=pos["order_id"], symbol=symbol, side=side,
                            entry_price=entry, initial_stop_loss=sl,
                            initial_take_profit=tp, quantity=qty,
                            entry_time=entry_dt
                        )
                        try:
                            await self._protect(pos)
                        except Exception as pe:
                            logger.warning("Could not set protective stop for adopted %s: %s", symbol, pe)
                        self.entries_blocked = False
                    else:
                        # Auto-adopt any untracked position from exchange to prevent system freeze
                        logger.warning("Auto-adopting untracked position %s (%s contracts at %s) to prevent system stall", symbol, qty, entry)
                        sl = round_price(entry * (1 - settings.STOP_LOSS_PERCENT), 2) if side == OrderSide.BUY else round_price(entry * (1 + settings.STOP_LOSS_PERCENT), 2)
                        tp = round_price(entry * 1.03, 2) if side == OrderSide.BUY else round_price(entry * 0.97, 2)
                        entry_dt = datetime.now(timezone.utc)
                        order_id = f"adopt-{symbol.replace('/', '')}-{int(entry_dt.timestamp())}"
                        pos = {
                            "order_id": order_id,
                            "symbol": symbol,
                            "side": side,
                            "quantity": qty,
                            "entry_price": entry,
                            "stop_loss": sl,
                            "take_profit": tp,
                            "entry_time": entry_dt,
                            "fee": 0.0
                        }
                        self.open_positions[symbol] = pos
                        self.trailing_manager.register_position(
                            order_id=pos["order_id"], symbol=symbol, side=side,
                            entry_price=entry, initial_stop_loss=sl,
                            initial_take_profit=tp, quantity=qty,
                            entry_time=entry_dt
                        )
                        try:
                            await self.db.record_trade_open(
                                order_id=order_id, strategy_name="AutoAdopted",
                                symbol=symbol, side=side.value, price=entry, quantity=qty,
                                fee=0.0, dt=entry_dt, is_paper=False
                            )
                        except Exception as de:
                            logger.warning("Could not record trade open for adopted %s: %s", symbol, de)
                        try:
                            await self._protect(pos)
                        except Exception as pe:
                            logger.warning("Could not set protective stop for adopted %s: %s", symbol, pe)
                        self.entries_blocked = False
        self._pending.clear()
        self._uncertain_symbols.clear()
        self.entries_blocked = False
        self._reconciled = True
        await self._persist()

    async def close_position_market(self, symbol: str, reason: str = "MANUAL_OPERATOR_CLOSE") -> Optional[dict]:
        _, pos = self._find_position(symbol)
        if not pos:
            return None
        ticker = await self.client.fetch_ticker(pos["symbol"])
        result = await self._emergency_market_close(pos, float(ticker.get("last") or 0), reason)
        if not result:
            return None
        return {"status": "SUCCESS", "symbol": symbol,
                "fill_price": result.get("average"), "reason": reason,
                "pnl_usdt": result.get("realized_pnl"),
                "remaining_quantity": result.get("remaining_quantity", 0)}

    async def close(self, timeout: float = 5.0) -> None:
        """Gracefully stop synchronization and outstanding work."""
        if self._sync_task:
            self._sync_task.cancel()
            await asyncio.gather(self._sync_task, return_exceptions=True)
        if self._background_tasks:
            logger.info(f"Waiting for {len(self._background_tasks)} background post-mortem task(s) to finish...")
            done, pending = await asyncio.wait(self._background_tasks, timeout=timeout)
            for t in pending:
                t.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
