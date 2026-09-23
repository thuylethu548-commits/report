# M2 Handoff Report: VyceClient Post-Mortem Generation & SQLite Persistence

## 1. Observation

Direct code observations from the repository (`c:\sunMy\trading_bot`):

### 1.1 `ai_advisory/vyce_client.py`
- **Connection Pooling & Lifetime**:
  Lines 82-106: `_client` is a persistent `httpx.AsyncClient` initialized with:
  ```python
  limits = httpx.Limits(
      max_keepalive_connections=5,
      max_connections=10,
      keepalive_expiry=30.0
  )
  timeout = httpx.Timeout(self.timeout, connect=2.0)
  self._client = httpx.AsyncClient(limits=limits, timeout=timeout, headers=self._headers)
  ```
  Client supports async context manager (`__aenter__` / `__aexit__`) and explicit `close()` (lines 108-120).
- **Model Alias Mapping**:
  Lines 11-17, 87-90: `MODEL_ALIASES` dict maps aliases (`claude-3-5-sonnet`, `claude-3.5-sonnet`, `claude-3-5-sonnet-20241022`, `claude-3-sonnet`, `deepseek-chat`) to target proxy model `claude-sonnet-4-6`.
- **Timeout Configuration**:
  Lines 75, 156-161: `self.timeout` defaults to `float(settings.AI_TIMEOUT_SECONDS)` (which is 3.0s in `config/settings.py` line 35).
  In `chat_completion()`:
  ```python
  except httpx.TimeoutException:
      logger.warning(f"Vyce AI request timed out after {self.timeout}s. Engaging Non-AI fallback.")
      return None
  ```
  *Gap observed*: `chat_completion()` lacks a per-call timeout parameter. For advisory veto, 3.0s is optimal, but post-mortem background analysis requires a 5.0s timeout per requirement.
- **Existing `generate_post_mortem` Method**:
  Lines 41-52, 210-278: `generate_post_mortem(self, trade_info: Dict[str, Any]) -> Dict[str, Any]` is already partially implemented:
  - Formats `trade_info` (strategy, symbol, entry, exit, pnl_usdt, pnl_percent, hold_duration_seconds, reason).
  - Queries Vyce AI using `POST_MORTEM_SYSTEM_PROMPT`.
  - Cleans JSON with `_clean_and_parse_json`.
  - Validates `title`, `details`, `lesson_learned`.
  - Catches parse errors and returns a hardcoded fallback dict (lines 271-278):
    ```python
    return {
        "category": "STOP_LOSS",
        "title": f"Dừng lỗ tự động {trade_info.get('symbol', 'BTC/USDT')} bảo toàn vốn",
        "details": f"Vị thế {trade_info.get('symbol')} đóng tại {trade_info.get('exit_price', 0.0):.2f} do chạm ngưỡng Stop Loss {trade_info.get('pnl_percent', 0.0):.2f}%.",
        "capital_impact": abs(pnl),
        "lesson_learned": "Bảo toàn vốn là ưu tiên số 1; kích hoạt fallback an toàn ghi nhận kỷ luật cắt lỗ tự động.",
        "operator": "Deterministic-Fallback"
    }
    ```

### 1.2 `ai_advisory/post_mortem.py` Status
- `find_by_name` confirmed `ai_advisory/post_mortem.py` does **NOT** exist.
- Code duplication observed:
  - `execution/paper_trader.py` (lines 192-260) defines `_trigger_auto_post_mortem(pos, exit_price, pnl_usdt, pnl_pct, reason)`.
  - `execution/binance_executor.py` (lines 147-215) defines an almost identical `_trigger_auto_post_mortem(...)`.
  - Both format `trade_info`, call `self.vyce_client.generate_post_mortem`, call `self.db.add_lesson`, and write to `audit_logs`.
- Architecture specification in `.agents/PROJECT.md` line 60-82 specifies:
  ```python
  async def analyze_and_record_lesson(
      self,
      trade_info: Dict[str, Any],
      db: Database
  ) -> Dict[str, Any]
  ```

### 1.3 Fallback Heuristics & Test Suite Behavior
- Current test suite status: `.venv\Scripts\pytest -v` passes **102/102 tests** in 23.32s.
- `tests/test_auto_post_mortem.py` has 2 tests:
  - `test_auto_post_mortem_triggered_on_stop_loss` (lines 26-100): Mocks `mock_vyce.generate_post_mortem`, triggers SL in `handle_market_tick`, verifies call, DB entry in `trading_lessons`, and audit log.
  - `test_auto_post_mortem_fallback_on_ai_failure` (lines 102-140): Mocks `mock_vyce.generate_post_mortem = AsyncMock(side_effect=RuntimeError("Vyce API timeout 3.0s"))`.
    In line 131-139:
    ```python
    lesson_id = await trader._trigger_auto_post_mortem(...)
    assert lesson_id is None
    ```
  - In `tests/test_m1_adversarial.py` lines 261-305:
    `test_post_mortem_corrupted_payloads_fallback` verifies that when `chat_completion` returns malformed/corrupted payloads, `generate_post_mortem` returns the fallback dict with `operator == "Deterministic-Fallback"`.

### 1.4 `data/storage.py` (Persistence Layer)
- Table `trading_lessons` schema (lines 118-128):
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
- Methods:
  - `add_lesson(self, category: str, title: str, details: str, capital_impact: float, lesson_learned: str, operator: str = "Operator") -> int` (lines 324-333): inserts record, returns `lastrowid`.
  - `get_lessons(self, limit: int = 50) -> List[Dict[str, Any]]` (lines 334-339): queries `ORDER BY id DESC LIMIT ?`.
  - `delete_lesson(self, lesson_id: int) -> bool` (lines 340-345).
  - Seeded defaults (lines 264-290): seeds 3 lessons (`MARKET_CRASH`, `SLIPPAGE`, `STOP_LOSS`) if table count is 0.
- Web layer integration:
  - `web/routes/api_routes.py`: `GET /api/v1/lessons` and `POST /api/v1/lessons` already exist and call `db.get_lessons` and `db.add_lesson`.
  - `web/routes/admin_routes.py`: `GET /admin/lessons` serves `templates/admin/lessons.html`.
  - `web/static/js/admin_app.js`: `loadLessons()` renders lesson cards with styling badges.

---

## 2. Logic Chain

1. **VyceClient Timeout Customization**:
   - *Premise*: Signal evaluation requires `< 3.0s` timeout on critical order path; post-mortem generation requires up to `5.0s` (`> 5.0s` is the timeout boundary) in background execution.
   - *Evidence*: `VyceClient._client` is instantiated with `self.timeout` (3.0s). `chat_completion()` does not take a per-request `timeout` argument.
   - *Deduction*: Adding `timeout: Optional[float] = None` to `chat_completion` allows `generate_post_mortem` to pass `timeout=5.0` (or `POST_MORTEM_TIMEOUT_SECONDS = 5.0`), allowing longer reasoning while keeping veto latency strictly under 3.0s.

2. **Unified Post-Mortem Service (`ai_advisory/post_mortem.py`)**:
   - *Premise*: Having duplicate `_trigger_auto_post_mortem` logic in both `paper_trader.py` and `binance_executor.py` violates DRY and diverges prompt engineering.
   - *Evidence*: Both files contain ~65 lines of identical formatting, calling, fallbacks, and DB insertions.
   - *Deduction*: Creating `ai_advisory/post_mortem.py` with `PostMortemEngine` providing `analyze_and_record_lesson(trade_info, db, audit_logs)` consolidates post-mortem logic. Both `PaperTrader` and `BinanceExecutor` can delegate to it.

3. **Multi-Category Prompt Engineering**:
   - *Premise*: User request requires structured output with diverse categories (`TECHNICAL_FAILURE`, `SLIPPAGE`, `VOLATILITY_SPIKE`, `STOP_LOSS`, `MARKET_CRASH`), title, details, capital_impact, lesson_learned.
   - *Evidence*: Current `POST_MORTEM_SYSTEM_PROMPT` in `vyce_client.py` defaults to `category="STOP_LOSS"` and does not list the other categories in prompt rules.
   - *Deduction*: Updating the prompt system instructions to explicitly enumerate allowed categories (`STOP_LOSS`, `SLIPPAGE`, `VOLATILITY_SPIKE`, `TECHNICAL_FAILURE`, `MARKET_CRASH`) and Vietnamese formatting guidance produces higher quality forensic insights.

4. **Deterministic Heuristic Fallback Specialization**:
   - *Premise*: When Vyce AI times out (> 5.0s) or fails with network errors, the system must generate a category-specific fallback rather than a generic one-size-fits-all string.
   - *Evidence*: `vyce_client.py` lines 270-278 currently only generates a `STOP_LOSS` message regardless of whether the exit was triggered by `SLIPPAGE`, `VOLATILITY_SPIKE`, or `TECHNICAL_FAILURE`.
   - *Deduction*: A heuristic rules engine mapping exit reason / trade attributes (`reason == "SLIPPAGE"`, `pnl_percent <= -3%`, `hold_duration_seconds < 60s`, etc.) to specific diagnostic lessons guarantees high-utility records even when offline.

5. **SQLite Storage & Schema Stability**:
   - *Premise*: SQLite schema must support all post-mortem fields and frontend queries without breaking existing data or tests.
   - *Evidence*: Table `trading_lessons` already contains `id`, `timestamp`, `category`, `title`, `details`, `capital_impact`, `lesson_learned`, `operator`. All methods (`add_lesson`, `get_lessons`) match exact signatures.
   - *Deduction*: No schema migration or table changes are required. The persistence layer is 100% production-ready.

---

## 3. Caveats

1. **Test Compatibility with `test_auto_post_mortem_fallback_on_ai_failure`**:
   - In `tests/test_auto_post_mortem.py`, line 139 asserts `assert lesson_id is None` when `mock_vyce.generate_post_mortem` raises `RuntimeError`.
   - If `PaperTrader._trigger_auto_post_mortem` is modified to swallow external caller-injected exceptions and force-insert a DB record, that specific unit test will fail.
   - Therefore, the heuristic fallback should reside **inside** `generate_post_mortem` (or inside `PostMortemEngine.generate_fallback_lesson`) so real network/timeout issues return a valid lesson dict, while unexpected exceptions raised from an explicitly mocked `vyce_client` still return `None` when calling `_trigger_auto_post_mortem`.
2. **Capital Impact Type Normalization**:
   - LLMs occasionally return formatted text such as `"$12.50 USDT (-1.5%)"` or negative numbers `"-12.5"`.
   - SQLite column `capital_impact` expects a `REAL` (numeric float >= 0), and frontend JavaScript uses `.toLocaleString()`.
   - Sanitization must parse strings with regex `abs(float(re.search(r'[\d\.]+', str(val)).group()))` to prevent JSON parsing crashes.
3. **Frontend Polling Interval**:
   - `/admin/lessons` currently loads lessons on page load (`DOMContentLoaded`).
   - If an automated post-mortem triggers in the background while the user has `/admin/lessons` open, the new card will not appear until manual refresh unless a 5s polling interval is added in `web/static/js/admin_app.js`.

---

## 4. Conclusion & Recommended Implementation Strategy

### Summary of Recommendations for Milestone 2 Worker:
1. **`ai_advisory/vyce_client.py` Enhancements**:
   - Add `timeout: Optional[float] = None` to `chat_completion()`, allowing per-request override (e.g. `client.post(url, json=payload, timeout=timeout)`).
   - In `generate_post_mortem(trade_info: Dict[str, Any])`:
     - Pass `timeout=5.0`.
     - Update `POST_MORTEM_SYSTEM_PROMPT` to support categories: `STOP_LOSS`, `SLIPPAGE`, `VOLATILITY_SPIKE`, `TECHNICAL_FAILURE`, `MARKET_CRASH`.
     - Enhance field extraction to sanitize `capital_impact` (handling string with symbols or numbers).
     - Refine deterministic fallback heuristics based on `trade_info.get("reason")` and `trade_info.get("pnl_percent")`.
2. **Create `ai_advisory/post_mortem.py`**:
   - Implement `PostMortemEngine` with `analyze_and_record_lesson(trade_info: Dict[str, Any], db: Database, audit_logs: Optional[list] = None) -> Optional[int]`.
   - Expose helper function `generate_heuristic_fallback(trade_info: Dict[str, Any]) -> Dict[str, Any]`.
3. **Refactor Execution Hooks**:
   - In `execution/paper_trader.py` and `execution/binance_executor.py`:
     - Retain `_trigger_auto_post_mortem` method signature for 100% backward compatibility with existing tests.
     - Delegate the underlying post-mortem generation and DB persistence to `PostMortemEngine`.
4. **`data/storage.py`**:
   - No schema changes required. Table `trading_lessons` and `add_lesson` / `get_lessons` are fully functional.
   - Optional: Add index `idx_trading_lessons_id` or `idx_trading_lessons_timestamp` if deemed necessary.
5. **Frontend UI Refresh**:
   - In `web/static/js/admin_app.js`, add `if (document.getElementById('lessons-container')) setInterval(loadLessons, 5000);` to ensure automatic live updates without manual page refresh.
6. **Testing**:
   - Expand `tests/test_auto_post_mortem.py` to cover all 5 post-mortem categories, timeout > 5.0s, network drop, and malformed JSON payloads.

---

## 5. Verification Method

### Step 1: Run Existing Test Suite
Run the test suite to ensure 100% baseline pass:
```powershell
.venv\Scripts\pytest -v
```
Expected result: **102 passed**.

### Step 2: Test Specific Post-Mortem Tests
```powershell
.venv\Scripts\pytest -v tests/test_auto_post_mortem.py tests/test_settings_and_lessons.py tests/test_m1_adversarial.py -k "post_mortem or lesson"
```
Expected result: All post-mortem and lesson tests pass cleanly.

### Step 3: Test Vyce AI Live Connectivity Script
```powershell
.venv\Scripts\python scripts/check_vyce_connectivity.py
```
Expected result: Live proxy endpoint connection test execution.

### Invalidation Conditions
This investigation strategy would be invalidated if:
- `trading_lessons` SQLite table schema is altered destructively, breaking existing seeded lessons or test fixtures.
- `PaperTrader._trigger_auto_post_mortem` signature is modified, breaking `tests/test_auto_post_mortem.py:test_auto_post_mortem_fallback_on_ai_failure`.
- Timeout in `vyce_client.py` causes signal veto calls in `RiskManager` to exceed 3.0s (veto calls must stay `< 3.0s`).
