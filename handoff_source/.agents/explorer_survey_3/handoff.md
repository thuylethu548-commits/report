# Handoff Report: Explorer Survey 3 (Database, Web Admin, Hot-Reload, and Test Suite)

**Date**: 2026-09-17  
**Investigator**: Explorer Survey 3  
**Working Directory**: `c:\sunMy\trading_bot\.agents\explorer_survey_3`  
**Mission**: Investigate SQLite setup & schema, Web Admin routes & UI, Hot-reload runtime mechanism, AI metrics display, and existing test suite.

---

## 1. Observation

### 1.1 SQLite Database Setup & Schema (`trading_bot.db`)
- **Connection Setup**: `data/storage.py:10-24` defines the `Database` class using `aiosqlite`.
  - Line 10: `def __init__(self, db_path: str = "trading_bot.db"):`
  - Line 15-17:
    ```python
    self._conn = await aiosqlite.connect(self.db_path)
    self._conn.row_factory = aiosqlite.Row
    await self._init_schema()
    ```
  - Configured in `config/settings.py:44`: `DATABASE_PATH: str = "trading_bot.db"`.
  - Instantiated in `main.py:53-54`:
    ```python
    db = Database(settings.DATABASE_PATH)
    await db.connect()
    ```
- **Existing Tables** (`data/storage.py:28-129`):
  1. `candles` (lines 29-40): `id` (PK AUTOINCREMENT), `symbol`, `timestamp`, `open`, `high`, `low`, `close`, `volume`, `UNIQUE(symbol, timestamp)`.
  2. `trades` (lines 44-60): `order_id` (PK TEXT), `strategy_name`, `symbol`, `side`, `entry_price`, `exit_price`, `quantity`, `fee`, `entry_time`, `exit_time`, `pnl_usdt`, `pnl_percent`, `is_paper`, `status`.
  3. `signals` (lines 64-77): `id` (PK AUTOINCREMENT), `strategy_name`, `symbol`, `side`, `price`, `stop_loss`, `take_profit`, `confidence`, `timestamp`, `approved`, `rejection_reason`.
  4. `ai_advisory_logs` (lines 81-91): `id` (PK AUTOINCREMENT), `symbol`, `regime`, `risk_score`, `trade_allowed`, `size_multiplier`, `reasoning`, `timestamp`.
  5. `equity_snapshots` (lines 95-103): `id` (PK AUTOINCREMENT), `timestamp`, `balance_usdt`, `equity_usdt`, `open_positions`, `daily_drawdown`.
  6. `system_settings` (lines 107-114): `key` (PK TEXT), `value`, `data_type`, `description`, `updated_at`.
  7. `trading_lessons` (lines 118-128):
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
     )
     ```
- **Methods for `trading_lessons`** (`data/storage.py:324-345`):
  - `add_lesson(category, title, details, capital_impact, lesson_learned, operator="Operator") -> int`
  - `get_lessons(limit=50) -> List[Dict[str, Any]]`
  - `delete_lesson(lesson_id: int) -> bool`
  - `_seed_defaults_and_lessons()` (lines 265-290) seeds 3 classic lessons (`MARKET_CRASH`, `SLIPPAGE`, `STOP_LOSS`).
- **Gap Identified for R2**:
  - The table `trading_lessons` exists and can store records, but there is currently **no automated event listener** connecting `PaperTrader` / `BinanceExecutor` Stop-Loss triggers to `VyceClient` (Claude-3.5-Sonnet) to generate and insert lessons into `trading_lessons`.

---

### 1.2 Web Admin Cockpit & FastAPI Routes
- **App Factory**: `web/app.py:21-58` (`create_web_app`):
  - Line 28: `app = FastAPI(title="ASTRA QUANT DESK & CLIENT PORTAL", version="3.0.0")`
  - Line 36: `app.mount("/static", StaticFiles(directory=static_dir), name="static")`
  - Line 39: `templates = Jinja2Templates(directory=templates_dir)`
  - Mounted Routers:
    - `client_router`: `web/routes/client_routes.py` (portal pages `/`, `/privacy`, `/terms`, `/risk-warning`, `/track-record`)
    - `admin_router`: `web/routes/admin_routes.py` (admin UI)
    - `api_router`: `web/routes/api_routes.py` (API mounted at `/api/v1` and `/api`)
- **Admin Page Endpoints** (`web/routes/admin_routes.py:10-75`):
  - `GET /admin` & `GET /admin/`: Renders `templates/admin/cockpit.html` with title and breadcrumb.
  - `GET /admin/settings`: Renders `templates/admin/settings.html`, populating form defaults from `db.get_all_settings()`.
  - `GET /admin/lessons`: Renders `templates/admin/lessons.html`.
  - `GET /admin/audit-logs`: Renders `templates/admin/audit_logs.html`.
- **API Endpoints** (`web/routes/api_routes.py:52-286`):
  - `GET /api/v1/status`: Returns system metrics: `balance_usdt`, `equity_usdt`, `circuit_breaker_tripped`, `trip_reason`, `last_price`, `performance`, `recent_trades`, `open_positions`, `ai_advisory_enabled`.
  - `GET /api/v1/candles`: Returns recent 60 candles with calculated `ema20` and `ema50`.
  - `GET /api/v1/fleet`: Returns telemetry for 10 agents (currently hardcoded static dict list).
  - `GET /api/v1/signals`: Returns recent 30 signals from SQLite.
  - `GET /api/v1/logs`: Returns in-memory `audit_logs[-40:]`.
  - `POST /api/v1/kill`: Triggers `circuit_breaker.trigger_emergency_kill(...)`.
  - `POST /api/v1/reset_circuit`: Calls `circuit_breaker.reset_circuit()`.
  - `POST /api/v1/test_trade`: Generates a `SignalEvent` for paper execution.
  - `GET /api/v1/settings`: Fetches all settings from `system_settings` table.
  - `POST /api/v1/settings`: Mutates runtime settings and writes to SQLite.
  - `GET /api/v1/lessons`: Fetches lessons from `trading_lessons` table.
  - `POST /api/v1/lessons`: Accepts `LessonInput` schema and inserts via `db.add_lesson(...)`.
- **Frontend & Polling Architecture**:
  - `web/templates/layouts/admin_base.html:72` displays `<span class="pulse-dot"></span> LIVE WEBSOCKET`.
  - However, in `web/static/js/admin_app.js:314-316`, communication is **HTTP REST Polling**:
    ```javascript
    setInterval(updateAdminCockpit, 2500);  // Every 2.5s -> GET /api/v1/status
    setInterval(updateAuditTerminal, 3000); // Every 3s -> GET /api/v1/logs
    setInterval(fetchAstraCandles, 5000);   // Every 5s -> GET /api/v1/candles
    ```
  - Backend WebSocket: `data/websocket_feed.py:47-88` connects to Binance public kline feed (`wss://stream.binance.com:9443/ws/<symbol>@kline_<timeframe>`). There is **no WebSocket server endpoint** in FastAPI to push ticks to the browser; the browser relies entirely on REST polling.

---

### 1.3 Hot-Reload Mechanism for Runtime Settings
- **Persistence Layer**:
  - `POST /api/v1/settings` in `web/routes/api_routes.py:208-264` accepts payload dict.
  - Inserts/Updates SQLite `system_settings` using `ON CONFLICT(key) DO UPDATE SET value = excluded.value...` via `db.set_setting()`.
- **Runtime Reload Mechanism**:
  - In `web/routes/api_routes.py:222-257`:
    ```python
    if key == "DAILY_MAX_DRAWDOWN_PERCENT":
        fval = float(val)
        if fval > 0.05: raise HTTPException(400, "...")
        settings.DAILY_MAX_DRAWDOWN_PERCENT = fval
        circuit_breaker.max_daily_drawdown = fval
    elif key == "TRADING_MODE":
        settings.TRADING_MODE = str(val).lower()
    elif key == "SYMBOL":
        settings.SYMBOL = str(val).upper()
    elif key == "TIMEFRAME":
        settings.TIMEFRAME = str(val)
    elif key == "ENABLE_AI_ADVISORY":
        settings.ENABLE_AI_ADVISORY = str(val).lower() in ("true", "1", "yes")
    ```
  - Python imports `settings` as a shared singleton module instance (`from config.settings import settings`).
  - Mutating attributes on `settings` immediately affects any module that reads `settings.<FIELD>` dynamically (e.g., `RiskManager.handle_signal` checks `settings.ENABLE_AI_ADVISORY`, `MarketRegimeClassifier.evaluate_market` checks `settings.ENABLE_AI_ADVISORY`).
- **Hard-Bounds Validation Enforced**:
  - `DAILY_MAX_DRAWDOWN_PERCENT` capped at `0.05` (5.0%).
  - `MAX_ORDER_SIZE_USDT` capped at `500.0`.
  - `TRADING_MODE` restricted to `paper` or `live`.
- **Startup Sync**:
  - In `main.py:89-100`, on bot boot, `db.get_all_settings()` is queried and applied to `settings` and `circuit_breaker`.

---

### 1.4 AI Advisory & Confidence Score Display in Cockpit
- **Admin UI Metric**:
  - In `web/templates/admin/cockpit.html:50-54`:
    ```html
    <div class="kpi-card">
        <div class="kpi-label">Chế Độ Thị Trường</div>
        <div class="kpi-val" style="color: var(--primary);" id="kpi-regime">BULLISH_TREND</div>
        <div class="kpi-sub">Cố vấn AI: Đang bật</div>
    </div>
    ```
- **Disconnection Observed**:
  - In `web/static/js/admin_app.js:9-79`, `updateAdminCockpit()` updates `pf`, `pnl`, `wr`, `tc`, `riskEl`, and `positions-tbody`, but **never updates `kpi-regime`**.
  - In `web/routes/api_routes.py:83-95`, `/api/v1/status` returns `"ai_advisory_enabled": settings.ENABLE_AI_ADVISORY`, but does **not include `latest_ai_advisory`** or confidence score.
  - In `main.py:102`, `create_web_app(db, circuit_breaker, event_bus, paper_trader, binance_client)` does **not pass `ai_classifier`** to the web app.
  - In `config/settings.py:32`, `VYCE_MODEL: str = "deepseek-chat"`. It needs to be configured for `claude-3-5-sonnet` as requested by R1.

---

### 1.5 Existing Test Suite & Execution
- **Test Runner**: Pytest 9.1.1 with `pytest-asyncio` (asyncio_mode = auto, loop_scope = function) via `pytest.ini:1-5`.
- **Environment**: Python 3.12.14 inside `c:\sunMy\trading_bot\.venv`.
- **Execution Command**:
  ```powershell
  .venv\Scripts\pytest
  # or with verbose flag:
  .venv\Scripts\pytest -v
  ```
- **Execution Output**:
  ```
  collected 10 items

  tests\test_ai_advisory.py ..                                             [ 20%]
  tests\test_paper_trader.py .                                             [ 30%]
  tests\test_risk_engine.py ....                                           [ 70%]
  tests\test_settings_and_lessons.py .                                     [ 80%]
  tests\test_strategies.py ..                                              [100%]

  ============================= 10 passed in 4.28s ==============================
  ```
  - **Pass Rate**: 10 passed, 0 failed (100% pass rate).
- **Test Modules & Fixtures**:
  - `tests/test_settings_and_lessons.py`: Tests seed defaults, setting mutations, seeded lessons, and custom lesson creation with `tmp_path`.
  - `tests/test_ai_advisory.py`: Uses `MockVyceClientSuccess` and `MockVyceClientTimeout` to test JSON extraction and quantitative fallback.
  - `tests/test_risk_engine.py`: Uses `@pytest_asyncio.fixture def setup_env` with clean teardown; tests drawdown calculation, emergency kill rejection, invalid SL rejection, and valid signal approval.
  - `tests/test_paper_trader.py`: Uses `@pytest_asyncio.fixture def setup_paper`; tests buy order matching, balance reduction, and take-profit market tick exit.
  - `tests/test_strategies.py`: Tests `EMATrendStrategy` golden cross and `RSIBollingerStrategy` oversold signals.

---

## 2. Logic Chain

```
[Observation 1.1: Database._init_schema() creates trading_lessons & seeds 3 lessons]
      │
      ├─► Logic Step 1: SQLite schema for trading lessons is fully prepared in data/storage.py:118-128.
      │
[Observation 1.1: PaperTrader & BinanceExecutor trigger Stop-Loss, but do not invoke Claude post-mortem]
      │
      ├─► Logic Step 2: Auto Post-Mortem (R2) requires an event hook on position close when reason == "STOP_LOSS"
      │                 or slippage is high, invoking VyceClient and saving results via db.add_lesson().
      │
[Observation 1.2: FastAPI has /admin/lessons and /api/v1/lessons endpoints]
      │
      ├─► Logic Step 3: Frontend /admin/lessons is already wired to fetch /api/v1/lessons (admin_app.js:205-244).
      │                 Once an auto post-mortem lesson is saved to DB, it immediately appears on the page.
      │
[Observation 1.3: POST /api/v1/settings updates SQLite & mutates settings.ENABLE_AI_ADVISORY in memory]
      │
      ├─► Logic Step 4: Hot-reload for AI Advisory toggle works instantly without restarting server because
      │                 RiskManager and MarketRegimeClassifier check settings.ENABLE_AI_ADVISORY per tick/signal.
      │
[Observation 1.4: /api/v1/status omits latest AI advisory and #kpi-regime is static in cockpit.html]
      │
      ├─► Logic Step 5: To satisfy R3, create_web_app must receive the AI advisory state (or query it from DB),
      │                 expose regime & confidence score in /api/v1/status, and updateAdminCockpit() must render it.
      │
[Observation 1.5: 10 existing tests run via .venv\Scripts\pytest with 100% pass rate]
      │
      └─► Logic Step 6: All new tests for Claude-3.5-Sonnet advisory and auto post-mortem can build upon
                        existing mock patterns (MockVyceClient, tmp_path SQLite databases) and integrate cleanly.
```

---

## 3. Caveats

1. **Symbol & Timeframe Hot-Reload Limitation**:
   - Modifying `SYMBOL` or `TIMEFRAME` via `/admin/settings` updates `settings.py` and SQLite, but does not dynamically disconnect/reconnect `BinanceWebSocketFeed` or re-initialize indicator history for strategies without a restart. However, `ENABLE_AI_ADVISORY`, `DAILY_MAX_DRAWDOWN_PERCENT`, and `MAX_ORDER_SIZE_USDT` hot-reload instantly.
2. **WebSocket Badge vs Actual Polling**:
   - The UI topbar shows `LIVE WEBSOCKET`, but this indicates that the bot backend is connected to Binance's WebSocket stream. The web dashboard communicates with FastAPI via REST polling (every 2.5s). No browser WebSocket is required unless sub-second UI updates are requested.
3. **VPS Live API Key vs Local Mock**:
   - Local `.env` contains `VYCE_API_KEY=mock_vyce_key` and `VYCE_MODEL=deepseek-chat`. On the live VPS, `VYCE_MODEL` must be set to `claude-3-5-sonnet` and live `VYCE_API_KEY` provided. Unit tests must continue to use mock clients (`MockVyceClient`) to ensure tests never fail due to missing internet access or proxy rate limits.
4. **Agent Telemetry Fleet Endpoint**:
   - `GET /api/v1/fleet` currently returns a static mocked array of 10 agents. If real-time agent metrics are required, dynamic counters should be plugged in.

---

## 4. Conclusion

1. **Database Readiness (R2)**:
   - `trading_bot.db` has the `trading_lessons` schema and `add_lesson()` / `get_lessons()` methods ready in `data/storage.py`.
   - Implementation needed for R2: An `AutoPostMortemEngine` listening to `PositionClosedEvent` (or `FillEvent` with `reason="STOP_LOSS"`), querying `VyceClient` (Claude-3.5-Sonnet) with a specialized post-mortem prompt, and writing the structured output directly to `trading_lessons`.
2. **Web Admin & Hot-Reload (R3)**:
   - `/admin`, `/admin/settings`, and `/admin/lessons` are functional and styled with responsive Jinja2 templates.
   - Hot-reload for `ENABLE_AI_ADVISORY` is functional via `POST /api/v1/settings` which mutates runtime memory and SQLite simultaneously.
   - To complete R3: Wire `latest_ai_advisory` into `GET /api/v1/status` and add DOM updating for `#kpi-regime` and confidence percentage in `web/static/js/admin_app.js`.
3. **Test Suite Baseline**:
   - Pytest test runner in `.venv\Scripts\pytest` is healthy: 10/10 tests passing in 4.28 seconds.
   - Test expansion pattern is established with `tmp_path` database fixtures and mock HTTP responses.

---

## 5. Verification Method

### 5.1 Run Test Suite
Execute the following PowerShell command in the project root:
```powershell
.venv\Scripts\pytest -v
```
**Expected Result**: 10 passed in ~4s.

### 5.2 Verify SQLite Schema & Tables
Execute PowerShell command to inspect tables in `trading_bot.db`:
```powershell
.venv\Scripts\python -c "import sqlite3; con = sqlite3.connect('trading_bot.db'); print([r[0] for r in con.execute('SELECT name FROM sqlite_master WHERE type=\'table\'').fetchall()])"
```
**Expected Result**:
`['candles', 'sqlite_sequence', 'trades', 'signals', 'ai_advisory_logs', 'equity_snapshots', 'system_settings', 'trading_lessons']`

### 5.3 Verify FastAPI Admin Routes
Execute PowerShell command:
```powershell
.venv\Scripts\python -c "import asyncio, httpx, data.storage, risk_engine.circuit_breaker, web.app`
`
async def main():`
`    db = data.storage.Database('trading_bot.db')`
`    await db.connect()`
`    cbr = risk_engine.circuit_breaker.CircuitBreaker()`
`    app = web.app.create_web_app(db, cbr)`
`    transport = httpx.ASGITransport(app=app)`
`    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:`
`        for p in ['/admin', '/admin/settings', '/admin/lessons', '/api/v1/status', '/api/v1/lessons']:`
`            res = await client.get(p)`
`            print(p, res.status_code)`
`    await db.close()`
`
asyncio.run(main())"
```
**Expected Result**:
All routes return 200 OK:
```
/admin 200
/admin/settings 200
/admin/lessons 200
/api/v1/status 200
/api/v1/lessons 200
```
