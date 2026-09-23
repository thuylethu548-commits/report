# Handoff Report: Quantitative Algorithms, Mathematics & State Machine Specifications for Autonomous Multi-Agent Trading System

**Author**: survey_explorer_2 (Quant & Strategy Surveyor)  
**Date**: 2026-09-22T02:35:00Z  
**Target Milestone**: Survey & Specifications for Autonomous Multi-Agent Trading (R1 - R5)  
**Parent Conversation ID**: e9b53268-5666-44c8-8876-b9e21cf9f943  
**Working Directory**: `c:\sunMy\trading_bot\.agents\survey_explorer_2`

---

## 1. Observation

Direct investigation of the codebase revealed the existing implementation anchors across all 5 requirement domains:

### 1.1 Existing Technical Foundation
1. **Multi-Timeframe Perception**:
   - `strategies/multi_timeframe.py` (lines 9-25, 90-125): `MultiTimeframeFilter` tracks 1h and 4h historical candle buffers (`candles_1h`, `candles_4h`), calculating `EMA(50)`. Evaluates confluence for BUY (`current_price >= ema_1h and current_price >= ema_4h`) and SHORT (`current_price < ema_1h and current_price < ema_4h`).
   - `strategies/ema_trend.py` (lines 40-55): Calculates `ema_fast` (span=9) and `ema_slow` (span=21) using `df["close"].ewm(span=..., adjust=False).mean()`, alongside True Range / ATR(14).
   - `strategies/rsi_bollinger.py` (lines 40-58): Calculates Bollinger Bands (SMA 20, 2.0 std) and RSI (14-period rolling mean of gains and losses).

2. **Adversarial Multi-Agent Debater**:
   - `ai_advisory/adversarial_debater.py` (lines 21-58, 61-180): 3-Round adversarial debate structure:
     * Round 1 (`ROUND1_BULL_PROMPT`): Bullish Momentum Strategist (`deepseek-v4.1`). Focuses on momentum, support, volume.
     * Round 2 (`ROUND2_BEAR_PROMPT`): Chief Skeptic & Devil's Advocate (`deepseek-v4-flash-lr`). Focuses on traps, fakeouts, resistance, funding rate.
     * Round 3 (`ROUND3_ARBITER_PROMPT`): Supreme Quantitative Risk Arbiter (`claude-sonnet-4-6`). Output: `approved`, `verdict`, `risk_score` (1-5), `confidence` (0.0-1.0), `size_multiplier` (0.2-1.0), `ruling_rationale`.
   - `ai_advisory/adversarial_debater.py` (lines 102-125): Runs Round 1 and Round 2 concurrently via `asyncio.gather(bull_task, bear_task)` with 13.0s individual timeout, then feeds transcripts to Arbiter.

3. **Dynamic Position Holding & Trailing Protocol**:
   - `execution/trailing_stop.py` (lines 9-39, 98-198):
     * `break_even_threshold_pct = 0.012` (+1.2% triggers Break-Even lock). Moves Stop-Loss to `entry_price * 1.002` (BUY) or `entry_price * 0.998` (SELL) to guarantee zero loss plus fee buffer.
     * `trailing_activation_pct = 0.020` (+2.0% triggers Dynamic Trailing Stop). Trails highest price by `effective_atr * atr_multiplier`.
     * `check_dead_trade_timer` (lines 201-262): Locks profit if position is slightly green (+0.2%) after 2 hours of sideways consolidation.
   - `tests/test_paper_trailing.py` (lines 58-96): Proves live event publishing of `BREAK_EVEN_LOCK` and `TRAILING_STOP_ADVANCE`.

4. **Market Psychology & Lessons Grounding**:
   - `trading_bot_schema.sql` (lines 122-131) & `data/storage.py` (lines 138-147, 582-607, 1060-1083):
     * Table `trading_lessons`: `(id INTEGER PRIMARY KEY, timestamp TEXT, category TEXT, title TEXT, details TEXT, capital_impact REAL, lesson_learned TEXT, operator TEXT)`.
     * Default seeded lessons include: `MARKET_CRASH` (Flash Crash 19/5/2021 circuit breaker), `SLIPPAGE` (CPI/NFP orderbook void), `STOP_LOSS` (Liquidity hunt wick trap).
   - `scripts/community_agent_farm.py` (lines 28-240, 269-350): Network of 20 community channels (Facebook pages, Reddit r/CryptoCurrency, r/nearprotocol, r/sui) extracting structured lessons (`HOLDING_DISCIPLINE`, `RISK_MANAGEMENT`, `PSYCHOLOGY`, `NARRATIVE_ANALYSIS`) and persisting to `trading_lessons`.
   - `risk_engine/risk_manager.py` (lines 301-318): Queries `db.get_lessons(limit=10)` and passes `hard_earned_lessons_to_respect` into `market_context` for AI advisory.

5. **Deterministic Hard Risk Bounds & Circuit Breaker**:
   - `risk_engine/circuit_breaker.py` (lines 10-85):
     * `target_daily_profit_usd = 10.0` (+10 USDT daily sprint goal triggers `house_money_mode = True`).
     * `max_daily_loss_usd = 3.5` (-$3.50 USDT daily loss triggers `is_tripped = True`, freezing all trading).
   - `risk_engine/risk_manager.py` (lines 144-286, 481-550):
     * Phase 1 (0ms): Deterministic checks for Circuit Breaker tripped, Max Open Positions (`len(self.open_positions) >= settings.MAX_OPEN_POSITIONS` where max=2), Single position per symbol limit (`MAX_POSITIONS_PER_SYMBOL = 1`), and Stop Loss presence.
     * Quantitative Fallback: `< 0.1ms` deterministic rule executing if AI times out or throws an exception. Validates Stop Loss corridor `[0.5%, 5.0%]`, confidence $\ge 0.70$, and de-rates size multiplier to `0.5x`.

6. **Test Verification**:
   - Pytest execution verified:
     * `pytest tests/test_trailing_stop.py tests/test_multi_timeframe.py`: 5 passed in 6.67s.
     * `pytest tests/test_risk_engine.py`: 18 passed in 48.86s.

---

## 2. Logic Chain: Detailed Quantitative & Algorithmic Specifications

Step-by-step deduction from observed system architecture to rigorous mathematical and state machine models for requirements R1 through R5:

```
+---------------------------------------------------------------------------------------+
|                                    PIPELINE OVERVIEW                                  |
|                                                                                       |
|  [R1: Multi-Timeframe Perception]                                                     |
|       15m, 1h, 4h Data Alignment + EMA 9/21, RSI 14, BB 20/2.0                       |
|       Volume RVOL & Z-Score Anomaly + Upper/Lower Liquidity Hunt Wicks                |
|                                     │                                                 |
|                                     ▼                                                 |
|  [R4: Market Psychology Grounding] ─► Context Ingestion (Past Lessons & Traps)        |
|                                     │                                                 |
|                                     ▼                                                 |
|  [R2: Adversarial VAR Council]                                                        |
|       Bull Agent (Momentum/Support) vs Bear Devil's Advocate (Trap/Wick Hunter)       |
|       Supreme Arbiter Consensus (Conf >= 0.80, Risk 1-5, Size Multiplier 0.2x-1.0x)   |
|                                     │                                                 |
|                                     ▼                                                 |
|  [R5: Deterministic Risk Bounds]                                                      |
|       Phase 1 Check: -$3.50u Circuit Breaker, Max 2 Portfolio, Max 1 Per Symbol      |
|       Fallback: < 100ms (measured < 0.1ms) deterministic fallback on timeout          |
|                                     │                                                 |
|                                     ▼                                                 |
|  [R3: Dynamic Position Holding Protocol ("Thế gồng coin")]                            |
|       Break-Even (+1.2% -> SL = Entry * 1.002)                                        |
|       Dynamic Trailing (+2.0% -> 1.0x ATR / Swing Low Ratchet)                        |
|       House Money Mode (+3.0% / +10u Day -> 80% TP, 0.2x Runner Locked at +1.5%)     |
+---------------------------------------------------------------------------------------+
```

---

### Module 1 (R1): Multi-Timeframe Perception & Indicator Synthesis

#### 1.1 Candle Synchronization & Non-Repainting Invariant
To prevent look-ahead bias and indicator repainting, multi-timeframe calculations must obey the **Closed Candle Synchronization Protocol**:
- Let $T_{15m}$ be the base timeframe ($900\text{ s}$).
- Higher timeframes: $T_{1h} = 4 \times T_{15m}$ ($3,600\text{ s}$), $T_{4h} = 16 \times T_{15m}$ ($14,400\text{ s}$).
- **Synchronization Invariant**: An indicator on timeframe $\tau \in \{15m, 1h, 4h\}$ is recomputed **only when candle $k_{\tau}$ is officially closed**:
  $$\text{Timestamp } t \pmod{\Delta t_{\tau}} = 0$$
- Circular buffers keep $N = 100$ closed candles for each timeframe:
  $$\mathcal{B}_{\tau} = \left[ C_{\tau, t - (N-1)}, \dots, C_{\tau, t-1}, C_{\tau, t} \right]$$
  where candle $C = (\text{timestamp}, O, H, L, C, V)$.

#### 1.2 Mathematical Indicator Specifications

##### 1. Exponential Moving Averages (EMA 9 and EMA 21)
The weighting multiplier $\alpha_k$ for a period $k$:
$$\alpha_k = \frac{2}{k + 1}, \quad \alpha_9 = \frac{2}{10} = 0.20, \quad \alpha_{21} = \frac{2}{22} = \frac{1}{11} \approx 0.090909$$
The recurrence relation for candle $t$:
$$EMA_{k, t} = \alpha_k \cdot P_{\text{close}, t} + (1 - \alpha_k) \cdot EMA_{k, t-1}$$
Trend state on timeframe $\tau$:
$$Trend_{\tau} = \begin{cases}
+1 \text{ (Bullish Momentum)} & \text{if } EMA_{9, \tau} > EMA_{21, \tau} \text{ and } P_{\text{close}, \tau} > EMA_{9, \tau} \\
-1 \text{ (Bearish Momentum)} & \text{if } EMA_{9, \tau} < EMA_{21, \tau} \text{ and } P_{\text{close}, \tau} < EMA_{9, \tau} \\
0 \text{ (Neutral / Consolidation)} & \text{otherwise}
\end{cases}$$

##### 2. Relative Strength Index (RSI 14) with Wilder's Exponential Smoothing
Price change: $\Delta P_t = P_t - P_{t-1}$.
Upward change $U_t = \max(\Delta P_t, 0)$, Downward change $D_t = \max(-\Delta P_t, 0)$.
Wilder's smoothed moving averages:
$$SMMA_U(t) = \frac{SMMA_U(t-1) \times 13 + U_t}{14}$$
$$SMMA_D(t) = \frac{SMMA_D(t-1) \times 13 + D_t}{14}$$
Relative Strength & Index:
$$RS_t = \frac{SMMA_U(t)}{SMMA_D(t) + 10^{-9}}, \quad RSI_t = 100 - \frac{100}{1 + RS_t}$$
- Healthy Bullish Momentum Corridor: $52 \le RSI_{14} \le 68$.
- Overbought Exhaustion: $RSI_{14} \ge 72$ (Extreme: $\ge 80$).
- Oversold Liquidation: $RSI_{14} \le 28$ (Extreme: $\le 20$).

##### 3. Bollinger Bands (20 periods, 2.0 standard deviations)
$$SMA_{20, t} = \frac{1}{20} \sum_{i=0}^{19} P_{t-i}$$
$$\sigma_{20, t} = \sqrt{\frac{1}{20} \sum_{i=0}^{19} (P_{t-i} - SMA_{20, t})^2}$$
$$Upper_t = SMA_{20, t} + 2.0 \cdot \sigma_{20, t}, \quad Lower_t = SMA_{20, t} - 2.0 \cdot \sigma_{20, t}$$
$$\%B_t = \frac{P_t - Lower_t}{Upper_t - Lower_t + 10^{-9}}$$
$$Bandwidth_t = \frac{Upper_t - Lower_t}{SMA_{20, t}}$$
- Bollinger Squeeze condition: $Bandwidth_t \le \min_{j=1..30}(Bandwidth_{t-j}) \times 1.10$.

##### 4. Multi-Timeframe Confluence Composite Index ($MTF_{confluence}$)
$$MTF_{confluence} = 0.20 \cdot Trend_{15m} + 0.40 \cdot Trend_{1h} + 0.40 \cdot Trend_{4h}$$
- Full Bullish Alignment: $MTF_{confluence} \ge 0.80$.
- Full Bearish Alignment: $MTF_{confluence} \le -0.80$.
- Conflict / Mixed: $-0.60 < MTF_{confluence} < 0.60$ (Signal generation should be gated or require elevated council conviction).

#### 1.3 Volume Anomaly Detection Engine
Volume baseline computed over a rolling 20-candle window:
$$\bar{V}_{20} = \frac{1}{20}\sum_{i=1}^{20} V_{t-i}, \quad \sigma_{V, 20} = \sqrt{\frac{1}{20}\sum_{i=1}^{20} (V_{t-i} - \bar{V}_{20})^2}$$
Relative Volume ($RVOL$) and Z-score ($Z_V$):
$$RVOL_t = \frac{V_t}{\bar{V}_{20} + 10^{-9}}, \quad Z_{V, t} = \frac{V_t - \bar{V}_{20}}{\sigma_{V, 20} + 10^{-9}}$$
Classification Rules:
1. `VOLUME_CLIMAX`: $RVOL_t \ge 2.5$ and $Z_{V, t} \ge 3.0$ (High exhaustion or institutional volume turnover).
2. `VOLUME_ABSORPTION_CHURN`: $RVOL_t \ge 2.0$ but candle body ratio $\frac{|C_t - O_t|}{H_t - L_t} < 0.30$ (Massive volume trapped in narrow range $\implies$ institutional block distribution/absorption).
3. `VOLUME_DRYOUT_DRIFT`: $RVOL_t \le 0.50$ (Price advance/decline unsupported by volume $\implies$ high vulnerability to fakeout).

#### 1.4 Liquidity Hunt Wick Detection Engine
Candle structural decomposition for candle $t$:
- Total Range: $R_t = H_t - L_t$.
- Real Body: $B_t = |C_t - O_t|$.
- Upper Wick: $W_{u, t} = H_t - \max(O_t, C_t)$.
- Lower Wick: $W_{l, t} = \min(O_t, C_t) - L_t$.

##### Bullish Liquidity Hunt (Spring / Stop Run on Lows)
Detects when market makers sweep retail stop-loss orders below local support before immediate recovery:
1. Wick Dominance: $W_{l, t} \ge 2.0 \cdot B_t$ AND $W_{l, t} \ge 0.50 \cdot R_t$.
2. Swing Low Pierced: $L_t < \min_{i=1..15}(L_{t-i})$.
3. Rejection Close: $C_t > \min_{i=1..15}(L_{t-i})$ (Reclaimed level before candle close).
4. Volume Spike: $RVOL_t \ge 1.50$.
$\implies$ Label: `LIQUIDITY_HUNT_SPRING_BULLISH` (High-probability Long opportunity).

##### Bearish Liquidity Hunt (Upthrust / Stop Run on Highs)
Detects when price spikes above resistance to trigger breakout orders and short stops, then drops:
1. Wick Dominance: $W_{u, t} \ge 2.0 \cdot B_t$ AND $W_{u, t} \ge 0.50 \cdot R_t$.
2. Swing High Pierced: $H_t > \max_{i=1..15}(H_{t-i})$.
3. Rejection Close: $C_t < \max_{i=1..15}(H_{t-i})$.
4. Volume Spike: $RVOL_t \ge 1.50$.
$\implies$ Label: `LIQUIDITY_HUNT_UPTHRUST_BEARISH` (Dangerous Bull Trap, mandatory Veto for Longs).

#### 1.5 Alert Synthesis Data Structure
```python
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
    trend_state: int             # +1, -1, 0
    close_price: float

@dataclass
class VolumeAnomalyState:
    rvol: float                  # e.g. 2.7x
    z_score: float               # e.g. 3.2
    anomaly_type: str            # "NORMAL" | "VOLUME_CLIMAX" | "CHURN" | "DRYOUT"

@dataclass
class LiquidityHuntState:
    is_detected: bool
    hunt_type: str               # "NONE" | "SPRING_BULLISH" | "UPTHRUST_BEARISH"
    wick_ratio: float
    swept_level: float

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
```

---

### Module 2 (R2): Adversarial 3-Tier VAR Council & Consensus Engine

```
       [Signal Generated: Technical Trigger]
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[Tier 1: Bull Thesis Agent]    [Tier 2: Bear Devil's Advocate]
- Trend Momentum & Confluence  - Trap & Fakeout Scrutiny
- Support Level Verification   - Liquidity Wick Hunting
- Expansion Volume Bias        - RSI/MACD Divergence Checks
       │                               │
       └───────────────┬───────────────┘
                       ▼
       [Tier 3: Supreme Quantitative Arbiter]
       - Evidence-Weighted Consensus Calculation
       - Gate 1: Confidence >= 0.80
       - Gate 2: Bear Risk Score <= 3 (Score 4-5 = Auto VETO)
       - Gate 3: Trap Veto Flag == False
       - Size Multiplier Allocation: 0.2x to 1.0x
```

#### 2.1 Council Roles & Formal Prompts

##### Tier 1: Bull Thesis Agent (Momentum & Structure Advocate)
- **Role**: Builds the strongest quantitative case for why this trade setup has a statistical edge.
- **Evaluation Criteria**:
  * $EMA_9 > EMA_{21}$ on $15m$ and $1h$.
  * Price holding above structural support ($P > Support_{swing}$).
  * Volume expanding on impulse waves ($RVOL \ge 1.2$).
  * $RSI_{14}$ ascending within 50 to 68 band.
- **Scoring Function**:
  $$Score_{bull} = 0.35 \cdot \mathbb{I}_{EMA} + 0.25 \cdot \mathbb{I}_{Support} + 0.20 \cdot \min\left(\frac{RVOL}{2.0}, 1.0\right) + 0.20 \cdot \mathbb{I}_{RSI\_ok}$$
  $$Confidence_{bull} = \min(1.0, \max(0.0, Score_{bull}))$$
- **Output JSON Schema**:
  ```json
  {
    "bull_thesis": "string (quant justification under 80 words)",
    "confidence": 0.85,
    "support_level": 60500.0,
    "momentum_tier": "STRONG | MODERATE | WEAK"
  }
  ```

##### Tier 2: Bear Devil's Advocate Agent (Chief Skeptic & Trap Hunter)
- **Role**: Forensic capital defender. Actively searches for fatal traps, liquidity grabs, and failure points.
- **Trap Scenarios Scanned**:
  1. `FAKEOUT_BREAKOUT`: Breakout above resistance with $RVOL < 0.90$ or upper wick $> 40\%$.
  2. `LIQUIDITY_GRAB_WICK`: $W_u \ge 2.0 \cdot B$ piercing high then closing back down.
  3. `BEARISH_DIVERGENCE`: $P_t > P_{t-k}$ while $RSI_t < RSI_{t-k} - 3.0$.
  4. `RESISTANCE_OVERHEAD`: Major order block or 4h resistance within $1.2 \times ATR$ above entry (R:R $< 1.5$).
  5. `HIGH_FUNDING_SQUEEZE`: Funding rate $> +0.03\%$ (Longs over-leveraged).
- **Trap Severity Score ($Score_{bear} \in \{1, 2, 3, 4, 5\}$)**:
  * 1: Clean, no visible traps or divergence.
  * 2: Minor overhead noise, manageable risk.
  * 3: Noticeable divergence or resistance near, manageable with tight stop.
  * 4: High trap probability (e.g. wick rejection or high funding).
  * 5: Fatal trap detected (clear bull trap fakeout, liquidity sweep reversal, or war/macro flash crash).
- **Output JSON Schema**:
  ```json
  {
    "bear_counter_thesis": "string (attack critique under 80 words)",
    "trap_detected": true,
    "trap_type": "FAKEOUT | WICK_HUNT | BEARISH_DIVERGENCE | RESISTANCE_WALL | NONE",
    "trap_risk_score": 4,
    "veto_recommended": true
  }
  ```

##### Tier 3: Supreme Quantitative Arbiter (Consensus & Sizing Engine)
- **Consensus Scoring Equation**:
  $$Confidence_{arbiter} = 0.60 \cdot Confidence_{bull} + 0.40 \cdot \left(1.0 - \frac{Score_{bear} - 1}{4}\right)$$
- **Strict Approval Decision Rules**:
  A trade is APPROVED if and only if **ALL FOUR** conditions are satisfied:
  1. $Confidence_{arbiter} \ge 0.80$
  2. $Score_{bear} \le 3$ (If $Score_{bear} \in \{4, 5\} \implies$ IMMEDIATE VETO)
  3. $Bear.trap\_detected == False$ OR ($Bear.trap\_detected == True$ AND $Score_{bear} \le 2$)
  4. $Confidence_{bull} \ge 0.70$
- **Size Multiplier ($M_{size} \in [0.2, 1.0]$)**:
  $$M_{size} = \begin{cases}
  0.0 & \text{if VETOED} \\
  0.20 & \text{if House Money Mode is active (capital defense)} \\
  1.00 & \text{if } Confidence_{arbiter} \ge 0.90 \text{ and } Score_{bear} == 1 \\
  0.75 & \text{if } 0.85 \le Confidence_{arbiter} < 0.90 \text{ and } Score_{bear} \le 2 \\
  0.50 & \text{if } 0.80 \le Confidence_{arbiter} < 0.85 \text{ and } Score_{bear} \le 3 \\
  0.20 & \text{if borderline approval}
  \end{cases}$$

#### 2.2 Trap Detection Scenarios & $\ge 85\%$ Trap Veto Rate Benchmark
To fulfill the acceptance criteria ($Veto\_Rate \ge 85\%$), the system must be benchmarked against a standardized 20-case test suite:
- **Test Suite Composition (20 Scenarios)**:
  * 6 Fakeout / Bull Trap breakouts at key resistance with low volume ($RVOL < 0.7$).
  * 5 Liquidity hunt wicks (long upper shadow sweeping highs before engulfing red candle).
  * 4 Bearish divergences at local double tops ($RSI$ making lower high while price makes higher high).
  * 3 High funding rate long-squeeze setups (Funding $> +0.035\%$).
  * 2 Low liquidity weekend pump setups.
- **Evaluation Metric**:
  $$Trap\_Veto\_Rate = \frac{\sum_{i=1}^{20} \mathbb{I}(\text{Vetoed}_i)}{20} \times 100\% \ge 85.0\% \quad (\ge 17 \text{ out of } 20)$$
- **Non-Distortion Constraint (Zero False Veto on True Trends)**:
  Council must concurrently pass $\ge 85\%$ of genuine trend-following breakout signals with strong volume ($RVOL \ge 2.0$, no divergence, higher timeframes bullish).

---

### Module 3 (R3): Dynamic Position Holding & Trailing Protocol ("Thế gồng coin")

```
   [State 1: OPEN_ACTIVE] 
   Initial Stop Loss: SL_0 = Entry - 1.5x ATR (BUY)
   Unrealized PnL < +1.2%
           │
           │ (PnL >= +1.2%)
           ▼
   [State 2: BREAK_EVEN_LOCKED]
   Stop Loss moved to: Entry * (1 + 0.002)
   Zero Risk Guaranteed. Ratchet: SL can NEVER loosen.
           │
           │ (PnL >= +2.0%)
           ▼
   [State 3: TRAILING_ACTIVE]
   Stop Loss tracks: Highest Price - 1.0x ATR
   Continuous ratcheting following swing lows.
           │
           │ (PnL >= +3.0% OR Daily Profit >= +10 USDT)
           ▼
   [State 4: HOUSE_MONEY_RUNNER]
   - Partial Take-Profit: Close 80% position at market
   - Secure +2.4% to +3.0% profit into balance
   - Remaining 20% (0.2x runner) Stop Loss locked at Entry + 1.5%
   - Trailing distance widened to 2.0x ATR to ride macro waves
```

#### 3.1 Formal State Machine Specifications

##### Variable Definitions
For an active position $i$:
- $P_{entry}$: fill price.
- $Q_0$: initial executed quantity.
- $Side \in \{\text{BUY}, \text{SELL}\}$.
- $SL_t$: current effective stop-loss price.
- $P_{high, t} = \max_{0 \le s \le t}(P_s)$: peak high price during the life of the position.
- $P_{low, t} = \min_{0 \le s \le t}(P_s)$: peak low price during the life of the position.
- $PnL_{pct, t}$:
  $$PnL_{pct, t} = \begin{cases}
  \frac{P_t - P_{entry}}{P_{entry}} & \text{if } Side == \text{BUY} \\
  \frac{P_{entry} - P_t}{P_{entry}} & \text{if } Side == \text{SELL}
  \end{cases}$$

##### State 1: `OPEN_ACTIVE`
- **Entry condition**: Order filled.
- **Initial Stop Loss**:
  $$SL_0 = \begin{cases}
  P_{entry} - 1.5 \times ATR_{15m} & \text{for BUY} \\
  P_{entry} + 1.5 \times ATR_{15m} & \text{for SELL}
  \end{cases}$$
  Subject to hard constraint: $\frac{|P_{entry} - SL_0|}{P_{entry}} \le 0.018$ (1.8% maximum capital risk).

##### State 2: `BREAK_EVEN_LOCKED`
- **Transition Trigger**:
  $$PnL_{pct, t} \ge +0.012 \quad (+1.20\%)$$
- **Fee Allowance Math ($\delta_{fees}$)**:
  Roundtrip trading incurs two taker executions plus potential execution slippage:
  $$\delta_{fees} = 2 \times Fee_{taker} + Slippage_{allowance}$$
  With standard Binance VIP 0 futures fee ($Fee_{taker} = 0.05\% = 0.0005$) and slippage buffer ($0.10\% = 0.0010$):
  $$\delta_{fees} = 2 \times 0.0005 + 0.0010 = 0.0020 \quad (+0.20\%)$$
- **Adjusted Stop Loss**:
  $$SL_{BE} = \begin{cases}
  P_{entry} \times (1.0 + \delta_{fees}) = P_{entry} \times 1.002 & \text{for BUY} \\
  P_{entry} \times (1.0 - \delta_{fees}) = P_{entry} \times 0.998 & \text{for SELL}
  \end{cases}$$
- **Invariant**:
  $$\text{Realized Net PnL at } SL_{BE} = Q_0 \cdot \left[ (P_{entry} \cdot 1.002) - P_{entry} \right] - \text{Roundtrip Fees} \ge 0.00 \text{ USDT}$$
  Guarantees **absolute zero capital loss**.

##### State 3: `TRAILING_ACTIVE`
- **Transition Trigger**:
  $$PnL_{pct, t} \ge +0.020 \quad (+2.00\%)$$
- **Trailing Step Calculation**:
  Effective ATR bounded to reasonable ranges ($0.005 \cdot P_t \le ATR_{eff} \le 0.05 \cdot P_t$):
  $$D_{trail} = 1.0 \times ATR_{eff}$$
  $$Candidate\_SL_t = \begin{cases}
  P_{high, t} - D_{trail} & \text{for BUY} \\
  P_{low, t} + D_{trail} & \text{for SELL}
  \end{cases}$$
- **Strict Monotonic Ratchet Rule (Never loosen)**:
  $$SL_t = \begin{cases}
  \max(SL_{t-1}, Candidate\_SL_t) & \text{for BUY} \\
  \min(SL_{t-1}, Candidate\_SL_t) & \text{for SELL}
  \end{cases}$$
  Every upward tick in $P_{high}$ moves $SL_t$ up; downward pullbacks leave $SL_t$ static until touched.

##### State 4: `HOUSE_MONEY_RUNNER`
- **Dual Activation Triggers**:
  1. **Position Milestone**: $PnL_{pct, t} \ge +0.030$ ($+3.00\%$), OR
  2. **Daily Profit Sprint Goal**: Cumulative daily realized profit $PnL_{daily} \ge +10.0$ USDT.
- **Two-Step Execution Protocol**:
  1. **Partial Take-Profit (80% Exit)**:
     - Close $80\%$ of position quantity: $Q_{closed} = 0.80 \times Q_t$.
     - Net profit realized: $\approx +2.4\%$ to $+3.0\%$ on $80\%$ of capital.
     - Account balance directly incremented with locked profit.
  2. **Establish Risk-Free Runner (20% Remaining)**:
     - Remaining position: $Q_{runner} = 0.20 \times Q_t$.
     - **Lock Runner Minimum Gain**:
       $$SL_{runner} = \begin{cases}
       P_{entry} \times 1.015 & \text{for BUY (+1.5% profit guaranteed)} \\
       P_{entry} \times 0.985 & \text{for SELL (+1.5% profit guaranteed)}
       \end{cases}$$
     - **Macro Wave Trailing**: Widen trailing multiplier to $k_{ATR} = 2.0$ (or trail on closed 1h candle swing lows) to prevent premature shakeouts, allowing the runner to ride 10%-50% macro multi-day impulses.
- **Account-Level House Money Sizing Constraint**:
  When $PnL_{daily} \ge +10.0$ USDT, any subsequent new trade opened on that UTC day has its allocation capped at $M_{size} \le 0.20$ ($20\%$ size). If a subsequent trade hits a full stop loss ($-1.8\%$), total loss is capped at:
  $$\text{Max Risk} = \$12.50 \times 0.20 \times 0.018 = \$0.045 \text{ USDT}$$
  The secured $+10.0$ USDT daily gain cannot be degraded.

---

### Module 4 (R4): Market Psychology & Lessons Grounding

#### 4.1 SQLite Schema & Lesson Taxonomy
Table `trading_lessons` in `trading_bot.db`:
```sql
CREATE TABLE IF NOT EXISTS trading_lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT NOT NULL,
    capital_impact REAL,
    lesson_learned TEXT NOT NULL,
    operator TEXT DEFAULT 'Astra-Supervisor'
);
```

#### 4.2 Taxonomy of Four Core Psychological Traps
1. **"Gồng lỗ buông xuôi" (`LOSING_HOLD_DESPAIR` / Loss Aversion & Sunk Cost)**:
   - *Behavioral Error*: Refusing to cut losses at $-1.8\%$, moving stop loss lower, or averaging down (DCA) into losing futures positions.
   - *Algorithmic Defense*: Mandatory code-level Stop-Loss; monotonic ratchet prohibits any downward adjustment of $SL$; `RiskManager` strictly rejects signals without positive stop-loss corridor.
   - *Seeded Lesson*: *"Không bao giờ nới Stop-loss. Lệnh chạm SL là bắt buộc cắt. Mọi nỗ lực DCA gồng lỗ trong futures đều dẫn tới thanh lý dây chuyền."*

2. **"Chốt non" (`PREMATURE_EXIT` / Disposition Effect)**:
   - *Behavioral Error*: Anxiously closing winning positions at $+0.2\% - +0.4\%$ to capture tiny profits, destroying the positive expected value ($EV$) of the strategy.
   - *Algorithmic Defense*: Disallowing discretionary early close before $+1.2\%$ Break-Even; enforcing $+3.0\%$ partial TP and 0.2x runner protocol to let trends run indefinitely.
   - *Seeded Lesson*: *"Chốt non tại +0.3% vì sợ mất lãi làm cụt tỷ lệ R:R. Hãy để cơ chế Break-Even và Trailing Stop tự động làm việc, giải phóng tâm lý sợ hãi."*

3. **"FOMO đu đỉnh" (`FOMO_BUY_TOP` / Climax Greed)**:
   - *Behavioral Error*: Entering Long when price has completed 3 consecutive extended green candles near Upper Bollinger Band with $RSI_{14} > 75$, buying into whale exit liquidity.
   - *Algorithmic Defense*: Bear Devil's Advocate specifically scans for $P \ge Upper\_BB$, distance from $EMA_{21} > 2.0 \times ATR$, and $RSI_{14} \ge 72 \implies$ Automatic VETO.
   - *Seeded Lesson*: *"Đu đỉnh khi giá đã cách quá xa EMA21 là tự nộp mạng cho cá mập chốt lời. Phải kiên nhẫn chờ giá pullback về EMA9/21 mới xem xét vào lệnh."*

4. **"Bẫy đòn bẩy cao" (`HIGH_LEVERAGE_GREED` / Revenge Trading)**:
   - *Behavioral Error*: Increasing leverage to 20x-50x after a losing trade to quickly recoup capital.
   - *Algorithmic Defense*: Settings enforce hard limit `FUTURES_LEVERAGE = 6`; max capital per trade capped at $25\%$ of equity; Size Multiplier de-rates to $0.2x$ on high volatility.
   - *Seeded Lesson*: *"Đòn bẩy trên 10x là đánh bạc. Tối đa 6x, tuân thủ tuyệt đối quy tắc phân bổ vốn 25% danh mục để tồn tại qua mọi cơn bão."*

#### 4.3 Lesson Grounding & Pre-Entry Context Injection Pipeline
Before the Adversarial Council convenes, `RiskManager` constructs an enriched prompt by querying SQLite `trading_lessons`:
```python
async def query_relevant_psychology_lessons(db: Database, symbol: str, rsi: float, mtf_trend: int) -> List[str]:
    # 1. Select category-targeted lessons based on current market condition
    categories = []
    if rsi >= 68.0:
        categories.append("FOMO_BUY_TOP")
    if rsi <= 32.0:
        categories.append("LOSING_HOLD_DESPAIR")
    categories.extend(["RISK_MANAGEMENT", "STOP_LOSS", "HOLDING_DISCIPLINE"])
    
    # 2. Fetch top 3-5 matching lessons from SQLite
    lessons = await db.get_lessons_by_categories(categories, limit=4)
    return [f"[{l['category']}] {l['title']}: {l['lesson_learned']}" for l in lessons]
```
The resulting lessons are injected into the VAR Council prompt:
```
[MANDATORY HISTORICAL LESSONS TO RESPECT - ASTRA CAPITAL DEFENSE]:
1. [FOMO_BUY_TOP] Thảm họa đu đỉnh khi RSI > 72: Tuyệt đối không Long nếu giá cách xa EMA21 > 2x ATR.
2. [STOP_LOSS] Bẫy quét râu Stop-Loss: Luôn kiểm tra xem cây nến trước có phải Liquidity Hunt không.
3. [HOLDING_DISCIPLINE] Thế gồng coin: Kích hoạt Break-Even tại +1.2%, không chốt non dưới +3.0%.

COUNCIL MANDATE:
- Bull Agent: Demonstrate why this trade does NOT violate these lessons.
- Bear Agent: Search specifically if this signal mimics any past blunder listed above.
- Supreme Arbiter: If signal matches any past mistake, issue an immediate VETO.
```

---

### Module 5 (R5): Deterministic Hard Risk Bounds & Circuit Breaker

```
[Signal Event Received]
           │
           ▼
[Phase 1: Deterministic Risk Gates (0.0 ms)]  <── Zero AI Override Permitted
├── Gate 1.1: Daily Loss Breaker (-$3.50 USDT) ──> IF tripped ──> REJECT (Freeze 24h)
├── Gate 1.2: Portfolio Position Cap (<= 2) ─────> IF >= 2 ──────> REJECT (Max Positions)
├── Gate 1.3: Symbol Position Cap (<= 1) ────────> IF >= 1 ──────> REJECT (Anti-Duplicate)
└── Gate 1.4: Mandatory Stop Loss Corridor ─────> IF invalid ───> REJECT (Invalid SL)
           │
     (All Passed)
           │
           ▼
[Phase 2: AI VAR Council or Fallback (< 100ms)]
├── AI Online & Responds in < 3.0s ───> Use Arbiter Verdict (Approve if Conf >= 0.80)
└── Timeout (> 3.0s) or Error ────────> Quantitative Fallback (< 0.1ms Deterministic)
                                         ├── SL Corridor: 0.5% - 5.0%
                                         ├── Signal Conf >= 0.70
                                         ├── Macro Trend: Price > 1h EMA50
                                         └── Size Multiplier: De-rate to 0.50x
```

#### 5.1 Deterministic Hard Risk Bounds
1. **Daily Max Loss Circuit Breaker**:
   - Hard threshold: $PnL_{daily, realized} \le -3.50$ USDT (measured from day start balance \$52.50 $\implies$ 6.67% max daily loss).
   - Once breached: `circuit_breaker.is_tripped = True`.
   - Master Kill-Switch: All subsequent entry signals rejected immediately with reason: `Circuit breaker tripped: Daily realized loss breached limit -$3.50 USDT`.
   - Cooldown Duration: Fixed 24h lock until reset at 00:00:00 UTC.
2. **Maximum Concurrent Positions**:
   - Portfolio Cap: $N_{portfolio} \le 2$ simultaneous open positions across all pairs.
   - Single Pair Cap: $N_{symbol} \le 1$ position per symbol (strict anti-duplicate gate).
   - Checked in Phase 1 before order sizing or network dispatch.
3. **Mandatory Stop Loss Corridor**:
   - BUY: $0 < SL < Price$ and $0.005 \le \frac{Price - SL}{Price} \le 0.050$ ($0.5\%$ to $5.0\%$).
   - SHORT: $SL > Price$ and $0.005 \le \frac{SL - Price}{Price} \le 0.050$.
   - Any signal with missing or inverted stop-loss is rejected at 0ms.

#### 5.2 Ultra-Fast Quantitative Fallback Protocol (< 100ms SLA)
- **SLA Benchmark**: Verified in `test_latency_spike_timeout_and_eventbus_throughput` and `test_empirical_close_position_non_blocking_sla_benchmark`. Internal quantitative logic executes in $< 0.1\text{ ms}$ (well below the $< 100\text{ms}$ ceiling).
- **Trigger Events**:
  1. Upstream AI timeout ($> 3.0\text{ s}$ standard, $> 32.0\text{ s}$ deep debate).
  2. Network connection failure (`httpx.ConnectError`, `httpx.TimeoutException`, HTTP 5xx).
  3. Corrupted or invalid JSON response payload from AI proxy.
- **Deterministic Fallback Algorithm**:
  ```python
  def execute_quantitative_fallback(signal: SignalEvent, mtf_filter: MultiTimeframeFilter) -> Dict[str, Any]:
      # 1. SELL / Exit order: Unconditional approval to facilitate capital defense
      if signal.side == OrderSide.SELL and signal.stop_loss <= 0:
          return {"approved": True, "size_multiplier": 1.0, "reasoning": "Exit approved unconditionally"}
      
      # 2. Stop loss corridor check [0.5%, 5.0%]
      sl_dist = abs(signal.price - signal.stop_loss) / signal.price
      if sl_dist < 0.005 or sl_dist > 0.050:
          return {"approved": False, "size_multiplier": 0.0, "reasoning": "Fallback Veto: SL corridor out of bounds"}
      
      # 3. Technical signal confidence threshold
      if signal.confidence < 0.70:
          return {"approved": False, "size_multiplier": 0.0, "reasoning": "Fallback Veto: Signal confidence < 0.70"}
      
      # 4. Multi-Timeframe Trend Confluence
      if mtf_filter:
          mtf_res = mtf_filter.check_confluence(signal.symbol, signal.price, side=signal.side.value)
          if not mtf_res.get("approved", True):
              return {"approved": False, "size_multiplier": 0.0, "reasoning": f"Fallback Veto: {mtf_res.get('reason')}"}
      
      # 5. Approved with 50% sizing de-rating
      return {
          "approved": True,
          "risk_score": 3,
          "confidence": signal.confidence,
          "size_multiplier": 0.50,
          "reasoning": f"Approved via Quantitative Fallback (SL valid, Conf={signal.confidence:.2f}, Size=0.5x)",
          "model": "quantitative-fallback",
          "fallback_used": True
      }
  ```

---

## 3. Caveats

1. **Sub-second Slippage in Volatile Altcoins**:
   - The Break-Even fee buffer $\delta_{fees} = 0.0020$ ($+0.20\%$) is sufficient for BTC/USDT and ETH/USDT under normal liquidity. However, for high-beta meme tokens (e.g. DOGE, 1000PEPE) during market news, slippage can occasionally exceed $0.30\%$. For high-beta symbols, $\delta_{fees}$ should be dynamically scaled to $1.5 \times ATR_{15m} / Price$ with a minimum floor of $0.0035$ ($+0.35\%$).
2. **Candle Alignment Across Exchanges**:
   - Closed-candle calculations assume standardized Binance 15m/1h/4h candle epoch intervals. Any clock drift on the VPS host exceeding 500ms could trigger premature indicator recalculation before the official exchange candle close. Host NTP synchronization is required.
3. **AI Council Latency vs Volatility**:
   - While the 3-round debate runs rounds 1 & 2 in parallel via `asyncio.gather`, total roundtrip inference via external LLMs can take 4.0s - 10.0s. In fast flash crashes, price can move 0.5% during debate. The Phase 1 deterministic checks and the $< 100\text{ms}$ quantitative fallback are critical fail-safes.
4. **Paper vs Live Execution Differences**:
   - In paper trading, stop orders are simulated with random slippage. In live Binance Futures, protective stops must be registered as native exchange conditional orders (`STOP_MARKET` with `reduceOnly=True` and `workingType="MARK_PRICE"`), as implemented in `execution/binance_executor.py` (lines 125-151).

---

## 4. Conclusion

1. **Architectural Readiness**:
   - Astra Quant Desk already possesses working modular foundations in `strategies/multi_timeframe.py`, `ai_advisory/adversarial_debater.py`, `execution/trailing_stop.py`, `risk_engine/circuit_breaker.py`, and `risk_engine/risk_manager.py`.
2. **Algorithmic Specifications Complete**:
   - **R1**: Standardized 15m/1h/4h alignment, non-repainting closed candle rule, mathematical definitions for EMA 9/21, RSI 14 Wilder, Bollinger Bands 20/2, Volume Z-score/RVOL, Upper/Lower Liquidity Hunt Wick formulas, and typed `MarketPerceptionPayload`.
   - **R2**: 3-Tier Council formulas: Bull momentum scoring, Bear trap taxonomy (5 trap classes), Supreme Arbiter confidence calculation ($C \ge 0.80$ gate, Bear score $\le 3$ gate), dynamic size multiplier ($0.2x - 1.0x$), and 20-scenario benchmark for $\ge 85\%$ trap veto rate.
   - **R3**: 4-stage "Thế gồng coin" state machine: `OPEN_ACTIVE` $\to$ `BREAK_EVEN_LOCKED` at $+1.2\%$ ($SL = Entry \times 1.002$) $\to$ `TRAILING_ACTIVE` at $+2.0\%$ (1.0x ATR monotonic ratchet) $\to$ `HOUSE_MONEY_RUNNER` at $+3.0\%$ or $+10$ USDT daily profit (80% partial TP, 0.2x runner locked at $+1.5\%$).
   - **R4**: SQLite `trading_lessons` schema, 4 core psychological trap definitions (gồng lỗ, chốt non, FOMO đu đỉnh, đòn bẩy cao), pre-entry targeted querying, and prompt context grounding.
   - **R5**: Phase 1 zero-latency kernel gates: $-\$3.50$ USDT daily loss lock, $\le 2$ concurrent portfolio positions, $\le 1$ per symbol, and $< 100\text{ms}$ deterministic quantitative fallback ($< 0.1\text{ms}$ verified).

---

## 5. Verification Method

To independently verify all claims, algorithms, and test suites documented in this report:

### 5.1 Automated Test Execution Commands
Run the automated test suites using the project's virtual environment:
```powershell
# 1. Verify Trailing Stop, Break-Even Lock, and Multi-Timeframe Filter
.venv\Scripts\pytest tests/test_trailing_stop.py tests/test_multi_timeframe.py -v

# 2. Verify Paper Trader Trailing Stop and Break-Even Event Bus Integration
.venv\Scripts\pytest tests/test_paper_trailing.py -v

# 3. Verify Risk Engine, Circuit Breaker (-$3.50u), and Quantitative Fallback
.venv\Scripts\pytest tests/test_risk_engine.py -v

# 4. Verify Adversarial Debate & Post-Mortem Integration
.venv\Scripts\pytest tests/test_m1_adversarial.py tests/test_auto_post_mortem.py -v
```

### 5.2 Files and Source Code to Inspect
- `strategies/multi_timeframe.py`: lines 9-125 (EMA confluence).
- `strategies/ema_trend.py`: lines 40-55 (EMA 9/21 and ATR).
- `strategies/rsi_bollinger.py`: lines 40-58 (RSI 14 and BB 20/2).
- `ai_advisory/adversarial_debater.py`: lines 21-58, 102-180 (3-Round Bull/Bear/Arbiter debate).
- `execution/trailing_stop.py`: lines 19-39, 98-198 (Break-Even +1.2%, Trailing +2.0%).
- `risk_engine/circuit_breaker.py`: lines 10-85 (-$3.50 daily max loss, +$10.0 profit target).
- `risk_engine/risk_manager.py`: lines 144-286 (Phase 1 hard bounds), lines 481-550 (quantitative fallback).
- `data/storage.py`: lines 582-607, 1060-1083 (`trading_lessons` schema and methods).

### 5.3 Invalidation Conditions
This specification shall be considered invalidated if:
1. Break-Even lock at $+1.2\%$ fails to cover taker commission and slippage (resulting in net negative PnL upon trigger).
2. Trailing Stop decreases (loosens) after a subsequent downward price tick for a Long position.
3. Total daily realized loss exceeds $-\$3.50$ USDT without tripping the circuit breaker.
4. Active concurrent positions exceed 2 on the account or exceed 1 on any individual pair.
5. The quantitative fallback takes $\ge 100\text{ms}$ to execute when the AI council times out.
