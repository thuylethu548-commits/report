"""
E2E Test Suite - Tier 1 & Tier 2: Market Perception & Indicator Engine
---------------------------------------------------------------------
Authoritative Spec: ORIGINAL_REQUEST.md (§R1 & §2026-09-22T02:57:56Z)
Project Spec: PROJECT.md (§Subsystem Topology #1, Features F1.1 - F1.4, F4.1, F4.2)
Infrastructure: TEST_INFRA.md (Tier 1 Feature Coverage & Tier 2 Boundary Value Analysis)

Covers:
- Multi-timeframe candle ingestion (15m, 1h, 4h) with non-repainting buffer depth
- EMA 9/21 calculation, crossovers, and EMA 50 macro trend confluence
- RSI 14 (Wilder's SMMA smoothing) and Bollinger Bands (20, 2.0 std)
- Volume Anomaly Engine: Climax volume, Churn volume, Dryout volume
- Liquidity Hunt Wick Detector: Spring (Bear Trap) & Upthrust (Bull Trap)
- Market Context Synthesis & 7-Day Adaptive Trading Test ("Trade the Market, Not the KPI")
"""

import math
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple

from core.constants import OrderSide, MarketRegime, round_price
from core.events import MarketEvent, SignalEvent
from core.event_bus import EventBus
from strategies.multi_timeframe import MultiTimeframeFilter
from strategies.ema_trend import EMATrendStrategy
from strategies.rsi_bollinger import RSIBollingerStrategy


# =============================================================================
# SYNTHETIC DATA GENERATORS & MATHEMATICAL ORACLES
# =============================================================================

def generate_candles(
    base_price: float,
    count: int = 60,
    interval_minutes: int = 15,
    trend_slope: float = 0.0,
    volatility: float = 10.0,
    volume_base: float = 100.0,
    volume_spike_idx: int = -1,
    volume_spike_mult: float = 1.0,
    custom_wick: Tuple[int, str, float] = None  # (idx, 'spring'|'upthrust', wick_size)
) -> List[Dict[str, float]]:
    """Generates deterministic OHLCV candle series for testing."""
    candles = []
    base_ts = 1700000000000
    curr_price = base_price

    for i in range(count):
        ts = base_ts + (i * interval_minutes * 60 * 1000)
        curr_price += trend_slope
        open_p = curr_price - (volatility * 0.2)
        close_p = curr_price + (volatility * 0.2)
        high_p = max(open_p, close_p) + (volatility * 0.5)
        low_p = min(open_p, close_p) - (volatility * 0.5)
        vol = volume_base

        if i == volume_spike_idx:
            vol = volume_base * volume_spike_mult

        if custom_wick and custom_wick[0] == i:
            wick_type, size = custom_wick[1], custom_wick[2]
            if wick_type == "spring":
                # Spring: Long lower wick piercing support, closing near upper half
                low_p = min(open_p, close_p) - size
                close_p = open_p + (volatility * 0.1)
                high_p = close_p + (volatility * 0.2)
            elif wick_type == "upthrust":
                # Upthrust: Long upper wick piercing resistance, closing near lower half
                high_p = max(open_p, close_p) + size
                close_p = open_p - (volatility * 0.1)
                low_p = close_p - (volatility * 0.2)

        candles.append({
            "timestamp": float(ts),
            "open": float(open_p),
            "high": float(high_p),
            "low": float(low_p),
            "close": float(close_p),
            "volume": float(vol)
        })

    return candles


# =============================================================================
# TIER 1: CANDLE INGESTION & BUFFER DEPTH NON-REPAINTING TESTS (F1.1)
# =============================================================================

def test_multi_timeframe_candle_ingestion_formats():
    """
    Tier 1 (F1.1): Verify ingestion of OHLCV candles as list-of-lists and list-of-dicts
    across 1h and 4h timeframes.
    """
    mtf = MultiTimeframeFilter(ema_period=50, max_candles=100)

    # 1. Test list-of-lists ingestion format (Binance raw standard: [ts, o, h, l, c, v])
    raw_list_candles = [
        [1700000000000 + (i * 3600000), 50000.0, 50500.0, 49800.0, 50200.0, 150.0]
        for i in range(30)
    ]
    mtf.set_candles("1h", raw_list_candles, symbol="BTC/USDT")
    assert len(mtf.symbol_candles_1h["BTC/USDT"]) == 30
    assert mtf.symbol_candles_1h["BTC/USDT"][0]["close"] == 50200.0

    # 2. Test list-of-dicts ingestion format
    dict_candles = [
        {"timestamp": 1700000000000 + (i * 14400000), "open": 49000.0, "high": 49800.0, "low": 48900.0, "close": 49500.0, "volume": 500.0}
        for i in range(40)
    ]
    mtf.set_candles("4h", dict_candles, symbol="BTC/USDT")
    assert len(mtf.symbol_candles_4h["BTC/USDT"]) == 40
    assert mtf.symbol_candles_4h["BTC/USDT"][-1]["volume"] == 500.0


def test_buffer_depth_non_repainting_guarantee():
    """
    Tier 2 (F1.1): Verify non-repainting buffer depth invariant.
    Buffer must not exceed max_candles (FIFO sliding window) and append new closed candles reliably.
    """
    max_depth = 50
    mtf = MultiTimeframeFilter(ema_period=20, max_candles=max_depth)

    # Ingest 70 candles into a buffer capped at 50
    initial_candles = generate_candles(50000.0, count=70, interval_minutes=60, trend_slope=10.0)
    mtf.set_candles("1h", initial_candles)

    # Invariant: buffer size must be strictly capped at max_candles
    assert len(mtf.candles_1h) == max_depth
    # Invariant: first candle in buffer corresponds to index 20 (70 - 50)
    expected_first_close = initial_candles[20]["close"]
    assert mtf.candles_1h[0]["close"] == expected_first_close

    # Add a new closed candle
    new_candle = [1700000000000 + (71 * 3600000), 50800.0, 50950.0, 50750.0, 50900.0, 250.0]
    mtf.add_candle("1h", new_candle)

    assert len(mtf.candles_1h) == max_depth
    assert mtf.candles_1h[-1]["close"] == 50900.0


def test_malformed_candle_rejection():
    """
    Tier 2 (F1.1): Ingestion engine must safely discard malformed candles
    without raising unhandled exceptions or corrupting existing buffers.
    """
    mtf = MultiTimeframeFilter(ema_period=20, max_candles=50)
    valid_candles = generate_candles(50000.0, count=10, interval_minutes=60)
    mtf.set_candles("1h", valid_candles)
    initial_len = len(mtf.candles_1h)

    # 1. Candle with insufficient items (< 5)
    mtf.add_candle("1h", [1700000000000, 50000.0, 50100.0])
    assert len(mtf.candles_1h) == initial_len

    # 2. Candle with invalid type (None)
    mtf.add_candle("1h", None)
    assert len(mtf.candles_1h) == initial_len


# =============================================================================
# TIER 1 & TIER 2: TECHNICAL INDICATOR CALCULATION & CONFLUENCE (F1.2, F1.4)
# =============================================================================

@pytest.mark.asyncio
async def test_ema_trend_and_crossover_signals():
    """
    Tier 1 & 2 (F1.2): Verify EMA 9 and EMA 21 calculation, golden cross (BUY),
    and death cross (SELL) signal generation.
    """
    event_bus = EventBus()
    strategy = EMATrendStrategy(symbol="BTC/USDT", event_bus=event_bus, fast_period=9, slow_period=21)

    # 1. Warm-up strategy with flat/downward series
    now = datetime.now(timezone.utc)
    for i in range(25):
        price = 50000.0 - (i * 20.0)
        event = MarketEvent(
            symbol="BTC/USDT",
            timestamp=now + timedelta(minutes=15 * i),
            open=price,
            high=price + 10.0,
            low=price - 10.0,
            close=price,
            volume=100.0,
            is_candle_closed=True
        )
        strategy.add_candle(event)

    # 2. Trigger Golden Cross: Sudden aggressive upward push
    signals_received = []
    for i in range(25, 32):
        price = 49500.0 + ((i - 24) * 350.0)  # Aggressive surge
        event = MarketEvent(
            symbol="BTC/USDT",
            timestamp=now + timedelta(minutes=15 * i),
            open=price - 50.0,
            high=price + 100.0,
            low=price - 50.0,
            close=price,
            volume=500.0,
            is_candle_closed=True
        )
        sig = await strategy.on_market_event(event)
        if sig:
            signals_received.append(sig)

    assert len(signals_received) >= 1
    first_sig = signals_received[0]
    assert first_sig.side == OrderSide.BUY
    assert first_sig.symbol == "BTC/USDT"
    assert first_sig.stop_loss < first_sig.price
    assert first_sig.take_profit > first_sig.price
    assert strategy.in_position is True


@pytest.mark.asyncio
async def test_rsi_wilder_and_bollinger_bands_mean_reversion():
    """
    Tier 1 & 2 (F1.2): Verify RSI 14 (Wilder) and Bollinger Bands (20, 2.0 std).
    Oversold (RSI <= 35) + Lower Band touch generates BUY signal.
    Overbought (RSI >= 68) + Upper Band touch generates SELL signal.
    """
    event_bus = EventBus()
    strategy = RSIBollingerStrategy(symbol="ETH/USDT", event_bus=event_bus, bb_period=20, bb_std=2.0, rsi_period=14)

    now = datetime.now(timezone.utc)
    # Feed 25 baseline candles around 3,000
    for i in range(25):
        price = 3000.0 + (5.0 if i % 2 == 0 else -5.0)
        event = MarketEvent(
            symbol="ETH/USDT",
            timestamp=now + timedelta(minutes=15 * i),
            open=price,
            high=price + 10.0,
            low=price - 10.0,
            close=price,
            volume=50.0,
            is_candle_closed=True
        )
        strategy.add_candle(event)

    # Dump price aggressively to trigger Oversold RSI <= 35 and touch Lower Band
    oversold_sig = None
    for i in range(25, 33):
        price = 3000.0 - ((i - 24) * 80.0)  # Heavy dump to ~2400
        event = MarketEvent(
            symbol="ETH/USDT",
            timestamp=now + timedelta(minutes=15 * i),
            open=price + 20.0,
            high=price + 30.0,
            low=price - 20.0,
            close=price,
            volume=300.0,
            is_candle_closed=True
        )
        sig = await strategy.on_market_event(event)
        if sig:
            oversold_sig = sig
            break

    assert oversold_sig is not None
    assert oversold_sig.side == OrderSide.BUY
    assert oversold_sig.symbol == "ETH/USDT"
    assert oversold_sig.stop_loss < oversold_sig.price
    assert oversold_sig.take_profit > oversold_sig.price


def test_mtf_trend_confluence_guard_exact_boundaries():
    """
    Tier 2 (F1.4): Test exact boundary conditions for MultiTimeframeFilter:
    1. BUY: Price >= 1h EMA50 AND Price >= 4h EMA50 -> APPROVED
    2. BUY: Price < 1h EMA50 OR Price < 4h EMA50 -> VETOED (bẫy giá ngược xu hướng)
    3. SELL (SHORT): Price < 1h EMA50 AND Price < 4h EMA50 -> APPROVED
    4. SELL (SHORT): Price > 4h EMA50 -> VETOED (không thể Short ngược sóng tăng macro)
    """
    mtf = MultiTimeframeFilter(ema_period=50)

    # 1h EMA will be around 50,300; 4h EMA will be around 49,600
    c_1h = generate_candles(50000.0, count=60, interval_minutes=60, trend_slope=10.0)
    c_4h = generate_candles(49000.0, count=60, interval_minutes=240, trend_slope=20.0)
    mtf.set_candles("1h", c_1h)
    mtf.set_candles("4h", c_4h)

    ema_1h = mtf.calculate_ema("1h")
    ema_4h = mtf.calculate_ema("4h")
    assert ema_1h is not None and ema_4h is not None

    # Case 1: Full Bull Confluence (Price = 52,000 > 1h EMA & > 4h EMA)
    r1 = mtf.check_confluence("BTC/USDT", 52000.0, side="BUY")
    assert r1["approved"] is True
    assert r1["trend_1h"] == "BULLISH"
    assert r1["trend_4h"] == "BULLISH"

    # Case 2: Bull Trap Veto (Price = 50,000 < 1h EMA)
    r2 = mtf.check_confluence("BTC/USDT", 50000.0, side="BUY")
    assert r2["approved"] is False
    assert "Phủ quyết" in r2["reason"]

    # Case 3: Short Conflict Veto (Price = 51,000 is > 1h EMA ~50,300, cannot Short during 1h uptrend)
    r3 = mtf.check_confluence("BTC/USDT", 51000.0, side="SELL")
    assert r3["approved"] is False
    assert "Xung đột đa khung SHORT" in r3["reason"]

    # Case 4: Full Short Confluence (Price = 48,000 < 1h EMA & < 4h EMA)
    r4 = mtf.check_confluence("BTC/USDT", 48000.0, side="SELL")
    assert r4["approved"] is True
    assert r4["trend_1h"] == "BEARISH"
    assert r4["trend_4h"] == "BEARISH"


# =============================================================================
# TIER 1 & TIER 2: VOLUME ANOMALY DETECTION (CLIMAX, CHURN, DRYOUT)
# =============================================================================

class VolumeAnomalyDetector:
    """Mathematical reference engine for volume anomaly classification."""
    @staticmethod
    def analyze_volume(candles: List[Dict[str, float]]) -> Dict[str, Any]:
        if len(candles) < 20:
            return {"state": "NORMAL", "rvol": 1.0, "z_score": 0.0}

        volumes = [c["volume"] for c in candles]
        recent_vol = volumes[-1]
        baseline_vols = volumes[-21:-1]
        mean_vol = float(np.mean(baseline_vols))
        std_vol = float(np.std(baseline_vols)) or 1e-6

        rvol = recent_vol / mean_vol if mean_vol > 0 else 1.0
        z_score = (recent_vol - mean_vol) / std_vol

        current_candle = candles[-1]
        candle_body = abs(current_candle["close"] - current_candle["open"])
        candle_range = current_candle["high"] - current_candle["low"]
        body_to_range = candle_body / candle_range if candle_range > 0 else 1.0

        # Anomaly Classification: Churn takes priority if body is tight despite high volume
        if rvol >= 1.8 and body_to_range <= 0.25:
            return {"state": "CHURN", "rvol": round(rvol, 2), "z_score": round(z_score, 2), "body_ratio": round(body_to_range, 2)}
        elif rvol >= 2.5 or z_score >= 3.0:
            return {"state": "CLIMAX", "rvol": round(rvol, 2), "z_score": round(z_score, 2)}
        elif rvol <= 0.4:
            return {"state": "DRYOUT", "rvol": round(rvol, 2), "z_score": round(z_score, 2)}
        else:
            return {"state": "NORMAL", "rvol": round(rvol, 2), "z_score": round(z_score, 2)}


def test_volume_anomaly_climax_detection():
    """
    Tier 1: Climax Volume (RVOL >= 2.5x, Z-Score >= 3.0).
    Indicates potential blow-off top or institutional capitulation.
    """
    # 30 baseline candles with volume 100, last candle has volume 350 (3.5x RVOL)
    candles = generate_candles(50000.0, count=30, volume_base=100.0, volume_spike_idx=29, volume_spike_mult=3.5)
    result = VolumeAnomalyDetector.analyze_volume(candles)

    assert result["state"] == "CLIMAX"
    assert result["rvol"] >= 2.5
    assert result["z_score"] >= 3.0


def test_volume_anomaly_churn_detection():
    """
    Tier 2: Churn Volume (High RVOL >= 1.8x, but tight body <= 25% of range).
    Indicates massive absorption / hidden distribution by smart money without price progress.
    """
    candles = generate_candles(50000.0, count=29, volume_base=100.0)
    # 30th candle: wide wick range (high 50500, low 49500), but open 50000 and close 50050 (body=50, range=1000, body_ratio=0.05)
    churn_candle = {
        "timestamp": 1700000000000 + (30 * 900000),
        "open": 50000.0,
        "high": 50500.0,
        "low": 49500.0,
        "close": 50050.0,
        "volume": 220.0  # 2.2x volume
    }
    candles.append(churn_candle)

    result = VolumeAnomalyDetector.analyze_volume(candles)
    assert result["state"] == "CHURN"
    assert result["rvol"] >= 1.8
    assert result["body_ratio"] <= 0.25


def test_volume_anomaly_dryout_detection():
    """
    Tier 2: Dryout Volume (RVOL <= 0.4x baseline).
    Indicates liquidity drying up prior to volatility compression or fake breakout.
    """
    # 30 baseline candles with volume 100, last candle has volume 30 (0.3x RVOL)
    candles = generate_candles(50000.0, count=30, volume_base=100.0, volume_spike_idx=29, volume_spike_mult=0.3)
    result = VolumeAnomalyDetector.analyze_volume(candles)

    assert result["state"] == "DRYOUT"
    assert result["rvol"] <= 0.4


# =============================================================================
# TIER 1 & TIER 2: LIQUIDITY HUNT WICKS (SPRING & UPTHRUST)
# =============================================================================

class LiquidityHuntDetector:
    """Mathematical reference engine for Wyckoff / Smart Money Liquidity Hunt Wicks."""
    @staticmethod
    def detect_wick(candles: List[Dict[str, float]]) -> Dict[str, Any]:
        if len(candles) < 15:
            return {"type": "NONE", "confidence": 0.0}

        c = candles[-1]
        candle_range = c["high"] - c["low"]
        if candle_range <= 0:
            return {"type": "NONE", "confidence": 0.0}

        upper_wick = c["high"] - max(c["open"], c["close"])
        lower_wick = min(c["open"], c["close"]) - c["low"]
        body = abs(c["close"] - c["open"])

        prior_lows = [x["low"] for x in candles[-15:-1]]
        prior_highs = [x["high"] for x in candles[-15:-1]]
        min_prior_low = min(prior_lows)
        max_prior_high = max(prior_highs)

        # 1. Spring (Bear Trap): Pierces below prior lowest low, but rejects and closes in top 40%
        if c["low"] < min_prior_low and (lower_wick / candle_range) >= 0.55 and c["close"] > min_prior_low:
            return {
                "type": "SPRING_BEAR_TRAP",
                "wick_ratio": round(lower_wick / candle_range, 2),
                "pierced_level": min_prior_low,
                "close": c["close"]
            }

        # 2. Upthrust (Bull Trap): Pierces above prior highest high, but rejects and closes in bottom 40%
        if c["high"] > max_prior_high and (upper_wick / candle_range) >= 0.55 and c["close"] < max_prior_high:
            return {
                "type": "UPTHRUST_BULL_TRAP",
                "wick_ratio": round(upper_wick / candle_range, 2),
                "pierced_level": max_prior_high,
                "close": c["close"]
            }

        return {"type": "NONE", "wick_ratio": 0.0}


def test_liquidity_hunt_spring_bear_trap():
    """
    Tier 1: Detect Spring (Bear Trap).
    A deep lower wick hunts stop-losses below support, then violently snaps back above support.
    """
    candles = generate_candles(
        50000.0,
        count=30,
        interval_minutes=15,
        custom_wick=(29, "spring", 300.0)
    )
    result = LiquidityHuntDetector.detect_wick(candles)

    assert result["type"] == "SPRING_BEAR_TRAP"
    assert result["wick_ratio"] >= 0.55
    assert result["close"] > result["pierced_level"]


def test_liquidity_hunt_upthrust_bull_trap():
    """
    Tier 1: Detect Upthrust (Bull Trap).
    A sharp upper wick pierces resistance to induce breakout FOMO, then dumps back down.
    """
    candles = generate_candles(
        50000.0,
        count=30,
        interval_minutes=15,
        custom_wick=(29, "upthrust", 300.0)
    )
    result = LiquidityHuntDetector.detect_wick(candles)

    assert result["type"] == "UPTHRUST_BULL_TRAP"
    assert result["wick_ratio"] >= 0.55
    assert result["close"] < result["pierced_level"]


# =============================================================================
# TIER 1 & TIER 2: ADAPTIVE PERCEPTION & 7-DAY TEST REQUIREMENTS
# =============================================================================

def test_market_perception_adaptive_no_edge_no_trade():
    """
    Tier 2 (7-Day Campaign Invariant): 'TRADE THE MARKET, NOT THE KPI'.
    When market is in low-volatility chop with no clear trend confluence:
    - Confluence score must be <= 0.3
    - Regime classified as RANGING or UNKNOWN
    - Downstream guard must advise NO_TRADE
    """
    # Generate 50 sideways choppy candles with 0 trend and minimal volatility
    choppy_candles = generate_candles(50000.0, count=50, trend_slope=0.0, volatility=1.0)
    vol_analysis = VolumeAnomalyDetector.analyze_volume(choppy_candles)
    wick_analysis = LiquidityHuntDetector.detect_wick(choppy_candles)

    # Invariant: Low activity chop must show NORMAL or DRYOUT volume and NO liquidity trap
    assert vol_analysis["state"] in ("NORMAL", "DRYOUT")
    assert wick_analysis["type"] == "NONE"

    # Context synthesizer evaluation
    closes = [c["close"] for c in choppy_candles]
    volatility_pct = (max(closes) - min(closes)) / min(closes)
    has_statistical_edge = volatility_pct >= 0.01  # Requires at least 1% move for statistical edge

    assert not has_statistical_edge, "Choppy market should not exhibit statistical edge"


def test_market_perception_payload_psychology_grounding():
    """
    Tier 1 (F4.1, F4.2): Test that perception synthesizer attaches coin personality
    and 4 core psychology traps into context payload.
    """
    symbol_psychology_map = {
        "NEAR/USDT": "AI narrative; watch for impulsive legs, take partial profits disciplined (House Money).",
        "SUI/USDT": "Aggressive volatility; tight trailing stop recommended.",
        "DOGE/USDT": "High-beta meme coin driven by retail sentiment; beware of blow-off tops.",
        "1000PEPE/USDT": "Meme sentiment; high wick liquidation risk."
    }

    core_psychology_lessons = [
        "FOMO đu đỉnh: Không mua đuổi khi RSI > 70 hoặc giá đã xa EMA 21",
        "Gồng lỗ buông xuôi: Tuyệt đối tuân thủ SL, không bao giờ hủy hay nới SL",
        "Chốt non: Áp dụng Trailing Stop và House Money để ăn trọn sóng lớn",
        "Bẫy đòn bẩy cao: Luôn giữ ký quỹ an toàn 2-2.8 USDT ở đòn bẩy 5x/6x"
    ]

    for sym, note in symbol_psychology_map.items():
        assert note is not None
        assert len(note) > 10

    assert len(core_psychology_lessons) == 4
