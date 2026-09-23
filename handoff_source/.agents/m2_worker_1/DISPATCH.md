# Dispatch for Milestone 2 Worker

## Identity & Mission
- Role: Milestone 2 Implementation Worker (Auto Post-Mortem & SQLite Lessons Engine)
- Working Directory: c:\sunMy\trading_bot\.agents\m2_worker_1
- Original Request Path: c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md
- Scope Document: c:\sunMy\trading_bot\.agents\PROJECT.md

## File Ownership
You exclusively own and may edit:
- `execution/paper_trader.py`
- `execution/binance_executor.py`
- `main.py` (wiring if needed)
- `tests/test_auto_post_mortem.py`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Context & Objectives
Requirement R2:
- Listen to position close events when a position hits Stop-Loss (`last_price <= pos["stop_loss"]` or exit reason `"STOP_LOSS"`) or experiences severe slippage.
- Call Claude-3.5-Sonnet via `VyceClient.generate_post_mortem(trade_info)` in a non-blocking background task (`asyncio.create_task`) so that order execution is instantaneous (0ms delay).
- Automatically record the post-mortem analysis into the SQLite table `trading_lessons` (`timestamp`, `category`, `title`, `details`, `capital_impact`, `lesson_learned`, `operator="Claude-3.5-Sonnet"`).
- Ensure the lessons are immediately queryable via `db.get_lessons()` for `/admin/lessons`.

## Detailed Tasks
1. In `execution/paper_trader.py`:
   - Accept optional `vyce_client: Optional[VyceClient] = None` in `__init__` (create one or use passed instance).
   - In `_close_position(self, pos_key: str, exit_price: float, reason: str)`:
     - After recording trade close in DB and publishing `FillEvent`, check:
       `if reason == "STOP_LOSS" or pnl_pct <= -settings.STOP_LOSS_PERCENT * 100:`
     - Launch background task:
       `asyncio.create_task(self._trigger_auto_post_mortem(pos_copy, exit_price, pnl_usdt, pnl_pct, reason))`
   - Implement `async def _trigger_auto_post_mortem(self, pos, exit_price, pnl_usdt, pnl_pct, reason)`:
     - Prepare `trade_info` dictionary.
     - Call `await self.vyce_client.generate_post_mortem(trade_info)`.
     - Insert into SQLite via `await self.db.add_lesson(...)`.
     - Log lesson creation to `logger.info` and in-memory `audit_logs` if available.
     - Ensure all exceptions are safely caught and logged so background tasks never crash the event loop.
2. In `execution/binance_executor.py`:
   - Implement similar non-blocking post-mortem trigger if positions close with Stop-Loss.
3. In `main.py`:
   - Pass `vyce_client=vyce_client` to `PaperTrader(..., vyce_client=vyce_client)`.
4. Create comprehensive automated unit tests in `tests/test_auto_post_mortem.py`:
   - Test Stop-Loss trigger creates a background task that calls `generate_post_mortem` and writes a lesson into SQLite `trading_lessons`.
   - Test Take-Profit does NOT trigger Stop-Loss post-mortem.
   - Test that post-mortem runs asynchronously and does not block position close or order fill.
   - Test database retrieval of the recorded lesson via `db.get_lessons()`.
5. Run pytest `.venv\Scripts\pytest -v` and verify all tests pass (100% pass rate).

## Output
Write report to `c:\sunMy\trading_bot\.agents\m2_worker_1\handoff.md`.
Send message when done.

## 2026-09-17T05:51:00Z
Received invocation:
Implement Milestone 2:
- Hook Stop-Loss detection in execution/paper_trader.py (and execution/binance_executor.py) when reason == "STOP_LOSS" or severe slippage/drawdown
- Launch non-blocking background task (asyncio.create_task) calling vyce_client.generate_post_mortem
- Automatically record lessons into SQLite trading_lessons table via db.add_lesson
- Ensure lessons immediately render on /admin/lessons and /api/v1/lessons
- Wire in main.py
- Add comprehensive unit tests in tests/test_auto_post_mortem.py
- Run pytest (.venv\Scripts\pytest -v) and ensure 100% pass rate.
Write your handoff report to c:\sunMy\trading_bot\.agents\m2_worker_1\handoff.md and notify parent.

