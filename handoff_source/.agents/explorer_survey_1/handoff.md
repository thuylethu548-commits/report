# Exploration Survey Report: Trading Bot Architecture, Signal & Execution Pipeline

**Agent**: Explorer Survey 1  
**Working Directory**: `c:\sunMy\trading_bot\.agents\explorer_survey_1`  
**Date**: 2026-09-17  
**Scope**: Codebase investigation of Signal Generation, Order Lifecycle & Execution, Risk Management & Stop-Loss Triggers, and Gatekeeper Hook Points for Claude-3.5-Sonnet Advisory Veto Engine.

---

## 1. Observation

Direct observations from source inspection and execution in `c:\sunMy\trading_bot`:

### A. Component Wiring & Runtime Entrypoint
- **File**: `c:\sunMy\trading_bot\main.py`
  - Lines 52-76: Instantiates core subsystems:
    - `Database(settings.DATABASE_PATH)` (line 53)
    - `EventBus()` (line 57)
    - `CircuitBreaker(max_daily_drawdown_percent=settings.DAILY_MAX_DRAWDOWN_PERCENT)` (line 61)
    - `RiskManager(event_bus, db, circuit_breaker)` (line 63)
    - `OrderManagementSystem(event_bus)` (line 66)
    - `PaperTrader(event_bus, db, circuit_breaker)` (line 67)
    - `BinanceClient()` & `BinanceExecutor(event_bus, binance_client, db)` (lines 68-69)
    - `MarketRegimeClassifier(event_bus, db)` (line 72)
    - `EMATrendStrategy(symbol=settings.SYMBOL, event_bus=event_bus)` (line 75)
    - `RSIBollingerStrategy(symbol=settings.SYMBOL, event_bus=event_bus)` (line 76)
  - Lines 79-83:
    ```python
    async def on_market_event(event: MarketEvent):
        await strategy_ema.on_market_event(event)
        await strategy_rsi.on_market_event(event)

    event_bus.subscribe(MarketEvent, on_market_event)
    ```
    *Observation*: `MarketEvent` is forwarded to both technical strategies, but `ai_classifier` is NOT invoked here.
  - Lines 88-100: Hot syncs system settings from SQLite `system_settings` table at startup, including `ENABLE_AI_ADVISORY`.
  - Lines 102-114: Launches FastAPI web application on `settings.DASHBOARD_HOST`:`settings.DASHBOARD_PORT` (default `127.0.0.1:8386`).
  - Lines 116-137: Starts `BinanceWebSocketFeed`, then fetches 60 historical candles via `binance_client.fetch_ohlcv` and pushes them to `strategy_ema.add_candle` and `strategy_rsi.add_candle` for warmup.

### B. Signal Generation Pipeline
- **Base Class**: `strategies/base_strategy.py`
  - Class `BaseStrategy(abc.ABC)` (line 12):
    - Stores candle history in `self._candles: List[dict]` up to `self.max_candles` (default 100/200).
    - `@property def dataframe` converts `_candles` to `pd.DataFrame` with `timestamp` index.
- **Strategy 1: EMA Trend**: `strategies/ema_trend.py`
  - Class `EMATrendStrategy(BaseStrategy)` (line 13).
  - Parameters: `fast_period=9`, `slow_period=21`, `atr_period=14`, `max_candles=100`.
  - State: `self.in_position = False` (line 19).
  - Processing (`on_market_event`, lines 21-86):
    - Rejects unclosed candles: `if not event.is_candle_closed: return None` (line 22).
    - Warmup check: `if len(df) < self.slow_period + 2: return None` (line 27).
    - Fast EMA: `df["close"].ewm(span=9, adjust=False).mean()` (line 31).
    - Slow EMA: `df["close"].ewm(span=21, adjust=False).mean()` (line 32).
    - 14-period ATR: True Range max of `(H-L, |H-C_prev|, |L-C_prev|)` (lines 35-41).
    - **BUY Condition (Golden Cross)** (lines 52-67):
      - Condition: `prev_fast <= prev_slow and curr_fast > curr_slow and not self.in_position`
      - Stop-Loss: `sl = round(price - (1.5 * atr), 2)`
      - Take-Profit: `tp = round(price + (3.0 * atr), 2)`
      - Confidence: `0.85`
      - Sets `self.in_position = True`
    - **SELL Condition (Death Cross / Exit)** (lines 69-82):
      - Condition: `prev_fast >= prev_slow and curr_fast < curr_slow and self.in_position`
      - Stop-Loss: `0.0`, Take-Profit: `0.0`
      - Confidence: `0.80`
      - Sets `self.in_position = False`
    - Event emission: `await self.event_bus.publish(signal)` (line 84).
- **Strategy 2: RSI Bollinger**: `strategies/rsi_bollinger.py`
  - Class `RSIBollingerStrategy(BaseStrategy)` (line 13).
  - Parameters: `bb_period=20`, `bb_std=2.0`, `rsi_period=14`, `max_candles=100`.
  - State: `self.in_position = False` (line 19).
  - Processing (`on_market_event`, lines 21-87):
    - Calculates 20-period SMA & STD bands (`bb_mid`, `bb_upper`, `bb_lower`) (lines 31-35).
    - Calculates 14-period RSI (lines 38-42).
    - **BUY Condition (Oversold Mean Reversion)** (lines 53-67):
      - Condition: `curr_rsi <= 35 and curr_close <= bb_lower * 1.002 and not self.in_position`
      - Stop-Loss: `sl = round(curr_close * 0.985, 2)` (1.5% below entry)
      - Take-Profit: `tp = round(bb_mid, 2)` (Mid Bollinger Band)
      - Confidence: `0.75`
      - Sets `self.in_position = True`
    - **SELL Condition (Overbought Exit)** (lines 70-82):
      - Condition: `(curr_rsi >= 68 or curr_close >= bb_upper) and self.in_position`
      - Stop-Loss: `0.0`, Take-Profit: `0.0`
      - Confidence: `0.75`
      - Sets `self.in_position = False`
    - Event emission: `await self.event_bus.publish(signal)` (line 85).
- **Manual Signal Ingestion**:
  - `web/routes/api_routes.py` lines 174-201 (`POST /api/v1/test_trade`):
    - Emits manual `SignalEvent(strategy_name="Manual-Operator", symbol=settings.SYMBOL, side=order_side, price=current_price, stop_loss=sl, take_profit=tp, confidence=0.95)` directly into `event_bus`.

### C. Order Lifecycle & Execution Pipeline
- **Signal Interception**: `risk_engine/risk_manager.py`
  - Subscribes to `SignalEvent`: `self.event_bus.subscribe(SignalEvent, self.handle_signal)` (line 24).
  - Subscribes to `AIAdvisoryEvent`: `self.event_bus.subscribe(AIAdvisoryEvent, self.handle_ai_advisory)` (line 25).
  - Method `handle_signal(self, signal: SignalEvent) -> Optional[OrderEvent]` (lines 30-120):
    - **Rule 1**: Checks `if self.circuit_breaker.is_tripped:` -> calls `_record_rejection(signal, reason)`, returns `None`.
    - **Rule 2**: Checks `if settings.ENABLE_AI_ADVISORY and self.latest_ai_advisory:`:
      - If `not self.latest_ai_advisory.trade_allowed` or `regime == MarketRegime.EXTREME_VOLATILITY` -> calls `_record_rejection(signal, reason)`, returns `None`.
    - **Rule 3**: Checks `if signal.side == OrderSide.BUY and len(self.open_positions) >= settings.MAX_OPEN_POSITIONS:` -> rejects if max positions reached.
    - **Rule 4**: Checks `if signal.side == OrderSide.BUY`: validates `signal.stop_loss > 0 and signal.stop_loss < signal.price` -> rejects if invalid.
    - **Position Sizing**:
      - `max_alloc = (circuit_breaker.current_equity or STARTING_BALANCE_USDT) * MAX_POSITION_PERCENT` (0.20 = 20%).
      - `ai_mult = self.latest_ai_advisory.size_multiplier if self.latest_ai_advisory else 1.0`.
      - `allocated_usdt = max_alloc * max(0.2, min(1.0, ai_mult))`.
      - `quantity = round(allocated_usdt / signal.price, 6)`.
    - **Approval & Emission**:
      - Records approved signal in SQLite table `signals` with `approved=1` via `self.db.save_signal` (lines 105-116).
      - Creates `OrderEvent(order_id=str(uuid.uuid4())[:12], ..., order_type=OrderType.MARKET, status=OrderStatus.PENDING)`.
      - Publishes: `await self.event_bus.publish(order_event)` (line 119).
- **OMS Tracking**: `execution/oms.py`
  - Subscribes to `OrderEvent` (line 15) and stores in `self.orders[order_id]`.
  - Subscribes to `FillEvent` (line 16) and updates `self.orders[order_id].status = OrderStatus.FILLED`.
- **Execution Handlers**:
  - `PaperTrader` in `execution/paper_trader.py`:
    - Subscribes to `OrderEvent` (line 27). Active when `settings.TRADING_MODE == "paper"`.
    - Applies simulated slippage `random.uniform(0.0001, 0.0003)` (line 63).
    - Computes `fill_price = round(order.price * (1.0 + slippage_pct), 2)`.
    - Deducts USDT `cost + fee` (fee rate = 0.1%), increases base asset balance (lines 66-74).
    - Populates `self.open_positions[f"{order.strategy_name}_{order.symbol}"]` (lines 77-88).
    - Calls `await self.db.record_trade_open(order_id, ..., status='OPEN')` (lines 90-100).
    - Publishes `FillEvent(..., is_paper=True)` (lines 102-114).
  - `BinanceExecutor` in `execution/binance_executor.py`:
    - Subscribes to `OrderEvent` (line 20). Active when `settings.TRADING_MODE != "paper"`.
    - Calls `await self.client.create_order(...)` via CCXT.
    - Records trade in SQLite via `db.record_trade_open` or `record_trade_close`.
    - Publishes `FillEvent(..., is_paper=False)`.

### D. Risk Management & Stop-Loss Triggers
- **Circuit Breaker**: `risk_engine/circuit_breaker.py`
  - Tracks `day_start_balance`, `current_balance`, `current_equity`, `is_tripped`, `trip_reason`.
  - Method `update_equity(balance, equity) -> bool` (lines 28-48):
    - Computes `drawdown = (day_start_balance - current_equity) / day_start_balance`.
    - If `drawdown >= max_daily_drawdown` (0.02 = 2%): sets `is_tripped = True`, freezes further orders.
- **Stop-Loss per Market Tick**: `execution/paper_trader.py`
  - Method `handle_market_tick(event: MarketEvent)` (lines 30-57):
    - Subscribed to `MarketEvent` (line 28).
    - Iterates `self.open_positions`:
      ```python
      # Stop-Loss Check:
      if pos["stop_loss"] > 0 and self.last_price <= pos["stop_loss"]:
          logger.warning(f"[Paper Stop Loss Hit] Order {pos_id} at price {self.last_price}")
          positions_to_close.append((pos_id, "STOP_LOSS"))

      # Take-Profit Check:
      elif pos["take_profit"] > 0 and self.last_price >= pos["take_profit"]:
          logger.info(f"[Paper Take Profit Hit] Order {pos_id} at price {self.last_price}")
          positions_to_close.append((pos_id, "TAKE_PROFIT"))
      ```
  - Method `_close_position(pos_key, exit_price, reason)` (lines 121-163):
    - Pops position from `self.open_positions`.
    - Calculates exit slippage, fee, `pnl_usdt`, and `pnl_percent`.
    - Calls `await self.db.record_trade_close(order_id, fill_price, exit_fee, exit_time, pnl_usdt, pnl_pct)`.
    - Publishes `FillEvent(side=OrderSide.SELL)`.

### E. AI Advisory Infrastructure & Database Schema
- **Vyce Client**: `ai_advisory/vyce_client.py`
  - `VyceClient.chat_completion(system_prompt, user_content)` sends HTTP POST to `{VYCE_BASE_URL}/chat/completions`.
  - Headers: `Authorization: Bearer {VYCE_API_KEY}`, `Content-Type: application/json`.
  - Payload: `{"model": self.model, "messages": [...], "temperature": 0.2, "max_tokens": 250}`.
  - Timeout: `settings.AI_TIMEOUT_SECONDS = 3.0` seconds with fallback returning `None`.
- **Regime Classifier**: `ai_advisory/regime_classifier.py`
  - `MarketRegimeClassifier.evaluate_market(df, symbol) -> AIAdvisoryEvent`:
    - Sends prompt with 24-period price change, volatility, and volume ratio.
    - Parses JSON: `regime`, `risk_score`, `trade_allowed`, `size_multiplier`, `reasoning`.
    - Saves record to SQLite `ai_advisory_logs` table via `db.save_ai_advisory`.
    - Publishes `AIAdvisoryEvent` to `event_bus`.
  - *Observation*: In `main.py`, `ai_classifier` is instantiated but `evaluate_market` is NEVER invoked during runtime loops.
- **SQLite Database Schema**: `data/storage.py` (lines 26-129)
  - Tables:
    - `candles`: `id, symbol, timestamp, open, high, low, close, volume`
    - `trades`: `order_id, strategy_name, symbol, side, entry_price, exit_price, quantity, fee, entry_time, exit_time, pnl_usdt, pnl_percent, is_paper, status`
    - `signals`: `id, strategy_name, symbol, side, price, stop_loss, take_profit, confidence, timestamp, approved, rejection_reason`
    - `ai_advisory_logs`: `id, symbol, regime, risk_score, trade_allowed, size_multiplier, reasoning, timestamp`
    - `equity_snapshots`: `id, timestamp, balance_usdt, equity_usdt, open_positions, daily_drawdown`
    - `system_settings`: `key, value, data_type, description, updated_at` (dynamic config, hot-reloaded)
    - `trading_lessons`: `id, timestamp, category, title, details, capital_impact, lesson_learned, operator`
  - Methods on Database: `add_lesson`, `get_lessons`, `delete_lesson`, `get_setting`, `set_setting`, `get_all_settings`.
- **Existing Test Suite**: `tests/`
  - Verified with `.venv\Scripts\pytest.exe -v`: All 10 tests passed (4.13s).

---

## 2. Logic Chain

From the direct observations above, we establish the following deductive chain:

1. **Signal Generation is Independent and Strategy-Scoped**:
   - Both `EMATrendStrategy` and `RSIBollingerStrategy` independently compute indicators on closed candles and publish `SignalEvent` to `EventBus` without knowledge of account balance, open positions, or AI regime.
   - Stop-Loss and Take-Profit calculations are deterministic: EMA Trend uses `1.5x ATR` / `3.0x ATR`; RSI Bollinger uses fixed `1.5%` / `BB Mid`.
2. **Execution is Gated by `RiskManager`**:
   - Every `SignalEvent` reaches `RiskManager.handle_signal` first.
   - `RiskManager` evaluates deterministic checks (CircuitBreaker, StopLoss bounds, position limits) and can veto the trade by calling `_record_rejection` and returning `None`.
   - Only approved signals produce `OrderEvent` and are dispatched to `PaperTrader` or `BinanceExecutor`.
3. **The Current Advisory Check is Inactive & Decoupled**:
   - `RiskManager` checks `settings.ENABLE_AI_ADVISORY and self.latest_ai_advisory` (lines 38-50).
   - However, `latest_ai_advisory` is only updated if `AIAdvisoryEvent` is received from the bus.
   - No background loop or trigger calls `evaluate_market` in `main.py`.
   - Furthermore, requirement R1 requires AI evaluation when a technical signal is generated ("Khi các thuật toán kỹ thuật sinh tín hiệu MUA/BÁN, AI đánh giá bối cảnh vĩ mô và chỉ cho phép lệnh đi tiếp nếu đồng thuận").
   - Therefore, the gatekeeper must actively evaluate signals inside `RiskManager.handle_signal` (or via an active advisory call before order emission) rather than passively reading a stale variable.
4. **The Stop-Loss Execution Path Lacks Post-Mortem Event Emission**:
   - When a stop-loss is triggered in `PaperTrader.handle_market_tick`, `_close_position` is called with `reason="STOP_LOSS"`.
   - `_close_position` logs the event and updates SQLite `trades` table, but `reason` is not persisted to the database nor included in `FillEvent`.
   - No event (`StopLossHitEvent` or `TradeClosedEvent`) is published to `EventBus`.
   - Consequently, there is currently no event trigger for Claude-3.5-Sonnet to conduct an Auto Post-Mortem and insert a record into `trading_lessons` (as required by R2).
5. **Dynamic Configuration & Hot-Reload is Already Established**:
   - `web/routes/api_routes.py` lines 207-263 (`POST /api/v1/settings`) supports runtime updates for `ENABLE_AI_ADVISORY`, `DAILY_MAX_DRAWDOWN_PERCENT`, `SYMBOL`, `TIMEFRAME`, etc., syncing directly into `settings` and SQLite `system_settings`.
   - `/admin/settings` and `/admin/lessons` are already functional web templates hooked to these APIs.
   - Adding Claude-3.5-Sonnet confidence and latest advisory to `/admin` only requires connecting the API response to the dashboard UI.

---

## 3. Data Structures & Contract Reference

### Core Events (`core/events.py`)
```python
@dataclass
class MarketEvent:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_candle_closed: bool = True

@dataclass
class SignalEvent:
    strategy_name: str
    symbol: str
    side: OrderSide  # BUY / SELL
    price: float
    timestamp: datetime
    stop_loss: float
    take_profit: float
    confidence: float = 1.0

@dataclass
class AIAdvisoryEvent:
    symbol: str
    timestamp: datetime
    regime: MarketRegime  # BULL_TREND, BEAR_TREND, RANGING, EXTREME_VOLATILITY, UNKNOWN
    risk_score: int       # 1 to 5
    trade_allowed: bool
    size_multiplier: float  # 0.0 to 1.0
    reasoning: str = ""

@dataclass
class OrderEvent:
    order_id: str
    strategy_name: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    status: OrderStatus = OrderStatus.PENDING

@dataclass
class FillEvent:
    order_id: str
    strategy_name: str
    symbol: str
    side: OrderSide
    fill_price: float
    quantity: float
    fee: float
    timestamp: datetime
    is_paper: bool = True
```

### Database Schema Table Contracts (`data/storage.py`)
| Table Name | Primary Key | Key Columns |
|---|---|---|
| `trading_lessons` | `id` (INTEGER AUTOINCREMENT) | `timestamp`, `category` (`MARKET_CRASH`, `SLIPPAGE`, `STOP_LOSS`, `CIRCUIT_BREAKER`, `MANUAL_NOTE`), `title`, `details`, `capital_impact` (REAL), `lesson_learned`, `operator` |
| `signals` | `id` (INTEGER AUTOINCREMENT) | `strategy_name`, `symbol`, `side`, `price`, `stop_loss`, `take_profit`, `confidence`, `timestamp`, `approved` (0/1), `rejection_reason` |
| `trades` | `order_id` (TEXT) | `strategy_name`, `symbol`, `side`, `entry_price`, `exit_price`, `quantity`, `fee`, `entry_time`, `exit_time`, `pnl_usdt`, `pnl_percent`, `is_paper`, `status` (`OPEN`/`CLOSED`) |
| `ai_advisory_logs` | `id` (INTEGER AUTOINCREMENT) | `symbol`, `regime`, `risk_score`, `trade_allowed`, `size_multiplier`, `reasoning`, `timestamp` |
| `system_settings` | `key` (TEXT) | `value`, `data_type`, `description`, `updated_at` |

---

## 4. Gatekeeper Hook Points for Advisory Veto Engine

### Recommended Hook Point: `RiskManager.handle_signal` (Synchronous Pre-Order Interception)
- **Target File**: `c:\sunMy\trading_bot\risk_engine\risk_manager.py`
- **Target Method**: `handle_signal(self, signal: SignalEvent) -> Optional[OrderEvent]`
- **Location**: Lines 38-50 (replacing passive cached check with an active advisory gatekeeper call).
- **Proposed Architecture**:
  1. When `settings.ENABLE_AI_ADVISORY` is True:
     - Gather market context (recent candles, current spread, volatility, strategy name, direction).
     - Query Claude-3.5-Sonnet via `VyceClient` using a dedicated Advisory Prompt.
     - Enforce `< 3.0s` timeout via `asyncio.wait_for(..., timeout=settings.AI_TIMEOUT_SECONDS)`.
  2. Fallback Mechanism:
     - On timeout or network error, log fallback and proceed based on technical signal confidence or safe deterministic rules (`trade_allowed=True`, `size_multiplier=0.5` or `1.0`).
  3. Decision Processing:
     - If AI vetos (`trade_allowed is False`):
       - Call `await self._record_rejection(signal, f"AI Advisory Veto: {reasoning}")`.
       - Return `None` (no `OrderEvent` is created; execution pipeline stops).
     - If AI approves:
       - Scale quantity using `size_multiplier`.
       - Record approval in SQLite `signals` and `ai_advisory_logs`.
       - Construct and publish `OrderEvent`.

### Auto Post-Mortem Hook Point for Stop-Loss (R2)
- **Target File**: `c:\sunMy\trading_bot\execution\paper_trader.py` (and `execution/binance_executor.py`)
- **Target Method**: `_close_position(self, pos_key: str, exit_price: float, reason: str)`
- **Location**: Line 162 (right after recording trade close in DB and publishing FillEvent).
- **Proposed Architecture**:
  1. Check condition: `if reason == "STOP_LOSS" or pnl_percent <= -settings.STOP_LOSS_PERCENT * 100:`.
  2. Spawn an asynchronous background task: `asyncio.create_task(post_mortem_engine.analyze_and_record(trade_data))`.
     - Non-blocking: will NOT freeze or delay the execution thread or web server.
  3. The Post-Mortem engine calls Claude-3.5-Sonnet via `VyceClient` to produce:
     - `category`: `"STOP_LOSS"`
     - `title`: e.g. `"Quét Stop-Loss lệnh Long BTC @ $60,000"`
     - `details`: Market conditions leading to exit
     - `capital_impact`: `abs(pnl_usdt)`
     - `lesson_learned`: Capital preservation rule
  4. Inserts into SQLite `trading_lessons` table via `await db.add_lesson(...)`.
  5. The `/admin/lessons` UI and `/api/v1/lessons` automatically display the new lesson on the next refresh/poll without server restart.

---

## 5. Caveats

1. **State Persistence of Strategies**:
   - `EMATrendStrategy` and `RSIBollingerStrategy` maintain `self.in_position = False` as an in-memory boolean flag. On bot restart, if a position is currently open in SQLite, the strategy state will reset to `False`.
2. **`RiskManager.open_positions` vs `PaperTrader.open_positions`**:
   - `RiskManager` defines `self.open_positions = {}` and checks `len(self.open_positions) >= settings.MAX_OPEN_POSITIONS` at line 52, but never updates it when `OrderEvent` is filled. `PaperTrader` maintains its own `open_positions`. For multi-position enforcement to work across components, `RiskManager` should sync with `PaperTrader` or listen to `FillEvent`.
3. **VPS Environment Configuration**:
   - In `.env`, `VYCE_MODEL` is set to `deepseek-chat` and `ENABLE_AI_ADVISORY=False`. On VPS, `VYCE_BASE_URL` and `VYCE_API_KEY` are provisioned, and `VYCE_MODEL` should be configured as `claude-3-5-sonnet`.
4. **WebSocket Feed in Tests**:
   - Live WebSocket requires external internet connectivity to `stream.binance.com:9443`. Unit tests isolate this by using `Database(tmp_path)` and mocked feeds.

---

## 6. Conclusion

- The codebase is modular, clean, and well-architected around an asynchronous `EventBus`.
- Strategy signals (`EMATrendStrategy`, `RSIBollingerStrategy`) cleanly transition to `SignalEvent`.
- `RiskManager` is the single authoritative gateway where signals are validated, sized, logged to SQLite, and transformed into executable `OrderEvent`s.
- Hooking Claude-3.5-Sonnet Advisory Veto into `RiskManager.handle_signal` (with `< 3.0s` timeout fallback) provides 100% interception before order dispatch with zero race conditions.
- Hooking Auto Post-Mortem into `PaperTrader._close_position` (and live trade close) via a non-blocking task cleanly addresses requirement R2, populating the existing SQLite `trading_lessons` schema for instant display on `/admin/lessons`.

---

## 7. Verification Method

To independently verify these findings:

1. **Run Full Test Suite**:
   ```powershell
   .venv\Scripts\pytest.exe -v
   ```
   Expected: 10 passed tests verifying strategy signals, circuit breaker tripping, paper trading TP/SL, dynamic settings, and AI advisory parsing.

2. **Verify Signal Event Flow & Risk Interception**:
   - Inspect `strategies/ema_trend.py:84` and `strategies/rsi_bollinger.py:85` for `event_bus.publish(signal)`.
   - Inspect `risk_engine/risk_manager.py:24` for `event_bus.subscribe(SignalEvent, self.handle_signal)`.
   - Inspect `risk_engine/risk_manager.py:119` for `event_bus.publish(order_event)`.

3. **Verify Stop-Loss Evaluation**:
   - Inspect `execution/paper_trader.py:42-45` for `self.last_price <= pos["stop_loss"]` trigger condition and line 56 calling `_close_position(pos_id, self.last_price, "STOP_LOSS")`.

4. **Verify Database Schema**:
   - Inspect `data/storage.py:116-128` to confirm `trading_lessons` schema matches post-mortem requirement.
