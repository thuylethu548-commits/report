# Handoff Report: Multi-Timeframe Closed Candle Synchronization, Technical Indicators, and Trend Confluence Engine

**Author**: m1_auton_explorer_1 (Teamwork Explorer for Milestone 1)  
**Date**: 2026-09-22T03:05:00Z  
**Target Milestone**: Milestone 1 (Multi-Timeframe Perception, Indicator Engine & Trend Confluence)  
**Parent Conversation ID**: e9b53268-5666-44c8-8876-b9e21cf9f943  
**Working Directory**: `c:\sunMy\trading_bot\.agents\m1_auton_explorer_1`  
**Project Root**: `c:\sunMy\trading_bot`  

---

## 1. Observation

Direct investigation of the project source code, test suites, and historical specifications revealed the current state and identified key architectural gaps:

### 1.1 Existing Implementations in Codebase

1. **`strategies/multi_timeframe.py` (lines 9–125)**:
   - `MultiTimeframeFilter` tracks 1h and 4h historical candle buffers (`candles_1h`, `candles_4h`) with `max_candles=200` (default) and calculates `EMA(50)` via `calculate_ema(timeframe, symbol)`.
   - `check_confluence(symbol, current_price, side)`:
     * For `BUY`: requires `current_price >= ema_1h` AND `current_price >= ema_4h`.
     * For `SELL` / `SHORT`: requires `current_price < ema_1h` AND `current_price < ema_4h`.
     * Returns a dictionary:
       ```python
       {
           "approved": bool,
           "reason": str,
           "ema_1h": Optional[float],
           "ema_4h": Optional[float],
           "trend_1h": "BULLISH" | "BEARISH" | "UNKNOWN",
           "trend_4h": "BULLISH" | "BEARISH" | "UNKNOWN"
       }
       ```
   - `warmup(binance_client, symbol)` (lines 226–241): Fetches 60 candles each for 1h and 4h timeframes via `binance_client.fetch_ohlcv(symbol, timeframe, limit=60)`.

2. **`strategies/ema_trend.py` (lines 39–51)**:
   - Calculates fast EMA (`span=9`) and slow EMA (`span=21`) using:
     ```python
     df["ema_fast"] = df["close"].ewm(span=self.fast_period, adjust=False).mean()
     df["ema_slow"] = df["close"].ewm(span=self.slow_period, adjust=False).mean()
     ```
   - Calculates True Range and ATR(14) using a simple rolling mean:
     ```python
     tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
     atr = tr.rolling(self.atr_period).mean().iloc[-1]
     ```

3. **`strategies/rsi_bollinger.py` (lines 39–52)**:
   - Calculates Bollinger Bands (SMA 20, 2.0 std):
     ```python
     sma = df["close"].rolling(self.bb_period).mean()
     std = df["close"].rolling(self.bb_period).std()
     df["bb_mid"] = sma
     df["bb_upper"] = sma + (self.bb_std * std)
     df["bb_lower"] = sma - (self.bb_std * std)
     ```
   - Calculates RSI(14) using simple rolling mean (SMA of gains and losses):
     ```python
     gain = delta.where(delta > 0, 0.0).rolling(self.rsi_period).mean()
     loss = (-delta.where(delta < 0, 0.0)).rolling(self.rsi_period).mean()
     rs = gain / (loss + 1e-9)
     df["rsi"] = 100 - (100 / (1 + rs))
     ```

4. **`risk_engine/risk_manager.py` (lines 271–286)**:
   - Calls `self.mtf_filter.check_confluence(signal.symbol, signal.price, side=side_str)` as Check 1.4 in Phase 1 deterministic gates.
   - If `approved == False`, vetoes the signal immediately and records `"🚫 MTF Veto [...]"`.

5. **`main.py` (lines 108, 164–169, 238–246)**:
   - Instantiates `mtf_filter = MultiTimeframeFilter(ema_period=settings.MTF_EMA_PERIOD)`.
   - Runs `await mtf_filter.warmup(binance_client, sym)` on startup.
   - However, during the live WebSocket event loop (`on_market_event` lines 164–186), closed market events are forwarded only to `strategies_ema` and `strategies_rsi`, but **never** passed into `mtf_filter.add_candle`!

6. **`tests/test_multi_timeframe.py` (lines 28–56, 58–117)**:
   - Verifies `MultiTimeframeFilter.calculate_ema` and `check_confluence`.
   - Verified passing: `pytest tests/test_multi_timeframe.py -v` -> 2 passed in 5.94s.

### 1.2 Critical Architectural Gaps Identified

| # | Gap Area | Current Code State | Milestone 1 Requirement |
|---|----------|-------------------|-------------------------|
| **G1** | 15m Base Candle Buffer | `MultiTimeframeFilter` only has `candles_1h` and `candles_4h`. No 15m buffer exists. | Maintain circular buffers of depth $N=100$ for all three timeframes: 15m, 1h, 4h. |
| **G2** | Multi-Symbol State Isolation | In `multi_timeframe.py:56`, `add_candle` does not accept `symbol`. Only global lists `candles_1h` and `candles_4h` are modified. | Thread-safe, symbol-keyed dictionary of circular buffers: `self.buffers[symbol][timeframe]`. |
| **G3** | Live Candle Synchronization | `main.py:164` never routes closed `MarketEvent` ticks to `mtf_filter`. 1h and 4h buffers become stale post-warmup. | Real-time automatic closed candle aggregation from 15m base into 1h and 4h candles upon official candle close. |
| **G4** | RSI Smoothing Discrepancy | `rsi_bollinger.py:48-49` uses `rolling(14).mean()` (SMA). | Wilder's authentic SMMA smoothing: $\alpha = 1/14$ ($Avg_t = (13 \cdot Avg_{t-1} + X_t)/14$). |
| **G5** | Missing Indicators on MTF | `MultiTimeframeFilter` only computes `EMA(50)`. No EMA 9/21, RSI 14, BB 20/2, or ATR 14. | Implement complete indicator suite across 15m, 1h, and 4h closed candles. |
| **G6** | Confluence Scoring Model | Binary True/False based solely on EMA 50. | Quantitative confluence score: $Score = 0.20 \cdot Trend_{15m} + 0.40 \cdot Trend_{1h} + 0.40 \cdot Trend_{4h} \in [-1.0, +1.0]$. |

---

## 2. Logic Chain

Step-by-step reasoning from observations to the finalized architectural design:

### Step 2.1: Multi-Timeframe Closed Candle Synchronization & Non-Repainting Invariant

To satisfy **Feature F1.1** without look-ahead bias or indicator repainting:

1. **Closed Candle Invariant**:
   - Indicator values must never change retroactively.
   - An indicator on timeframe $\tau \in \{15m, 1h, 4h\}$ is calculated **only on closed candles**.
   - An incoming tick or in-progress candle (`is_candle_closed == False`) is **never appended** to the buffer.

2. **Circular Buffer Specification**:
   - Buffer depth: $N = 100$ closed candles per timeframe per symbol.
   - Data structure: `collections.deque(maxlen=100)` or list slice `[-100:]`.
   - Each candle dictionary contains:
     ```python
     {
         "timestamp": float,  # Epoch timestamp in ms or seconds
         "open": float,
         "high": float,
         "low": float,
         "close": float,
         "volume": float
     }
     ```

3. **Dual Ingestion Channels**:
   - **Channel A (Direct External Feed / Warmup / Tests)**:
     `set_candles(timeframe, raw_candles, symbol=None)` and `add_candle(timeframe, candle, symbol=None)`.
     Directly stores closed candles from Binance REST API (`fetch_ohlcv`) or test fixtures.
   - **Channel B (Dynamic Auto-Aggregation from 15m Base)**:
     In live trading, `BinanceWebSocketFeed` only subscribes to `@kline_15m`. When a 15m candle closes (`is_candle_closed == True`), `mtf_filter.add_candle("15m", candle, symbol=symbol)` triggers auto-aggregation:
     * Duration: $\Delta t_{15m} = 900\text{ s}$ ($900,000\text{ ms}$).
     * Let $T_{open}$ be the candle open timestamp.
     * Calculate candle completion time: $T_{close\_epoch} = T_{open} + 900\text{ s}$ (if seconds) or $T_{open} + 900,000\text{ ms}$ (if milliseconds).
     * **1h Boundary Trigger**:
       $$\text{If } (T_{close\_epoch} \pmod{3600\text{ s}} == 0) \quad [\text{or } T_{close\_epoch} \pmod{3,600,000\text{ ms}} == 0]:$$
       The 1h candle has closed! Aggregate the last 4 candles from `buffers[symbol]["15m"]`:
       - $Open_{1h} = C_{15m}[-4].open$
       - $High_{1h} = \max_{i=-4..-1}(C_{15m}[i].high)$
       - $Low_{1h} = \min_{i=-4..-1}(C_{15m}[i].low)$
       - $Close_{1h} = C_{15m}[-1].close$
       - $Volume_{1h} = \sum_{i=-4..-1}(C_{15m}[i].volume)$
       - $Timestamp_{1h} = C_{15m}[-4].timestamp$
       Append to `buffers[symbol]["1h"]`.
     * **4h Boundary Trigger**:
       $$\text{If } (T_{close\_epoch} \pmod{14400\text{ s}} == 0) \quad [\text{or } T_{close\_epoch} \pmod{14,400,000\text{ ms}} == 0]:$$
       The 4h candle has closed! Aggregate the last 16 candles from `buffers[symbol]["15m"]` (or the last 4 candles from `buffers[symbol]["1h"]`):
       - $Open_{4h} = C_{15m}[-16].open$
       - $High_{4h} = \max_{i=-16..-1}(C_{15m}[i].high)$
       - $Low_{4h} = \min_{i=-16..-1}(C_{15m}[i].low)$
       - $Close_{4h} = C_{15m}[-1].close$
       - $Volume_{4h} = \sum_{i=-16..-1}(C_{15m}[i].volume)$
       - $Timestamp_{4h} = C_{15m}[-16].timestamp$
       Append to `buffers[symbol]["4h"]`.

   *De-duplication rule*: Before appending an auto-aggregated candle, check if the last candle in `buffers[symbol]["1h"]` has the same timestamp. If identical, replace it; if newer, append. This prevents duplicate candles if external feeds and auto-aggregation run concurrently.

---

### Step 2.2: Mathematical Indicator Specifications

To fulfill **Feature F1.2**, implement exact, numerically stable indicator formulas:

#### 1. Exponential Moving Averages (EMA 9, EMA 21, and EMA 50)
- Smoothing factor: $\alpha_k = \frac{2}{k + 1}$.
  * $\alpha_9 = \frac{2}{10} = 0.20$
  * $\alpha_{21} = \frac{2}{22} = \frac{1}{11} \approx 0.090909$
  * $\alpha_{50} = \frac{2}{51} \approx 0.039216$
- Recurrence:
  $$EMA_{k, t} = \alpha_k \cdot P_{close, t} + (1 - \alpha_k) \cdot EMA_{k, t-1}$$
- Implementation: `pd.Series(closes).ewm(span=k, adjust=False).mean().iloc[-1]`.
- Minimum buffer requirement: at least 5 candles for baseline; 25+ candles for full convergence.

#### 2. Relative Strength Index (RSI 14) with Wilder's SMMA Smoothing
- Difference: $\Delta P_t = P_{close, t} - P_{close, t-1}$.
- Upward change: $U_t = \max(\Delta P_t, 0.0)$.
- Downward change: $D_t = \max(-\Delta P_t, 0.0)$.
- Wilder's Smoothing ($n = 14$, $\alpha = 1/14$):
  $$AvgGain_t = \frac{13 \cdot AvgGain_{t-1} + U_t}{14}$$
  $$AvgLoss_t = \frac{13 \cdot AvgLoss_{t-1} + D_t}{14}$$
- Initial seed at $t = 14$:
  $$AvgGain_{14} = \frac{1}{14}\sum_{i=1}^{14} U_i, \quad AvgLoss_{14} = \frac{1}{14}\sum_{i=1}^{14} D_i$$
- Relative Strength & Index:
  $$RS_t = \frac{AvgGain_t}{AvgLoss_t + 10^{-12}}, \quad RSI_{14, t} = 100.0 - \frac{100.0}{1.0 + RS_t}$$
  * If $AvgLoss_t == 0$: $RSI = 100.0$ if $AvgGain_t > 0$ else $50.0$.
- Minimum buffer requirement: $\ge 15$ candles.

#### 3. Bollinger Bands (20 periods, 2.0 standard deviations)
- Middle Band (SMA 20):
  $$SMA_{20, t} = \frac{1}{20}\sum_{i=0}^{19} P_{close, t-i}$$
- Standard Deviation:
  $$\sigma_{20, t} = \sqrt{\frac{1}{20}\sum_{i=0}^{19} (P_{close, t-i} - SMA_{20, t})^2}$$
- Upper & Lower Bands:
  $$Upper_t = SMA_{20, t} + 2.0 \cdot \sigma_{20, t}$$
  $$Lower_t = SMA_{20, t} - 2.0 \cdot \sigma_{20, t}$$
- Bandwidth & %B:
  $$Bandwidth_t = \frac{Upper_t - Lower_t}{SMA_{20, t} + 10^{-12}}$$
  $$\%B_t = \frac{P_{close, t} - Lower_t}{Upper_t - Lower_t + 10^{-12}}$$
- Minimum buffer requirement: $\ge 20$ candles.

#### 4. Average True Range (ATR 14) with Wilder's Smoothing
- True Range:
  $$TR_t = \max\left( High_t - Low_t, \, |High_t - Close_{t-1}|, \, |Low_t - Close_{t-1}| \right)$$
  For $t = 0$: $TR_0 = High_0 - Low_0$.
- Wilder's Smoothing ($n = 14$, $\alpha = 1/14$):
  $$ATR_{14, t} = \frac{13 \cdot ATR_{14, t-1} + TR_t}{14}$$
- Minimum buffer requirement: $\ge 14$ candles (fallback: $P_{close} \times 0.015$).

---

### Step 2.3: Multi-Timeframe Trend Confluence Scoring Engine

To satisfy **Feature F1.4**:

#### 1. Per-Timeframe Momentum Direction ($Trend_{\tau}$)
For each timeframe $\tau \in \{15m, 1h, 4h\}$:
$$Trend_{\tau} = \begin{cases}
+1.0 \text{ (Bullish Momentum)} & \text{if } EMA_{9, \tau} > EMA_{21, \tau} \text{ and } P_{close, \tau} > EMA_{9, \tau} \\
-1.0 \text{ (Bearish Momentum)} & \text{if } EMA_{9, \tau} < EMA_{21, \tau} \text{ and } P_{close, \tau} < EMA_{9, \tau} \\
0.0 \text{ (Neutral / Consolidation)} & \text{otherwise}
\end{cases}$$
*(If buffer has insufficient candles to calculate indicators, $Trend_{\tau} = 0.0$)*.

#### 2. Weighted Confluence Composite Score
$$Score_{confluence} = 0.20 \cdot Trend_{15m} + 0.40 \cdot Trend_{1h} + 0.40 \cdot Trend_{4h}$$
- Range: $[-1.00, +1.00]$.
- Complete 27-State Truth Table & Regime Classification:
  * **$Score \ge +0.80$** $\implies$ `STRONG_BULL` (e.g. $+1, +1, +1 \implies +1.00$; $0, +1, +1 \implies +0.80$). Both 1h and 4h are bullish.
  * **$+0.60 \le Score < +0.80$** $\implies$ `MODERATE_BULL` (e.g. $-1, +1, +1 \implies +0.60$ [Pullback dip in bull trend]; $+1, 0, +1 \implies +0.60$).
  * **$Score \le -0.80$** $\implies$ `STRONG_BEAR` (e.g. $-1, -1, -1 \implies -1.00$; $0, -1, -1 \implies -0.80$). Both 1h and 4h are bearish.
  * **$-0.80 < Score \le -0.60$** $\implies$ `MODERATE_BEAR` (e.g. $+1, -1, -1 \implies -0.60$ [Dead-cat bounce in bear trend]; $-1, 0, -1 \implies -0.60$).
  * **$-0.60 < Score < +0.60$** $\implies$ `RANGING_OR_CONFLICT` (Timeframe divergence, e.g. 1h bull but 4h bear).

#### 3. Signal Gating in `check_confluence`
- **BUY (LONG) Validation**:
  * Approved if:
    1. $Trend_{1h} \ge 0$ AND $Trend_{4h} \ge 0$ (or $P_{close} \ge EMA_{50, 1h}$ and $P_{close} \ge EMA_{50, 4h}$), AND
    2. $Score_{confluence} \ge +0.60$.
  * If $Score_{confluence} < 0.0$ or $Trend_{1h} == -1$ or $Trend_{4h} == -1$: VETO with reason detailing the conflicting timeframe.
- **SELL (SHORT) Validation**:
  * Approved if:
    1. $Trend_{1h} \le 0$ AND $Trend_{4h} \le 0$ (or $P_{close} < EMA_{50, 1h}$ and $P_{close} < EMA_{50, 4h}$), AND
    2. $Score_{confluence} \le -0.60$.
  * If $Score_{confluence} > 0.0$ or $Trend_{1h} == 1$ or $Trend_{4h} == 1$: VETO.
- **Startup Warmup Grace**: If fewer than 5 candles are loaded, pass with `approved=True` and reason `"Chưa đủ dữ liệu nến 1h/4h (Khởi động hệ thống), tạm thời cho phép theo dõi."` (exact backward compatibility with legacy test assertions).

---

### Step 2.4: Code Structure, Method Signatures, and Backwards Compatibility

#### 1. Data Structure Definitions
```python
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Union

@dataclass
class TimeframeMetrics:
    timeframe: str               # "15m", "1h", "4h"
    close_price: float
    ema_9: Optional[float]
    ema_21: Optional[float]
    ema_50: Optional[float]
    rsi_14: Optional[float]
    bb_upper: Optional[float]
    bb_mid: Optional[float]
    bb_lower: Optional[float]
    bb_bandwidth: Optional[float]
    bb_percent_b: Optional[float]
    atr_14: Optional[float]
    trend_state: int             # +1, -1, 0
```

#### 2. Enhanced Class Signature in `strategies/multi_timeframe.py`
```python
class MultiTimeframeFilter:
    def __init__(
        self,
        ema_period: int = 50,
        max_candles: int = 100,
        fast_ema: int = 9,
        slow_ema: int = 21,
        rsi_period: int = 14,
        bb_period: int = 20,
        bb_std: float = 2.0,
        atr_period: int = 14
    ):
        self.ema_period = ema_period
        self.max_candles = max_candles
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.rsi_period = rsi_period
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.atr_period = atr_period

        # Symbol-isolated buffers: symbol -> { "15m": [...], "1h": [...], "4h": [...] }
        self.buffers: Dict[str, Dict[str, List[Dict[str, float]]]] = {}

        # Backward compatibility properties mapping to default buffers
        self.candles_15m: List[Dict[str, float]] = []
        self.candles_1h: List[Dict[str, float]] = []
        self.candles_4h: List[Dict[str, float]] = []
        self.symbol_candles_1h: Dict[str, List[Dict[str, float]]] = {}
        self.symbol_candles_4h: Dict[str, List[Dict[str, float]]] = {}
```

#### 3. Method Signatures and Return Types
1. **`set_candles`**:
   ```python
   def set_candles(
       self,
       timeframe: str,
       raw_candles: Union[List[List[Any]], List[Dict[str, Any]]],
       symbol: Optional[str] = None
   ) -> None
   ```
2. **`add_candle`**:
   ```python
   def add_candle(
       self,
       timeframe: str,
       candle: Union[List[Any], Dict[str, Any]],
       symbol: Optional[str] = None,
       auto_aggregate: bool = True
   ) -> None
   ```
3. **`calculate_ema`**:
   ```python
   def calculate_ema(
       self,
       timeframe: str,
       symbol: Optional[str] = None,
       period: Optional[int] = None
   ) -> Optional[float]
   ```
4. **`calculate_rsi`**:
   ```python
   def calculate_rsi(
       self,
       timeframe: str,
       symbol: Optional[str] = None,
       period: int = 14
   ) -> Optional[float]
   ```
5. **`calculate_bollinger_bands`**:
   ```python
   def calculate_bollinger_bands(
       self,
       timeframe: str,
       symbol: Optional[str] = None,
       period: int = 20,
       std: float = 2.0
   ) -> Optional[Dict[str, float]]
   ```
   Returns: `{"upper": float, "mid": float, "lower": float, "bandwidth": float, "percent_b": float}`.
6. **`calculate_atr`**:
   ```python
   def calculate_atr(
       self,
       timeframe: str,
       symbol: Optional[str] = None,
       period: int = 14
   ) -> Optional[float]
   ```
7. **`get_timeframe_metrics`**:
   ```python
   def get_timeframe_metrics(
       self,
       timeframe: str,
       symbol: Optional[str] = None
   ) -> Optional[TimeframeMetrics]
   ```
8. **`calculate_confluence_score`**:
   ```python
   def calculate_confluence_score(
       self,
       symbol: Optional[str] = None
   ) -> Dict[str, Any]
   ```
   Returns:
   ```python
   {
       "score": float,            # e.g. +0.80
       "trend_15m": int,          # +1, -1, 0
       "trend_1h": int,           # +1, -1, 0
       "trend_4h": int,           # +1, -1, 0
       "regime": str,             # "STRONG_BULL" | "MODERATE_BULL" | "STRONG_BEAR" | "MODERATE_BEAR" | "RANGING_OR_CONFLICT"
       "metrics": Dict[str, Optional[TimeframeMetrics]]
   }
   ```
9. **`check_confluence`** (100% Backward Compatible):
   ```python
   def check_confluence(
       self,
       symbol: str,
       current_price: float,
       side: str = "BUY"
   ) -> Dict[str, Any]
   ```
   Returns exact superset of existing schema:
   ```python
   {
       "approved": bool,
       "reason": str,
       "ema_1h": Optional[float],
       "ema_4h": Optional[float],
       "trend_1h": str,           # "BULLISH" | "BEARISH" | "UNKNOWN"
       "trend_4h": str,           # "BULLISH" | "BEARISH" | "UNKNOWN"
       # Enhanced Milestone 1 fields:
       "confluence_score": float, # -1.0 to +1.0
       "trend_15m": str,          # "BULLISH" | "BEARISH" | "NEUTRAL" | "UNKNOWN"
       "regime": str,             # Macro regime classification
       "metrics_15m": Optional[Dict[str, Any]],
       "metrics_1h": Optional[Dict[str, Any]],
       "metrics_4h": Optional[Dict[str, Any]]
   }
   ```
10. **`warmup`**:
    ```python
    async def warmup(self, binance_client, symbol: str) -> None
    ```
    Fetches 15m, 1h, and 4h historical candles (limit=100 each).

---

### Step 2.5: Integration Wiring Points in Existing Files

1. **`main.py` (lines 164–170)**:
   In `on_market_event`:
   ```python
   # In on_market_event(event: MarketEvent):
   if event.is_candle_closed:
       # Update Multi-Timeframe Engine in real-time
       mtf_filter.add_candle("15m", {
           "timestamp": event.timestamp.timestamp() if hasattr(event.timestamp, "timestamp") else float(event.timestamp),
           "open": event.open,
           "high": event.high,
           "low": event.low,
           "close": event.close,
           "volume": event.volume
       }, symbol=event.symbol, auto_aggregate=True)
   ```
2. **`main.py` (lines 244–246)**:
   In `warmup`: `await mtf_filter.warmup(binance_client, sym)` will now load 15m, 1h, and 4h buffers.
3. **`risk_engine/risk_manager.py` (lines 272–286, 307–320)**:
   Passes `mtf_res["confluence_score"]` and `mtf_res["metrics_15m"]` into `market_context` for AI Council and downstream perception synthesis.

---

## 3. Caveats

1. **Exchange Clock Drift and Epoch Boundaries**:
   - Auto-aggregation relies on candle timestamps aligning with modular multiples of $3,600\text{ s}$ and $14,400\text{ s}$. Binance UTC candle timestamps are strictly aligned ($00\text{m}$, $15\text{m}$, $30\text{m}$, $45\text{m}$). If an unconventional broker or mock source emits unaligned timestamps, auto-aggregation should fall back to counting modulo 4 of consecutive 15m candles.
2. **Missing Candles in WebSocket Stream**:
   - If a network disconnect occurs and 1 or 2 15m candles are missed, auto-aggregating across the gap could produce a distorted 1h candle. To safeguard against this, the periodic background patrol in `telegram_notifier.py` or a dedicated 15m timer should periodically fetch REST candles via `binance_client.fetch_ohlcv` to heal any gaps.
3. **Buffer Warmup Depth**:
   - Wilder's RSI SMMA converges asymptotically. While 15 candles are mathematically sufficient to produce an initial RSI, having the full $N=100$ depth ensures that initial value bias decays to $< 0.05$ points difference from true infinite-history RSI.

---

## 4. Conclusion

1. **Architecture Ready for Implementation**:
   - `strategies/multi_timeframe.py` can be upgraded cleanly without breaking any existing strategy (`EMATrendStrategy`, `RSIBollingerStrategy`) or test suite (`test_multi_timeframe.py`, `test_risk_engine.py`).
2. **All 4 Objectives Fully Addressed**:
   - **Sync & Buffers**: $N=100$ non-repainting circular buffer depth per symbol for 15m, 1h, 4h; automatic closed-candle aggregation on hour and 4-hour epoch boundaries.
   - **Indicators**: Exact mathematical formulas for EMA 9/21/50, Wilder's SMMA RSI 14, Bollinger Bands 20/2.0 std, and ATR 14.
   - **Confluence Score**: $0.20 \cdot Trend_{15m} + 0.40 \cdot Trend_{1h} + 0.40 \cdot Trend_{4h} \in [-1.0, +1.0]$ with 27-state truth table and 5 macro regimes.
   - **Backwards Compatibility**: Returns dict maintaining all legacy keys while introducing typed `TimeframeMetrics` and rich telemetry.

---

## 5. Verification Method

### 5.1 Independent Test Execution Commands
Verify existing and new multi-timeframe test suites using the project virtual environment:

```powershell
# 1. Run multi-timeframe unit tests
.venv\Scripts\pytest tests/test_multi_timeframe.py -v

# 2. Run strategy unit tests (EMA Trend & RSI Bollinger)
.venv\Scripts\pytest tests/test_strategies.py -v

# 3. Run full risk engine tests
.venv\Scripts\pytest tests/test_risk_engine.py -k "test_mtf" -v
```

### 5.2 Verification Script for Indicator Accuracy
Execute this quick benchmark to independently verify indicator calculation accuracy:

```powershell
.venv\Scripts\python.exe -c "
import numpy as np, pandas as pd
from strategies.multi_timeframe import MultiTimeframeFilter

mtf = MultiTimeframeFilter(ema_period=50, max_candles=100)
# Generate 100 synthetic candles
candles = [[1700000000000 + i*900000, 100+i, 102+i, 99+i, 101+i, 1000.0] for i in range(100)]
mtf.set_candles('15m', candles, symbol='BTC/USDT')
mtf.set_candles('1h', candles, symbol='BTC/USDT')
mtf.set_candles('4h', candles, symbol='BTC/USDT')

res = mtf.check_confluence('BTC/USDT', 205.0, side='BUY')
print('Confluence Score:', res.get('confluence_score'))
print('Approved:', res.get('approved'))
assert res['approved'] is True
assert 'confluence_score' in res
print('Verification Successful!')
"
```

### 5.3 Invalidation Conditions
This specification shall be considered invalidated if:
1. Indicators calculate or repaint on in-progress candles (`is_candle_closed == False`).
2. Confluence score produces a value outside $[-1.0, +1.0]$.
3. Existing test `tests/test_multi_timeframe.py` fails due to missing keys or signature changes.
4. Auto-aggregated 1h high/low fails to encompass the extreme high/low of its constituent 15m candles.
