import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger("CircuitBreaker")


class CircuitBreaker:
    def __init__(
        self,
        max_daily_drawdown_percent: float = 0.07,
        target_daily_profit_usd: float = 10.0,
        max_daily_loss_usd: float = 3.5,
        house_money_mode_enabled: bool = True
    ):
        self.max_daily_drawdown = max_daily_drawdown_percent
        self.target_daily_profit_usd = target_daily_profit_usd
        self.max_daily_loss_usd = max_daily_loss_usd
        self.house_money_mode_enabled = house_money_mode_enabled

        self.day_start_balance = 0.0
        self.current_balance = 0.0
        self.current_equity = 0.0
        self.daily_realized_pnl = 0.0

        self.is_tripped = False
        self.trip_reason = ""
        self.is_profit_locked = False
        self.house_money_mode = False
        self.last_reset_date = datetime.now(timezone.utc).date()

    @property
    def current_drawdown(self) -> float:
        if self.day_start_balance > 0 and self.current_equity > 0:
            dd = (self.day_start_balance - self.current_equity) / self.day_start_balance
            return max(0.0, dd * 100)
        return 0.0

    def reset_daily_metrics(self, current_balance: float, force: bool = False) -> None:
        today = datetime.now(timezone.utc).date()
        if force or today > self.last_reset_date or self.day_start_balance <= 0.0:
            self.day_start_balance = current_balance
            self.current_balance = current_balance
            self.current_equity = current_balance
            self.daily_realized_pnl = 0.0
            self.is_tripped = False
            self.trip_reason = ""
            self.is_profit_locked = False
            self.house_money_mode = False
            self.last_reset_date = today
            logger.info(
                f"[CircuitBreaker] Daily metrics reset. Start Balance: ${self.day_start_balance:.2f} | "
                f"Target Profit: +${self.target_daily_profit_usd:.2f} | Max Loss: -${self.max_daily_loss_usd:.2f}"
            )

    def add_realized_pnl(self, pnl: float) -> None:
        """Records realized PnL from a closed trade and evaluates daily sprint limits."""
        self.daily_realized_pnl += pnl
        logger.info(
            f"[CircuitBreaker] Realized PnL update: trade={pnl:+.4f} USDT | "
            f"Daily Total={self.daily_realized_pnl:+.4f} USDT (Target: +${self.target_daily_profit_usd:.2f}, Limit: -${self.max_daily_loss_usd:.2f})"
        )

        # 1. Check Target Profit Reached (+10 USDT)
        if self.daily_realized_pnl >= self.target_daily_profit_usd:
            self.is_profit_locked = True
            if self.house_money_mode_enabled:
                self.house_money_mode = True
                logger.info(
                    f"[TARGET REACHED] Daily profit {self.daily_realized_pnl:+.2f} USDT reached target +${self.target_daily_profit_usd:.2f}! "
                    f"Switching to HOUSE MONEY MODE (size multiplier 0.2x, maximum capital preservation)."
                )
            else:
                self.trip_reason = f"Daily profit target +${self.target_daily_profit_usd:.2f} achieved! Trading locked to preserve gains."
                logger.info(f"[CIRCUIT BREAKER LOCK] {self.trip_reason}")

        # 2. Check Daily Max Loss Reached (-3.5 USDT)
        elif self.daily_realized_pnl <= -self.max_daily_loss_usd and not self.is_tripped:
            self.is_tripped = True
            self.trip_reason = (
                f"Daily realized loss {self.daily_realized_pnl:+.2f} USDT breached limit -${self.max_daily_loss_usd:.2f}! "
                f"ALL TRADING FROZEN FOR 24H TO PRESERVE CAPITAL."
            )
            logger.critical(f"[CIRCUIT BREAKER TRIPPED] {self.trip_reason}")

    def update_equity(self, balance: float, equity: float) -> bool:
        """
        Updates account balance and equity. Checks drawdown.
        Returns True if breaker is OK, False if TRIPPED.
        """
        if self.day_start_balance <= 0.0:
            self.day_start_balance = balance

        self.current_balance = balance
        self.current_equity = equity

        # Check daily drawdown against day_start_balance
        if self.day_start_balance > 0:
            drawdown = (self.day_start_balance - self.current_equity) / self.day_start_balance
            if drawdown >= self.max_daily_drawdown and not self.is_tripped:
                self.is_tripped = True
                self.trip_reason = f"Daily drawdown {drawdown * 100:.2f}% breached maximum allowed {self.max_daily_drawdown * 100:.2f}%."
                logger.error(f"[CIRCUIT BREAKER TRIPPED] {self.trip_reason} - ALL TRADING FROZEN.")
                return False

        return not self.is_tripped

    def trigger_emergency_kill(self, reason: str = "Manual Emergency Kill Triggered") -> None:
        self.is_tripped = True
        self.trip_reason = reason
        logger.critical(f"[EMERGENCY KILL SWITCH ACTIVATED] Reason: {reason}")

    def reset_circuit(self, new_balance: float = None) -> None:
        self.is_tripped = False
        self.trip_reason = ""
        self.is_profit_locked = False
        self.house_money_mode = False
        self.daily_realized_pnl = 0.0
        if new_balance is not None and new_balance > 0:
            self.day_start_balance = new_balance
            self.current_balance = new_balance
            self.current_equity = new_balance
        logger.info(f"[CIRCUIT BREAKER RESET] Circuit breaker manually reset. Is tripped: {self.is_tripped}")
