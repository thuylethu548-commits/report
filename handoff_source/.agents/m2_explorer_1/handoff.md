# Milestone 2 Exploration Report: Stop-Loss Hook in Execution Layer

## 1. Observation

### 1.1 Position Lifecycle in `execution/paper_trader.py`
- **Position Opening** (`execution/paper_trader.py:76-126`):
  - In `handle_order(self, order: OrderEvent)`: When `order.side == OrderSide.BUY` and `settings.TRADING_MODE == "paper"`:
    - Calculates fill price with simulated slippage `slippage_pct = random.uniform(0.0001, 0.0003)`:
      ```python
      fill_price = round(order.price * (1.0 + slippage_pct), 2)
      cost = fill_price * order.quantity
      fee = cost * self.fee_rate
      ```
    - Verifies sufficient USDT balance (`self.balance_usdt < (cost + fee)`).
    - Deducts `(cost + fee)` from `self.balance_usdt` and adds `order.quantity` to `self.base_asset_balance`.
    - Keyed by `pos_key = f"{order.strategy_name}_{order.symbol}"` into `self.open_positions[pos_key] = {...}` containing:
      `order_id`, `strategy_name`, `symbol`, `side`, `entry_price`, `quantity`, `stop_loss`, `take_profit`, `entry_time` (`datetime.now(timezone.utc)`), `fee`.
    - Invokes `await self.db.record_trade_open(...)` and emits `FillEvent(side=OrderSide.BUY)`.

- **Position Exit Detection** (`execution/paper_trader.py:42-69` and `128-132`):
  - **Market Tick Trigger** (`handle_market_tick`):
    Iterates through `self.open_positions.items()`.
    Stop-Loss trigger check (`execution/paper_trader.py:54-56`):
    ```python
    if pos["stop_loss"] > 0 and self.last_price <= pos["stop_loss"]:
        logger.warning(f"[Paper Stop Loss Hit] Order {pos_id} at price {self.last_price}")
        positions_to_close.append((pos_id, "STOP_LOSS"))
    ```
    Take-Profit trigger check (`execution/paper_trader.py:59-61`):
    ```python
    elif pos["take_profit"] > 0 and self.last_price >= pos["take_profit"]:
        logger.info(f"[Paper Take Profit Hit] Order {pos_id} at price {self.last_price}")
        positions_to_close.append((pos_id, "TAKE_PROFIT"))
    ```
    Closes all identified positions with `await self._close_position(pos_id, self.last_price, reason)`.
  - **Strategy Exit Trigger** (`handle_order`):
    When `order.side == OrderSide.SELL`, calls `await self._close_position(pos_key, order.price, "STRATEGY_EXIT")`.

- **Position Close Implementation & PnL Calculation** (`execution/paper_trader.py:133-176`):
  - Position is popped and cloned:
    ```python
    pos = self.open_positions.pop(pos_key)
    pos_copy = dict(pos)
    ```
  - Exit slippage is applied:
    `fill_price = round(exit_price * (1.0 - random.uniform(0.0001, 0.0003)), 2)`
  - Returns calculated:
    `gross_return = fill_price * pos["quantity"]`
    `exit_fee = gross_return * self.fee_rate`
    `net_return = gross_return - exit_fee`
    `self.balance_usdt += net_return`
    `self.base_asset_balance = max(0.0, self.base_asset_balance - pos["quantity"])`
  - PnL calculations (`execution/paper_trader.py:148-151`):
    ```python
    total_fees = pos["fee"] + exit_fee
    pnl_usdt = round(net_return - (pos["entry_price"] * pos["quantity"]), 4)
    cost_basis = pos["entry_price"] * pos["quantity"]
    pnl_pct = round((pnl_usdt / cost_basis) * 100.0, 2) if cost_basis > 0 else 0.0
    ```
  - Trade close recorded to SQLite via `await self.db.record_trade_close(...)` and `FillEvent(side=OrderSide.SELL)` published to `event_bus`.

- **Post-Mortem Trigger Hook in PaperTrader** (`execution/paper_trader.py:177-191`):
  ```python
  sl_threshold = -abs(settings.STOP_LOSS_PERCENT * 100)
  is_sl_reason = reason == "STOP_LOSS"
  is_severe_drawdown = pnl_pct <= sl_threshold
  is_severe_slippage = reason in ("SLIPPAGE", "SEVERE_SLIPPAGE") or (
      exit_price > 0 and ((exit_price - fill_price) / exit_price) >= 0.005
  )

  if is_sl_reason or is_severe_drawdown or is_severe_slippage:
      task = asyncio.create_task(
          self._trigger_auto_post_mortem(pos_copy, fill_price, pnl_usdt, pnl_pct, reason)
      )
      self._background_tasks.add(task)
      task.add_done_callback(self._background_tasks.discard)
  ```

---

### 1.2 Position Lifecycle and Stop-Loss Capture in `execution/binance_executor.py`
- **Subscription Scope** (`execution/binance_executor.py:34`):
  `BinanceExecutor` only subscribes to `OrderEvent` via `self.event_bus.subscribe(OrderEvent, self.handle_order)`. It does NOT subscribe to `MarketEvent`.
- **Live Order Execution** (`execution/binance_executor.py:36-145`):
  - Rejects if `settings.TRADING_MODE == "paper"`.
  - Dispatches order to Binance via `await self.client.create_order(symbol=order.symbol, order_type="market", side=order.side.value.lower(), amount=order.quantity)`.
  - Extracts `fill_price`, `filled_qty`, and `fee`.
  - On `BUY`: Stores open position in `self.open_positions[pos_key]` and calls `self.db.record_trade_open(...)`.
  - On `SELL` (`execution/binance_executor.py:91-140`):
    - Extracts position from `self.open_positions.pop(pos_key, None)`.
    - PnL calculations (`execution/binance_executor.py:96-99`):
      ```python
      cost_basis = pos["entry_price"] * filled_qty
      gross_return = fill_price * filled_qty
      pnl_usdt = round(gross_return - cost_basis - fee - pos.get("fee", 0.0), 4)
      pnl_pct = round((pnl_usdt / cost_basis) * 100.0, 2) if cost_basis > 0 else 0.0
      ```
    - Persists close in DB via `await self.db.record_trade_close(...)`.
    - Stop-Loss & Anomaly Detection (`execution/binance_executor.py:127-140`):
      ```python
      sl_threshold = -abs(settings.STOP_LOSS_PERCENT * 100)
      is_stop_loss = (pos and pos.get("stop_loss", 0.0) > 0 and fill_price <= pos["stop_loss"])
      is_severe_drawdown = pnl_pct <= sl_threshold
      expected_price = order.price
      is_severe_slippage = expected_price > 0 and ((expected_price - fill_price) / expected_price) >= 0.005

      if is_stop_loss or is_severe_drawdown or is_severe_slippage:
          reason = "STOP_LOSS" if is_stop_loss else ("SLIPPAGE" if is_severe_slippage else "SEVERE_DRAWDOWN")
          task = asyncio.create_task(
              self._trigger_auto_post_mortem(pos_copy, fill_price, pnl_usdt, pnl_pct, reason)
          )
          self._background_tasks.add(task)
          task.add_done_callback(self._background_tasks.discard)
      ```

---

### 1.3 `_trigger_auto_post_mortem` Implementation Analysis
- **Non-blocking Execution & Task Tracking**:
  - Both `PaperTrader` (line 36) and `BinanceExecutor` (line 31) declare `self._background_tasks: Set[asyncio.Task] = set()`.
  - Tasks are created with `task = asyncio.create_task(...)`, added to the set `self._background_tasks.add(task)`, and registered with `task.add_done_callback(self._background_tasks.discard)`.
- **Exception Shielding**:
  - The coroutine body is wrapped in `try: ... except Exception as e: logger.error(..., exc_info=True); return None`.
  - In addition, `VyceClient.generate_post_mortem` (`ai_advisory/vyce_client.py:270-278`) includes internal fallback returning a deterministic lesson dictionary if HTTP or parsing fails.
- **Trade Metadata Passed**:
  The dictionary passed to `generate_post_mortem` contains all 10 required fields:
  1. `order_id`: `pos.get("order_id", "")`
  2. `symbol`: `pos.get("symbol", settings.SYMBOL)`
  3. `strategy_name`: `pos.get("strategy_name", "Unknown")`
  4. `entry_price`: `float(pos.get("entry_price", 0.0))`
  5. `exit_price`: `float(exit_price)`
  6. `quantity`: `float(pos.get("quantity", 0.0))`
  7. `pnl_usdt`: `float(pnl_usdt)`
  8. `pnl_percent`: `float(pnl_pct)`
  9. `hold_duration_seconds`: `round(max(0.0, (datetime.now(timezone.utc) - entry_time).total_seconds()), 1)`
  10. `reason`: `reason`
- **Persistence & Audit Logging**:
  - Records lesson via `await self.db.add_lesson(...)` with `category`, `title`, `details`, `capital_impact`, `lesson_learned`, `operator`.
  - Logs critical/warning entry to `self.audit_logs` if injected.

---

### 1.4 Dependency Injection & Wiring in `main.py`
- In `execution/paper_trader.py:18-25`:
  ```python
  def __init__(
      self,
      event_bus: EventBus,
      db: Database,
      circuit_breaker: CircuitBreaker,
      vyce_client: Optional[VyceClient] = None,
      audit_logs: Optional[List[Dict[str, Any]]] = None
  ):
      self.event_bus = event_bus
      self.db = db
      self.circuit_breaker = circuit_breaker
      self.vyce_client = vyce_client or VyceClient()
      self.audit_logs = audit_logs
  ```
- In `execution/binance_executor.py:17-24`:
  ```python
  def __init__(
      self,
      event_bus: EventBus,
      binance_client: BinanceClient,
      db: Database,
      vyce_client: Optional[VyceClient] = None,
      audit_logs: Optional[List[Dict[str, Any]]] = None
  ):
      self.event_bus = event_bus
      self.client = binance_client
      self.db = db
      self.vyce_client = vyce_client or VyceClient()
      self.audit_logs = audit_logs
  ```
- Current wiring in `main.py:61-74`:
  ```python
  # 3. Vyce AI Client (Shared Keep-Alive Connection Pool)
  vyce_client = VyceClient()

  # 4. Risk Engine
  circuit_breaker = CircuitBreaker(max_daily_drawdown_percent=settings.DAILY_MAX_DRAWDOWN_PERCENT)
  circuit_breaker.reset_daily_metrics(settings.STARTING_BALANCE_USDT)
  risk_manager = RiskManager(event_bus, db, circuit_breaker, vyce_client=vyce_client)

  # 5. OMS & Execution
  oms = OrderManagementSystem(event_bus)
  paper_trader = PaperTrader(event_bus, db, circuit_breaker)
  binance_client = BinanceClient()
  binance_executor = BinanceExecutor(event_bus, binance_client, db)
  ```
  **Direct observation**: `main.py` creates a shared `vyce_client` on line 62, but passes it ONLY to `risk_manager` on line 67. Line 71 (`PaperTrader`) and line 73 (`BinanceExecutor`) do NOT receive `vyce_client=vyce_client` or `audit_logs=audit_logs`. Therefore, both instantiate separate unshared `VyceClient()` instances with separate HTTP connection pools.

---

### 1.5 Code Modularization & Architecture Alignment
- In `PROJECT.md:103-104`, the architecture specifies:
  - `ai_advisory/post_mortem.py`: Auto post-mortem service with structured prompt and SQLite insertion.
  - Contract: `async def analyze_and_record_lesson(self, trade_info: Dict[str, Any], db: Database) -> Dict[str, Any]`
- Currently, `ai_advisory/post_mortem.py` does not exist on disk. Instead, the logic is implemented directly in `PaperTrader` and `BinanceExecutor`, while the network prompt handling is in `VyceClient.generate_post_mortem`.
- Running test suite: `& 'c:\sunMy\trading_bot\.venv\Scripts\pytest.exe' -v` yielded **102 passed in 22.78s**.

---

## 2. Logic Chain

1. **Trade Exit & Stop-Loss Identification**:
   - In paper mode, price movement is received through `MarketEvent`. When `last_price <= pos["stop_loss"]`, the event is conclusively identified as `"STOP_LOSS"`, immediately terminating the position and generating financial metrics (`pnl_usdt`, `pnl_percent`).
   - In live mode, execution occurs on Binance. When a sell fill completes, `fill_price <= pos["stop_loss"]` or severe drawdown `pnl_pct <= sl_threshold` identifies the exit as a stop-loss event.
   - Therefore, the exit reason determination in both modules accurately differentiates normal strategy profit taking/exits from loss-protection stops.

2. **PnL Calculation Consistency**:
   - `PaperTrader` calculates `pnl_usdt = round(net_return - cost_basis, 4)` where `net_return = gross_return - exit_fee`.
   - `BinanceExecutor` calculates `pnl_usdt = round(gross_return - cost_basis - fee - pos.get("fee", 0.0), 4)` which additionally subtracts entry fee `pos.get("fee", 0.0)`.
   - To maintain identical reporting consistency between simulation and production, `PaperTrader` should also subtract `pos.get("fee", 0.0)`.

3. **Background Task Execution and Memory Safety**:
   - In Python `asyncio`, creating a coroutine with `asyncio.create_task()` without maintaining a reference exposes the task to early garbage collection if the event loop executes a garbage collection cycle while the task awaits HTTP I/O.
   - Retaining references in `self._background_tasks` and registering a discard callback (`task.add_done_callback(self._background_tasks.discard)`) ensures tasks remain alive for the full duration of the AI analysis and SQLite insertion without leaking memory.

4. **Fault Tolerance and Exception Shielding**:
   - The primary purpose of an automated trading engine is capital preservation and fast order execution. Any secondary analytics (such as LLM post-mortems) must never delay or fail the primary trade lifecycle.
   - Because `_trigger_auto_post_mortem` is launched asynchronously *after* position state cleanup and DB trade close recording, and because all internal exceptions are caught within `try...except Exception`, failure of the LLM or network outage has zero impact on bot stability.

5. **Dependency Injection & Resource Efficiency**:
   - `VyceClient` maintains an `httpx.AsyncClient` with a connection pool (`max_keepalive_connections=5, max_connections=10`).
   - By not injecting `vyce_client` in `main.py`, three separate HTTP clients with independent connection pools and connection timeouts are instantiated.
   - Injecting `vyce_client=vyce_client` across `RiskManager`, `PaperTrader`, and `BinanceExecutor` optimizes VPS connection resources and socket reuse.
   - Injecting a unified `audit_logs` list allows real-time operator alerts from post-mortem executions to stream directly to `/admin/audit-logs` and `/api/v1/status`.

---

## 3. Caveats

1. **Market Tick Listening in `BinanceExecutor`**:
   - Currently, `BinanceExecutor` only triggers Stop-Loss analysis when receiving a SELL `OrderEvent`. If Binance exchange-side stop-loss orders are not placed at entry, or if `BinanceExecutor` does not listen to `MarketEvent`, a market drop will not trigger an automatic exit in `BinanceExecutor` unless an external component publishes a SELL `OrderEvent`.
   - Consideration: If live trading is enabled without native Binance OCO/stop orders, `BinanceExecutor` should subscribe to `MarketEvent` to trigger emergency market sell orders when `pos["stop_loss"]` is breached.
2. **Post-Mortem Engine Abstraction (`ai_advisory/post_mortem.py`)**:
   - While `_trigger_auto_post_mortem` works inside `PaperTrader` and `BinanceExecutor`, introducing `ai_advisory/post_mortem.py` with `PostMortemEngine` as defined in `PROJECT.md` eliminates duplicated code between `PaperTrader` and `BinanceExecutor`.
3. **Database Concurrency Under High Load**:
   - `aiosqlite` uses a single shared connection with a serialized worker thread. Long transactions or concurrent writes from post-mortem, candle ingestion, and trade logging could encounter transient lock contention if not kept concise.

---

## 4. Conclusion & Recommended Strategy for Milestone 2

### Summary Assessment
Milestone 2 core mechanics (`_close_position`, Stop-Loss detection, PnL computation, non-blocking `asyncio.create_task` with `_background_tasks` tracking, exception shielding, and metadata structuring) are already implemented with solid foundations in `execution/paper_trader.py` and `execution/binance_executor.py`.

### Recommended Implementation Roadmap for M2:
1. **Unify Dependency Injection in `main.py`**:
   - Instantiate a shared `audit_logs = []` in `main.py`.
   - Pass `vyce_client=vyce_client` and `audit_logs=audit_logs` into `PaperTrader` and `BinanceExecutor`.
   - Pass `audit_logs=audit_logs` into `create_web_app`.
2. **Harmonize Net PnL Calculation in `PaperTrader`**:
   - Include entry fee in `PaperTrader._close_position` PnL formula (`net_return - cost_basis - pos.get("fee", 0.0)`) for strict mathematical parity with `BinanceExecutor`.
3. **Create `ai_advisory/post_mortem.py` (Per `PROJECT.md`)**:
   - Implement `PostMortemEngine` providing `analyze_and_record_lesson(trade_info, db)`.
   - Refactor `PaperTrader._trigger_auto_post_mortem` and `BinanceExecutor._trigger_auto_post_mortem` to delegate to `PostMortemEngine`.
4. **Expand Test Coverage for M2**:
   - Add unit tests for `BinanceExecutor` stop-loss hook and post-mortem trigger.
   - Add tests verifying background task set lifecycle (`_background_tasks` add and discard).
   - Add tests verifying all metadata fields (including `hold_duration_seconds` and PnL impact).
   - Verify 100% pass across the complete test suite.

---

## 5. Verification Method

1. **Run Full Automated Test Suite**:
   ```powershell
   & 'c:\sunMy\trading_bot\.venv\Scripts\pytest.exe' tests/ -v
   ```
   *Expected outcome*: All 102 existing tests pass with 0 failures.
2. **Inspect Code Locations**:
   - `execution/paper_trader.py:48-69` (SL detection on tick)
   - `execution/paper_trader.py:133-191` (`_close_position`, PnL calculations, task scheduling)
   - `execution/paper_trader.py:192-260` (`_trigger_auto_post_mortem` implementation)
   - `execution/binance_executor.py:91-145` (Live exit and SL detection)
   - `execution/binance_executor.py:147-215` (`_trigger_auto_post_mortem` live implementation)
   - `main.py:61-75` (Dependency injection sites)
3. **Invalidation Conditions**:
   - Any modification that allows an AI timeout or failure in `_trigger_auto_post_mortem` to raise an uncaught exception or block `_close_position`.
   - Any omission of the 10 required metadata fields when querying `VyceClient.generate_post_mortem`.
   - Failure to retain task references in `_background_tasks` causing garbage collection warnings.
