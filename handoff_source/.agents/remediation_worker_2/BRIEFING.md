# BRIEFING — 2026-09-17T14:25:05+07:00

## Mission
Implement exact fixes requested by Challenger 2: confidence score pipeline propagation and startup dynamic settings restoration.

## 🔒 My Identity
- Archetype: teamwork_preview_worker
- Roles: implementer, qa, specialist
- Working directory: c:\sunMy\trading_bot\.agents\remediation_worker_2
- Original parent: d6049e3d-064c-42dc-b752-8c0497cec35c
- Milestone: M2/M3 Remediation

## 🔒 Key Constraints
- DO NOT CHEAT. All implementations must be genuine.
- Minimal change principle: only modify what is necessary.
- 100% pytest pass rate.
- Verified live Vyce AI connectivity.

## Current Parent
- Conversation ID: d6049e3d-064c-42dc-b752-8c0497cec35c
- Updated: 2026-09-17T14:25:05+07:00

## Task Summary
- **What to build**:
  1. `core/events.py`: add `confidence: float = 1.0` to `AIAdvisoryEvent`.
  2. `data/storage.py`: schema migration and `confidence` column support in `ai_advisory_logs` and `save_ai_advisory`.
  3. `risk_engine/risk_manager.py`: propagate `confidence` in `handle_signal`.
  4. `ai_advisory/regime_classifier.py`: propagate `confidence` in `classify_and_broadcast` / `evaluate_market`.
  5. `main.py`: restore `VYCE_MODEL` and `AI_TIMEOUT_SECONDS` from SQLite settings on startup.
  6. Tests: add tests in `tests/test_confidence_and_settings_sync.py`; run full test suite and connectivity check.
- **Success criteria**: 100% pytest pass rate, connectivity check passes, `confidence` properly retrieved in status.
- **Interface contracts**: `c:\sunMy\trading_bot\.agents\PROJECT.md`
- **Code layout**: `c:\sunMy\trading_bot\.agents\PROJECT.md § Code Layout`

## Key Decisions Made
- `AIAdvisoryEvent`: added `confidence: float = 1.0` as dataclass attribute.
- `Database._init_schema`: added `confidence REAL DEFAULT 1.0` to table definition and added a safe `ALTER TABLE` migration wrapped in try/except for existing database files.
- `Database.save_ai_advisory`: added `confidence: float = 1.0` parameter and column in SQL INSERT statement.
- `RiskManager.handle_signal`: extracted `confidence = float(ai_decision.get("confidence", 1.0))` and passed to `AIAdvisoryEvent` and `self.db.save_ai_advisory`.
- `MarketRegimeClassifier`: updated prompt schema, default state, and parsed `confidence` with default `1.0`. Added alias `classify_and_broadcast = evaluate_market`.
- `main.py`: restored `VYCE_MODEL` and `AI_TIMEOUT_SECONDS` from SQLite settings on startup.
- `web/routes/api_routes.py` & `web/routes/admin_routes.py`: localized router initialization within factory functions to avoid cross-test db connection leakage.
- Live database `trading_bot.db`: safely migrated and confirmed live on port 8386.

## Artifact Index
- `c:\sunMy\trading_bot\.agents\remediation_worker_2\DISPATCH.md` — Assignment instructions
- `c:\sunMy\trading_bot\.agents\remediation_worker_2\BRIEFING.md` — Agent state & identity
- `c:\sunMy\trading_bot\.agents\remediation_worker_2\progress.md` — Liveness & heartbeat log
- `c:\sunMy\trading_bot\.agents\remediation_worker_2\handoff.md` — 5-component completion report
- `c:\sunMy\trading_bot\tests\test_confidence_and_settings_sync.py` — New automated tests

## Change Tracker
- **Files modified**:
  - `core/events.py`: Added `confidence: float = 1.0` to `AIAdvisoryEvent`.
  - `data/storage.py`: Added `confidence` column, safe migration, and parameter to `save_ai_advisory`.
  - `risk_engine/risk_manager.py`: Extracted and propagated `confidence`.
  - `ai_advisory/regime_classifier.py`: Extracted and propagated `confidence`, added alias.
  - `main.py`: Added settings restoration for `VYCE_MODEL` and `AI_TIMEOUT_SECONDS`.
  - `web/routes/api_routes.py`: Localized `router` inside `get_api_router`.
  - `web/routes/admin_routes.py`: Localized `router` inside `get_admin_router`.
  - `tests/test_confidence_and_settings_sync.py`: Added 5 new regression and behavioral unit tests.
- **Build status**: PASS (135/135 tests passed)
- **Pending issues**: None

## Quality Status
- **Build/test result**: 135 passed in 35.02s (100% pass rate)
- **Lint status**: Clean
- **Tests added/modified**: 5 new tests covering storage, migration, RiskManager, RegimeClassifier, and settings sync.

## Loaded Skills
- None
