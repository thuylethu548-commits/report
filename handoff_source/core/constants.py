from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class MarketRegime(str, Enum):
    BULL_TREND = "bull_trend"
    BEAR_TREND = "bear_trend"
    RANGING = "ranging"
    EXTREME_VOLATILITY = "extreme_volatility"
    UNKNOWN = "unknown"


class TradingMode(str, Enum):
    PAPER = "paper"
    TESTNET = "testnet"
    LIVE = "live"


def round_price(val: float, ref_price: float | None = None) -> float:
    """Format and round price according to order of magnitude (BTC vs Alt vs Meme coins)."""
    ref = abs(ref_price) if ref_price is not None and ref_price != 0 else abs(val)
    if ref >= 100.0:
        return round(val, 2)
    elif ref >= 1.0:
        return round(val, 4)
    elif ref >= 0.01:
        return round(val, 5)
    else:
        return round(val, 7)

