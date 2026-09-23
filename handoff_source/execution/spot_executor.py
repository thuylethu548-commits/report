import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any
from config.settings import settings
from core.constants import OrderSide
from core.events import MarketEvent
from core.event_bus import EventBus
from data.storage import Database

logger = logging.getLogger("SpotExecutor")

_default_spot_executor: Optional["SpotExecutor"] = None

def get_spot_executor(
    event_bus: Optional[EventBus] = None,
    db: Optional[Database] = None,
    binance_client: Optional[Any] = None
) -> "SpotExecutor":
    global _default_spot_executor
    if _default_spot_executor is None:
        _default_spot_executor = SpotExecutor(event_bus=event_bus, db=db, binance_client=binance_client)
    return _default_spot_executor



class SpotExecutor:
    """
    Spot Execution Engine:
    Handles non-leveraged Spot trading (Buy & Hold / Smart DCA) on Binance.
    Zero liquidation risk, zero funding fees, pure asset accumulation.
    """
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        db: Optional[Database] = None,
        binance_client: Optional[Any] = None
    ):
        self.event_bus = event_bus
        self.db = db
        self.binance_client = binance_client
        self.mode = settings.TRADING_MODE  # 'paper' or 'live'
        self.spot_balance_usdt = getattr(settings, "SPOT_STARTING_BALANCE_USDT", 500.0)
        self.holdings: Dict[str, Dict[str, float]] = {
            "BTC/USDT": {"amount": 0.0, "avg_price": 0.0, "cost": 0.0},
            "ETH/USDT": {"amount": 0.0, "avg_price": 0.0, "cost": 0.0},
            "SOL/USDT": {"amount": 0.0, "avg_price": 0.0, "cost": 0.0},
        }
        self.last_prices: Dict[str, float] = {}
        self.realized_pnl = 0.0
        self.total_spot_trades = 0

        global _default_spot_executor
        _default_spot_executor = self
        logger.info(f"SpotExecutor initialized in [{self.mode.upper()}] mode. Capital: {self.spot_balance_usdt:.2f} USDT")

    def update_price(self, symbol: str, price: float) -> None:
        self.last_prices[symbol] = price

    async def execute_spot_buy(self, symbol: str, usdt_amount: float, current_price: float, reason: str = "DCA_BUY") -> Dict[str, Any]:
        """Execute a spot purchase (accumulation)."""
        if usdt_amount > self.spot_balance_usdt:
            logger.warning(f"[Spot] Insufficient USDT ({self.spot_balance_usdt:.2f} < {usdt_amount:.2f}) to buy {symbol}")
            return {"success": False, "reason": "Insufficient Spot Balance"}

        coin_qty = round(usdt_amount / current_price, 6)
        fee = usdt_amount * 0.001  # 0.1% Binance spot fee
        net_usdt = usdt_amount + fee

        if self.mode == "live" and self.binance_client:
            try:
                # Live Binance Spot Market Order
                order = self.binance_client.create_market_buy_order(symbol, coin_qty)
                logger.info(f"[Spot LIVE BUY] {symbol} {coin_qty} @ ${current_price:.2f} | ID: {order.get('id')}")
            except Exception as e:
                logger.error(f"[Spot LIVE BUY ERROR] {e}")
                return {"success": False, "error": str(e)}

        # Update Paper/Internal Portfolio
        self.spot_balance_usdt -= net_usdt
        curr_hold = self.holdings.setdefault(symbol, {"amount": 0.0, "avg_price": 0.0, "cost": 0.0})
        total_qty = curr_hold["amount"] + coin_qty
        total_cost = curr_hold["cost"] + usdt_amount
        new_avg = total_cost / total_qty if total_qty > 0 else current_price

        curr_hold["amount"] = total_qty
        curr_hold["avg_price"] = new_avg
        curr_hold["cost"] = total_cost
        self.total_spot_trades += 1

        logger.info(f"[Spot BUY] {symbol} {coin_qty} @ ${current_price:.2f} (Total Hold: {total_qty:.6f}, Avg: ${new_avg:.2f}) | Remaining USDT: ${self.spot_balance_usdt:.2f}")

        # Record to database if available
        if self.db:
            try:
                order_id = f"spot-{symbol.replace('/', '')}-{int(datetime.now(timezone.utc).timestamp())}"
                await self.db.record_trade_open(
                    order_id=order_id,
                    strategy_name=f"Spot_DCA_{reason}",
                    symbol=symbol,
                    side="BUY",
                    price=current_price,
                    quantity=coin_qty,
                    fee=fee,
                    dt=datetime.now(timezone.utc),
                    is_paper=(self.mode == "paper")
                )
            except Exception as e:
                logger.error(f"[Spot DB Error] {e}")

        return {
            "success": True,
            "symbol": symbol,
            "side": "BUY",
            "quantity": coin_qty,
            "price": current_price,
            "remaining_usdt": self.spot_balance_usdt
        }

    async def execute_spot_sell(self, symbol: str, percent: float, current_price: float, reason: str = "TAKE_PROFIT") -> Dict[str, Any]:
        """Execute a spot sell (take profit)."""
        curr_hold = self.holdings.get(symbol, {"amount": 0.0, "avg_price": 0.0, "cost": 0.0})
        avail_qty = curr_hold["amount"]
        if avail_qty <= 0:
            return {"success": False, "reason": "No holdings to sell"}

        sell_qty = round(avail_qty * (percent / 100.0), 6)
        usdt_gross = sell_qty * current_price
        fee = usdt_gross * 0.001
        usdt_net = usdt_gross - fee

        cost_portion = curr_hold["avg_price"] * sell_qty
        pnl = usdt_net - cost_portion
        self.realized_pnl += pnl

        if self.mode == "live" and self.binance_client:
            try:
                order = self.binance_client.create_market_sell_order(symbol, sell_qty)
                logger.info(f"[Spot LIVE SELL] {symbol} {sell_qty} @ ${current_price:.2f} | PnL: +${pnl:.2f}")
            except Exception as e:
                logger.error(f"[Spot LIVE SELL ERROR] {e}")
                return {"success": False, "error": str(e)}

        # Update Portfolio
        self.spot_balance_usdt += usdt_net
        curr_hold["amount"] -= sell_qty
        curr_hold["cost"] -= cost_portion
        self.total_spot_trades += 1

        logger.info(f"[Spot SELL] {symbol} {sell_qty} @ ${current_price:.2f} | PnL: {pnl:+.2f} USDT | Remaining USDT: ${self.spot_balance_usdt:.2f}")

        if self.db:
            try:
                order_id = f"spot-sell-{symbol.replace('/', '')}-{int(datetime.now(timezone.utc).timestamp())}"
                await self.db.record_trade_open(
                    order_id=order_id,
                    strategy_name=f"Spot_{reason}",
                    symbol=symbol,
                    side="SELL",
                    price=current_price,
                    quantity=sell_qty,
                    fee=fee,
                    dt=datetime.now(timezone.utc),
                    is_paper=(self.mode == "paper")
                )
                await self.db.record_trade_close(
                    order_id=order_id,
                    exit_price=current_price,
                    fee=fee,
                    exit_time=datetime.now(timezone.utc),
                    pnl_usdt=pnl,
                    pnl_percent=(pnl / cost_portion * 100.0) if cost_portion > 0 else 0.0
                )
            except Exception as e:
                logger.error(f"[Spot DB Error] {e}")

        return {
            "success": True,
            "symbol": symbol,
            "side": "SELL",
            "quantity": sell_qty,
            "price": current_price,
            "pnl": pnl,
            "remaining_usdt": self.spot_balance_usdt
        }

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Return full Spot portfolio valuation and PnL."""
        total_val = self.spot_balance_usdt
        holdings_summary = []
        for sym, h in self.holdings.items():
            amt = h["amount"]
            if amt > 0:
                cur_price = self.last_prices.get(sym, h["avg_price"])
                cur_val = amt * cur_price
                unreal_pnl = cur_val - h["cost"]
                roi_pct = (unreal_pnl / h["cost"] * 100) if h["cost"] > 0 else 0.0
                total_val += cur_val
                holdings_summary.append({
                    "symbol": sym,
                    "amount": round(amt, 6),
                    "avg_price": round(h["avg_price"], 2),
                    "current_price": round(cur_price, 2),
                    "current_value": round(cur_val, 2),
                    "unrealized_pnl": round(unreal_pnl, 2),
                    "roi_percent": round(roi_pct, 2)
                })

        return {
            "mode": self.mode,
            "usdt_balance": round(self.spot_balance_usdt, 2),
            "total_portfolio_value": round(total_val, 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "total_trades": self.total_spot_trades,
            "holdings": holdings_summary
        }
