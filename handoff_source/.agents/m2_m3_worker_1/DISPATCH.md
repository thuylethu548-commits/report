## 2026-09-17T07:02:10Z

You are M2/M3 Implementation and Refinement Worker (teamwork_preview_worker).
Your working directory is: c:\sunMy\trading_bot\.agents\m2_m3_worker_1

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY: Read the original user request first:
c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md
Also read the project architecture:
c:\sunMy\trading_bot\.agents\PROJECT.md
Read the three explorer handoff reports:
- c:\sunMy\trading_bot\.agents\m2_explorer_1\handoff.md
- c:\sunMy\trading_bot\.agents\m2_explorer_2\handoff.md
- c:\sunMy\trading_bot\.agents\m2_explorer_3\handoff.md

Your tasks:
1. `main.py`:
   - Pass `vyce_client=vyce_client, audit_logs=audit_logs` when initializing `PaperTrader` and `BinanceExecutor`.
   - Pass `audit_logs=audit_logs` to `create_web_app`.
   - In `finally:` shutdown block, call `await paper_trader.close()` and `await binance_executor.close()` before closing `binance_client`, `vyce_client`, and `db`.
2. `execution/paper_trader.py` and `execution/binance_executor.py`:
   - Implement `async def close(self, timeout: float = 5.0) -> None` to gracefully await any in-flight background post-mortem tasks before shutdown.
   - Ensure PaperTrader pnl_usdt subtracts `pos.get("fee", 0.0)` for exact parity with BinanceExecutor.
3. `ai_advisory/vyce_client.py`:
   - Add `timeout: Optional[float] = None` parameter to `chat_completion()` to allow per-call timeout override (e.g. 5.0s for post-mortem while preserving 3.0s default for signal veto).
   - In `generate_post_mortem`, use `timeout=5.0`.
4. `data/storage.py`:
   - Update `get_lessons` query to `SELECT * FROM trading_lessons ORDER BY timestamp DESC, id DESC LIMIT ?`.
5. `web/static/js/admin_app.js`:
   - Add auto-refresh polling for lessons: if `#lessons-container` exists, run `setInterval(loadLessons, 3000)`.
6. `tests/test_auto_post_mortem.py`:
   - Expand test coverage:
     a) Unit tests for `generate_post_mortem` (valid JSON, markdown code-fences, missing field fallback, timeout fallback).
     b) Non-blocking latency test: verify `_close_position` completes in strictly `< 5.0ms` using `time.perf_counter()` when post-mortem network call takes 1,000ms.
     c) API route test verifying `/api/v1/lessons` returns lessons ordered by `timestamp DESC`.
     d) Test for `close()` method waiting for background tasks.
7. Verification:
   - Run `.venv\Scripts\pytest -v` across the entire project test suite. Require 100% pass rate.
   - Run `scripts/check_vyce_connectivity.py` with `.venv\Scripts\python scripts/check_vyce_connectivity.py` to confirm live Vyce AI proxy connectivity.
   - Document all test outputs, commands, and file changes in `c:\sunMy\trading_bot\.agents\m2_m3_worker_1\handoff.md`.

Keep `progress.md` updated with liveness timestamps.
Send a message when finished.
