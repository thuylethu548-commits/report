import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger("MultiTimeframeFilter")


class MultiTimeframeFilter:
    """
    Multi-Timeframe Trend Confluence Engine (15m execution + 1h + 4h Macro Trend).
    Protects capital by vetoing any BUY signal unless higher timeframes confirm the bullish trend:
    Condition: Price > EMA(50) on 1h AND Price > EMA(50) on 4h.
    Eliminates fakeouts and bear-market bull traps.
    """
    def __init__(self, ema_period: int = 50, max_candles: int = 200):
        self.ema_period = ema_period
        self.max_candles = max_candles
        self.candles_1h: List[Dict[str, float]] = []
        self.candles_4h: List[Dict[str, float]] = []
        self.symbol_candles_1h: Dict[str, List[Dict[str, float]]] = {}
        self.symbol_candles_4h: Dict[str, List[Dict[str, float]]] = {}

    def set_candles(self, timeframe: str, raw_candles: Union[List[List[Any]], List[Dict[str, Any]]], symbol: Optional[str] = None) -> None:
        """Sets historical candles for a specific timeframe ('1h' or '4h')."""
        parsed: List[Dict[str, float]] = []
        for c in raw_candles:
            if isinstance(c, list) and len(c) >= 5:
                parsed.append({
                    "timestamp": float(c[0]),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5]) if len(c) > 5 else 0.0
                })
            elif isinstance(c, dict):
                parsed.append({
                    "timestamp": float(c.get("timestamp", 0)),
                    "open": float(c.get("open", 0)),
                    "high": float(c.get("high", 0)),
                    "low": float(c.get("low", 0)),
                    "close": float(c.get("close", 0)),
                    "volume": float(c.get("volume", 0))
                })

        if timeframe.lower() in ("1h", "60m"):
            self.candles_1h = parsed[-self.max_candles:]
            if symbol:
                self.symbol_candles_1h[symbol] = parsed[-self.max_candles:]
        elif timeframe.lower() in ("4h", "240m"):
            self.candles_4h = parsed[-self.max_candles:]
            if symbol:
                self.symbol_candles_4h[symbol] = parsed[-self.max_candles:]

    def add_candle(self, timeframe: str, candle: Union[List[Any], Dict[str, Any]]) -> None:
        """Appends a new closed candle to the corresponding timeframe buffer."""
        parsed: Optional[Dict[str, float]] = None
        if isinstance(candle, list) and len(candle) >= 5:
            parsed = {
                "timestamp": float(candle[0]),
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]) if len(candle) > 5 else 0.0
            }
        elif isinstance(candle, dict):
            parsed = {
                "timestamp": float(candle.get("timestamp", 0)),
                "open": float(candle.get("open", 0)),
                "high": float(candle.get("high", 0)),
                "low": float(candle.get("low", 0)),
                "close": float(candle.get("close", 0)),
                "volume": float(candle.get("volume", 0))
            }

        if parsed is None:
            return

        if timeframe.lower() in ("1h", "60m"):
            self.candles_1h.append(parsed)
            if len(self.candles_1h) > self.max_candles:
                self.candles_1h.pop(0)
        elif timeframe.lower() in ("4h", "240m"):
            self.candles_4h.append(parsed)
            if len(self.candles_4h) > self.max_candles:
                self.candles_4h.pop(0)

    def calculate_ema(self, timeframe: str, symbol: Optional[str] = None) -> Optional[float]:
        """Calculates current EMA(50) for the given timeframe and symbol."""
        if symbol and timeframe.lower() in ("1h", "60m") and symbol in self.symbol_candles_1h:
            candles = self.symbol_candles_1h[symbol]
        elif symbol and timeframe.lower() in ("4h", "240m") and symbol in self.symbol_candles_4h:
            candles = self.symbol_candles_4h[symbol]
        else:
            candles = self.candles_1h if timeframe.lower() in ("1h", "60m") else self.candles_4h

        if len(candles) < 5:  # Need at least a few candles to compute baseline
            return None

        closes = [c["close"] for c in candles]
        series = pd.Series(closes)
        ema_series = series.ewm(span=self.ema_period, adjust=False).mean()
        val = float(ema_series.iloc[-1])
        return round(val, 2) if not np.isnan(val) else None

    def check_confluence(self, symbol: str, current_price: float, side: str = "BUY") -> Dict[str, Any]:
        """
        Evaluates multi-timeframe confluence for a BUY or SELL (SHORT) signal on a specific symbol.
        Returns:
            {
                "approved": bool,
                "reason": str,
                "ema_1h": float or None,
                "ema_4h": float or None,
                "trend_1h": "BULLISH" | "BEARISH" | "UNKNOWN",
                "trend_4h": "BULLISH" | "BEARISH" | "UNKNOWN"
            }
        """
        ema_1h = self.calculate_ema("1h", symbol=symbol)
        ema_4h = self.calculate_ema("4h", symbol=symbol)

        trend_1h = "UNKNOWN"
        trend_4h = "UNKNOWN"

        if ema_1h is not None:
            trend_1h = "BULLISH" if current_price >= ema_1h else "BEARISH"

        if ema_4h is not None:
            trend_4h = "BULLISH" if current_price >= ema_4h else "BEARISH"

        side_upper = str(side).upper()

        # 1. Confluence check for BUY / LONG
        if side_upper == "BUY":
            if ema_1h is not None and ema_4h is not None:
                if trend_1h == "BULLISH" and trend_4h == "BULLISH":
                    return {
                        "approved": True,
                        "reason": f"Đồng thuận đa khung (1h + 4h): Giá ${current_price:,.2f} > 1h EMA50 (${ema_1h:,.2f}) & 4h EMA50 (${ema_4h:,.2f}).",
                        "ema_1h": ema_1h,
                        "ema_4h": ema_4h,
                        "trend_1h": trend_1h,
                        "trend_4h": trend_4h
                    }
                else:
                    veto_reasons = []
                    if trend_1h != "BULLISH":
                        veto_reasons.append(f"1h giảm (Giá < EMA50 ${ema_1h:,.2f})")
                    if trend_4h != "BULLISH":
                        veto_reasons.append(f"4h giảm (Giá < EMA50 ${ema_4h:,.2f})")
                    reason_str = ", ".join(veto_reasons)
                    return {
                        "approved": False,
                        "reason": f"Phủ quyết đa khung thời gian: {reason_str}. Bẫy giá ngược xu hướng vĩ mô!",
                        "ema_1h": ema_1h,
                        "ema_4h": ema_4h,
                        "trend_1h": trend_1h,
                        "trend_4h": trend_4h
                    }
            elif ema_1h is not None:
                approved = (trend_1h == "BULLISH")
                reason = f"Khung 1h {'BULLISH' if approved else 'BEARISH'} (Giá: ${current_price:,.2f} vs EMA50: ${ema_1h:,.2f})."
                return {
                    "approved": approved,
                    "reason": reason,
                    "ema_1h": ema_1h,
                    "ema_4h": None,
                    "trend_1h": trend_1h,
                    "trend_4h": "UNKNOWN"
                }

        # 2. Confluence check for SELL / SHORT
        elif side_upper in ("SELL", "SHORT"):
            if ema_1h is not None and ema_4h is not None:
                if trend_1h == "BEARISH" and trend_4h == "BEARISH":
                    return {
                        "approved": True,
                        "reason": f"Đồng thuận đa khung SHORT (1h + 4h): Giá ${current_price:,.2f} < 1h EMA50 (${ema_1h:,.2f}) & 4h EMA50 (${ema_4h:,.2f}).",
                        "ema_1h": ema_1h,
                        "ema_4h": ema_4h,
                        "trend_1h": trend_1h,
                        "trend_4h": trend_4h
                    }
                elif trend_1h == "BEARISH":
                    return {
                        "approved": True,
                        "reason": f"Đồng thuận ngắn hạn SHORT (1h): Giá ${current_price:,.2f} < 1h EMA50 (${ema_1h:,.2f}).",
                        "ema_1h": ema_1h,
                        "ema_4h": ema_4h,
                        "trend_1h": trend_1h,
                        "trend_4h": trend_4h
                    }
                else:
                    return {
                        "approved": False,
                        "reason": f"Xung đột đa khung SHORT: 1h={trend_1h}, 4h={trend_4h}. Không thể Short ngược sóng tăng.",
                        "ema_1h": ema_1h,
                        "ema_4h": ema_4h,
                        "trend_1h": trend_1h,
                        "trend_4h": trend_4h
                    }
            elif ema_1h is not None:
                approved = (trend_1h == "BEARISH")
                reason = f"Khung 1h {'BEARISH cho SHORT' if approved else 'BULLISH, từ chối SHORT'}."
                return {
                    "approved": approved,
                    "reason": reason,
                    "ema_1h": ema_1h,
                    "ema_4h": None,
                    "trend_1h": trend_1h,
                    "trend_4h": "UNKNOWN"
                }

        # If insufficient data during startup warmup, pass cautiously
        return {
            "approved": True,
            "reason": "Chưa đủ dữ liệu nến 1h/4h (Khởi động hệ thống), tạm thời cho phép theo dõi.",
            "ema_1h": None,
            "ema_4h": None,
            "trend_1h": "UNKNOWN",
            "trend_4h": "UNKNOWN"
        }

    async def warmup(self, binance_client, symbol: str) -> None:
        """Fetches historical 1h and 4h candles via BinanceClient."""
        try:
            logger.info(f"[MultiTimeframeFilter] Warming up 1h candles for {symbol}...")
            candles_1h = await binance_client.fetch_ohlcv(symbol, timeframe="1h", limit=60)
            self.set_candles("1h", candles_1h, symbol=symbol)

            logger.info(f"[MultiTimeframeFilter] Warming up 4h candles for {symbol}...")
            candles_4h = await binance_client.fetch_ohlcv(symbol, timeframe="4h", limit=60)
            self.set_candles("4h", candles_4h, symbol=symbol)

            ema_1h = self.calculate_ema("1h", symbol=symbol)
            ema_4h = self.calculate_ema("4h", symbol=symbol)
            logger.info(f"[MultiTimeframeFilter] Warmup complete for {symbol}. 1h EMA50: {ema_1h} | 4h EMA50: {ema_4h}")
        except Exception as e:
            logger.warning(f"[MultiTimeframeFilter] Warmup failed for {symbol} (offline/mock): {e}")
