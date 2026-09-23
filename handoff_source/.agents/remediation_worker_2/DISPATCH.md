## 2026-09-17T07:18:03Z

You are Remediation Worker 2 (teamwork_preview_worker).
Your working directory is: c:\sunMy\trading_bot\.agents\remediation_worker_2

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY: Read the original user request first:
c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md
Also read the project architecture:
c:\sunMy\trading_bot\.agents\PROJECT.md
Read the Challenger 2 handoff report specifying the defects:
c:\sunMy\trading_bot\.agents\challenger_2\handoff.md

Your task is to implement the exact fixes requested by Challenger 2:
1. `core/events.py`:
   - Add `confidence: float = 1.0` to dataclass `AIAdvisoryEvent`.
2. `data/storage.py`:
   - In `_init_schema()` table `ai_advisory_logs`, add column `confidence REAL DEFAULT 1.0`.
   - Add safe migration block in `_init_schema()`:
     ```python
     try:
         await cursor.execute("ALTER TABLE ai_advisory_logs ADD COLUMN confidence REAL DEFAULT 1.0")
     except Exception:
         pass
     ```
   - In `save_ai_advisory`: add `confidence: float = 1.0` to method parameters and SQL `INSERT INTO ai_advisory_logs (symbol, regime, risk_score, trade_allowed, size_multiplier, reasoning, timestamp, confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`.
3. `risk_engine/risk_manager.py`:
   - In `handle_signal`, extract `confidence = float(ai_decision.get("confidence", 1.0))` and pass `confidence=confidence` when emitting `AIAdvisoryEvent` and calling `self.db.save_ai_advisory`.
4. `ai_advisory/regime_classifier.py`:
   - In `classify_and_broadcast`, extract `confidence` and pass `confidence=confidence` to `AIAdvisoryEvent` and `self.db.save_ai_advisory`.
5. `main.py`:
   - In the startup loop restoring settings from SQLite (lines 94-106):
     ```python
     elif k == "VYCE_MODEL":
         settings.VYCE_MODEL = str(v)
     elif k == "AI_TIMEOUT_SECONDS":
         settings.AI_TIMEOUT_SECONDS = float(v)
     ```
6. Tests:
   - Add a test verifying `confidence` is stored in SQLite and appears in `GET /api/v1/status` `latest_ai_advisory`.
   - Run full test suite: `.venv\Scripts\pytest -v` (must be 100% pass rate).
   - Run `scripts/check_vyce_connectivity.py` with `.venv\Scripts\python scripts/check_vyce_connectivity.py` to confirm live connectivity.

Write your report to `c:\sunMy\trading_bot\.agents\remediation_worker_2\handoff.md`.
Keep `progress.md` updated with liveness timestamps.
Send a message when finished.
