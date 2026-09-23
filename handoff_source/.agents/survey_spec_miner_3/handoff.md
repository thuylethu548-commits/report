# Autonomous Multi-Agent Teamwork (R1-R5) Specification Mining Report

**Agent Identity:** survey_spec_miner_3 (`teamwork_preview_spec_miner`)  
**Project Root:** `c:\sunMy\trading_bot`  
**Working Directory:** `c:\sunMy\trading_bot\.agents\survey_spec_miner_3`  
**Timestamp:** 2026-09-22T02:40:00Z  
**Target Spec:** `ORIGINAL_REQUEST.md` (Section `## 2026-09-22T02:15:20Z`) & Codebase Architecture  

---

## 1. Observation

Direct observations extracted from authoritative specification files, configuration singletons, source modules, and test suites in `c:\sunMy\trading_bot`:

### 1.1. Authoritative Requirements Source (`ORIGINAL_REQUEST.md`)
Lines 38 to 82 of `c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md`:
```markdown
## 2026-09-22T02:15:20Z
Nghiên cứu và chuẩn hóa hệ thống Đa Tác tử Tự chủ (Multi-Agent Teamwork) phục vụ phân tích thị trường, tranh biện phản biện đối kháng (VAR Hội đồng), tối ưu "thế gồng coin & quản trị lệnh" (Dynamic Trailing Stop, Break-Even, House Money Mode) và tự học từ kho bài học thực chiến/tâm lý giao dịch để tự động hóa ra quyết định với tỷ lệ thắng (Win Rate) cao.

Requirements:
- R1. Bộ lọc Thị trường & Tổng hợp Cảnh báo Đa Tác tử (Multi-Agent Market Perception & Alert Synthesis)
- R2. Hội đồng Tranh biện Đối kháng Tự chủ (Autonomous Adversarial VAR Council & Consensus Engine)
- R3. Giao thức "Thế gồng coin & Bảo toàn Lợi nhuận" (Dynamic Position Holding & Trailing Protocol)
- R4. Tích hợp Kho tri thức Bài học Thực chiến & Tâm lý Giao dịch (Market Psychology & Community Lessons Grounding)
- R5. Chốt chặn An toàn Lượng hóa Độc lập (Deterministic Risk Engine & Circuit Breaker)
```

### 1.2. Existing Codebase & Implementation Baseline
1. **Configuration & Parameters (`config/settings.py`):**
   - `TARGET_DAILY_PROFIT_USD: float = 10.0` (Line 41)
   - `MAX_DAILY_LOSS_USD: float = 3.5` (Line 42)
   - `HOUSE_MONEY_MODE_ENABLED: bool = True` (Line 43)
   - `MAX_POSITION_PERCENT: float = 0.25` (Line 44)
   - `MAX_OPEN_POSITIONS: int = 2` (Line 47)
   - `MAX_POSITIONS_PER_SYMBOL: int = 1` (Line 48)
   - `AI_COUNCIL_MODE: str = "consensus"` (Line 80)
   - `ENABLE_ADVERSARIAL_DEBATE: bool = True` (Line 81)
   - `ENABLE_MULTI_TIMEFRAME: bool = True` (Line 51)
   - `MTF_EMA_PERIOD: int = 50` (Line 52)
   - `ENABLE_TIME_WINDOW_GUARD: bool = True` (Line 55)

2. **VAR Council & Adversarial Debater (`ai_advisory/adversarial_debater.py`):**
   - 3-Round Debate Architecture:
     - Round 1 (Bullish Momentum Strategist): `bull_model = "deepseek-v4.1"`, prompt focuses on EMA alignment, RSI trajectory, volume breakout potential (Lines 21-30, 66).
     - Round 2 (Bear Devil's Advocate Risk Officer): `bear_model = "deepseek-v4-flash-lr"`, prompt focuses on overhead resistance, liquidity hunt wicks, bear/bull traps, overbought/oversold exhaustion (Lines 32-41, 68).
     - Round 3 (Supreme Quantitative Risk Arbiter): `arbiter_model = "claude-sonnet-4-6"`, prompt enforces institutional judgment output schema with `approved: bool`, `verdict: str`, `risk_score: int` (1-5), `confidence: float`, `size_multiplier: float` (0.2-1.0), `ruling_rationale: str` (Lines 43-58, 70).
   - Parallel Execution: Bull & Bear tasks executed concurrently via `asyncio.gather(bull_task, bear_task)` with 13.0s individual timeout (Lines 103-123).
   - Injected Community Intelligence: Symbol heuristics for NEAR, SUI, DOGE, PEPE dynamically appended to context (Lines 86-93).

3. **Position Holding & Trailing Protocol (`execution/trailing_stop.py`):**
   - Thresholds in `TrailingStopState` (Lines 19-21):
     - `break_even_threshold_pct: float = 0.012` (+1.2% PnL triggers Break-Even).
     - `trailing_activation_pct: float = 0.020` (+2.0% PnL triggers Dynamic Trailing).
     - `atr_multiplier: float = 1.0`.
   - Break-Even buffer calculation:
     - For BUY (Line 130): `new_sl = round_price(state.entry_price * 1.002, state.entry_price)` (+0.2% fee buffer).
     - For SHORT (Line 181): `new_sl = round_price(state.entry_price * 0.998, state.entry_price)` (-0.2% fee buffer).
   - Trailing Stop advance:
     - BUY (Lines 106-108): `effective_atr = current_atr if (0 < current_atr < state.entry_price * 0.05) else (current_price * 0.005)`; `candidate_sl = round_price(state.highest_price - trailing_distance, state.entry_price)`.
     - Monotonic condition: `candidate_sl > state.current_stop_loss` (never loosens).
     - SHORT (Lines 156-161): `candidate_sl = round_price(state.lowest_price + trailing_distance, state.entry_price)`. Lowered monotonically (`candidate_sl < state.current_stop_loss`).
   - Dead-Trade Timer (Lines 201-263): If position held for `>= 7200.0s` (2 hours) and PnL `>= +0.2%` without trigger, locks in profit at `entry_price * 1.001` (BUY) or `entry_price * 0.999` (SHORT).

4. **Deterministic Risk Engine & Circuit Breaker (`risk_engine/circuit_breaker.py` & `risk_engine/risk_manager.py`):**
   - Daily profit lock / House money mode (`CircuitBreaker.add_realized_pnl`, Lines 65-72):
     - When `daily_realized_pnl >= target_daily_profit_usd` (+10.0 USDT): `is_profit_locked = True`, `house_money_mode = True`.
     - In `RiskManager.handle_signal` (Lines 220-231, 419-422): When `house_money_mode == True`, order size multiplier capped at `min(ai_mult, 0.20)` (0.2x size).
   - Hard circuit breaker (`CircuitBreaker.add_realized_pnl`, Lines 78-84):
     - When `daily_realized_pnl <= -max_daily_loss_usd` (-$3.50 USDT): `is_tripped = True`. All subsequent orders rejected.
   - Position concurrency constraints (`RiskManager.handle_signal`, Lines 233-256):
     - `len(self.open_positions) >= settings.MAX_OPEN_POSITIONS` (limit 2) -> Rejection.
     - `active_count >= max_per_symbol` (limit 1) -> Duplicate Position Veto.
   - Quantitative Fallback (`RiskManager._execute_quantitative_fallback`, Lines 481-550):
     - Executed when AI times out or fails.
     - Corridors: Stop-loss must be between 0.5% and 5.0% (`0.005 <= sl_dist_pct <= 0.05`).
     - Confidence: Minimum 0.70 (`signal.confidence >= 0.70`).
     - Size de-rating: Multiplier reduced to `0.50x`.
     - SELL/Exit signals: Approved unconditionally.

5. **Existing Automated Test Baseline:**
   - Command: `.venv\Scripts\pytest -q tests/test_trailing_stop.py tests/test_paper_trader.py` -> `4 passed in 3.47s`.
   - Command: `.venv\Scripts\pytest -q tests/test_risk_engine.py` -> `18 passed in 49.92s`.
   - Total existing test files in `tests/`: 30 files covering risk engine, paper trader, adversarial debater, multi-timeframe, security, post-mortem.

---

## 2. Logic Chain

1. **Step 1 (Scope & Source Deduction):**
   - The user request requires extracting, formalizing, and cataloging the complete feature inventory, acceptance criteria, and benchmark validation constraints for requirements R1, R2, R3, R4, R5 specified in `ORIGINAL_REQUEST.md` (## 2026-09-22T02:15:20Z).
   - Observations 1.1 and 1.2 demonstrate that the foundation exists in code across `ai_advisory/`, `risk_engine/`, `execution/`, and `tests/`.

2. **Step 2 (Feature Deconstruction):**
   - R1 maps to 4 atomic features: Multi-Timeframe Ingestion, Indicator Computation, Context Synthesis, Pre-Council Technical Filtering.
   - R2 maps to 5 atomic features: Round 1 Bull Thesis Generation, Round 2 Bear Devil's Advocate Critique, Round 3 Supreme Arbiter Adjudication, Quantitative Output Formatting, Adversarial Trap Veto Efficacy (>=85%).
   - R3 maps to 5 atomic features: Break-Even Stop Lock (+1.2%), Dynamic Trailing Stop (+2.0%), House Money Mode (+3.0% / +10 USDT), Dead-Trade Timer (>2h), Non-blocking Tick Engine.
   - R4 maps to 4 atomic features: Lessons Historical Context Injection, Symbol-Specific Psychology Grounding, Auto Post-Mortem Forensic Generation, SQLite & Admin Dashboard Sync.
   - R5 maps to 5 atomic features: -$3.50 Hard Daily Loss Breaker, Portfolio Concurrency Constraints (2 total, 1/symbol), Ultra-Fast Quantitative Fallback (<100ms), Multi-Layer Pre-Entry Safety Gates, Dual Paper/Live Execution Fidelity.
   - Total: 23 atomic feature units cataloged.

3. **Step 3 (Acceptance Criteria Formalization):**
   - Mathematical and boolean criteria from the user prompt are translated into testable predicates (e.g., `trap_veto_rate >= 0.85`, `new_sl == round_price(entry * 1.002)`, `realized_loss <= -3.50`, `t_fallback < 100ms`).

4. **Step 4 (E2E Test Tier Architecture):**
   - A 5-tier testing breakdown is synthesized to provide complete verification from happy path (Tier 1) up to adversarial stress and live dual parity (Tier 5).

---

## 3. Atomic Feature Inventory (Features Discovered)

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| F1.1 | R1: Market Perception | Multi-Timeframe Candle Ingestion | Ingests 15m, 1h, 4h OHLCV candles via WebSocket and SQLite storage | Symbol, Timeframe, Candle stream | In-memory candle buffers, SQLite `candles` table | Discard malformed candles, reconnect WebSocket | `strategies/multi_timeframe.py`, `core/events.py` |
| F1.2 | R1: Market Perception | Technical Indicator Engine | Calculates EMA 9/21/50, RSI 14, Bollinger Bands (20, 2), ATR 14 across active timeframes | Price series, timeframe data | Calculated indicators dict (`ema_1h`, `ema_4h`, `rsi`, `bb_upper`, `atr`) | None if insufficient candle history (<50 periods) | `strategies/`, `strategies/multi_timeframe.py` |
| F1.3 | R1: Market Perception | Market Context Synthesis | Formats rich market state including recent candles, volatility regime, account equity, and open positions into JSON context | `SignalEvent`, `Database` candles, `CircuitBreaker` equity | Structured `market_context` dict | Fallback to empty context if DB read fails | `risk_engine/risk_manager.py:307-320` |
| F1.4 | R1: Market Perception | MTF Trend Confluence Guard | Pre-council filter ensuring trade direction aligns with 1h and 4h EMA-50 trend | Symbol, price, side (`BUY`/`SELL`) | `{"approved": bool, "trend_1h": str, "trend_4h": str, "reason": str}` | Vetoes signal before AI if counter-trend | `risk_engine/risk_manager.py:272-286`, `strategies/multi_timeframe.py` |
| F2.1 | R2: VAR Council | Bullish Momentum Thesis (Round 1) | Prompting momentum strategist LLM (`deepseek-v4.1`) to defend signal with technical momentum arguments | `signal_summary`, `ROUND1_BULL_PROMPT` | `{"bull_thesis": str, "confidence": float}` | Fallback to default momentum string if LLM fails/times out | `ai_advisory/adversarial_debater.py:21-30, 103-135` |
| F2.2 | R2: VAR Council | Bear Devil's Advocate (Round 2) | Prompting risk skeptic LLM (`deepseek-v4-flash-lr`) to challenge setup for traps, liquidity wicks, and resistance | `signal_summary`, `ROUND2_BEAR_PROMPT` | `{"bear_counter_thesis": str, "trap_risk_score": int}` | Fallback to default trap critique if LLM fails/times out | `ai_advisory/adversarial_debater.py:32-41, 113-144` |
| F2.3 | R2: VAR Council | Supreme Arbiter Adjudication (Round 3) | Binding adjudication by `claude-sonnet-4-6` reviewing Bull vs Bear arguments to approve or veto trade | Bull thesis, Bear critique, signal data | `{"approved": bool, "verdict": str, "risk_score": int, "confidence": float, "size_multiplier": float, "ruling_rationale": str}` | Returns `approved=False`, `VETOED_TIMEOUT`, engages fallback | `ai_advisory/adversarial_debater.py:43-58, 146-218` |
| F2.4 | R2: VAR Council | Institutional Verdict Formatting | Validates and clamps arbiter output into strict institutional format: risk_score 1-5, confidence 0.0-1.0, size_multiplier 0.2-1.0 | Raw JSON response from arbiter LLM | Sanitized dictionary with guaranteed types and bounded ranges | Sanitizes invalid JSON, strips markdown code fences | `ai_advisory/adversarial_debater.py:201-211` |
| F2.5 | R2: VAR Council | Adversarial Trap Veto Engine | Vetoes technical signals exhibiting fakeout characteristics, liquidity hunt wicks, or severe overhead resistance | Synthetic & live adversarial trap signals | Rejection record persisted to SQLite `signals` table (`approved=0`) | Traps flagged with `risk_score >= 4` or `approved=False` | `ORIGINAL_REQUEST.md §R2`, `ai_advisory/adversarial_debater.py` |
| F3.1 | R3: Holding Protocol | Break-Even Stop Lock (+1.2% Gain) | Automatically advances Stop-Loss to entry price +/- 0.2% fee buffer when trade profit reaches +1.2% | `order_id`, `current_price` where PnL >= +1.2% | `TrailingStopEvent` (`action="BREAK_EVEN_LOCK"`, `new_sl=entry*1.002` for BUY) | SL never reverts lower; triggered only once per position | `execution/trailing_stop.py:127-147, 178-198` |
| F3.2 | R3: Holding Protocol | Dynamic Trailing Stop (+2.0% Gain) | Continuously trails local highs/lows at 1.0x ATR distance once trade profit reaches +2.0% | `order_id`, `current_price`, `current_atr` | `TrailingStopEvent` (`action="TRAILING_STOP_ADVANCE"`, `new_sl=highest-ATR`) | SL is strictly monotonic (never widens or loosens) | `execution/trailing_stop.py:102-126, 152-177` |
| F3.3 | R3: Holding Protocol | House Money Mode Engine | Switches portfolio to House Money Mode upon reaching +3.0% position gain or +10.0 USDT daily profit | Trade PnL >= +3.0% or `CircuitBreaker.daily_realized_pnl >= +10.0` | `house_money_mode = True`, restricts runner & subsequent orders to 0.2x size | Prevents capital give-back; locks accumulated profits | `risk_engine/circuit_breaker.py:65-72`, `execution/trailing_stop.py` |
| F3.4 | R3: Holding Protocol | Dead-Trade Profit Lock Timer | Detects positions stalled for > 2 hours without hitting TP and locks in green PnL if between +0.2% and +0.8% | `order_id`, `current_price`, `current_time` (>7200s hold) | `{"action": "DEAD_TRADE_PROFIT_LOCK", "new_sl": entry*1.001}` | Only triggers if position is slightly profitable (+0.2% - +0.8%) | `execution/trailing_stop.py:201-263` |
| F3.5 | R3: Holding Protocol | Non-Blocking Tick Execution | Evaluates trailing stop and break-even rules on every market tick in sub-millisecond in-memory operations | `MarketEvent` ticks from WebSocket | Immediate SL update, async `TrailingStopEvent` emission | Zero DB lock latency on price tick loop | `execution/paper_trader.py:85-177`, `execution/trailing_stop.py` |
| F4.1 | R4: Lessons Grounding | Historical Lessons DB Injection | Queries recent post-mortem lessons from SQLite `trading_lessons` and feeds them into AI market context | `Database.get_lessons(limit=10)` | `hard_earned_lessons_to_respect` list in `market_context` | Degrades gracefully to empty list if DB locked/empty | `risk_engine/risk_manager.py:302-306` |
| F4.2 | R4: Lessons Grounding | Symbol-Specific Community Psychology | Enriches signal evaluation prompt with known coin personality traits (NEAR AI narrative, SUI volatility, DOGE/PEPE meme sentiment) | `signal.symbol` | Injected community heuristic notes in debate prompt | Silent fallback to standard prompt if symbol has no custom rule | `ai_advisory/adversarial_debater.py:84-94` |
| F4.3 | R4: Lessons Grounding | Auto Post-Mortem Forensic Generator | Asynchronous background task querying Claude Sonnet to dissect closed Stop-Loss trades into root causes and lessons | Closed trade metadata (`order_id`, `entry`, `exit`, `pnl`, `reason`) | Structured forensic dict (`title`, `details`, `capital_impact`, `lesson_learned`) | Deterministic fallback post-mortem generated if AI unreachable | `ai_advisory/vyce_client.py:536-610`, `execution/paper_trader.py` |
| F4.4 | R4: Lessons Grounding | SQLite Lessons Table & UI Sync | Persists post-mortem lessons into `trading_lessons` table and renders them dynamically on `/admin/lessons` | Forensic post-mortem dict | SQLite insertion, REST endpoint `/api/v1/lessons`, web template | Non-blocking `asyncio.create_task` ensures execution is never stalled | `data/storage.py`, `web/routes/api_routes.py`, `PROJECT.md §M2` |
| F5.1 | R5: Risk Engine | Hard Daily Loss Circuit Breaker | Halts all trading activity for 24h if cumulative daily realized loss breaches -$3.50 USDT | `CircuitBreaker.add_realized_pnl(pnl)` | `is_tripped = True`, `trip_reason = "...breached limit -$3.50..."` | Rejects all subsequent `SignalEvent`s with warning log | `risk_engine/circuit_breaker.py:77-84`, `risk_engine/risk_manager.py:213-217` |
| F5.2 | R5: Risk Engine | Portfolio Concurrency Constraints | Enforces max 2 open positions across portfolio and max 1 open position per symbol | `RiskManager.open_positions` dictionary | Order approval or rejection with reason | Rejects incoming entry if `len >= 2` or `symbol_count >= 1` | `risk_engine/risk_manager.py:233-256`, `config/settings.py:47-48` |
| F5.3 | R5: Risk Engine | Ultra-Fast Quantitative Fallback (<100ms) | Deterministic mathematical fallback executed when AI times out (>3.0s or >32s) or errors | `SignalEvent`, rejection reason | `{"approved": bool, "regime": "ranging", "risk_score": 3, "size_multiplier": 0.5, "fallback_used": True}` | Enforces SL corridor [0.5%, 5.0%], confidence >= 0.70; approves SELL unconditionally | `risk_engine/risk_manager.py:481-550` |
| F5.4 | R5: Risk Engine | Pre-Entry Multi-Gate Shield | Cascading safety checks: Auto-Trade switch, 15m Cooldown, Red-Flag Time Window, Macro War Defense, Funding Squeeze | `SignalEvent`, `settings`, `TimeWindowRiskGuard`, `MacroScanner` | Signal passed to AI or rejected at Phase 1 (0ms) | Rejection recorded to SQLite `signals` table (`approved=0`) | `risk_engine/risk_manager.py:143-286` |
| F5.5 | R5: Risk Engine | Dual Execution Fidelity (Paper vs Live) | Uniform order management, position tracking, and trailing stop state machine in both PaperTrader and BinanceExecutor | `OrderEvent`, `FillEvent`, `MarketEvent` | Fills, PnL updates, SL/TP triggers across Paper simulation and Binance USD-M Live Futures | Full state restoration from SQLite `execution_state` upon server restart | `execution/paper_trader.py`, `execution/binance_executor.py` |

---

## 4. Formalized Acceptance Criteria & Benchmark Assertions

Every acceptance criterion from `ORIGINAL_REQUEST.md` and the user prompt is formalized into an exact, testable programmatic assertion:

### Criterion 1: VAR Council >= 85% Trap Veto Rate on Adversarial Scenarios
- **Specification:** The 3-round VAR Council must identify and veto at least 85% of adversarial trap setups (bull/bear traps, false breakouts, liquidity hunt wicks) while preserving valid trend breakouts.
- **Formal Assertion 1 (Adversarial Trap Veto Efficacy):**
  $$\text{Trap Veto Rate} = \frac{\sum_{i=1}^{N_{\text{trap}}} \mathbb{I}(\text{result}_i.\text{approved} = \text{False})}{N_{\text{trap}}} \ge 0.85 \quad (85.0\%)$$
  Tested across $N_{\text{trap}} \ge 20$ synthetic trap scenarios.
- **Formal Assertion 2 (False Veto / Sensitivity Protection):**
  $$\text{Trend Approval Rate} = \frac{\sum_{j=1}^{N_{\text{trend}}} \mathbb{I}(\text{result}_j.\text{approved} = \text{True})}{N_{\text{trend}}} \ge 0.90 \quad (90.0\%)$$
  Tested across $N_{\text{trend}} \ge 20$ clean trend-confluence setups (False Positive Veto $\le 10\%$).

### Criterion 2: Arbiter Verdict Strict Output Schema
- **Specification:** The final verdict from the Supreme Quantitative Arbiter must include quantitative rationale, integer risk score (1-5), size multiplier (0.2-1.0), and decision.
- **Formal Assertion:**
  $$\forall \text{ verdict } V: \begin{cases}
  V.\text{approved} \in \{\text{True}, \text{False}\} \\
  V.\text{verdict} \in \{\text{"APPROVED\_LONG"}, \text{"APPROVED\_SHORT"}, \text{"VETOED"}, \text{"VETOED\_TIMEOUT"}\} \\
  V.\text{risk\_score} \in \mathbb{Z} \cap [1, 5] \\
  V.\text{confidence} \in [0.0, 1.0] \\
  V.\text{size\_multiplier} \in [0.2, 1.0] \\
  \text{len}(V.\text{ruling\_rationale}) > 0 \text{ and } \text{word\_count}(V.\text{ruling\_rationale}) \le 60 \\
  V.\text{approved} = \text{True} \implies (V.\text{confidence} \ge 0.80 \text{ and } V.\text{risk\_score} \le 3) \\
  (V.\text{risk\_score} \ge 4 \text{ or } V.\text{confidence} < 0.80) \implies V.\text{approved} = \text{False}
  \end{cases}$$

### Criterion 3: Break-Even Activation at Exactly +1.2%
- **Specification:** When an open position reaches $+1.2\%$ unrealized gain, Stop-Loss must automatically move to the entry price adjusted by a $+0.2\%$ fee buffer.
- **Formal Assertion:**
  - For **BUY / Long**:
    $$\text{PnL}_{\text{pct}} = \frac{P_{\text{current}} - P_{\text{entry}}}{P_{\text{entry}}} \ge 0.012 \implies \text{SL}_{\text{new}} = \text{round\_price}(P_{\text{entry}} \times 1.002, P_{\text{entry}})$$
  - For **SELL / Short**:
    $$\text{PnL}_{\text{pct}} = \frac{P_{\text{entry}} - P_{\text{current}}}{P_{\text{entry}}} \ge 0.012 \implies \text{SL}_{\text{new}} = \text{round\_price}(P_{\text{entry}} \times 0.998, P_{\text{entry}})$$
  - **Boundary Invariance:** At $\text{PnL}_{\text{pct}} = +0.0119$ ($+1.19\%$), $\text{SL}$ remains at initial $\text{SL}_{\text{initial}}$ and $\text{break\_even\_triggered} = \text{False}$. At $\text{PnL}_{\text{pct}} = +0.0120$, $\text{SL}$ moves to $\text{SL}_{\text{new}}$ and $\text{break\_even\_triggered} = \text{True}$.

### Criterion 4: Trailing Stop Continuous Update Without Locking/Latency
- **Specification:** Once price reaches $+2.0\%$ gain, Trailing Stop continuously locks in profit based on local extremes ($1.0\times$ ATR buffer) with non-locking tick execution.
- **Formal Assertion 1 (Monotonic Ratchet Property):**
  - For **BUY**: $\text{SL}_{t+1} \ge \text{SL}_t$ for all ticks $t$. Never decreases.
  - For **SHORT**: $\text{SL}_{t+1} \le \text{SL}_t$ for all ticks $t$. Never increases.
- **Formal Assertion 2 (Latency SLA):**
  $$\text{Latency}(\text{TrailingStopManager.update\_price}) < 1.0\text{ms} \quad (\text{empirical p99 } < 0.2\text{ms})$$
  Must not execute blocking database I/O on the market tick handling thread.

### Criterion 5: House Money Mode Activation (+3.0% Position Gain or Daily Profit >= +10.0 USDT)
- **Specification:** Transition to House Money Mode occurs when an open position reaches $+3.0\%$ or cumulative daily realized profit reaches $+10.0$ USDT. Allocation is restricted to $0.2\times$ size.
- **Formal Assertion 1 (Trigger Condition):**
  $$\text{HouseMoneyActive} = \text{True} \iff (\text{PositionPnL} \ge +0.030 \lor \text{CircuitBreaker.daily\_realized\_pnl} \ge +10.00\,\text{USDT})$$
- **Formal Assertion 2 (Sizing Multiplier Cap):**
  $$\text{HouseMoneyActive} = \text{True} \implies \text{EffectiveSizeMultiplier} = \min(\text{ai\_mult}, 0.20)$$
  $$\text{AllocatedCapital} \le \text{PortfolioEquity} \times \text{MAX\_POSITION\_PERCENT} \times 0.20$$

### Criterion 6: Hard Risk Circuit Breaker at Daily Loss <= -$3.50 USDT
- **Specification:** When cumulative realized loss reaches $-\$3.50$ USDT, circuit breaker immediately trips and blocks all new trades for the day.
- **Formal Assertion:**
  $$\text{CircuitBreaker.daily\_realized\_pnl} \le -3.50\,\text{USDT} \implies \begin{cases}
  \text{cb.is\_tripped} = \text{True} \\
  \text{RiskManager.handle\_signal}(\text{new\_signal}) \to \text{None (Rejected)}
  \end{cases}$$
  **Boundary Check:** At $-\$3.4999$, $\text{is\_tripped} = \text{False}$; at $-\$3.5000$, $\text{is\_tripped} = \text{True}$.

### Criterion 7: Portfolio Position Constraints (Max 2 Open, Max 1 per Symbol)
- **Specification:** Max 2 concurrent open positions across the desk, max 1 open position per symbol.
- **Formal Assertion:**
  $$\text{CanOpen}(S, \text{sym}) \iff \left(|\text{open\_positions}| < 2 \land \sum_{p \in \text{open\_positions}} \mathbb{I}(p.\text{symbol} = \text{sym}) < 1\right)$$
  Violation results in immediate Phase 1 deterministic rejection.

### Criterion 8: Quantitative Fallback SLA (< 100ms Response Time)
- **Specification:** If AI times out or encounters network/server failures, quantitative fallback must resolve in $< 100$ms.
- **Formal Assertion:**
  $$\text{ExecutionTime}(\text{_execute\_quantitative\_fallback}) < 100.0\,\text{ms} \quad (\text{empirical benchmark } < 1.0\,\text{ms})$$
  Safety corridor rules enforced:
  $$\text{Approved}_{\text{fallback}} = \text{True} \iff \begin{cases}
  \text{side} = \text{SELL}, \text{ or} \\
  \text{side} = \text{BUY} \land 0.005 \le \frac{P_{\text{entry}} - \text{SL}}{P_{\text{entry}}} \le 0.050 \land \text{confidence} \ge 0.70
  \end{cases}$$
  If approved, $\text{size\_multiplier} = 0.50$.

### Criterion 9: 100% Pass on Automated Tests with Zero Regressions
- **Specification:** All existing and newly created test suites must pass 100% without regression.
- **Formal Assertion:**
  $$\text{pytest exit code} = 0 \land \text{failed} = 0 \land \text{errors} = 0$$
  Across `test_risk_engine.py`, `test_paper_trader.py`, `test_trailing_stop.py`, `test_m1_adversarial.py`, `test_auto_post_mortem.py`, etc.

### Criterion 10: Seamless Dual Operation (Paper Simulation and Live Futures)
- **Specification:** Identical position management, trailing stop calculation, and risk enforcement between PaperTrader and BinanceExecutor.
- **Formal Assertion:**
  $$\forall \text{ event } E \in \{\text{Signal}, \text{Order}, \text{MarketTick}\}: \quad \Delta_{\text{logic}}(\text{PaperTrader}, \text{BinanceExecutor}) = \emptyset$$
  Both systems instantiate `TrailingStopManager`, calculate identical break-even and trailing stop price levels, and persist state to SQLite.

---

## 5. Edge Cases Discovered

| # | Feature | Input Scenario | Observed / Specified Behavior |
|---|---------|----------------|-------------------------------|
| E1 | Break-Even Stop Lock | Price hits $+1.199\%$ gain ($< +1.2\%$) | Break-Even does NOT trigger; `break_even_triggered` remains False; SL unchanged. |
| E2 | Break-Even Stop Lock | Price reaches $+1.200\%$ gain exactly | Break-Even triggers; SL moved to $P_{\text{entry}} \times 1.002$ (BUY) or $P_{\text{entry}} \times 0.998$ (SHORT); `break_even_triggered` set to True. |
| E3 | Break-Even Monotonicity | Price drops to $+0.3\%$ after Break-Even was triggered | SL stays locked at $P_{\text{entry}} \times 1.002$; does not revert downward. |
| E4 | Dynamic Trailing Stop | Price pulls back from $+2.8\%$ peak to $+2.2\%$ | Highest price remains at $+2.8\%$ peak; candidate SL is lower than current SL; SL is NOT lowered. |
| E5 | Trailing Stop ATR Boundary | ATR is 0 or exceeds 5% of price (anomalous spike) | Falls back to default $0.5\%$ price buffer ($P_{\text{current}} \times 0.005$) to prevent stop displacement. |
| E6 | Circuit Breaker Exact Limit | Cumulative daily loss reaches exactly $-\$3.5000$ USDT | Circuit breaker trips immediately (`is_tripped = True`); rejects next signal with freeze message. |
| E7 | Circuit Breaker Float Rounding | Cumulative loss is $-\$3.4999$ USDT | Breaker does NOT trip; signal evaluated normally. |
| E8 | House Money Mode Transition | Cumulative daily profit hits exactly $+\$10.0000$ USDT | `is_profit_locked = True`, `house_money_mode = True`; order size multiplier capped to $0.20\times$. |
| E9 | Portfolio Concurrency | 2 positions already active; BUY signal for 3rd symbol arrives | Rejected at Phase 1 deterministic check with reason `"Maximum open positions reached (2/2)"`. |
| E10 | Duplicate Symbol Protection | Active position in BTC/USDT; new BUY signal for BTC/USDT arrives | Rejected with `"Duplicate Position Veto: BTC/USDT already has 1 active position(s)"`. |
| E11 | Opposing Signal Reduction | Active BUY position in BTC/USDT; SELL signal arrives with $\text{SL} \le 0$ | Recognizes position reduction/exit; emits `OrderEvent` with `reduce_only=True` bypassing entry gates. |
| E12 | Quantitative Fallback Corridor | Stop-loss distance is $0.4\%$ ($< 0.5\%$ minimum) | Fallback rejects signal: `"Stop Loss distance 0.40% outside safe corridor [0.5%, 5.0%]"`. |
| E13 | Quantitative Fallback Corridor | Stop-loss distance is $5.1\%$ ($> 5.0\%$ maximum) | Fallback rejects signal: `"Stop Loss distance 5.10% outside safe corridor [0.5%, 5.0%]"`. |
| E14 | Quantitative Fallback Confidence | Signal confidence is $0.69$ ($< 0.70$ threshold) | Fallback rejects signal: `"Signal confidence (0.69) below safe threshold 0.70"`. |
| E15 | Quantitative Fallback SELL | AI times out on a SELL / Exit signal | Fallback approves SELL signal unconditionally to ensure risk reduction. |
| E16 | LLM Markdown Code Fences | LLM wraps JSON response in ` ```json ... ``` ` | `_clean_and_parse_json` strips backticks and whitespace; successfully parses JSON dict. |
| E17 | Corrupted LLM Response | LLM returns non-JSON chatter or truncated JSON | Handled gracefully via try/except; logs error and engages deterministic quantitative fallback. |
| E18 | Arbiter Low Confidence Approval | LLM returns `approved: true` but `confidence: 0.65` | Risk Arbiter rules mandate rejection if confidence $< 0.80$; trade is vetoed. |
| E19 | Extreme Market Volatility | Arbiter returns `approved: true` with `regime: "EXTREME_VOLATILITY"` | `RiskManager` overrides approval; strictly vetoes trade due to extreme market risk. |
| E20 | SQLite Lock Under Concurrency | Transient SQLite busy error during signal or advisory logging | Exception caught and logged as warning; approved order still published to EventBus without failure. |
| E21 | Dead-Trade Timer Holding | Trade held 2h 5m with $+0.4\%$ profit | Dead-trade timer locks in profit by moving SL to $P_{\text{entry}} \times 1.001$. |
| E22 | Dead-Trade Timer Negative PnL | Trade held 2h 5m with $-0.5\%$ loss | Dead-trade timer does not trigger; original stop-loss remains active. |
| E23 | Red Flag Time Window | Signal arrives at 14:58 VN during Binance Funding Rate window | `TimeWindowRiskGuard` intercepts signal and vetoes trade to avoid liquidity wicks. |
| E24 | Force Flag Override | Signal contains `force = True` | Bypasses cooldown, time window guard, MTF filter, and AI advisory; executes directly. |
| E25 | Zero-Balance Edge Case | Account balance is less than required margin + fee | PaperTrader / BinanceExecutor rejects order with `"Insufficient USDT balance"`. |

---

## 6. End-to-End (E2E) Test Tier Breakdown

To guarantee institutional rigor and zero regressions across the multi-agent stack, the validation strategy is decomposed into 5 distinct testing tiers:

### Tier 1: Feature Coverage (Happy Path)
- **Objective:** Verify nominal functionality for each feature operating in isolation under valid inputs.
- **Coverage Scope:**
  - `T1.1`: Market perception ingest (15m, 1h, 4h candle generation and EMA calculation).
  - `T1.2`: VAR council 3-round debate happy path (Bull thesis $\to$ Bear critique $\to$ Arbiter approval $\to$ valid verdict schema).
  - `T1.3`: Break-Even Stop Lock (+1.2% profit advances SL to entry $+0.2\%$).
  - `T1.4`: Dynamic Trailing Stop advancement (+2.0% profit triggers $1.0\times$ ATR trailing).
  - `T1.5`: House Money Mode activation upon $+3.0\%$ gain.
  - `T1.6`: Post-Mortem creation on Stop-Loss exit with SQLite persistence.
  - `T1.7`: Order event dispatch, PaperTrader fill, and portfolio balance deduction.

### Tier 2: Boundary and Corner Cases
- **Objective:** Stress-test exact numeric thresholds, fee buffers, and concurrency barriers.
- **Coverage Scope:**
  - `T2.1`: Break-Even boundary: $+1.19\%$ (no trigger) vs $+1.20\%$ (triggers).
  - `T2.2`: Trailing Stop boundary: $+1.99\%$ (no trigger) vs $+2.00\%$ (triggers).
  - `T2.3`: Hard loss limit: $-\$3.49$ (pass) vs $-\$3.50$ (breaker trips).
  - `T2.4`: House Money limit: $+\$9.99$ (normal) vs $+\$10.00$ (switches to House Money 0.2x).
  - `T2.5`: Portfolio limits: exactly 2 positions open $\to$ attempt 3rd $\to$ hard rejection.
  - `T2.6`: Duplicate symbol limit: 1 BTC/USDT position active $\to$ attempt 2nd BTC/USDT $\to$ hard rejection.
  - `T2.7`: Stop-loss corridor boundaries: $0.49\%$ (rejected), $0.50\%$ (accepted), $5.00\%$ (accepted), $5.01\%$ (rejected).
  - `T2.8`: Precision rounding (`round_price`) for BTC ($\ge 100$), Altcoins ($\ge 1.0$), and Memecoins ($< 0.01$).

### Tier 3: Cross-Feature Interactions
- **Objective:** Validate asynchronous event coordination and state transitions between subsystems.
- **Coverage Scope:**
  - `T3.1`: VAR Council approval + Trailing Stop running + Circuit Breaker profit lock: Trade 1 reaches $+10$ USDT daily profit; Trade 2 is evaluated and its size multiplier is automatically clamped to $0.20\times$.
  - `T3.2`: Stop-Loss hit triggers circuit breaker ($-\$3.50$) while a second signal is queued on EventBus $\to$ queued signal must be rejected at Phase 1 before execution.
  - `T3.3`: Post-mortem background generation occurs concurrently with active market ticks without causing event loop lag ($< 5.0$ms).
  - `T3.4`: Multiple symbols simultaneously updating trailing stop positions without data corruption or memory leaks.

### Tier 4: Real-World Trading Scenarios
- **Objective:** Simulate complex multi-candle market scenarios mimicking live crypto market conditions.
- **Coverage Scope:**
  - `T4.1 - Bull Trap Rally:` Rapid price surge into major 4H resistance with declining volume $\to$ Bull Strategist approves, Bear Advocate identifies exhaustion & overhead liquidity hunt $\to$ Arbiter vetoes with `risk_score=4`.
  - `T4.2 - Liquidity Hunt Wick:` Sudden 3% price dump and immediate recovery within 1 candle $\to$ Time Window Guard or Funding Sentinel identifies squeeze risk $\to$ signals vetoed or trailing stop maintains proper ATR buffer without premature exit.
  - `T4.3 - Sprint to House Money:` 3 consecutive winning trades generating $+3.5$ USDT, $+3.8$ USDT, $+3.2$ USDT ($+10.5$ USDT total) $\to$ system smoothly transitions to House Money mode, locks profit, and scales remaining trades to $0.2\times$.
  - `T4.4 - Dead-Trade Resolution:` Sideways consolidation for 2h 15m $\to$ Dead-Trade timer fires, locks in $+0.1\%$ profit buffer, avoids holding during unpredictable weekend chop.

### Tier 5: Adversarial Stress Testing
- **Objective:** Subject the architecture to extreme environmental, upstream, and network faults.
- **Coverage Scope:**
  - `T5.1 - Extreme Latency Spike:` AI proxy delays response by $5.0$s $\to$ system enforces timeout ($3.0$s / $32.0$s), activates quantitative fallback within $< 100$ms SLA, and drains EventBus smoothly.
  - `T5.2 - Corrupted & Malformed LLM Payloads:` Injection of invalid JSON, markdown code fences, non-JSON chatter, negative size multipliers, and missing keys $\to$ system handles all gracefully with zero unhandled exceptions.
  - `T5.3 - Cascading Network Outage:` Complete loss of upstream connectivity (HTTP 500, 502, 503, connection refused) $\to$ quantitative fallback activates immediately for all signals.
  - `T5.4 - Flash Crash & Rapid SL Burst:` 5 concurrent Stop-Loss executions within $500$ms $\to$ non-blocking background dispatch ensures no tick loop stalling, circuit breaker trips reliably at $-\$3.50$.

---

## 7. Caveats

1. **Vyce AI External API Dependency:** Full live execution of the 3-round VAR council requires an active connection to the Vyce AI / ETFBit proxies. In automated offline CI/CD, mock transports (`MockVyceAdvisor`, `MockCorruptedTransport`) must be utilized to maintain determinism.
2. **Binance Testnet Limitations:** Testing live Futures execution on Binance USD-M Testnet requires valid API credentials in `.env`. Paper simulation (`TRADING_MODE="paper"`) provides 100% test coverage without exchange dependencies.
3. **ATR Smoothing Warm-up:** In cold starts, ATR requires a minimum history of 14 candles; prior to that, the trailing stop manager defaults to a $0.5\%$ price buffer.

---

## 8. Conclusion

The specification mining of the Astra Quant Desk Multi-Agent Teamwork upgrade (Requirements R1 to R5) has identified a comprehensive, robust architectural foundation already partially implemented and ready for formal completion. 
- **R1** provides multi-timeframe perception and alert synthesis.
- **R2** establishes the 3-round adversarial VAR council (DeepSeek Bull vs DeepSeek Bear vs Claude Arbiter) targeting $\ge 85\%$ trap veto accuracy.
- **R3** details exact numerical thresholds for Break-Even ($+1.2\%$), Dynamic Trailing ($+2.0\%$), and House Money ($+3.0\%$ or $+\$10$ USDT).
- **R4** grounds agent debates with SQLite community lessons and automated post-mortems.
- **R5** guarantees deterministic survival via the $-\$3.50$ USDT hard loss circuit breaker, 2-position concurrency limit, and $< 100$ms quantitative fallback SLA.

The complete feature inventory (23 atomic features), 10 formalized acceptance criteria assertions, 25 edge cases, and 5-tier E2E test breakdown provide the complete blueprint for implementation and verification.

---

## 9. Verification Method

To independently verify the facts, thresholds, and tests documented in this report:

1. **Verify Baseline Test Suites:**
   ```powershell
   .venv\Scripts\pytest -q tests/test_trailing_stop.py tests/test_paper_trader.py
   .venv\Scripts\pytest -q tests/test_risk_engine.py
   ```
   *Expected result:* 100% pass (22 tests total: 4 in trailing/paper, 18 in risk engine).

2. **Verify Configuration Constants:**
   - Inspect `config/settings.py`: Lines 41-48 (`TARGET_DAILY_PROFIT_USD = 10.0`, `MAX_DAILY_LOSS_USD = 3.5`, `MAX_OPEN_POSITIONS = 2`, `MAX_POSITIONS_PER_SYMBOL = 1`).

3. **Verify Trailing Stop Thresholds:**
   - Inspect `execution/trailing_stop.py`: Lines 19-20 (`break_even_threshold_pct = 0.012`, `trailing_activation_pct = 0.020`).
   - Inspect Line 130 (`entry_price * 1.002` for BUY break-even) and Line 181 (`entry_price * 0.998` for SHORT break-even).

4. **Verify VAR Council 3-Round Debater:**
   - Inspect `ai_advisory/adversarial_debater.py`: Lines 66-70 (`bull_model`, `bear_model`, `arbiter_model`) and Lines 103-160 (parallel Rounds 1 & 2 followed by Round 3 Arbiter).

5. **Invalidation Conditions:**
   - This specification report is invalidated if `ORIGINAL_REQUEST.md` thresholds are altered, if `TARGET_DAILY_PROFIT_USD` or `MAX_DAILY_LOSS_USD` are changed, or if baseline test suites fail.
