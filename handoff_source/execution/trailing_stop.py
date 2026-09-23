import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from core.constants import OrderSide, round_price

logger = logging.getLogger("TrailingStopManager")


class TrailingStopState:
    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: OrderSide,
        entry_price: float,
        initial_stop_loss: float,
        initial_take_profit: float,
        quantity: float,
        break_even_threshold_pct: float = 0.015,   # +1.5% triggers Break-Even
        trailing_activation_pct: float = 0.020,     # +2.0% triggers Dynamic Trailing
        atr_multiplier: float = 1.2,
        entry_time: Optional[datetime] = None
    ):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.current_stop_loss = initial_stop_loss
        self.take_profit = initial_take_profit
        self.quantity = quantity
        self.highest_price = entry_price
        self.lowest_price = entry_price
        self.break_even_triggered = False
        self.trailing_triggered = False
        self.break_even_threshold_pct = break_even_threshold_pct
        self.trailing_activation_pct = trailing_activation_pct
        self.atr_multiplier = atr_multiplier
        self.entry_time = entry_time or datetime.now(timezone.utc)


class TrailingStopManager:
    """
    Production-grade Dynamic Trailing Stop & Break-Even Lock Manager.
    Guarantees that profitable trades lock capital and ride massive trends safely.
    """
    def __init__(self):
        self.positions: Dict[str, TrailingStopState] = {}

    def register_position(
        self,
        order_id: str,
        symbol: str,
        side: OrderSide,
        entry_price: float,
        initial_stop_loss: float,
        initial_take_profit: float,
        quantity: float,
        break_even_threshold_pct: float = 0.012,
        trailing_activation_pct: float = 0.020,
        atr_multiplier: float = 1.0,
        entry_time: Optional[datetime] = None
    ) -> TrailingStopState:
        state = TrailingStopState(
            order_id=order_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            initial_stop_loss=initial_stop_loss,
            initial_take_profit=initial_take_profit,
            quantity=quantity,
            break_even_threshold_pct=break_even_threshold_pct,
            trailing_activation_pct=trailing_activation_pct,
            atr_multiplier=atr_multiplier,
            entry_time=entry_time
        )
        self.positions[order_id] = state
        logger.info(f"[TrailingStop] Registered position {order_id} @ ${entry_price:,.2f}. SL: ${initial_stop_loss:,.2f}")
        return state

    def remove_position(self, order_id: str) -> None:
        if order_id in self.positions:
            del self.positions[order_id]

    def update_price(
        self,
        order_id: str,
        current_price: float,
        current_atr: float = 250.0
    ) -> Optional[Dict[str, Any]]:
        """
        Updates current market price for an open position and computes trailing/break-even adjustments.
        Returns a dict describing the adjustment if modified, or None.
        """
        state = self.positions.get(order_id)
        if not state or current_price <= 0:
            return None

        if state.side == OrderSide.BUY:
            state.highest_price = max(state.highest_price, current_price)
            pnl_pct = (current_price - state.entry_price) / state.entry_price

            # 1. Dynamic Trailing Stop check (+2.0% PnL)
            if pnl_pct >= state.trailing_activation_pct:
                state.trailing_triggered = True
                state.break_even_triggered = True
                effective_atr = current_atr if (0 < current_atr < state.entry_price * 0.05) else (current_price * 0.006)
                trailing_distance = effective_atr * state.atr_multiplier
                candidate_sl = round_price(state.highest_price - trailing_distance, state.entry_price)

                if candidate_sl > state.current_stop_loss:
                    old_sl = state.current_stop_loss
                    state.current_stop_loss = candidate_sl
                    logger.info(
                        f"[Trailing Stop Advance] New High ${state.highest_price:,.2f}. "
                        f"Advanced SL from ${old_sl:,.2f} to ${candidate_sl:,.2f}."
                    )
                    return {
                        "action": "TRAILING_STOP_ADVANCE",
                        "order_id": order_id,
                        "old_sl": old_sl,
                        "new_sl": candidate_sl,
                        "highest_price": state.highest_price,
                        "pnl_pct": round(pnl_pct * 100, 2),
                        "reason": f"Giá phá đỉnh ${state.highest_price:,.2f}, dời Trailing Stop bám theo {state.atr_multiplier:.1f}x ATR."
                    }

            # 2. Break-Even Stop check (+1.5% PnL)
            if not state.break_even_triggered and pnl_pct >= state.break_even_threshold_pct:
                # Move SL to Entry + 0.2% (fee buffer)
                new_sl = round_price(state.entry_price * 1.002, state.entry_price)
                if new_sl > state.current_stop_loss:
                    old_sl = state.current_stop_loss
                    state.current_stop_loss = new_sl
                    state.break_even_triggered = True
                    logger.info(
                        f"[Break-Even Lock] Position {order_id} reached +{pnl_pct*100:.2f}%. "
                        f"Moved SL to ${new_sl:,.2f} to guarantee ZERO RISK."
                    )
                    return {
                        "action": "BREAK_EVEN_LOCK",
                        "order_id": order_id,
                        "old_sl": old_sl,
                        "new_sl": new_sl,
                        "pnl_pct": round(pnl_pct * 100, 2),
                        "reason": f"Lãi đạt +{pnl_pct*100:.1f}%, dời Stop-Loss lên hòa vốn bảo toàn vốn."
                    }

        elif state.side == OrderSide.SELL:
            state.lowest_price = min(state.lowest_price, current_price)
            pnl_pct = (state.entry_price - current_price) / state.entry_price

            # 1. Dynamic Trailing Stop check (+2.0% PnL for SHORT)
            if pnl_pct >= state.trailing_activation_pct:
                state.trailing_triggered = True
                state.break_even_triggered = True
                effective_atr = current_atr if (0 < current_atr < state.entry_price * 0.05) else (current_price * 0.006)
                trailing_distance = effective_atr * state.atr_multiplier
                candidate_sl = round_price(state.lowest_price + trailing_distance, state.entry_price)

                # For SHORT, we move SL DOWN to protect profit
                if state.current_stop_loss <= 0 or candidate_sl < state.current_stop_loss:
                    old_sl = state.current_stop_loss
                    state.current_stop_loss = candidate_sl
                    logger.info(
                        f"[Trailing Stop Advance SHORT] New Low ${state.lowest_price:,.2f}. "
                        f"Lowered SL from ${old_sl:,.2f} to ${candidate_sl:,.2f}."
                    )
                    return {
                        "action": "TRAILING_STOP_ADVANCE",
                        "order_id": order_id,
                        "old_sl": old_sl,
                        "new_sl": candidate_sl,
                        "lowest_price": state.lowest_price,
                        "pnl_pct": round(pnl_pct * 100, 2),
                        "reason": f"Giá phá đáy ${state.lowest_price:,.2f}, hạ Trailing Stop bám theo {state.atr_multiplier:.1f}x ATR."
                    }

            # 2. Break-Even Stop check (+1.5% PnL for SHORT)
            if not state.break_even_triggered and pnl_pct >= state.break_even_threshold_pct:
                # Move SL to Entry - 0.2% (fee buffer below entry)
                new_sl = round_price(state.entry_price * 0.998, state.entry_price)
                if state.current_stop_loss <= 0 or new_sl < state.current_stop_loss:
                    old_sl = state.current_stop_loss
                    state.current_stop_loss = new_sl
                    state.break_even_triggered = True
                    logger.info(
                        f"[Break-Even Lock SHORT] Position {order_id} reached +{pnl_pct*100:.2f}%. "
                        f"Lowered SL to ${new_sl:,.2f} to guarantee ZERO RISK."
                    )
                    return {
                        "action": "BREAK_EVEN_LOCK",
                        "order_id": order_id,
                        "old_sl": old_sl,
                        "new_sl": new_sl,
                        "pnl_pct": round(pnl_pct * 100, 2),
                        "reason": f"Lãi đạt +{pnl_pct*100:.1f}%, hạ Stop-Loss xuống hòa vốn bảo toàn vốn."
                    }

        return None

    def check_dead_trade_timer(
        self,
        order_id: str,
        current_price: float,
        current_time: Optional[datetime] = None,
        max_hold_seconds: float = 7200.0
    ) -> Optional[Dict[str, Any]]:
        """
        Reddit r/algotrading Best Practice: Dead-Trade Timer.
        If a trade stalls for > max_hold_seconds (default 2h) without reaching TP,
        and is slightly profitable (+0.2% - +0.8%), lock in green PnL immediately.
        """
        state = self.positions.get(order_id)
        if not state or current_price <= 0:
            return None

        now_dt = current_time or datetime.now(timezone.utc)
        hold_seconds = (now_dt - state.entry_time).total_seconds()
        if hold_seconds >= max_hold_seconds:
            if state.side == OrderSide.BUY:
                pnl_pct = (current_price - state.entry_price) / state.entry_price if state.entry_price > 0 else 0.0
                if pnl_pct >= 0.002 and not state.break_even_triggered:
                    new_sl = round(state.entry_price * 1.001, 2)
                    if new_sl > state.current_stop_loss:
                        old_sl = state.current_stop_loss
                        state.current_stop_loss = new_sl
                        state.break_even_triggered = True
                        logger.info(
                            f"[Dead-Trade Timer BUY] Order {order_id} held for {round(hold_seconds/60)}m. "
                            f"Locked in profit SL: ${new_sl:,.2f}"
                        )
                        return {
                            "action": "DEAD_TRADE_PROFIT_LOCK",
                            "order_id": order_id,
                            "old_sl": old_sl,
                            "new_sl": new_sl,
                            "hold_minutes": round(hold_seconds / 60, 1),
                            "pnl_pct": round(pnl_pct * 100, 2),
                            "reason": f"Dead-Trade Timer ({round(hold_seconds/60)}p đi ngang): Khóa lãi dương ${new_sl:,.2f} bảo toàn vốn."
                        }
            elif state.side == OrderSide.SELL:
                pnl_pct = (state.entry_price - current_price) / state.entry_price if state.entry_price > 0 else 0.0
                if pnl_pct >= 0.002 and not state.break_even_triggered:
                    new_sl = round(state.entry_price * 0.999, 2)
                    if state.current_stop_loss <= 0 or new_sl < state.current_stop_loss:
                        old_sl = state.current_stop_loss
                        state.current_stop_loss = new_sl
                        state.break_even_triggered = True
                        logger.info(
                            f"[Dead-Trade Timer SHORT] Order {order_id} held for {round(hold_seconds/60)}m. "
                            f"Locked in profit SL: ${new_sl:,.2f}"
                        )
                        return {
                            "action": "DEAD_TRADE_PROFIT_LOCK",
                            "order_id": order_id,
                            "old_sl": old_sl,
                            "new_sl": new_sl,
                            "hold_minutes": round(hold_seconds / 60, 1),
                            "pnl_pct": round(pnl_pct * 100, 2),
                            "reason": f"Dead-Trade Timer ({round(hold_seconds/60)}p đi ngang): Khóa lãi dương ${new_sl:,.2f} bảo toàn vốn."
                        }

        return None


