# Plan — teamwork_preview_orchestrator_2

## Strategy Overview
Complete the remaining milestones for Astra Quant Desk AI upgrade:
1. **Milestone 2: Auto Post-Mortem & SQLite Lessons Engine**
   - Hook Stop-Loss exit in `execution/paper_trader.py` (and `execution/binance_executor.py`).
   - Call `vyce_client.generate_post_mortem(trade_info)` as a non-blocking background task.
   - Insert into SQLite `trading_lessons` table via `db.add_lesson(...)`.
   - Verify non-blocking latency, write comprehensive unit/integration tests in `tests/test_auto_post_mortem.py`.
   - Gate review: 2 Reviewers, 2 Challengers, 1 Forensic Auditor.
2. **Milestone 3: Dynamic Dashboard Controls & Hot-Reload**
   - Update `GET /api/v1/status` in `web/routes/api_routes.py` to expose `latest_ai_advisory`.
   - Update `web/static/js/admin_app.js` to dynamically bind regime and confidence score on `/admin`.
   - Verify `/admin/settings` hot-reloading `ENABLE_AI_ADVISORY`, `VYCE_MODEL`, and `AI_TIMEOUT_SECONDS` without server restart.
   - Gate review.
3. **E2E Testing Track**
   - Create `scripts/check_vyce_connectivity.py` for direct live Vyce AI proxy verification.
   - Validate 4-tier requirement-driven test suite (Tiers 1-4) and publish `TEST_READY.md`.
4. **Final Milestone & Port 8386 System Verification**
   - Pass 100% of all test suites (existing 10 + 100 M1 + M2 + M3 + E2E).
   - Live server verification on port 8386:
     - AI Advisory logs with approve/reject rationale.
     - Simulated Stop-Loss creates `trading_lessons` record and renders on `/admin/lessons`.
     - FastAPI & WebSockets maintain low latency without freezing.
   - Report completion to Sentinel for Victory Audit.
