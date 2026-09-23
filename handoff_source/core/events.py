from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from .constants import OrderSide, OrderType, OrderStatus, MarketRegime


@dataclass
class MarketEvent:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_candle_closed: bool = True


@dataclass
class SignalEvent:
    strategy_name: str
    symbol: str
    side: OrderSide
    price: float
    timestamp: datetime
    stop_loss: float
    take_profit: float
    confidence: float = 1.0
    force: bool = False


@dataclass
class AIAdvisoryEvent:
    symbol: str
    timestamp: datetime
    regime: MarketRegime
    risk_score: int  # 1 (Safe) to 5 (Extreme risk)
    trade_allowed: bool
    size_multiplier: float  # 0.0 to 1.0
    reasoning: str = ""
    confidence: float = 1.0


@dataclass
class OrderEvent:
    order_id: str
    strategy_name: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    status: OrderStatus = OrderStatus.PENDING
    reduce_only: bool = False


@dataclass
class FillEvent:
    order_id: str
    strategy_name: str
    symbol: str
    side: OrderSide
    fill_price: float
    quantity: float
    fee: float
    timestamp: datetime
    is_paper: bool = True
    reduce_only: bool = False
    position_id: str = ""
    position_side: Optional[OrderSide] = None


@dataclass
class TrailingStopEvent:
    order_id: str
    symbol: str
    action: str  # "BREAK_EVEN_LOCK" or "TRAILING_STOP_ADVANCE"
    old_sl: float
    new_sl: float
    current_price: float
    pnl_pct: float
    reason: str
    timestamp: datetime
