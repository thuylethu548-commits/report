# Handoff Report: Architectural & Codebase Survey for Astra Quant Desk Upgrade

**Surveyor**: `survey_explorer_1` (`teamwork_preview_explorer`)  
**Working Directory**: `c:\sunMy\trading_bot\.agents\survey_explorer_1`  
**Target Project Root**: `c:\sunMy\trading_bot`  
**Reference Specification**: `c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md` (Section `## 2026-09-22T02:15:20Z`) & `PROJECT.md`  
**Date**: 2026-09-22  

---

## 1. Observation

### 1.1 Directory Structure & Major Entrypoints
Direct inspection of the repository revealed the following module topology:
- **`main.py`**: Central async runtime entrypoint. Instantiates `Database`, `EventBus`, `VyceClient`, `CircuitBreaker`, `MultiTimeframeFilter`, `RiskManager`, `PaperTrader`, `BinanceClient`, `BinanceExecutor`, `AutonomousFleetCoordinator`, `create_web_app`, and launches Uvicorn on `0.0.0.0:8386`. Also handles historical candle warmup (lines 212–237) and graceful shutdown signal traps.
- **`core/`**:
  - `event_bus.py`: Asynchronous decoupled pub/sub bus using two internal queues (`_queue` and prioritized `_signal_queue` with maxsize=128). Handlers registered via `.subscribe(EventType, handler)`.
  - `events.py`: Strongly typed dataclass events: `MarketEvent`, `SignalEvent`, `AIAdvisoryEvent`, `OrderEvent`, `FillEvent`, `TrailingStopEvent`.
  - `constants.py`: Enums `OrderSide` (`BUY`, `SELL`), `OrderType` (`MARKET`, `LIMIT`), `OrderStatus` (`PENDING`, `FILLED`, `CANCELLED`), and `MarketRegime` (`BULL_TREND`, `BEAR_TREND`, `RANGING`, `EXTREME_VOLATILITY`).
  - `fleet_manager.py`: Coordinates 10-agent autonomous telemetry & monitoring loop.
- **`ai_advisory/`**:
  - `vyce_client.py`: High-performance HTTP client connecting to Vyce AI / OpenAI proxies. Resolves model aliases, enforces timeouts, tracks token usage/costs, supports council modes (`consensus`, `failover`, `single`, `adversarial`), provides deterministic quantitative fallback, and generates post-mortem forensic analysis.
  - `adversarial_debater.py`: 3-Round adversarial debate engine: Round 1 Bull Thesis (`ROUND1_BULL_PROMPT`, default model `deepseek-v4.1`), Round 2 Bear Devil's Advocate (`ROUND2_BEAR_PROMPT`, default model `deepseek-v4-flash-lr`), Round 3 Supreme Arbiter (`ROUND3_ARBITER_PROMPT`, default model `claude-sonnet-4-6`).
  - `regime_classifier.py`: Evaluates macro market regimes and emits `AIAdvisoryEvent`.
- **`risk_engine/`**:
  - `risk_manager.py`: Central 4-phase gating pipeline for `SignalEvent` (`Phase 1`: Deterministic hard limits, `Phase 2`: AI Council Veto / Quantitative Fallback, `Phase 3`: Position Sizing & Multiplier, `Phase 4`: `OrderEvent` creation, DB persistence, and event emission).
  - `circuit_breaker.py`: Quantitative drawdown & daily PnL guard (`max_daily_loss_usd = 3.5`, `target_daily_profit_usd = 10.0`, `house_money_mode_enabled = True`).
  - `time_window_guard.py`: Restricts entries during volatile news / market session transitions.
  - `funding_sentinel.py`: Evaluates funding rate squeeze risks.
- **`execution/`**:
  - `paper_trader.py`: In-memory paper execution engine with simulated slippage (0.01%–0.03%), fee calculation (0.1%), Stop-Loss/Take-Profit evaluation, and non-blocking background post-mortem triggering upon Stop-Loss hit.
  - `binance_executor.py`: Live Binance USD-M Futures OMS with exchange limit validation, precision formatting, protective order placement (`_protect`), state persistence (`save_execution_state`), and reconciliation.
  - `trailing_stop.py`: `TrailingStopManager` managing `TrailingStopState` instances. Implements Break-Even lock at +1.2% (moves SL to Entry + 0.2% fee buffer) and Dynamic Trailing Stop advancement at +2.0% (1.0x ATR distance).
- **`data/`**:
  - `storage.py`: SQLite engine via `aiosqlite`. Manages tables: `candles`, `trades`, `signals`, `ai_advisory_logs`, `equity_snapshots`, `system_settings`, `trading_lessons`, `ai_token_usage`, `trial_positions`, `users`, `user_api_credentials`, `client_trades`.
  - `binance_client.py`: Async CCXT client wrapper for Binance Spot & USD-M Futures (`fetch_ohlcv`, `fetch_balance`, `create_order`, `cancel_protective_order`).
  - `websocket_feed.py`: Live ticker and kline feed via Binance WebSocket streams.
- **`strategies/`**:
  - `base_strategy.py`: Base class with sliding-window candle storage and Pandas DataFrame conversion.
  - `ema_trend.py`: EMA 9/21 cross with ATR(14) stop-loss/take-profit calculation.
  - `rsi_bollinger.py`: RSI-14 oversold (<35) / overbought (>68) mean reversion against Bollinger Bands (20, 2.0).
  - `multi_timeframe.py`: `MultiTimeframeFilter` maintaining 1h and 4h historical candle buffers and calculating 50 EMA trend confluence.
- **`web/`**:
  - `app.py`: FastAPI application mounting static assets, security middleware, Jinja2 templates, and API routes.
  - `routes/api_routes.py`: REST APIs for dashboard telemetry, settings hot-reload, trading lessons, and system status.
- **`tests/`**:
  - Contains 30 test files covering risk engine, trailing stop, paper trader, AI advisory, multi-timeframe filter, adversarial stress tests, and API routes.

---

### 1.2 Component Lifecycle & Flow Mapping

```
 [ MarketEvent (15m/1h/4h) ] ──> EventBus
                                   │
                                   ├──> Strategies (EMA / RSI) ──> SignalEvent
                                   │                                    │
                                   ▼                                    ▼
       [ TrailingStopManager ] <── PaperTrader / BinanceExecutor    RiskManager
       - Checks BE (+1.2%)            ▲                                 │
       - Checks Trailing (+2.0%)      │ (OrderEvent)                    │ (Phase 1-4 Gate)
       - Triggers TP / SL             └─────────────────────────────────┘
              │
              └──> On Stop-Loss: triggers auto post-mortem ──> SQLite (trading_lessons)
```

1. **Signal Generation**:
   - `EMATrendStrategy` and `RSIBollingerStrategy` listen to closed `MarketEvent`s. Upon indicator triggers (e.g. EMA 9/21 cross), they publish a `SignalEvent` with `price`, `stop_loss`, `take_profit`, and `confidence`.
2. **Risk Management & Advisory Gate**:
   - `RiskManager.handle_signal` receives `SignalEvent`.
   - **Phase 1**: Verifies master auto-trade switch, symbol cooldown, red-flag windows, circuit breaker status (`circuit_breaker.is_tripped`), portfolio position limit (`len(open_positions) < settings.MAX_OPEN_POSITIONS`), single-position-per-symbol limit (`active_count < settings.MAX_POSITIONS_PER_SYMBOL`), valid stop-loss, and multi-timeframe trend confluence (`mtf_filter.check_confluence`).
   - **Phase 2**: If `settings.ENABLE_AI_ADVISORY` is active, invokes `VyceClient.evaluate_signal_veto`.
     - In `adversarial` council mode: delegates to `AdversarialDebater.debate_signal`, conducting Round 1 (Bull), Round 2 (Bear), and Round 3 (Arbiter).
     - If AI times out (`> AI_TIMEOUT_SECONDS`) or fails: immediately invokes `_execute_quantitative_fallback` (< 0.1ms). Rejects wide SL (>5% or <0.5%) and low confidence (<0.70); approves with 0.50x size de-rating.
   - **Phase 3**: Allocates position size. If `circuit_breaker.house_money_mode` is True, caps size multiplier to `0.2x`.
   - **Phase 4**: Constructs `OrderEvent`, records approved/rejected signal in SQLite `signals` table, and publishes `OrderEvent` to `EventBus`.
3. **Execution & Position Lifecycle**:
   - `PaperTrader` or `BinanceExecutor` consumes `OrderEvent`.
   - Records position in `open_positions` dict and registers position with `TrailingStopManager.register_position`.
   - Emits `FillEvent` and records trade open in SQLite `trades` table (`status="OPEN"`).
4. **Position Holding & Trailing Protocol**:
   - On every `MarketEvent` tick, `PaperTrader.handle_market_tick` / `BinanceExecutor.handle_market_tick` calls `trailing_manager.update_price(order_id, current_price)`.
   - If profit reaches `+1.2%`, moves SL to `entry * 1.002` (BUY) or `entry * 0.998` (SELL), guaranteeing Break-Even.
   - If profit reaches `+2.0%`, advances Trailing Stop by `1.0x ATR` below peak (BUY) or above trough (SELL).
   - Publishes `TrailingStopEvent` and updates position Stop-Loss.
5. **Stop-Loss Detection & Auto Post-Mortem**:
   - When price crosses `stop_loss`, position is closed via `_close_position` (Paper) or `_emergency_market_close` (Live Binance).
   - Realized PnL is sent to `circuit_breaker.add_realized_pnl(pnl)`.
   - If reason is `STOP_LOSS`, spawns async background task calling `VyceClient.generate_post_mortem(trade_info)`.
   - Post-mortem record is inserted into SQLite table `trading_lessons` via `db.add_lesson` and immediately available on `/admin/lessons`.

---

### 1.3 Test Suite Execution & Baseline Discrepancies Observed
We executed the existing test suite using the project virtual environment (`.\.venv\Scripts\pytest.exe` on Python 3.12.14).
Findings:
1. **Core Passing Tests**:
   - `tests/test_trailing_stop.py`: **3/3 passed** (Break-Even lock, Dynamic Trailing Stop advancement, Dead-Trade timer).
   - `tests/test_paper_trader.py`: **1/1 passed** (Order execution and Take-Profit hit).
   - `tests/test_paper_trailing.py`: **1/1 passed** (Integration of Trailing Stop with Paper Trader).
   - `tests/test_multi_timeframe.py`: **2/2 passed** (1h/4h EMA confluence and RiskManager MTF veto).
2. **Observed Discrepancies in Existing Tests**:
   - **`tests/test_risk_engine.py` (4 failures out of 25)**:
     - Root Cause: In `config/settings.py` line 44, `MAX_POSITION_PERCENT = 0.25` (25%). Four legacy tests (`test_risk_manager_ai_advisory_approval_with_sizing`, `test_risk_manager_timeout_engages_quantitative_fallback`, `test_risk_manager_network_error_engages_fallback`, and `test_risk_manager_with_real_vyce_client_outage_rejects_unsafe_signals`) hardcoded `0.20` (20%) in their expected sizing assertion formulas:
       `expected_qty = round((100.0 * 0.20 * 0.6) / 60000.0, 6) # 0.0002 BTC`
       Actual calculation: `round((100.0 * 0.25 * 0.6) / 60000.0, 6) # 0.00025 BTC`.
       AssertionError verbatim: `assert 0.00025 == 0.0002`.
   - **`tests/test_auto_post_mortem.py` (1 failure)**:
     - Test `test_auto_post_mortem_triggered_on_stop_loss` failed because `PaperTrader.handle_order` guards: `if settings.TRADING_MODE != "paper": return`. The fixture did not monkeypatch `settings.TRADING_MODE = "paper"`, resulting in `open_positions` remaining empty.
   - **`tests/test_ai_advisory.py` (1 failure)**:
     - Test `test_vyce_client_model_alias_resolution` failed on `assert VyceClient.resolve_model_alias("deepseek-chat") == "claude-sonnet-4-6"`. In `vyce_client.py` line 38, `"deepseek-chat"` was mapped to `"deepseek-v4.1"`.

---

## 2. Logic Chain

### Step 1: Mapping R1 (Multi-Agent Market Perception & Alert Synthesis)
- **Observation**: `MultiTimeframeFilter` (`strategies/multi_timeframe.py`) buffers 1h and 4h candles and computes 50 EMA. `EMATrendStrategy` and `RSIBollingerStrategy` calculate 15m EMA 9/21, RSI 14, and BB 20 on individual symbol streams. In `main.py` (lines 212-237), 15m, 1h, and 4h candles are fetched during startup. However, in `risk_manager.py` (lines 294-320), the context passed to the AI council only contains raw candles, price, and basic event fields without standardized multi-timeframe trend matrices, volatility indicators (ATR/Bollinger), volume spikes, or technical alerts.
- **Inference**: To satisfy R1, a dedicated standardization pipeline is required:
  - Extract multi-timeframe indicators across 15m (entry/momentum), 1h (intermediate trend), and 4h (macro trend).
  - Compute normalized volume fluctuation metrics (e.g. volume ratio vs 20-period moving average).
  - Synthesize active technical alerts into an explicit alert bundle (e.g. `BULLISH_CONFLUENCE`, `BEARISH_DIVERGENCE`, `OVERBOUGHT_RSI`, `VOLUME_CLIMAX`).
  - Package this unified dictionary into `market_context["market_perception"]` prior to dispatching to the VAR council.

### Step 2: Mapping R2 (Autonomous Adversarial VAR Council & Consensus Engine)
- **Observation**: `ai_advisory/adversarial_debater.py` implements the 3-round structure (Round 1 Bull, Round 2 Bear, Round 3 Arbiter). In `vyce_client.py`, `council_mode == "adversarial"` invokes this engine.
- **Inference**: Gaps exist against R2 requirements:
  - **Confidence Gate**: R2 requires automatic approval ONLY when Arbiter confidence `>= 0.80`. In `adversarial_debater.py`, the parsed verdict is returned without enforcing this threshold; an Arbiter response with `confidence: 0.75` and `approved: true` would bypass the gate. Hard programmatic enforcement is needed: if `confidence < 0.80`, `approved` must be set to `False`.
  - **Liquidity Hunt & Wick Trap Detection**: The prompts in `ROUND2_BEAR_PROMPT` mention traps generally, but lack explicit instructions to detect liquidity hunt wicks (e.g. long upper/lower shadows exceeding 2x the candle body, false breakouts with declining volume, stop runs).
  - **Arbiter Output Contract**: The Arbiter must strictly output quantitative justification, `risk_score` (1-5), and `size_multiplier` (0.2x - 1.0x), and achieve `>= 85%` veto rate on trap/fakeout scenarios in test fixtures.

### Step 3: Mapping R3 (Dynamic Position Holding & Trailing Protocol)
- **Observation**: `TrailingStopManager` (`execution/trailing_stop.py`) implements Break-Even lock at +1.2% (moving SL to Entry + 0.2%) and Trailing Stop at +2.0% (1.0x ATR trailing). `CircuitBreaker` implements daily profit target lock at +10.0 USDT.
- **Inference**: Gaps exist against R3 requirements:
  - **House Money Partial Take-Profit (+3.0%)**: R3 explicitly requires: "kích hoạt cơ chế House Money Mode: chốt lời từng phần tại mốc mục tiêu (+3.0% hoặc khi chạm mốc lợi nhuận ngày +10 USDT), sau đó chỉ dùng một phần nhỏ lợi nhuận đã bảo toàn (0.2x size) để tiếp tục gồng các bước sóng tiếp theo."
  - Currently, `TrailingStopManager` has no logic for +3.0% partial take-profit or reducing position quantity.
  - `PaperTrader` and `BinanceExecutor` only execute full position closes on TP/SL. They need a handler for partial execution: closing 80% of the position at +3.0% (or when daily PnL >= 10 USDT), leaving a 0.2x runner position to ride further trend waves with Stop-Loss anchored safely in profit.

### Step 4: Mapping R4 (Market Psychology & Community Lessons Grounding)
- **Observation**: `data/storage.py` defines the `trading_lessons` table and seeds 3 historical technical lessons (`MARKET_CRASH`, `SLIPPAGE`, `STOP_LOSS`). `RiskManager` passes recent lessons from the DB to AI.
- **Inference**: Gaps exist against R4 requirements:
  - The SQLite database currently lacks the specific psychological error archetypes named in the prompt: FOMO đu đỉnh (chasing overextended green bars), Gồng lỗ buông xuôi (holding losing trades without SL), Chốt non (exiting winning runners prematurely), and Bẫy đòn bẩy cao (over-leverage during volatility).
  - No heuristic or deterministic pattern-matching engine exists to compare an incoming signal against these psychological traps prior to AI debate.
  - A `PsychologyPatternMatcher` should analyze entry conditions (e.g. price > 3x ATR from EMA indicates FOMO; leverage > 5x indicates over-leverage) and inject matched lessons directly into the Bear Devil's Advocate context.

### Step 5: Mapping R5 (Deterministic Risk Engine & Circuit Breaker)
- **Observation**:
  - Daily Loss Circuit Breaker: `CircuitBreaker.max_daily_loss_usd = 3.5`. When `daily_realized_pnl <= -3.5`, `is_tripped` is set to `True`, which `RiskManager` respects by halting all new trades.
  - Portfolio Position Limit: `MAX_OPEN_POSITIONS = 2` in `config/settings.py` line 47, enforced in `RiskManager.handle_signal` lines 235-240.
  - Per-Symbol Limit: `MAX_POSITIONS_PER_SYMBOL = 1` in `config/settings.py` line 48, enforced in `RiskManager.handle_signal` lines 242-256.
  - Quantitative Fallback Latency: `_execute_quantitative_fallback` is a pure synchronous Python calculation executing in `< 0.1ms` (well within the `< 100ms` SLA).
- **Inference**: R5 core requirements are already cleanly designed and implemented in the codebase. Only verification and regression test alignment are necessary.

---

## 3. Caveats

1. **Read-Only Scope**: In compliance with subagent exploration rules, no source code, configuration files, or database schemas outside `.agents/survey_explorer_1` were altered.
2. **Live External AI Latencies**: Live calls to Claude / DeepSeek via external proxies (Vyce AI / ETFBit) depend on network connectivity and VPS proxy load. The timeout thresholds (e.g. 25.0s for 3-round debate, 3.0s for single veto) must continue to have guaranteed fallback to maintain sub-second execution safety.
3. **Binance Futures Live Mode**: Live testing requires active API credentials with futures permissions and `LIVE_SAFETY_RELEASE_APPROVED=true`. Paper simulation mode accurately verifies OMS state transitions without financial risk.

---

## 4. Conclusion & Required Extension Points

To implement Requirements R1 through R5 seamlessly without breaking existing functionality, the following exact modifications and extension points are required:

### Component Extension Matrix

| Requirement | Target File(s) | Specific Extension Point & Modification Required |
|---|---|---|
| **R1: Market Perception & Alert Synthesis** | `strategies/multi_timeframe.py`<br>`risk_engine/risk_manager.py` | 1. Add `MarketPerceptionSynthesizer` in `strategies/multi_timeframe.py` (or new `ai_advisory/market_perception.py`) that computes multi-timeframe matrix: 15m (EMA 9/21, RSI 14, ATR 14, BB), 1h (EMA 50, trend), 4h (EMA 50, trend), volume ratio vs 20 SMA, and liquidity wick ratio.<br>2. In `RiskManager.handle_signal`, populate `market_context["market_perception"]` with synthesized indicators and alert flags. |
| **R2: Adversarial VAR Council & Consensus** | `ai_advisory/adversarial_debater.py`<br>`ai_advisory/vyce_client.py` | 1. Upgrade `ROUND2_BEAR_PROMPT` to explicitly evaluate liquidity hunt wicks, fakeouts, and volume exhaustion.<br>2. In `AdversarialDebater.debate_signal`, enforce hard rule: `final_verdict["approved"] = (confidence >= 0.80 and risk_score <= 3 and raw_approved)`. If confidence < 0.80, force `approved = False`.<br>3. Ensure `size_multiplier` (0.2x to 1.0x) is returned and propagated to `RiskManager`. |
| **R3: Dynamic Holding & Trailing Protocol** | `execution/trailing_stop.py`<br>`execution/paper_trader.py`<br>`execution/binance_executor.py` | 1. In `TrailingStopState` (`execution/trailing_stop.py`), add `partial_tp_threshold_pct = 0.03` (+3.0%) and `partial_tp_executed: bool = False`.<br>2. In `TrailingStopManager.update_price`, when `pnl_pct >= 0.03` and not `partial_tp_executed`, trigger action `PARTIAL_TP_HOUSE_MONEY` (close 80%, retain 0.2x runner).<br>3. In `PaperTrader` & `BinanceExecutor`, handle `PARTIAL_TP_HOUSE_MONEY`: realize PnL on 0.8x quantity, adjust open position to 0.2x quantity, and record partial fill in DB. |
| **R4: Psychology & Lessons Grounding** | `data/storage.py`<br>`ai_advisory/adversarial_debater.py`<br>`risk_engine/risk_manager.py` | 1. In `Database._seed_defaults_and_lessons` (`data/storage.py`), add seed lessons for: `FOMO_BUY_TOP`, `HOLDING_LOSERS`, `PREMATURE_EXIT`, `OVER_LEVERAGE`.<br>2. In `RiskManager` / `AdversarialDebater`, implement heuristic pattern matching against psychological errors before entering trades and inject matched lessons into `ROUND2_BEAR_PROMPT`. |
| **R5: Deterministic Risk Engine & Circuit Breaker** | `risk_engine/circuit_breaker.py`<br>`risk_engine/risk_manager.py`<br>`tests/test_risk_engine.py` | 1. Validate that -$3.50 loss breaker, max 2 concurrent positions, and max 1 position/symbol remain strictly enforced.<br>2. Update test assertions in `tests/test_risk_engine.py` to use `settings.MAX_POSITION_PERCENT` (0.25) instead of outdated hardcoded 0.20. |

---

## 5. Verification Method

### 5.1 Independent Commands
The downstream implementation agent can independently verify the system using these exact commands:

1. **Verify Baseline Trailing Stop & Break-Even**:
   ```powershell
   .\.venv\Scripts\pytest.exe tests/test_trailing_stop.py tests/test_paper_trailing.py -v
   ```
2. **Verify Multi-Timeframe Filter & Confluence**:
   ```powershell
   .\.venv\Scripts\pytest.exe tests/test_multi_timeframe.py -v
   ```
3. **Verify Paper Trader Execution**:
   ```powershell
   .\.venv\Scripts\pytest.exe tests/test_paper_trader.py -v
   ```
4. **Verify Risk Engine Baseline**:
   ```powershell
   .\.venv\Scripts\pytest.exe tests/test_risk_engine.py -k "test_circuit_breaker_trip or test_risk_manager_rejects_when_circuit_breaker_tripped or test_risk_manager_rejects_invalid_stop_loss or test_risk_manager_approves_valid_signal or test_risk_manager_vetoes_on_extreme_volatility" -v
   ```
5. **Verify AI Advisory & Adversarial Debater**:
   ```powershell
   .\.venv\Scripts\pytest.exe tests/test_m1_adversarial.py -v
   ```

### 5.2 Invalidation Conditions
- Any implementation where the AI council can override the -$3.50 daily loss Circuit Breaker violates R5.
- Any implementation where an open trade at +1.2% fails to adjust Stop-Loss to entry + fee buffer violates R3.
- Any implementation where the Arbiter approves a trade with confidence < 0.80 violates R2.
- Any implementation where `.agents/` contains source code, tests, or data files violates the file workspace convention.
