# Soft Handoff — Project Orchestrator Generation 1 to Generation 2

## 1. Milestone State
- **Phase 0: Codebase Survey & Decomposition**: **DONE**. Comprehensive survey performed across 3 parallel Explorers. Architecture, Feature Inventory, Milestones, and Interface Contracts documented in `c:\sunMy\trading_bot\.agents\PROJECT.md`.
- **Milestone 1: Live Vyce AI Integration & Advisory Veto Engine**: **DONE**.
  - `config/settings.py`: Resolved `ANTHROPIC_API_KEY` fallback, `/v1` URL normalization, and model alias remapping (`deepseek-chat`, `claude-3-5-sonnet` -> `claude-sonnet-4-6`).
  - `ai_advisory/vyce_client.py`: Persistent `httpx.AsyncClient` with keep-alive connection pooling, `evaluate_signal_veto`, strict timeout handling, and defense-in-depth quantitative fallback (`[0.5%, 5.0%]` SL corridor, `>= 0.70` confidence).
  - `risk_engine/risk_manager.py`: Active AI Advisory Veto Gatekeeper in `handle_signal`, dual-layer `< 3.0s` timeout (`asyncio.wait_for`), defense-in-depth fallback re-validation, dynamic position sizing (`size_multiplier`), `FillEvent` position synchronization, and safe SQLite error wrapping.
  - `main.py`: Shared singleton `VyceClient` wired to `RiskManager` and `MarketRegimeClassifier`, with graceful connection drain in `finally:` block.
  - Automated Tests: **100 tests passing 100% in 24.02s** across unit, integration, and adversarial suites.
- **Milestone 2: Auto Post-Mortem & SQLite Lessons Engine**: **NOT STARTED (PLANNED)**. Scope: hook Stop-Loss position close in `execution/paper_trader.py` (and `execution/binance_executor.py`) to launch a background task calling `vyce_client.generate_post_mortem`, persisting lessons into SQLite `trading_lessons` via `db.add_lesson`, and rendering on `/admin/lessons`.
- **Milestone 3: Dynamic Dashboard Controls & Hot-Reload**: **NOT STARTED (PLANNED)**. Scope: Expose `latest_ai_advisory` in `GET /api/v1/status`, dynamically bind `#kpi-regime` and confidence score in `web/static/js/admin_app.js`, and verify `/admin/settings` runtime hot-reload.
- **E2E Testing Track**: **PLANNED**. Standalone live Vyce AI connectivity script (`scripts/check_vyce_connectivity.py`) and 4-tier requirement-driven test suite.
- **Final Milestone**: **PLANNED**. 100% pass across all test tiers, Tier 5 adversarial hardening, and end-to-end live verification running on port 8386.

## 2. Active Subagents
All 16 subagents from Generation 1 have delivered their completion reports and are retired per the iron rule (no reuse after handoff):
- 3 Survey Explorers (`31532a48`, `ef0cc3ca`, `42a49dc2`) — completed
- 3 M1 Explorers (`a7a314b8`, `801f3d93`, `595d56ae`) — completed
- 1 M1 Worker 1 (`3e2f6937`) — completed
- 2 M1 Reviewers (`5cb417d1`, `2846b985`) — completed
- 2 M1 Challengers (`e6f052ab`, `ed7ddf30`) — completed
- 1 M1 Forensic Auditor (`1dba46c9`) — completed (CLEAN)
- 3 M1 R2 Explorers (`903e607f`, `82f537c8`, `a6981457`) — completed
- 1 M1 Worker 2 (`fbe99f24`) — completed (100/100 tests passed)

No subagents are currently running.

## 3. Pending Decisions
None. All architectural contracts and fallback unification questions have been resolved and verified with passing test suites.

## 4. Remaining Work (Next Steps for Successor)
1. **Initialize State**: Start your own heartbeat cron (`schedule(CronExpression="*/10 * * * *")`), initialize your `BRIEFING.md`, and inherit parent `f2380e8c-f47b-480e-b025-bb86b8c0bc88` (the sentinel).
2. **Execute Milestone 2 (Auto Post-Mortem & SQLite Lessons Engine)**:
   - In `execution/paper_trader.py` (line 162 in `_close_position`) and `execution/binance_executor.py`: when `reason == "STOP_LOSS"` or `pnl_percent <= -settings.STOP_LOSS_PERCENT * 100`, launch non-blocking background task:
     `asyncio.create_task(self._trigger_auto_post_mortem(pos, fill_price, pnl_usdt))`
   - In `_trigger_auto_post_mortem`: call `self.vyce_client.generate_post_mortem(trade_info)`, and insert into SQLite `trading_lessons` using `await self.db.add_lesson(category=lesson["category"], title=lesson["title"], details=lesson["details"], capital_impact=lesson["capital_impact"], lesson_learned=lesson["lesson_learned"], operator="Claude-3.5-Sonnet")`.
   - Ensure non-blocking execution (zero latency penalty on position exit).
   - Write unit tests in `tests/test_auto_post_mortem.py`.
3. **Execute Milestone 3 (Dashboard Controls & Hot-Reload)**:
   - Wire `latest_ai_advisory` into `GET /api/v1/status` in `web/routes/api_routes.py`.
   - Update `web/static/js/admin_app.js` to dynamically bind `data.latest_ai_advisory` to `#kpi-regime` and confidence score percentage in `cockpit.html`.
   - Ensure runtime toggle on `/admin/settings` hot-reloads `ENABLE_AI_ADVISORY` without server restart.
4. **Execute E2E Testing Track**:
   - Create `scripts/check_vyce_connectivity.py` to test live connectivity to Vyce AI proxy with Claude Sonnet (`claude-sonnet-4-6`).
   - Create comprehensive E2E test suite covering Tiers 1-4 and publish `TEST_READY.md`.
5. **Final Milestone & Port 8386 Verification**:
   - Run 100% of test suite.
   - Launch server on port 8386, simulate technical signal (observe advisory log approve/veto), simulate Stop-Loss hit (verify record appears in SQLite `trading_lessons` and renders at `http://127.0.0.1:8386/admin/lessons`).
   - Deliver completion report to Sentinel (`f2380e8c-f47b-480e-b025-bb86b8c0bc88`) for Victory Audit.

## 5. Key Artifacts
- `c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md` — Original verbatim user requirements
- `c:\sunMy\trading_bot\.agents\PROJECT.md` — Global architecture, feature inventory, milestone tracking
- `c:\sunMy\trading_bot\.agents\TEST_INFRA.md` — Test methodology and coverage matrix
- `c:\sunMy\trading_bot\.agents\teamwork_preview_orchestrator_1\GATE_STATUS.md` — Milestone gate logs
- `c:\sunMy\trading_bot\.agents\teamwork_preview_orchestrator_1\BRIEFING.md` — Gen 1 briefing
- `c:\sunMy\trading_bot\.agents\teamwork_preview_orchestrator_1\progress.md` — Gen 1 progress tracker
