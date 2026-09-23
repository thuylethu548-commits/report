import asyncio
import logging
from typing import Optional, Dict, Any
import ccxt

logger = logging.getLogger("FundingSentinel")


class FundingSentinel:
    """
    Monitors real-time Binance Futures Funding Rates to detect overcrowded retail positioning
    and protect the desk from Long/Short Liquidation Squeezes orchestrated by Market Makers.
    """
    def __init__(
        self,
        exchange: Optional[Any] = None,
        max_long_funding_pct: float = 0.03,    # Over 0.03% per 8h -> Long Squeeze danger
        max_short_funding_pct: float = -0.03,  # Below -0.03% per 8h -> Short Squeeze danger
        cache_ttl_seconds: int = 120           # Cache funding rate for 2 minutes
    ):
        self.exchange = exchange
        self.max_long_funding_pct = max_long_funding_pct
        self.max_short_funding_pct = max_short_funding_pct
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_exchange(self):
        if self.exchange:
            return self.exchange
        return ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})

    async def get_funding_rate(self, symbol: str) -> Optional[float]:
        """
        Fetches the current 8h funding rate percentage (e.g. 0.0100 for 0.01%).
        Utilizes an in-memory cache to avoid exchange rate limits.
        """
        import time
        now = time.time()
        cached = self._cache.get(symbol)
        if cached and (now - cached["timestamp"] < self.cache_ttl_seconds):
            return cached["rate_pct"]

        try:
            ex = self._get_exchange()
            # If exchange method is async or sync, handle appropriately
            if asyncio.iscoroutinefunction(getattr(ex, "fetch_funding_rate", None)):
                data = await ex.fetch_funding_rate(symbol)
            else:
                data = await asyncio.to_thread(ex.fetch_funding_rate, symbol)

            rate = data.get("fundingRate")
            if rate is not None:
                rate_pct = round(float(rate) * 100.0, 4)
                self._cache[symbol] = {"rate_pct": rate_pct, "timestamp": now}
                return rate_pct
        except Exception as e:
            logger.warning(f"Failed to fetch funding rate for {symbol}: {e}")
            if cached:
                return cached["rate_pct"]
        return None

    async def evaluate_squeeze_risk(self, symbol: str, side: str) -> Dict[str, Any]:
        """
        Evaluates whether entering a position aligns with an overcrowded market.
        Returns:
            {
                "safe": bool,
                "funding_rate_pct": float,
                "reason": str,
                "warning": Optional[str]
            }
        """
        rate_pct = await self.get_funding_rate(symbol)
        side_upper = side.upper()

        if rate_pct is None:
            # Fallback safe: Allow with default neutral rating
            return {
                "safe": True,
                "funding_rate_pct": 0.0,
                "reason": "Funding rate unavailable (neutral pass)",
                "warning": None
            }

        # 1. Overcrowded Long Danger
        if side_upper == "BUY" and rate_pct >= self.max_long_funding_pct:
            return {
                "safe": False,
                "funding_rate_pct": rate_pct,
                "reason": f"Funding Rate quá cao ({rate_pct:.4f}% >= {self.max_long_funding_pct}%) - Đám đông Long áp đảo, nguy cơ bẫy Long Squeeze quét râu xuống.",
                "warning": "HIGH_LONG_SQUEEZE_RISK"
            }

        # 2. Overcrowded Short Danger
        if side_upper == "SELL" and rate_pct <= self.max_short_funding_pct:
            return {
                "safe": False,
                "funding_rate_pct": rate_pct,
                "reason": f"Funding Rate quá âm ({rate_pct:.4f}% <= {self.max_short_funding_pct}%) - Đám đông Short áp đảo, nguy cơ Short Squeeze quét giá lên.",
                "warning": "HIGH_SHORT_SQUEEZE_RISK"
            }

        return {
            "safe": True,
            "funding_rate_pct": rate_pct,
            "reason": f"Funding Rate bình thường ({rate_pct:.4f}%), không có tín hiệu bẫy thanh lý.",
            "warning": None
        }
