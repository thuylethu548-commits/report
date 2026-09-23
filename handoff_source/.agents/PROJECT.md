# Project: Astra Quant Desk — 7-DAY ADAPTIVE TRADING TEST (Autonomous Multi-Agent System)

## Campaign Identity & Core Philosophy
- **Campaign Name**: "7-DAY ADAPTIVE TRADING TEST" (Initial Capital = 50 USDT, Binance Futures Live Balance = $55.44 USDT).
- **Core Philosophy**: **"TRADE THE MARKET, NOT THE KPI."**
  - Never force trade volume or rigid profit targets.
  - Adaptive Execution: High-quality statistical edge -> trade; Choppy/low-opportunity market -> reduce frequency; Extreme volatility -> reduce size / increase selectivity; **NO EDGE -> NO TRADE**.
  - Strict Prohibitions: No opening trades merely to hit count targets; No increasing leverage/risk to recoup losses; No Martingale; No Revenge trading; Never loosen or widen Stop-Loss.

## Mandatory Trade Lifecycle
Every trade candidate must pass through the standardized 9-stage pipeline:
`MARKET SCAN` → `ANALYSIS` → `MULTI-AGENT DEBATE` → `CONFIDENCE` → `RISK CHECK` → `TRADE / NO TRADE` → `MONITORING` → `EXIT` → `POST-MORTEM`.

## The 10 Golden Audit Questions
Every trade execution must record structured audit evidence answering:
1. **WHY TRADE?**: Market thesis and statistical trigger.
2. **WHY THIS ASSET?**: Symbol selection justification and liquidity.
3. **WHY THIS DIRECTION?**: Multi-timeframe trend confluence and momentum.
4. **WHY NOW?**: Timing trigger (candle close, breakout confirmation).
5. **WHAT EVIDENCE?**: Indicators (EMA 9/21, RSI 14, BB 20/2, Volume RVOL).
6. **WHAT COULD MAKE THIS WRONG?**: Bear Devil's Advocate failure modes.
7. **WHAT DID THE OPPOSING AGENT SAY?**: Exact counter-thesis and trap warnings.
8. **WHY WAS THE OPPOSING ARGUMENT ACCEPTED OR REJECTED?**: Supreme Arbiter ruling rationale.
9. **WHAT WAS THE RISK?**: Stop-loss distance, capital allocation ($10-$14 notional), risk score (1-5).
10. **WHAT ACTUALLY HAPPENED?**: Post-trade execution outcome, PnL, MAE/MFE, and post-mortem lesson.

## Architecture
Astra Quant Desk is an autonomous multi-agent quantitative trading system with an asynchronous event-driven core, an adversarial VAR council (Bull Thesis vs Bear Devil's Advocate vs Supreme Quantitative Arbiter), dynamic position holding ("Thế gồng coin"), psychology/lessons grounding, and deterministic risk circuit breaker.

### Subsystem Topology
1. **Perception & Indicator Engine**:
   - Ingests 15m, 1h, and 4h closed candles (`strategies/multi_timeframe.py`, `core/events.py`).
   - Computes EMA 9/21, RSI 14 (Wilder's SMMA), Bollinger Bands (20, 2.0 std), ATR(14), Volume RVOL / Z-scores, and Liquidity Hunt Wick patterns.
   - Synthesizes market state into structured `MarketPerceptionPayload`.
2. **Adversarial VAR Council & Consensus Engine**:
   - Round 1 (Bull Thesis, `deepseek-v4.1`): builds momentum and support thesis.
   - Round 2 (Bear Devil's Advocate, `deepseek-v4-flash-lr`): scans for bull/bear traps, false breakouts, liquidity hunt wicks, divergence, and psychology trap patterns. Assigns trap risk score (1-5).
   - Round 3 (Supreme Quantitative Arbiter, `claude-sonnet-4-6`): evaluates evidence, computes consensus confidence ($C \ge 0.80$ gate, $Score_{bear} \le 3$), size multiplier ($0.2x - 1.0x$), and transparent rationale.
   - Answers Golden Questions 1–8 prior to order entry.
3. **Dynamic Position Holding & Trailing Protocol ("Thế gồng coin")**:
   - 4-stage state machine (`execution/trailing_stop.py`):
     * `OPEN_ACTIVE`: entry stop loss at 1.5x ATR.
     * `BREAK_EVEN_LOCKED`: triggered at $+1.2\%$ unrealized gain, moves SL to `entry * 1.002` (BUY) or `entry * 0.998` (SELL) with $+0.2\%$ fee buffer. Monotonic ratchet.
     * `TRAILING_ACTIVE`: triggered at $+2.0\%$ gain, advances SL at $1.0x$ ATR distance below peak (BUY) or above trough (SELL).
     * `HOUSE_MONEY_RUNNER`: triggered at $+3.0\%$ position gain or $+10.0$ USDT daily profit. Executes partial take-profit (closes 80% position, securing profit into balance), remaining 0.2x runner SL locked at $+1.5\%$ gain with widened $2.0x$ ATR trail to ride macro waves risk-free.
     * Dead-trade timer: locks $+0.1\%$ profit if trade consolidates $> 2$ hours within $+0.2\%$ to $+0.8\%$.
4. **Market Psychology & Lessons Grounding**:
   - SQLite table `trading_lessons` (`data/storage.py`) seeded with 4 core behavioral traps: FOMO đu đỉnh, Gồng lỗ buông xuôi, Chốt non, and Bẫy đòn bẩy cao.
   - Dynamic context injection pipeline querying relevant historical lessons and feeding them into the VAR council before order approval.
5. **Deterministic Hard Risk Bounds & Circuit Breaker**:
   - Zero-AI Phase 1 gates (`risk_engine/circuit_breaker.py`, `risk_engine/risk_manager.py`):
     * Hard -$3.50 USDT daily loss circuit breaker (24h freeze).
     * Portfolio limit: max 2 open positions across desk, max 1 open position per symbol.
     * Sizing calibrated for $50 USDT base capital (Binance Futures current balance $55.44 USDT): safe notional size $10-$14 USDT (margin 2 - 2.8 USDT at 5x leverage).
     * Ultra-fast quantitative fallback: < 100ms deterministic rule upon AI timeout or network outage.
6. **Reporting & Admin Cockpit Workflow**:
   - SQLite table `trade_audit_trails` recording the 10 Golden Questions per trade.
   - Daily Report & 7-Day Final Report generation evaluating 6 Pillars: Profitability + Risk Control + Decision Quality + Data Quality + Reasoning Quality + System Reliability.
   - Admin Panel View (`/admin/workflow`) displaying live multi-agent debate transcript and pipeline visualization.

---

## Feature Inventory

| # | ID | Feature | Description | Milestone | Source |
|---|----|---------|-------------|-----------|--------|
| 1 | F1.1 | Multi-Timeframe Candle Ingestion | Ingests 15m, 1h, 4h OHLCV closed candles with non-repainting buffer depth N=100. | M1 | ORIGINAL_REQUEST §R1 |
| 2 | F1.2 | Technical Indicator Engine | Calculates EMA 9/21, RSI 14 (Wilder), BB 20/2, and ATR 14 across active timeframes. | M1 | ORIGINAL_REQUEST §R1 |
| 3 | F1.3 | Market Context Synthesis | Packages multi-timeframe matrices, volume anomalies, and active alerts into `MarketPerceptionPayload`. | M1 | ORIGINAL_REQUEST §R1 |
| 4 | F1.4 | MTF Trend Confluence Guard | Pre-council filter ensuring trade direction aligns with 1h and 4h EMA-50 trend. | M1 | ORIGINAL_REQUEST §R1 |
| 5 | F2.1 | Bullish Momentum Thesis (Round 1) | Prompting momentum strategist LLM (`deepseek-v4.1`) to defend signal with technical momentum arguments. | M2 | ORIGINAL_REQUEST §R2 |
| 6 | F2.2 | Bear Devil's Advocate (Round 2) | Prompting risk skeptic LLM (`deepseek-v4-flash-lr`) to challenge setup for traps, liquidity wicks, and resistance. | M2 | ORIGINAL_REQUEST §R2 |
| 7 | F2.3 | Supreme Arbiter Adjudication (Round 3) | Binding adjudication by `claude-sonnet-4-6` enforcing confidence >= 0.80 and bear risk score <= 3. | M2 | ORIGINAL_REQUEST §R2 |
| 8 | F2.4 | Institutional Verdict & 10 Golden Questions | Formats arbiter output into 10 Golden Questions audit trail and records round-by-round transcripts. | M2 | ORIGINAL_REQUEST §R2 & §2026-09-22T02:57:56Z |
| 9 | F2.5 | Adversarial Trap Veto Engine | Vetoes technical signals exhibiting fakeout characteristics, achieving >= 85% trap veto rate. | M2 | ORIGINAL_REQUEST §R2 |
| 10 | F3.1 | Break-Even Stop Lock (+1.2% Gain) | Automatically advances Stop-Loss to entry price +/- 0.2% fee buffer when profit reaches +1.2%. | M3 | ORIGINAL_REQUEST §R3 |
| 11 | F3.2 | Dynamic Trailing Stop (+2.0% Gain) | Continuously trails local highs/lows at 1.0x ATR distance once profit reaches +2.0% (monotonic ratchet). | M3 | ORIGINAL_REQUEST §R3 |
| 12 | F3.3 | House Money Mode Engine (+3.0% / +10 USDT) | Triggers partial take-profit (close 80%), locks remaining 0.2x runner at +1.5% profit, caps subsequent orders to 0.2x. | M3 | ORIGINAL_REQUEST §R3 |
| 13 | F3.4 | Dead-Trade Profit Lock Timer | Detects positions stalled > 2h with +0.2% to +0.8% profit and locks in +0.1% buffer. | M3 | ORIGINAL_REQUEST §R3 |
| 14 | F3.5 | Non-Blocking Tick Execution | Evaluates trailing stop and break-even rules on every market tick in sub-millisecond in-memory operations. | M3 | ORIGINAL_REQUEST §R3 |
| 15 | F4.1 | Historical Lessons DB Injection | Queries recent post-mortem lessons from SQLite `trading_lessons` and injects into market context. | M1 | ORIGINAL_REQUEST §R4 |
| 16 | F4.2 | Symbol-Specific Community Psychology | Enriches prompt with coin personality traits (NEAR AI narrative, SUI volatility, DOGE/PEPE sentiment). | M1 | ORIGINAL_REQUEST §R4 |
| 17 | F4.3 | Auto Post-Mortem Forensic Generator | Asynchronous background task querying Claude Sonnet to dissect Stop-Loss trades into lessons learned (Golden Question 10). | M2 | ORIGINAL_REQUEST §R4 |
| 18 | F4.4 | SQLite Lessons Table & UI Sync | Persists lessons into `trading_lessons` table and renders them dynamically on `/admin/lessons`. | M1 | ORIGINAL_REQUEST §R4 |
| 19 | F5.1 | Hard Daily Loss Circuit Breaker | Halts all trading activity for 24h if cumulative daily realized loss breaches -$3.50 USDT. | M4 | ORIGINAL_REQUEST §R5 |
| 20 | F5.2 | Portfolio Concurrency Constraints | Enforces max 2 open positions across portfolio and max 1 open position per symbol. | M4 | ORIGINAL_REQUEST §R5 |
| 21 | F5.3 | Ultra-Fast Quantitative Fallback (< 100ms) | Deterministic fallback executed when AI times out or errors, enforcing SL corridor [0.5%, 5.0%] and conf >= 0.70. | M4 | ORIGINAL_REQUEST §R5 |
| 22 | F5.4 | Pre-Entry Multi-Gate Shield | Cascading safety checks: Auto-Trade switch, 15m Cooldown, Red-Flag Time Window, Macro War Defense, Funding Squeeze. | M4 | ORIGINAL_REQUEST §R5 |
| 23 | F5.5 | Dual Execution Fidelity (Paper vs Live) | Calibrated sizing for 50 USDT capital (safe $10-$14 notional, no forced trade count) across Paper & Binance. | M4 | ORIGINAL_REQUEST §R5 |
| 24 | F6.1 | Trade Audit Trail & 10 Golden Questions DB | SQLite table `trade_audit_trails` recording full 10 Golden Questions per trade candidate. | M2 | ORIGINAL_REQUEST §2026-09-22T02:57:56Z |
| 25 | F6.2 | Daily & 7-Day Performance Report Engine | Generates daily and 7-day reports evaluating the 6 pillars (PnL, Win Rate, Expectancy, Profit Factor, MAE/MFE). | M4 | ORIGINAL_REQUEST §2026-09-22T02:57:56Z |
| 26 | F6.3 | Admin Workflow & Debate Transcript Panel | Web view at `/admin/workflow` visualizing the 9-stage pipeline and full debate transcripts. | M2 | ORIGINAL_REQUEST §2026-09-22T02:57:56Z |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Multi-Timeframe Perception, Alert Synthesis & Psychology Grounding | Features F1.1, F1.2, F1.3, F1.4, F4.1, F4.2, F4.4: 15m/1h/4h alignment, indicator engine, volume anomaly & liquidity wick detection, SQLite psychology lesson seeding (FOMO, gồng lỗ, chốt non, đòn bẩy cao), and context injection pipeline. | none | IN_PROGRESS |
| M2 | Autonomous Adversarial VAR Council, 10 Golden Questions & Workflow Panel | Features F2.1, F2.2, F2.3, F2.4, F2.5, F4.3, F6.1, F6.3: 3-round debate (Bull vs Bear vs Arbiter), strict confidence gate ($C \ge 0.80$, $Score_{bear} \le 3$), size multiplier (0.2x-1.0x), >=85% trap veto efficacy, 10 Golden Questions audit trail, and `/admin/workflow` panel view. | M1 | PLANNED |
| M3 | Dynamic Position Holding Protocol ("Thế gồng coin") & House Money Runner | Features F3.1, F3.2, F3.3, F3.4, F3.5: Break-Even stop lock at +1.2% (+0.2% fee buffer), Dynamic Trailing Stop at +2.0% (1.0x ATR monotonic ratchet), House Money Mode at +3.0% or +10 USDT daily gain (80% partial TP, 0.2x runner locked at +1.5%), dead-trade timer (>2h), and partial OMS execution in Paper & Binance. | M1 | PLANNED |
| M4 | Deterministic Risk Engine, Circuit Breaker, 50u Adaptive Guard & Reporting | Features F5.1, F5.2, F5.3, F5.4, F5.5, F6.2: -$3.50 USDT hard loss circuit breaker, max 2 portfolio positions, max 1 per symbol, safe 50u sizing ($10-$14 notional, Trade the Market Not the KPI), <100ms fallback SLA, and 6-Pillar Daily/7-Day report generator. | M1, M2, M3 | PLANNED |
| Test | E2E Testing Track & Test Suite Creation | 5-tier test suite (Tiers 1-4 opaque-box requirement tests, Tier 5 adversarial stress tests), test infrastructure `TEST_INFRA.md`, publish `TEST_READY.md`. | none (Parallel) | IN_PROGRESS |
| Final | Final E2E Pass, Hardening & Port 8386 Live Operation | 100% pass on E2E test suite (Tiers 1-4), Tier 5 adversarial hardening, live server run on port 8386. | M1, M2, M3, M4, Test | PLANNED |

---

## Code Layout
- `config/settings.py`: Configuration singleton, daily loss breaker limit (-$3.50), profit target (+10.0), position limits (max 2 total, max 1/symbol), 50u sizing parameters ($10-$14 notional).
- `strategies/multi_timeframe.py`: Closed-candle alignment, 15m/1h/4h indicator calculation, EMA 50 trend confluence.
- `ai_advisory/market_perception.py`: Volume RVOL/Z-score anomaly engine, Liquidity Hunt Wick detector (spring/upthrust), and perception synthesizer.
- `ai_advisory/adversarial_debater.py`: 3-Round adversarial debate engine (Bull, Bear, Arbiter), trap veto engine, 10 Golden Questions generator, debate transcript logging.
- `ai_advisory/vyce_client.py`: Keep-alive HTTP client, timeout enforcement, fallback handler, post-mortem generation.
- `execution/trailing_stop.py`: 4-stage position holding protocol (Break-Even +1.2%, Trailing +2.0%, House Money +3.0% / +10u, dead-trade timer).
- `execution/paper_trader.py`: Paper OMS with partial take-profit support (0.8x exit, 0.2x runner) and non-blocking post-mortem dispatch.
- `execution/binance_executor.py`: Live Binance USD-M Futures OMS with partial execution and protective orders.
- `risk_engine/circuit_breaker.py`: -$3.50 daily loss kill switch, +10.0 daily profit lock.
- `risk_engine/risk_manager.py`: 4-phase gating pipeline, deterministic Phase 1 gates, quantitative fallback (<100ms).
- `data/storage.py`: SQLite schema for `trading_lessons`, `trade_audit_trails` (10 Golden Questions), daily snapshots.
- `web/routes/api_routes.py`: REST APIs for dashboard telemetry, `/api/v1/workflow`, `/api/v1/audit-trail`, settings, and lessons.
- `web/templates/admin/workflow.html`: Admin visual workflow panel.
- `tests/`: Automated test suite (Tiers 1-5).
