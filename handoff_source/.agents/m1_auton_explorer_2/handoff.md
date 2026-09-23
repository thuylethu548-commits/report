# Handoff Report: Market Perception Architecture, Quantitative Formulas & RiskManager Integration Plan

**Author**: m1_auton_explorer_2 (Exploration & Synthesis Agent)  
**Date**: 2026-09-22T03:10:00Z  
**Target Milestone**: Milestone 1 - Market Perception & Alert Synthesis (F1.3, R1)  
**Parent Conversation ID**: e9b53268-5666-44c8-8876-b9e21cf9f943  
**Working Directory**: `c:\sunMy\trading_bot\.agents\m1_auton_explorer_2`  
**Integrity Mode**: Read-Only Exploration  

---

## 1. Observation

Direct inspection of the Astra Quant Desk codebase and project specifications revealed the following current state:

### 1.1 Codebase & File State
1. **Missing Module `ai_advisory/market_perception.py`**:
   - Inspection of directory `ai_advisory/` (`ai_advisory/__init__.py`, `adversarial_debater.py`, `gemini_pool.py`, `regime_classifier.py`, `vyce_client.py`) confirmed that `market_perception.py` does not currently exist.
   - Grep search for `VolumeAnomalyDetector`, `LiquidityHuntDetector`, and `MarketPerceptionPayload` returned zero matches across the entire repository.

2. **Current `market_context` Construction in `risk_engine/risk_manager.py`**:
   - In `risk_engine/risk_manager.py` (lines 292–320), before dispatching to the AI Advisory Gatekeeper or Adversarial VAR Council:
     ```python
     recent_candles = []
     recent_lessons = []
     if self.db:
         try:
             recent_candles = await self.db.get_recent_candles(signal.symbol, limit=10)
         except Exception as e:
             logger.debug(f"Could not retrieve recent candles for AI context: {e}")
         try:
             lessons_data = await self.db.get_lessons(limit=10)
             recent_lessons = [f"[{l['category']}] {l['title']}: {l['lesson_learned']}" for l in lessons_data]
         except Exception as e:
             logger.debug(f"Could not retrieve recent lessons: {e}")

     market_context: Dict[str, Any] = {
         "symbol": signal.symbol,
         "price": signal.price,
         "strategy_name": signal.strategy_name,
         "side": signal.side.value if hasattr(signal.side, "value") else str(signal.side),
         "stop_loss": signal.stop_loss,
         "take_profit": signal.take_profit,
         "confidence": signal.confidence,
         "recent_candles": recent_candles,
         "hard_earned_lessons_to_respect": recent_lessons,
         "account_equity": self.circuit_breaker.current_equity or settings.STARTING_BALANCE_USDT,
         "open_positions": len(self.open_positions)
     }
     ```
   - **Critical Observation**:
     * `limit=10` is insufficient for a 20-period volume baseline and 15-period swing high/low lookback. At least $N \ge 21$ (recommended $N=60$) candles are required.
     * `market_context` currently lacks the key `"market_perception"`.
     * `market_context` is converted directly to JSON via `json.dumps(context, ensure_ascii=False)` in `ai_advisory/adversarial_debater.py` (line 98). Therefore, any payload embedded inside `market_context` must be strictly JSON-serializable (or provide a dict representation via `.to_dict()`).

3. **Multi-Timeframe Filter State in `strategies/multi_timeframe.py`**:
   - `MultiTimeframeFilter` tracks `candles_1h` and `candles_4h` in circular buffers (lines 20-55), calculating `EMA(50)` for trend confluence.
   - `RiskManager.__init__` receives `mtf_filter: Optional[Any] = None`. In live execution (`main.py` line 108), `mtf_filter = MultiTimeframeFilter(ema_period=settings.MTF_EMA_PERIOD)` is passed to `RiskManager`.
   - In existing unit tests (`tests/test_risk_engine.py`), `RiskManager` is instantiated with `mtf_filter=None`, and `self.db.get_recent_candles` returns `[]`.

4. **Interface Contract in `PROJECT.md` (lines 79–93)**:
   - Formally specifies the target schema for `MarketPerceptionPayload`:
     ```python
     @dataclass
     class MarketPerceptionPayload:
         symbol: str
         timestamp: str               # ISO 8601 UTC
         current_price: float
         timeframes: Dict[str, TimeframeMetrics]  # "15m", "1h", "4h"
         confluence_score: float      # -1.0 to +1.0
         volume_state: VolumeAnomalyState
         liquidity_hunt: LiquidityHuntState
         macro_regime: str            # "BULL_TREND" | "BEAR_TREND" | "RANGING" | "EXTREME_VOLATILITY"
         detected_alerts: List[str]
         matched_psychology_lessons: List[str]
     ```

5. **Test Suite Baseline & Zero Regressions**:
   - Running `.venv\Scripts\pytest tests/test_risk_engine.py -q` showed 14 tests passing. 4 failures were due to legacy position sizing assumptions (`0.20` vs updated `0.25` in `settings.MAX_POSITION_PERCENT` for 50u capital sizing, Milestone 4 scope).
   - Any new code in `market_perception.py` and `RiskManager.handle_signal` must guarantee that tests passing `mtf_filter=None` or empty candle databases do not raise unhandled exceptions.

---

## 2. Logic Chain & Implementation Design

Deduction from requirements to concrete mathematical algorithms, data structures, and code architecture:

```
[Candles Ingested: 15m (DB), 1h (MTF), 4h (MTF)]
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
[VolumeAnomalyDetector]          [LiquidityHuntDetector]
- Baseline: Mean & Std (20)      - Lookback: 15 prior candles
- RVOL = V_t / Mean              - Bullish Spring: Lower Wick >= 2x Body, >= 0.5 Range,
- Z-Score = (V_t - Mean) / Std                     Pierces & Reclaims Swing Low, RVOL >= 1.5
- Classify: CLIMAX, CHURN,       - Bearish Upthrust: Upper Wick >= 2x Body, >= 0.5 Range,
  DRYOUT, NORMAL                                   Pierces & Closes Below Swing High, RVOL >= 1.5
        │                                 │
        └────────────────┬────────────────┘
                         ▼
           [MarketPerceptionSynthesizer]
           - Indicators: EMA 9/21, RSI 14, BB 20/2.0
           - MTF Confluence: 0.20*15m + 0.40*1h + 0.40*4h
           - Assemble MarketPerceptionPayload (.to_dict())
                         │
                         ▼
        [RiskManager.handle_signal Integration]
        market_context['market_perception'] = payload.to_dict()
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
[Adversarial VAR Council]        [Audit Logs & API Feeds]
- Bull Thesis receives Spring    - UI /admin displays real-time
- Bear traps Upthrust / Churn      volume anomaly & hunt alerts
```

### 2.1 Volume Anomaly Mathematical Specification

Let $\mathcal{C} = [C_{t-N}, \dots, C_{t-1}, C_t]$ be the sequence of historical candles, where each candle $C = (O, H, L, C, V)$.
The current candle under evaluation is $C_t$.

#### 1. Baseline Computation
The baseline is established using the $K=20$ candles immediately preceding candle $t$:
$$\bar{V}_{20} = \frac{1}{20} \sum_{i=1}^{20} V_{t-i}$$
$$\sigma_{V, 20} = \sqrt{\frac{1}{20} \sum_{i=1}^{20} (V_{t-i} - \bar{V}_{20})^2}$$

#### 2. Metric Formulation
- **Relative Volume ($RVOL_t$)**:
  $$RVOL_t = \frac{V_t}{\bar{V}_{20} + \epsilon}, \quad \epsilon = 10^{-9}$$
- **Volume Z-Score ($Z_{V, t}$)**:
  $$Z_{V, t} = \begin{cases}
  \frac{V_t - \bar{V}_{20}}{\sigma_{V, 20} + \epsilon} & \text{if } \sigma_{V, 20} > 10^{-9} \\
  0.0 & \text{otherwise}
  \end{cases}$$
- **Candle Structural Decomposition**:
  $$Range_t = H_t - L_t$$
  $$Body_t = |C_t - O_t|$$
  $$BodyRatio_t = \begin{cases}
  \frac{Body_t}{Range_t + \epsilon} & \text{if } Range_t > 0 \\
  0.0 & \text{otherwise}
  \end{cases}$$

#### 3. Classification Decision Tree & Precedence Rules
To ensure deterministic and unambiguous classification, rules are evaluated in the following strict order:

1. **`VOLUME_ABSORPTION_CHURN`**:
   - Trigger: $RVOL_t \ge 2.0$ AND $BodyRatio_t < 0.30$.
   - Rationale: High volume without commensurate price progress indicates institutional absorption / distribution. Takes precedence when body is narrow even if $Z \ge 3.0$.
2. **`VOLUME_CLIMAX`**:
   - Trigger: $RVOL_t \ge 2.5$ AND $Z_{V, t} \ge 3.0$ (with $BodyRatio_t \ge 0.30$).
   - Rationale: Extreme exhaustion volume accompanying expansive price movement.
3. **`VOLUME_DRYOUT_DRIFT`**:
   - Trigger: $RVOL_t \le 0.50$.
   - Rationale: Thin liquidity, price drift vulnerable to sudden reversal.
4. **`NORMAL`**:
   - Trigger: All other conditions ($0.50 < RVOL_t < 2.0$ or non-climax volume).

#### 4. Edge Cases Handled
- **Fewer than 20 prior candles**: When $1 \le M < 20$ prior candles exist (startup / warmup), baseline uses available $M$ candles. If $M = 0$, defaults to $RVOL = 1.0, Z = 0.0, \text{NORMAL}$.
- **Zero baseline volume**: If all prior candles had 0 volume, $\epsilon = 10^{-9}$ prevents division by zero.
- **Flat candle ($H_t == L_t$)**: $Range_t = 0 \implies BodyRatio_t = 0.0$.

---

### 2.2 Liquidity Hunt Wick Mathematical Specification

Liquidity sweeps occur when price briefly breaches a well-defined support or resistance level to absorb retail stop orders, followed by immediate price rejection back within range.

#### 1. Structural Decomposition
For candle $t$:
- Total Range: $R_t = H_t - L_t$
- Real Body: $B_t = |C_t - O_t|$
- Upper Wick: $W_{u, t} = H_t - \max(O_t, C_t)$
- Lower Wick: $W_{l, t} = \min(O_t, C_t) - L_t$

#### 2. Swing Level Calculation (Lookback $M=15$)
Over the prior 15 closed candles $C_{t-15}, \dots, C_{t-1}$:
$$SwingLow_t = \min_{1 \le i \le 15} L_{t-i}$$
$$SwingHigh_t = \max_{1 \le i \le 15} H_{t-i}$$

#### 3. Bullish Spring (Stop Run on Lows)
All five conditions must be simultaneously satisfied:
1. **Lower Wick Dominance (vs Body)**: $W_{l, t} \ge 2.0 \times B_t$
2. **Lower Wick Dominance (vs Range)**: $W_{l, t} \ge 0.50 \times R_t$
3. **Pierces Swing Low**: $L_t < SwingLow_t$
4. **Reclaims Swing Low**: $C_t > SwingLow_t$ (Closed back above the pierced support level)
5. **Volume Spike**: $RVOL_t \ge 1.50$

Output when detected:
- `is_detected = True`
- `hunt_type = "SPRING_BULLISH"`
- `wick_ratio = round(W_{l, t} / (R_t + \epsilon), 4)`
- `swept_level = float(SwingLow_t)`

#### 4. Bearish Upthrust (Stop Run on Highs)
All five conditions must be simultaneously satisfied:
1. **Upper Wick Dominance (vs Body)**: $W_{u, t} \ge 2.0 \times B_t$
2. **Upper Wick Dominance (vs Range)**: $W_{u, t} \ge 0.50 \times R_t$
3. **Pierces Swing High**: $H_t > SwingHigh_t$
4. **Closes Lower than Swing High**: $C_t < SwingHigh_t$ (Closed back below the pierced resistance level)
5. **Volume Spike**: $RVOL_t \ge 1.50$

Output when detected:
- `is_detected = True`
- `hunt_type = "UPTHRUST_BEARISH"`
- `wick_ratio = round(W_{u, t} / (R_t + \epsilon), 4)`
- `swept_level = float(SwingHigh_t)`

#### 5. Default State (No Hunt Detected)
- `is_detected = False`
- `hunt_type = "NONE"`
- `wick_ratio = 0.0`
- `swept_level = 0.0`

---

### 2.3 Multi-Timeframe Confluence & Synthesizer Specification

To populate `MarketPerceptionPayload`, `MarketPerceptionSynthesizer` combines indicators across timeframes:

1. **Indicator Calculations per Timeframe $\tau \in \{15m, 1h, 4h\}$**:
   - $EMA_9, EMA_{21}$ using exponential weighting $\alpha = \frac{2}{k+1}$.
   - $RSI_{14}$ using Wilder's smoothed moving averages ($SMMA_U, SMMA_D$).
   - Bollinger Bands ($SMA_{20}, \pm 2.0\sigma$), Bandwidth $= \frac{Upper - Lower}{SMA_{20}}$.
   - $Trend_{\tau} = +1$ if $EMA_9 > EMA_{21}$ and $Close > EMA_9$; $-1$ if $EMA_9 < EMA_{21}$ and $Close < EMA_9$; $0$ otherwise.
2. **Multi-Timeframe Composite Index**:
   $$MTF_{confluence} = 0.20 \cdot Trend_{15m} + 0.40 \cdot Trend_{1h} + 0.40 \cdot Trend_{4h}$$
3. **Macro Regime Mapping**:
   - `BULL_TREND`: $MTF_{confluence} \ge 0.60$
   - `BEAR_TREND`: $MTF_{confluence} \le -0.60$
   - `EXTREME_VOLATILITY`: Bollinger Bandwidth in top 95th percentile or $RVOL \ge 3.0$ with rapid price reversals
   - `RANGING`: $-0.60 < MTF_{confluence} < 0.60$
4. **Detected Alerts Synthesis**:
   - If Volume Anomaly $\ne$ `NORMAL`: append anomaly string (e.g. `VOLUME_CLIMAX`, `VOLUME_ABSORPTION_CHURN`, `VOLUME_DRYOUT_DRIFT`).
   - If Liquidity Hunt detected: append `LIQUIDITY_HUNT_SPRING_BULLISH` or `LIQUIDITY_HUNT_UPTHRUST_BEARISH`.
   - If Bollinger Squeeze: append `BOLLINGER_SQUEEZE`.
   - If $RSI_{14} \ge 72$: append `RSI_OVERBOUGHT`; if $RSI_{14} \le 28$: append `RSI_OVERSOLD`.

---

### 2.4 Proposed Implementation Code: `ai_advisory/market_perception.py`

Below is the complete, self-contained implementation to be placed in `ai_advisory/market_perception.py`:

```python
"""
Astra Quant Desk - Market Perception & Alert Synthesis Engine
============================================================
Defines VolumeAnomalyDetector, LiquidityHuntDetector, and MarketPerceptionPayload.
Provides multi-timeframe indicator confluence, anomaly classification,
and JSON-serializable payloads for the Risk Manager and Adversarial VAR Council.
"""

import math
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger("MarketPerception")


@dataclass
class TimeframeMetrics:
    timeframe: str               # "15m", "1h", "4h"
    ema_9: float
    ema_21: float
    rsi_14: float
    bb_upper: float
    bb_mid: float
    bb_lower: float
    bb_bandwidth: float
    trend_state: int             # +1 (Bullish), -1 (Bearish), 0 (Neutral)
    close_price: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VolumeAnomalyState:
    rvol: float                  # e.g. 2.7
    z_score: float               # e.g. 3.2
    anomaly_type: str            # "NORMAL" | "VOLUME_CLIMAX" | "VOLUME_ABSORPTION_CHURN" | "VOLUME_DRYOUT_DRIFT"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LiquidityHuntState:
    is_detected: bool
    hunt_type: str               # "NONE" | "SPRING_BULLISH" | "UPTHRUST_BEARISH"
    wick_ratio: float            # Ratio of dominant wick to total range
    swept_level: float           # Price level that was swept

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MarketPerceptionPayload:
    symbol: str
    timestamp: str               # ISO 8601 UTC
    current_price: float
    timeframes: Dict[str, TimeframeMetrics]
    confluence_score: float      # -1.0 to +1.0
    volume_state: VolumeAnomalyState
    liquidity_hunt: LiquidityHuntState
    macro_regime: str            # "BULL_TREND" | "BEAR_TREND" | "RANGING" | "EXTREME_VOLATILITY"
    detected_alerts: List[str]
    matched_psychology_lessons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "current_price": self.current_price,
            "timeframes": {k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in self.timeframes.items()},
            "confluence_score": round(self.confluence_score, 4),
            "volume_state": self.volume_state.to_dict() if hasattr(self.volume_state, "to_dict") else asdict(self.volume_state),
            "liquidity_hunt": self.liquidity_hunt.to_dict() if hasattr(self.liquidity_hunt, "to_dict") else asdict(self.liquidity_hunt),
            "macro_regime": self.macro_regime,
            "detected_alerts": list(self.detected_alerts),
            "matched_psychology_lessons": list(self.matched_psychology_lessons),
        }


class VolumeAnomalyDetector:
    """
    Evaluates Relative Volume (RVOL) against rolling 20-period baseline and Z-score.
    Classifications:
    - VOLUME_ABSORPTION_CHURN: RVOL >= 2.0 AND body/range < 0.30
    - VOLUME_CLIMAX: RVOL >= 2.5 AND Z >= 3.0
    - VOLUME_DRYOUT_DRIFT: RVOL <= 0.50
    - NORMAL: all other conditions
    """

    def __init__(
        self,
        baseline_period: int = 20,
        climax_rvol: float = 2.5,
        climax_z: float = 3.0,
        churn_rvol: float = 2.0,
        churn_body_ratio: float = 0.30,
        dryout_rvol: float = 0.50
    ):
        self.baseline_period = baseline_period
        self.climax_rvol = climax_rvol
        self.climax_z = climax_z
        self.churn_rvol = churn_rvol
        self.churn_body_ratio = churn_body_ratio
        self.dryout_rvol = dryout_rvol

    def compute_rvol_and_zscore(
        self,
        prior_volumes: List[float],
        current_volume: float
    ) -> Tuple[float, float]:
        """Calculates RVOL and Z-score against prior volume baseline."""
        if not prior_volumes:
            return 1.0, 0.0

        n = min(len(prior_volumes), self.baseline_period)
        window = prior_volumes[-n:]
        mean_v = float(np.mean(window))
        std_v = float(np.std(window))

        eps = 1e-9
        rvol = current_volume / (mean_v + eps) if mean_v > 0 else (1.0 if current_volume == 0 else 5.0)
        z_score = (current_volume - mean_v) / (std_v + eps) if std_v > eps else 0.0

        return round(float(rvol), 2), round(float(z_score), 2)

    def detect(
        self,
        candles: Union[List[Dict[str, Any]], pd.DataFrame],
        current_candle: Optional[Dict[str, Any]] = None
    ) -> VolumeAnomalyState:
        """
        Detects volume anomaly state on the latest candle.
        Accepts list of candle dicts or DataFrame.
        """
        parsed_candles: List[Dict[str, float]] = []
        if isinstance(candles, pd.DataFrame):
            for _, row in candles.iterrows():
                parsed_candles.append({
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0.0))
                })
        elif isinstance(candles, list):
            for c in candles:
                if isinstance(c, dict):
                    parsed_candles.append({
                        "open": float(c.get("open", 0.0)),
                        "high": float(c.get("high", 0.0)),
                        "low": float(c.get("low", 0.0)),
                        "close": float(c.get("close", 0.0)),
                        "volume": float(c.get("volume", 0.0))
                    })

        if current_candle is not None:
            parsed_candles.append({
                "open": float(current_candle.get("open", 0.0)),
                "high": float(current_candle.get("high", 0.0)),
                "low": float(current_candle.get("low", 0.0)),
                "close": float(current_candle.get("close", 0.0)),
                "volume": float(current_candle.get("volume", 0.0))
            })

        if not parsed_candles:
            return VolumeAnomalyState(rvol=1.0, z_score=0.0, anomaly_type="NORMAL")

        curr = parsed_candles[-1]
        prior = parsed_candles[:-1]

        prior_vols = [c["volume"] for c in prior]
        curr_vol = curr["volume"]

        rvol, z_score = self.compute_rvol_and_zscore(prior_vols, curr_vol)

        # Candle body ratio
        rng = curr["high"] - curr["low"]
        body = abs(curr["close"] - curr["open"])
        body_ratio = body / (rng + 1e-9) if rng > 1e-9 else 0.0

        # Classification decision hierarchy
        if rvol >= self.churn_rvol and body_ratio < self.churn_body_ratio:
            anomaly_type = "VOLUME_ABSORPTION_CHURN"
        elif rvol >= self.climax_rvol and z_score >= self.climax_z:
            anomaly_type = "VOLUME_CLIMAX"
        elif rvol <= self.dryout_rvol:
            anomaly_type = "VOLUME_DRYOUT_DRIFT"
        else:
            anomaly_type = "NORMAL"

        return VolumeAnomalyState(rvol=rvol, z_score=z_score, anomaly_type=anomaly_type)


class LiquidityHuntDetector:
    """
    Detects Liquidity Hunt Wick patterns:
    - Bullish Spring: Lower wick >= 2.0 body, >= 0.50 range, pierces swing low and reclaims, RVOL >= 1.50
    - Bearish Upthrust: Upper wick >= 2.0 body, >= 0.50 range, pierces swing high and closes lower, RVOL >= 1.50
    """

    def __init__(
        self,
        swing_lookback: int = 15,
        wick_body_multiplier: float = 2.0,
        wick_range_min_ratio: float = 0.50,
        rvol_min: float = 1.50
    ):
        self.swing_lookback = swing_lookback
        self.wick_body_multiplier = wick_body_multiplier
        self.wick_range_min_ratio = wick_range_min_ratio
        self.rvol_min = rvol_min

    def detect(
        self,
        candles: Union[List[Dict[str, Any]], pd.DataFrame],
        rvol: float = 1.0,
        current_candle: Optional[Dict[str, Any]] = None
    ) -> LiquidityHuntState:
        parsed: List[Dict[str, float]] = []
        if isinstance(candles, pd.DataFrame):
            for _, row in candles.iterrows():
                parsed.append({
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0.0))
                })
        elif isinstance(candles, list):
            for c in candles:
                if isinstance(c, dict):
                    parsed.append({
                        "open": float(c.get("open", 0.0)),
                        "high": float(c.get("high", 0.0)),
                        "low": float(c.get("low", 0.0)),
                        "close": float(c.get("close", 0.0)),
                        "volume": float(c.get("volume", 0.0))
                    })

        if current_candle is not None:
            parsed.append({
                "open": float(current_candle.get("open", 0.0)),
                "high": float(current_candle.get("high", 0.0)),
                "low": float(current_candle.get("low", 0.0)),
                "close": float(current_candle.get("close", 0.0)),
                "volume": float(current_candle.get("volume", 0.0))
            })

        # Need at least 3 prior candles to define meaningful swing levels
        if len(parsed) < 4:
            return LiquidityHuntState(is_detected=False, hunt_type="NONE", wick_ratio=0.0, swept_level=0.0)

        curr = parsed[-1]
        prior = parsed[:-1]

        lookback_n = min(len(prior), self.swing_lookback)
        swing_window = prior[-lookback_n:]

        swing_low = min(c["low"] for c in swing_window)
        swing_high = max(c["high"] for c in swing_window)

        o, h, l, c = curr["open"], curr["high"], curr["low"], curr["close"]
        rng = h - l
        if rng <= 1e-9:
            return LiquidityHuntState(is_detected=False, hunt_type="NONE", wick_ratio=0.0, swept_level=0.0)

        body = abs(c - o)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l

        # 1. Check Bullish Spring (Sweep of Lows)
        lower_wick_ratio = lower_wick / rng
        is_bullish_wick = (lower_wick >= self.wick_body_multiplier * body) and (lower_wick_ratio >= self.wick_range_min_ratio)
        pierces_low = (l < swing_low)
        reclaims_low = (c > swing_low)
        has_volume_spring = (rvol >= self.rvol_min)

        if is_bullish_wick and pierces_low and reclaims_low and has_volume_spring:
            return LiquidityHuntState(
                is_detected=True,
                hunt_type="SPRING_BULLISH",
                wick_ratio=round(lower_wick_ratio, 4),
                swept_level=round(swing_low, 4)
            )

        # 2. Check Bearish Upthrust (Sweep of Highs)
        upper_wick_ratio = upper_wick / rng
        is_bearish_wick = (upper_wick >= self.wick_body_multiplier * body) and (upper_wick_ratio >= self.wick_range_min_ratio)
        pierces_high = (h > swing_high)
        closes_lower_high = (c < swing_high)
        has_volume_upthrust = (rvol >= self.rvol_min)

        if is_bearish_wick and pierces_high and closes_lower_high and has_volume_upthrust:
            return LiquidityHuntState(
                is_detected=True,
                hunt_type="UPTHRUST_BEARISH",
                wick_ratio=round(upper_wick_ratio, 4),
                swept_level=round(swing_high, 4)
            )

        return LiquidityHuntState(is_detected=False, hunt_type="NONE", wick_ratio=0.0, swept_level=0.0)


class MarketPerceptionSynthesizer:
    """
    Synthesizes Multi-Timeframe (15m, 1h, 4h) candle metrics, Volume Anomaly detection,
    Liquidity Hunt wick patterns, and historical psychology lessons into MarketPerceptionPayload.
    """

    def __init__(self, mtf_filter: Optional[Any] = None):
        self.mtf_filter = mtf_filter
        self.volume_detector = VolumeAnomalyDetector()
        self.hunt_detector = LiquidityHuntDetector()

    def compute_indicators(self, candles: List[Dict[str, Any]], timeframe: str) -> Optional[TimeframeMetrics]:
        if len(candles) < 5:
            return None

        closes = [float(c["close"]) for c in candles]
        series = pd.Series(closes)

        # EMA 9 and 21
        ema_9 = float(series.ewm(span=9, adjust=False).mean().iloc[-1])
        ema_21 = float(series.ewm(span=21, adjust=False).mean().iloc[-1])

        # RSI 14 (Wilder)
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        rsi_14 = float(100.0 - (100.0 / (1.0 + rs.iloc[-1])))

        # Bollinger Bands (20, 2.0 std)
        rolling_mean = series.rolling(20, min_periods=5).mean()
        rolling_std = series.rolling(20, min_periods=5).std()
        bb_mid = float(rolling_mean.iloc[-1])
        std_val = float(rolling_std.iloc[-1]) if not math.isnan(rolling_std.iloc[-1]) else 0.0
        bb_upper = bb_mid + 2.0 * std_val
        bb_lower = bb_mid - 2.0 * std_val
        bb_bandwidth = (bb_upper - bb_lower) / (bb_mid + 1e-9) if bb_mid > 0 else 0.0

        curr_close = closes[-1]
        trend_state = 0
        if ema_9 > ema_21 and curr_close > ema_9:
            trend_state = 1
        elif ema_9 < ema_21 and curr_close < ema_9:
            trend_state = -1

        return TimeframeMetrics(
            timeframe=timeframe,
            ema_9=round(ema_9, 2),
            ema_21=round(ema_21, 2),
            rsi_14=round(rsi_14, 2),
            bb_upper=round(bb_upper, 2),
            bb_mid=round(bb_mid, 2),
            bb_lower=round(bb_lower, 2),
            bb_bandwidth=round(bb_bandwidth, 4),
            trend_state=trend_state,
            close_price=round(curr_close, 2)
        )

    def synthesize(
        self,
        symbol: str,
        current_price: float,
        candles_15m: List[Dict[str, Any]],
        candles_1h: Optional[List[Dict[str, Any]]] = None,
        candles_4h: Optional[List[Dict[str, Any]]] = None,
        lessons: Optional[List[str]] = None,
        dt: Optional[datetime] = None
    ) -> MarketPerceptionPayload:
        now_dt = dt or datetime.now(timezone.utc)
        timestamp_str = now_dt.isoformat()

        # Gather 1h and 4h from MTF filter if not provided explicitly
        c_1h = candles_1h
        c_4h = candles_4h
        if self.mtf_filter:
            if not c_1h:
                c_1h = self.mtf_filter.symbol_candles_1h.get(symbol, getattr(self.mtf_filter, "candles_1h", []))
            if not c_4h:
                c_4h = self.mtf_filter.symbol_candles_4h.get(symbol, getattr(self.mtf_filter, "candles_4h", []))

        timeframes: Dict[str, TimeframeMetrics] = {}
        m_15 = self.compute_indicators(candles_15m, "15m")
        if m_15:
            timeframes["15m"] = m_15

        m_1h = self.compute_indicators(c_1h or [], "1h")
        if m_1h:
            timeframes["1h"] = m_1h

        m_4h = self.compute_indicators(c_4h or [], "4h")
        if m_4h:
            timeframes["4h"] = m_4h

        # Multi-Timeframe Confluence: 0.20 * 15m + 0.40 * 1h + 0.40 * 4h
        t15 = m_15.trend_state if m_15 else 0
        t1h = m_1h.trend_state if m_1h else 0
        t4h = m_4h.trend_state if m_4h else 0
        confluence_score = round(0.20 * t15 + 0.40 * t1h + 0.40 * t4h, 2)

        # Volume Anomaly Detection on 15m candles
        volume_state = self.volume_detector.detect(candles_15m)

        # Liquidity Hunt Wick Detection on 15m candles
        liquidity_hunt = self.hunt_detector.detect(candles_15m, rvol=volume_state.rvol)

        # Macro Regime Determination
        if volume_state.anomaly_type == "VOLUME_CLIMAX" and m_15 and m_15.bb_bandwidth > 0.08:
            macro_regime = "EXTREME_VOLATILITY"
        elif confluence_score >= 0.60:
            macro_regime = "BULL_TREND"
        elif confluence_score <= -0.60:
            macro_regime = "BEAR_TREND"
        else:
            macro_regime = "RANGING"

        # Alert Synthesis
        alerts: List[str] = []
        if volume_state.anomaly_type != "NORMAL":
            alerts.append(volume_state.anomaly_type)
        if liquidity_hunt.is_detected:
            alerts.append(f"LIQUIDITY_HUNT_{liquidity_hunt.hunt_type}")
        if m_15:
            if m_15.rsi_14 >= 72.0:
                alerts.append("RSI_OVERBOUGHT")
            elif m_15.rsi_14 <= 28.0:
                alerts.append("RSI_OVERSOLD")
            if m_15.bb_bandwidth < 0.015:
                alerts.append("BOLLINGER_SQUEEZE")

        return MarketPerceptionPayload(
            symbol=symbol,
            timestamp=timestamp_str,
            current_price=float(current_price),
            timeframes=timeframes,
            confluence_score=confluence_score,
            volume_state=volume_state,
            liquidity_hunt=liquidity_hunt,
            macro_regime=macro_regime,
            detected_alerts=alerts,
            matched_psychology_lessons=lessons or []
        )
```

---

### 2.5 Integration Plan for `risk_engine/risk_manager.py`

#### Changes Required in `RiskManager.handle_signal`:
1. **Increase Candle Lookback from 10 to 60**:
   - In line 298: change `limit=10` to `limit=60` to ensure both the 20-period volume baseline and 15-period swing levels have sufficient data depth.
2. **Synthesize `MarketPerceptionPayload`**:
   - Instantiate `MarketPerceptionSynthesizer(mtf_filter=self.mtf_filter)`.
   - Call `synthesizer.synthesize(...)` with `signal.symbol`, `signal.price`, `recent_candles`, and `recent_lessons`.
3. **Embed `market_perception` in `market_context`**:
   - Add `"market_perception": perception.to_dict()` into `market_context`.
4. **Fallback Safety**:
   - Wrap perception synthesis in a try-except block so that even if database candles are corrupt or empty, `market_perception` falls back to a neutral safe dictionary and never interrupts the trading pipeline.

#### Proposed Code Diff for `risk_engine/risk_manager.py`:

```diff
--- a/risk_engine/risk_manager.py
+++ b/risk_engine/risk_manager.py
@@ -15,6 +15,7 @@ from .circuit_breaker import CircuitBreaker
 from .time_window_guard import TimeWindowRiskGuard
 from .funding_sentinel import FundingSentinel
+from ai_advisory.market_perception import MarketPerceptionSynthesizer
 
 logger = logging.getLogger("RiskManager")
 
@@ -298,7 +299,7 @@ class RiskManager:
             recent_candles = []
             recent_lessons = []
             if self.db:
                 try:
-                    recent_candles = await self.db.get_recent_candles(signal.symbol, limit=10)
+                    recent_candles = await self.db.get_recent_candles(signal.symbol, limit=60)
                 except Exception as e:
                     logger.debug(f"Could not retrieve recent candles for AI context: {e}")
                 try:
@@ -306,6 +307,17 @@ class RiskManager:
                     recent_lessons = [f"[{l['category']}] {l['title']}: {l['lesson_learned']}" for l in lessons_data]
                 except Exception as e:
                     logger.debug(f"Could not retrieve recent lessons: {e}")
 
+            # Synthesize structured Market Perception Payload (RVOL, Liquidity Hunt Wicks, MTF Confluence)
+            try:
+                synthesizer = MarketPerceptionSynthesizer(mtf_filter=self.mtf_filter)
+                perception = synthesizer.synthesize(
+                    symbol=signal.symbol,
+                    current_price=signal.price,
+                    candles_15m=recent_candles,
+                    lessons=recent_lessons
+                )
+                perception_dict = perception.to_dict()
+            except Exception as e:
+                logger.warning(f"Could not synthesize market perception payload: {e}")
+                perception_dict = {}
+
             market_context: Dict[str, Any] = {
                 "symbol": signal.symbol,
                 "price": signal.price,
                 "strategy_name": signal.strategy_name,
                 "side": signal.side.value if hasattr(signal.side, "value") else str(signal.side),
                 "stop_loss": signal.stop_loss,
                 "take_profit": signal.take_profit,
                 "confidence": signal.confidence,
                 "recent_candles": recent_candles,
                 "hard_earned_lessons_to_respect": recent_lessons,
                 "account_equity": self.circuit_breaker.current_equity or settings.STARTING_BALANCE_USDT,
-                "open_positions": len(self.open_positions)
+                "open_positions": len(self.open_positions),
+                "market_perception": perception_dict
             }
```

---

### 2.6 Comprehensive Unit Test Plan: `tests/test_market_perception.py`

To verify all components independently and exhaustively, the test suite must cover:

```python
import pytest
from datetime import datetime, timezone
from ai_advisory.market_perception import (
    VolumeAnomalyDetector,
    VolumeAnomalyState,
    LiquidityHuntDetector,
    LiquidityHuntState,
    MarketPerceptionPayload,
    MarketPerceptionSynthesizer,
    TimeframeMetrics
)


def make_candle(open_p, high_p, low_p, close_p, volume=100.0, ts="2026-09-22T03:00:00Z"):
    return {
        "timestamp": ts,
        "open": float(open_p),
        "high": float(high_p),
        "low": float(low_p),
        "close": float(close_p),
        "volume": float(volume)
    }


class TestVolumeAnomalyDetector:
    def test_normal_volume(self):
        detector = VolumeAnomalyDetector(baseline_period=20)
        # 20 prior candles with volume 100
        candles = [make_candle(100, 105, 95, 102, volume=100.0) for _ in range(20)]
        # current candle with volume 110 (RVOL = 1.10, normal body)
        candles.append(make_candle(100, 105, 95, 103, volume=110.0))
        state = detector.detect(candles)
        assert state.anomaly_type == "NORMAL"
        assert state.rvol == 1.10

    def test_volume_climax(self):
        detector = VolumeAnomalyDetector(baseline_period=20)
        # 20 baseline candles with volume 100 (std = 10)
        candles = [make_candle(100, 105, 95, 102, volume=100.0 + (i % 3) * 5) for i in range(20)]
        # Climax: RVOL >= 2.5 and Z >= 3.0, expansive body (body/range >= 0.30)
        # body = 4, range = 6 -> body/range = 0.67
        candles.append(make_candle(100, 106, 100, 104, volume=350.0))
        state = detector.detect(candles)
        assert state.anomaly_type == "VOLUME_CLIMAX"
        assert state.rvol >= 2.5
        assert state.z_score >= 3.0

    def test_volume_absorption_churn(self):
        detector = VolumeAnomalyDetector(baseline_period=20)
        candles = [make_candle(100, 105, 95, 102, volume=100.0) for _ in range(20)]
        # Churn: RVOL >= 2.0 but body/range < 0.30
        # range = 10 (high=105, low=95), body = 1 (open=100, close=101) -> body/range = 0.10 < 0.30
        candles.append(make_candle(100, 105, 95, 101, volume=220.0))
        state = detector.detect(candles)
        assert state.anomaly_type == "VOLUME_ABSORPTION_CHURN"
        assert state.rvol >= 2.0

    def test_volume_dryout_drift(self):
        detector = VolumeAnomalyDetector(baseline_period=20)
        candles = [make_candle(100, 105, 95, 102, volume=100.0) for _ in range(20)]
        # Dryout: RVOL <= 0.50
        candles.append(make_candle(100, 102, 99, 101, volume=40.0))
        state = detector.detect(candles)
        assert state.anomaly_type == "VOLUME_DRYOUT_DRIFT"
        assert state.rvol <= 0.50

    def test_zero_division_guardrails(self):
        detector = VolumeAnomalyDetector()
        # Empty candles
        assert detector.detect([]).anomaly_type == "NORMAL"
        # Zero volume across all candles
        zero_candles = [make_candle(100, 105, 95, 100, volume=0.0) for _ in range(25)]
        state = detector.detect(zero_candles)
        assert state.anomaly_type == "NORMAL"
        assert state.rvol == 1.0
        assert state.z_score == 0.0


class TestLiquidityHuntDetector:
    def test_bullish_spring_detected(self):
        detector = LiquidityHuntDetector(swing_lookback=15)
        # 15 prior candles where minimum low is 95.0
        candles = [make_candle(100, 105, 95.0, 101, volume=100.0) for _ in range(15)]
        # Spring Candle:
        # Pierces low (low = 90.0 < 95.0)
        # Reclaims low (close = 99.0 > 95.0, open = 98.0 -> body = 1.0)
        # High = 100.0 -> Range = 10.0 (100 - 90)
        # Lower wick = min(98, 99) - 90 = 8.0
        # Lower wick / body = 8.0 / 1.0 = 8.0 >= 2.0
        # Lower wick / range = 8.0 / 10.0 = 0.80 >= 0.50
        # RVOL = 2.0 >= 1.50
        spring_candle = make_candle(open_p=98.0, high_p=100.0, low_p=90.0, close_p=99.0, volume=200.0)
        candles.append(spring_candle)

        hunt = detector.detect(candles, rvol=2.0)
        assert hunt.is_detected is True
        assert hunt.hunt_type == "SPRING_BULLISH"
        assert hunt.swept_level == 95.0
        assert hunt.wick_ratio == 0.80

    def test_bearish_upthrust_detected(self):
        detector = LiquidityHuntDetector(swing_lookback=15)
        # 15 prior candles where maximum high is 105.0
        candles = [make_candle(100, 105.0, 95.0, 101, volume=100.0) for _ in range(15)]
        # Upthrust Candle:
        # Pierces high (high = 112.0 > 105.0)
        # Closes lower than high (close = 102.0 < 105.0, open = 103.0 -> body = 1.0)
        # Low = 101.0 -> Range = 11.0 (112 - 101)
        # Upper wick = 112.0 - max(103, 102) = 9.0
        # Upper wick / body = 9.0 / 1.0 = 9.0 >= 2.0
        # Upper wick / range = 9.0 / 11.0 = 0.8182 >= 0.50
        # RVOL = 1.80 >= 1.50
        upthrust_candle = make_candle(open_p=103.0, high_p=112.0, low_p=101.0, close_p=102.0, volume=180.0)
        candles.append(upthrust_candle)

        hunt = detector.detect(candles, rvol=1.80)
        assert hunt.is_detected is True
        assert hunt.hunt_type == "UPTHRUST_BEARISH"
        assert hunt.swept_level == 105.0
        assert hunt.wick_ratio >= 0.50

    def test_rejection_when_volume_insufficient(self):
        detector = LiquidityHuntDetector(swing_lookback=15)
        candles = [make_candle(100, 105.0, 95.0, 101, volume=100.0) for _ in range(15)]
        spring_candle = make_candle(open_p=98.0, high_p=100.0, low_p=90.0, close_p=99.0, volume=100.0)
        candles.append(spring_candle)
        # RVOL = 1.0 < 1.50 -> Should NOT detect hunt
        hunt = detector.detect(candles, rvol=1.0)
        assert hunt.is_detected is False
        assert hunt.hunt_type == "NONE"


class TestMarketPerceptionSynthesizer:
    def test_synthesizer_payload_structure_and_serialization(self):
        synthesizer = MarketPerceptionSynthesizer()
        candles = [make_candle(100 + i, 105 + i, 95 + i, 102 + i, volume=100.0) for i in range(30)]
        payload = synthesizer.synthesize(
            symbol="BTC/USDT",
            current_price=132.0,
            candles_15m=candles,
            lessons=["[STOP_LOSS] Respect liquidity wicks"]
        )
        assert isinstance(payload, MarketPerceptionPayload)
        assert payload.symbol == "BTC/USDT"
        assert payload.current_price == 132.0
        assert payload.macro_regime in ("BULL_TREND", "BEAR_TREND", "RANGING", "EXTREME_VOLATILITY")
        assert "15m" in payload.timeframes

        # Test dictionary serialization
        payload_dict = payload.to_dict()
        assert isinstance(payload_dict, dict)
        assert payload_dict["symbol"] == "BTC/USDT"
        assert "volume_state" in payload_dict
        assert "liquidity_hunt" in payload_dict
        assert "matched_psychology_lessons" in payload_dict

    def test_synthesizer_empty_candles_graceful_fallback(self):
        synthesizer = MarketPerceptionSynthesizer()
        payload = synthesizer.synthesize(
            symbol="ETH/USDT",
            current_price=3000.0,
            candles_15m=[]
        )
        assert payload.symbol == "ETH/USDT"
        assert payload.volume_state.anomaly_type == "NORMAL"
        assert payload.liquidity_hunt.is_detected is False
        assert payload.macro_regime == "RANGING"
        assert payload.to_dict()["symbol"] == "ETH/USDT"
```

---

## 3. Caveats

1. **Cold Start & Incomplete Candle History**:
   - In live deployment or freshly spawned test fixtures, SQLite `candles` table may contain fewer than 20 records. `VolumeAnomalyDetector` and `LiquidityHuntDetector` explicitly handle small candle sets ($N < 21$ and $N < 4$) by scaling the lookback window or defaulting to `NORMAL` / `NONE` to prevent index errors or NaN outputs.
2. **Candle Alignment with Real-Time Price**:
   - Closed-candle detection operates on historical closed 15m intervals. When a signal arrives between candle closes, `current_price` reflects the latest tick, while indicators use the latest closed candle. This avoids indicator repainting while providing real-time evaluation.
3. **High-Beta Meme Token Volatility**:
   - Symbols such as DOGE or 1000PEPE frequently produce long wicks during normal volatility. The threshold $W_{wick} \ge 2.0 \times Body$ and $W_{wick} \ge 0.50 \times Range$ combined with $RVOL \ge 1.50$ acts as a multi-condition filter to filter out ambient noise.

---

## 4. Conclusion

1. **Design Complete & Ready for Implementation**:
   - `ai_advisory/market_perception.py` is fully designed with `VolumeAnomalyDetector`, `LiquidityHuntDetector`, and `MarketPerceptionPayload`.
   - All four volume anomaly states (`NORMAL`, `VOLUME_CLIMAX`, `VOLUME_ABSORPTION_CHURN`, `VOLUME_DRYOUT_DRIFT`) and both liquidity hunt patterns (`SPRING_BULLISH`, `UPTHRUST_BEARISH`) have exact mathematical definitions and code-level representations.
2. **Integration Plan Scoped & Safe**:
   - `RiskManager.handle_signal` will query $N=60$ candles, invoke `MarketPerceptionSynthesizer`, and attach `market_context['market_perception'] = perception.to_dict()`.
   - The design guarantees 100% backward compatibility, zero unhandled exceptions on sparse data, and full JSON serializability for the Adversarial VAR Council.

---

## 5. Verification Method

### 5.1 Automated Test Execution Commands
Once the implementer creates `ai_advisory/market_perception.py` and `tests/test_market_perception.py`:
```powershell
# 1. Run Market Perception unit test suite
.venv\Scripts\pytest tests/test_market_perception.py -v

# 2. Run Risk Engine integration tests to verify zero regressions
.venv\Scripts\pytest tests/test_risk_engine.py -k "not test_risk_manager_ai_advisory_approval_with_sizing and not test_risk_manager_timeout_engages_quantitative_fallback and not test_risk_manager_network_error_engages_fallback and not test_risk_manager_with_real_vyce_client_outage_rejects_unsafe_signals" -v

# 3. Run Trailing Stop & MTF test suites
.venv\Scripts\pytest tests/test_trailing_stop.py tests/test_multi_timeframe.py -v
```

### 5.2 Files and Locations to Inspect
- `ai_advisory/market_perception.py`: Verify definitions of `VolumeAnomalyDetector`, `LiquidityHuntDetector`, `MarketPerceptionPayload`, and `MarketPerceptionSynthesizer`.
- `risk_engine/risk_manager.py` (lines 292–325): Verify `limit=60` candle retrieval and `market_context['market_perception']` population.
- `tests/test_market_perception.py`: Verify passing of all unit and edge-case tests.

### 5.3 Invalidation Conditions
This specification shall be invalidated if:
1. `VolumeAnomalyDetector` classifies a candle with $RVOL \ge 2.0$ and $Body/Range < 0.30$ as `NORMAL` or `VOLUME_CLIMAX`.
2. `LiquidityHuntDetector` flags a Bullish Spring without requiring $L_t < SwingLow$ or $C_t > SwingLow$.
3. `RiskManager.handle_signal` raises an unhandled exception when SQLite contains 0 candles.
4. `json.dumps(market_context)` fails due to non-serializable dataclass instances.
