# M2 Explorer 3 Handoff Report: UI/API Rendering, main.py Wiring, and Test Suite Design

**Author**: M2 Explorer 3 (teamwork_preview_explorer)  
**Date**: 2026-09-17  
**Working Directory**: `c:\sunMy\trading_bot\.agents\m2_explorer_3`  
**Milestone**: Milestone 2 (Auto Post-Mortem, SQLite Lessons Engine, main.py Wiring & Test Harness)

---

## 1. Observation

### 1.1 `main.py` Instantiation & Wiring
- **Database & EventBus**:
  - `main.py:54-55`:
    ```python
    db = Database(settings.DATABASE_PATH)
    await db.connect()
    ```
  - `main.py:58-59`:
    ```python
    event_bus = EventBus()
    event_bus.start()
    ```
- **VyceClient Shared Pool**:
  - `main.py:62`:
    ```python
    vyce_client = VyceClient()
    ```
  - `main.py:67`: `risk_manager = RiskManager(event_bus, db, circuit_breaker, vyce_client=vyce_client)` successfully receives the shared `vyce_client`.
  - `main.py:76`: `ai_classifier = MarketRegimeClassifier(event_bus, db, client=vyce_client)` successfully receives the shared `vyce_client`.
- **Execution Engines (Omission Observed)**:
  - `main.py:71`:
    ```python
    paper_trader = PaperTrader(event_bus, db, circuit_breaker)
    ```
  - `main.py:73`:
    ```python
    binance_executor = BinanceExecutor(event_bus, binance_client, db)
    ```
  - `execution/paper_trader.py:23-29`:
    ```python
    def __init__(
        self,
        event_bus: EventBus,
        db: Database,
        circuit_breaker: CircuitBreaker,
        vyce_client: Optional[VyceClient] = None,
        audit_logs: Optional[List[Dict[str, Any]]] = None
    ):
        ...
        self.vyce_client = vyce_client or VyceClient()
    ```
  - `execution/binance_executor.py:22-28`:
    ```python
    def __init__(
        self,
        event_bus: EventBus,
        binance_client: BinanceClient,
        db: Database,
        vyce_client: Optional[VyceClient] = None,
        audit_logs: Optional[List[Dict[str, Any]]] = None
    ):
        ...
        self.vyce_client = vyce_client or VyceClient()
    ```
  - **Direct Observation**: Because `vyce_client` and `audit_logs` are omitted in `main.py:71` and `main.py:73`, both `PaperTrader` and `BinanceExecutor` instantiate their own fallback `VyceClient()` instances, creating duplicate HTTP client pools and leaving `self.audit_logs` as `None` (preventing auto post-mortem events from being appended to the live operator audit log).
- **Background Tasks & Shutdown Sequence**:
  - `execution/paper_trader.py:36`: `self._background_tasks: Set[asyncio.Task] = set()`
  - `execution/paper_trader.py:186-190`:
    ```python
    task = asyncio.create_task(
        self._trigger_auto_post_mortem(pos_copy, fill_price, pnl_usdt, pnl_pct, reason)
    )
    self._background_tasks.add(task)
    task.add_done_callback(self._background_tasks.discard)
    ```
  - `execution/paper_trader.py` and `binance_executor.py` have **no `close()` or `stop()` method** implemented.
  - `main.py:161-171`:
    ```python
    finally:
        logger.info("Shutting down Trading Lab services...")
        await ws_feed.stop()
        await event_bus.stop()
        await binance_client.close()
        await vyce_client.close()
        await db.close()
        server.should_exit = True
        await dashboard_task
        logger.info("All services stopped safely.")
    ```
  - **Direct Observation**: During shutdown, `main.py` closes `vyce_client` and `db` immediately without waiting for running tasks in `paper_trader._background_tasks` or `binance_executor._background_tasks`. Any in-flight post-mortem task will raise `RuntimeError: Cannot operate on closed database` or `httpx.ClientClosed`.

---

### 1.2 Web UI and API Routes
- **`web/routes/admin_routes.py:51-61`**:
  ```python
  @router.get("/lessons", response_class=HTMLResponse)
  async def admin_lessons(request: Request):
      return templates.TemplateResponse(
          request=request,
          name="admin/lessons.html",
          context={
              "title": "Sổ Tay Bài Học Xương Máu — Astra Desk",
              "current_page": "lessons",
              "breadcrumb": "SỔ TAY BÀI HỌC XƯƠNG MÁU & QUẢN TRỊ RỦI RO"
          }
      )
  ```
- **`web/templates/admin/lessons.html:26`**:
  Contains `<div class="card-body" id="lessons-container"><!-- Populated via admin_app.js --></div>` and form `<form id="add-lesson-form" onsubmit="addLessonSubmit(event)">`.
- **`web/templates/layouts/admin_base.html:38-40`**:
  Sidebar navigation link: `<a href="/admin/lessons" class="nav-item {% if current_page == 'lessons' %}active{% endif %}"><span>🛡️</span> Bài Học Xương Máu</a>`.
- **`web/routes/api_routes.py:285-288`**:
  ```python
  # === TRADING LESSONS ENDPOINTS ("Bài học xương máu") ===
  @router.get("/lessons")
  async def get_lessons(limit: int = 50):
      return await db.get_lessons(limit=limit)
  ```
- **`data/storage.py:334-338`**:
  ```python
  async def get_lessons(self, limit: int = 50) -> List[Dict[str, Any]]:
      async with self._conn.cursor() as cursor:
          await cursor.execute("SELECT * FROM trading_lessons ORDER BY id DESC LIMIT ?", (limit,))
          rows = await cursor.fetchall()
          return [dict(row) for row in rows]
  ```
  - **Direct Observation**: `db.get_lessons()` currently orders by `id DESC`. To strictly satisfy the requirement: *"Ensure it returns the lessons list ordered by timestamp DESC"*, the query must explicitly specify `ORDER BY timestamp DESC, id DESC LIMIT ?`.
- **`web/static/js/admin_app.js:220-259` & `318-331`**:
  - Function `loadLessons()` fetches `/api/v1/lessons` and injects lesson cards into `#lessons-container`.
  - In `DOMContentLoaded` (lines 318-331), `loadLessons()` is called once upon initial page load, but is **not** included in the periodic `setInterval` loops (unlike `updateAdminCockpit` at 2500ms and `updateAuditTerminal` at 3000ms).

---

### 1.3 Test Suite Status & Baseline
- Executed project test command: `.venv\Scripts\pytest -v`.
- Result: **102 passed in 23.23s** (100% pass rate).
- Current tests in `tests/test_auto_post_mortem.py` (lines 1-140):
  1. `test_auto_post_mortem_triggered_on_stop_loss`: Tests SL trigger, mocks `mock_vyce.generate_post_mortem` completely, asserts lesson written to `test_db`.
  2. `test_auto_post_mortem_fallback_on_ai_failure`: Tests fallback when `generate_post_mortem` raises `RuntimeError`.
- Missing in `tests/test_auto_post_mortem.py`:
  - Direct unit test of `VyceClient.generate_post_mortem` covering JSON parsing, markdown code fences, corrupted/empty field recovery, and deterministic fallback.
  - Integration assertion verifying that `asyncio.create_task` fires (checking task registry).
  - High-precision non-blocking timing test asserting `_close_position` execution time is strictly `< 5.0ms` during simulated slow AI network latency.

---

## 2. Logic Chain

```
[Observation 1.1: main.py lines 71, 73 omit vyce_client]
        │
        ▼
[Each engine instantiates an unshared VyceClient with its own connection pool]
        │
        ▼
[Resource duplication, connection leakage, and unclosed HTTP clients at shutdown]
        │
        ▼
[Recommendation: Pass vyce_client=vyce_client and shared audit_logs to both PaperTrader and BinanceExecutor in main.py]

[Observation 1.1: PaperTrader & BinanceExecutor have no close() method]
        │
        ▼
[On SIGINT/SIGTERM, main.py closes db and vyce_client immediately while background post-mortem tasks may still be writing]
        │
        ▼
[Tasks crash with RuntimeError / connection aborted, dropping post-mortem lessons]
        │
        ▼
[Recommendation: Add async def close(self, timeout=5.0) to both execution engines and await them in main.py finally block before closing DB]

[Observation 1.2: storage.py:336 queries ORDER BY id DESC]
        │
        ▼
[Requirement demands lessons list ordered by timestamp DESC]
        │
        ▼
[Recommendation: Change query to SELECT * FROM trading_lessons ORDER BY timestamp DESC, id DESC LIMIT ?]

[Observation 1.2: admin_app.js only calls loadLessons() on page load]
        │
        ▼
[Requirement R2 states: "Dữ liệu hiển thị ngay lập tức trên giao diện /admin/lessons mà không cần can thiệp thủ công"]
        │
        ▼
[Recommendation: Add setInterval(loadLessons, 3000) when #lessons-container is present in DOM]

[Observation 1.3: test_auto_post_mortem.py lacks unit tests for generate_post_mortem & non-blocking latency benchmark]
        │
        ▼
[Risk of regression or trade blocking during Vyce AI network latency]
        │
        ▼
[Recommendation: Design 4-tier comprehensive test harness in tests/test_auto_post_mortem.py maintaining 100% pass rate]
```

---

## 3. Caveats
1. **Windows Event Loop Signal Handler**: On Windows, `loop.add_signal_handler(sig, signal_handler)` raises `NotImplementedError` (handled safely in `main.py:154` via `KeyboardInterrupt`). Tests for shutdown should mock or simulate cancellation rather than relying on OS POSIX signals.
2. **Timing Jitter on Slow CI / Virtualized VPS**: Python `asyncio.create_task` takes ~0.05ms–0.2ms. The non-blocking test threshold of `< 5.0ms` is resilient, but tests should use `time.perf_counter()` and test against a simulated network latency of at least `500ms` or `1000ms` to provide a clear order-of-magnitude separation.
3. **Milestone Boundary**: Settings hot-reload controls (`POST /api/v1/settings`) are part of Milestone 3; however, the API route is already defined in `api_routes.py` and must not be altered in ways that conflict with M3.

---

## 4. Conclusion

### 4.1 Recommended Changes to `main.py`
1. **Instantiate shared `audit_logs` and wire into engines & web app**:
   ```python
   # Line 69: Shared in-memory audit log buffer
   audit_logs: List[Dict[str, Any]] = []

   # Lines 70-74: OMS & Execution with injected vyce_client and audit_logs
   oms = OrderManagementSystem(event_bus)
   paper_trader = PaperTrader(event_bus, db, circuit_breaker, vyce_client=vyce_client, audit_logs=audit_logs)
   binance_client = BinanceClient()
   binance_executor = BinanceExecutor(event_bus, binance_client, db, vyce_client=vyce_client, audit_logs=audit_logs)

   # Line 106: Web App receiving shared audit_logs
   web_app = create_web_app(db, circuit_breaker, event_bus, paper_trader, binance_client, audit_logs=audit_logs)
   ```
2. **Add `close()` method to `PaperTrader` and `BinanceExecutor`**:
   In `execution/paper_trader.py` and `execution/binance_executor.py`:
   ```python
   async def close(self, timeout: float = 5.0) -> None:
       """Gracefully awaits any in-flight background post-mortem tasks before shutdown."""
       if self._background_tasks:
           logger.info(f"Waiting for {len(self._background_tasks)} background post-mortem task(s) to finish...")
           done, pending = await asyncio.wait(self._background_tasks, timeout=timeout)
           for t in pending:
               t.cancel()
   ```
3. **Orderly shutdown sequence in `main.py:161-171`**:
   ```python
   finally:
       logger.info("Shutting down Trading Lab services...")
       await ws_feed.stop()
       await event_bus.stop()
       # 1. Gracefully flush post-mortem tasks before closing clients and DB
       await paper_trader.close()
       await binance_executor.close()
       # 2. Close external clients & DB
       await binance_client.close()
       await vyce_client.close()
       await db.close()
       # 3. Terminate dashboard server
       server.should_exit = True
       await dashboard_task
       logger.info("All services stopped safely.")
   ```

### 4.2 Recommended Changes to Web UI and API Routes
1. **`data/storage.py` `get_lessons`**:
   Update line 336:
   ```python
   async def get_lessons(self, limit: int = 50) -> List[Dict[str, Any]]:
       async with self._conn.cursor() as cursor:
           await cursor.execute("SELECT * FROM trading_lessons ORDER BY timestamp DESC, id DESC LIMIT ?", (limit,))
           rows = await cursor.fetchall()
           return [dict(row) for row in rows]
   ```
2. **`web/static/js/admin_app.js` Auto-Polling**:
   Add polling hook inside `DOMContentLoaded`:
   ```javascript
   if (document.getElementById('lessons-container')) {
       setInterval(loadLessons, 3000);
   }
   ```
3. **`web/app.py`**:
   Accept `audit_logs: Optional[List[Dict[str, Any]]] = None` parameter in `create_web_app`:
   ```python
   def create_web_app(
       db: Database,
       circuit_breaker: CircuitBreaker,
       event_bus: Optional[EventBus] = None,
       paper_trader: Optional[PaperTrader] = None,
       binance_client: Optional[BinanceClient] = None,
       audit_logs: Optional[List[Dict[str, Any]]] = None
   ) -> FastAPI:
       if audit_logs is None:
           audit_logs = []
       ...
   ```

### 4.3 Test Suite Design for `tests/test_auto_post_mortem.py`
The test suite must include four distinct test categories:

#### Category 1: Unit Tests for `generate_post_mortem`
- `test_generate_post_mortem_valid_json`:
  Mock HTTP response with valid Claude-3.5-Sonnet JSON payload. Verify parsed keys: `category`, `title`, `details`, `capital_impact`, `lesson_learned`, `operator == "Claude-3.5-Sonnet"`.
- `test_generate_post_mortem_markdown_fence_cleaning`:
  Mock HTTP response containing Markdown fence (```json ... ```). Verify successful parsing without error.
- `test_generate_post_mortem_missing_field_fallback`:
  Mock HTTP response with missing `title` or `details`. Verify it cleanly triggers deterministic fallback with `operator == "Deterministic-Fallback"` and `capital_impact == abs(pnl_usdt)`.
- `test_generate_post_mortem_network_timeout_fallback`:
  Mock `httpx.TimeoutException`. Verify non-crashing deterministic fallback.

#### Category 2: Integration Test for Stop-Loss Trigger & Persistence
- `test_auto_post_mortem_integration_stop_loss_trigger`:
  1. Initialize `PaperTrader` with `test_db` fixture and mocked `VyceClient`.
  2. Open BUY position at 60,000 USDT with SL at 59,000 USDT.
  3. Publish `MarketEvent` tick at 58,800 USDT.
  4. Assert `len(trader._background_tasks) > 0` (verifying `asyncio.create_task` was fired).
  5. `await asyncio.gather(*trader._background_tasks)`.
  6. Assert `mock_vyce.generate_post_mortem.assert_called_once()`.
  7. Query `await test_db.get_lessons()`. Assert record exists in SQLite with `category == "STOP_LOSS"`, non-empty `title`, `details`, and `capital_impact > 0`.
  8. Assert audit log received post-mortem entry.

#### Category 3: Non-Blocking Execution Latency Test
- `test_close_position_non_blocking_latency`:
  1. Configure `mock_vyce.generate_post_mortem` with an intentional `await asyncio.sleep(1.0)` delay (1,000ms network round-trip simulation).
  2. Create open position in `PaperTrader`.
  3. Measure elapsed time of `await trader._close_position(pos_key, exit_price=58500.0, reason="STOP_LOSS")` using `time.perf_counter()`.
  4. **Strict Assertion**: `elapsed_ms < 5.0` (assert position closing completes in < 5ms without awaiting the 1,000ms network task).
  5. Assert post-mortem task is active in `trader._background_tasks`.
  6. Await `asyncio.gather(*trader._background_tasks)` and verify the lesson is subsequently committed to SQLite.

#### Category 4: API Endpoint Test
- `test_api_lessons_ordering`:
  1. Seed SQLite with multiple lessons having distinct timestamps.
  2. Call `GET /api/v1/lessons` via `httpx.AsyncClient(app=web_app, base_url="http://test")`.
  3. Verify HTTP 200 and assert lessons list is strictly sorted by `timestamp DESC`.

---

## 5. Verification Method

### 5.1 Test Execution Command
Run the project's standard pytest command:
```powershell
.venv\Scripts\pytest -v
```
All existing 102 tests plus the new tests in `tests/test_auto_post_mortem.py` must achieve 100% pass rate.

### 5.2 Specific File Inspection Targets
1. `c:\sunMy\trading_bot\main.py`: Inspect lines 71, 73 (presence of `vyce_client=vyce_client, audit_logs=audit_logs`) and shutdown lines 164-165 (`await paper_trader.close()`, `await binance_executor.close()`).
2. `c:\sunMy\trading_bot\execution\paper_trader.py`: Inspect `close()` method implementation and `_trigger_auto_post_mortem` task tracking.
3. `c:\sunMy\trading_bot\execution\binance_executor.py`: Inspect `close()` method implementation and live task tracking.
4. `c:\sunMy\trading_bot\data\storage.py`: Inspect line 336 for `ORDER BY timestamp DESC, id DESC LIMIT ?`.
5. `c:\sunMy\trading_bot\web\static\js\admin_app.js`: Inspect `setInterval(loadLessons, 3000)`.
6. `c:\sunMy\trading_bot\tests\test_auto_post_mortem.py`: Run targeted test:
   ```powershell
   .venv\Scripts\pytest tests/test_auto_post_mortem.py -v
   ```

### 5.3 Invalidation Conditions
- Any test taking > 5ms in `test_close_position_non_blocking_latency`.
- Unhandled `RuntimeError: Cannot operate on closed database` during `main.py` shutdown.
- Regression in any of the 102 existing unit/adversarial tests.
- `/api/v1/lessons` returning unsorted or ascending records.
