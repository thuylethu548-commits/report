# Dispatch for M1 Worker 2 (Iteration 2)

## Identity & Mission
- Role: Milestone 1 Iteration 2 Implementation Worker
- Working Directory: c:\sunMy\trading_bot\.agents\m1_worker_2
- Original Request Path: c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md
- Scope Documents:
  - `c:\sunMy\trading_bot\.agents\PROJECT.md`
  - `c:\sunMy\trading_bot\.agents\m1_r2_explorer_1\handoff.md`
  - `c:\sunMy\trading_bot\.agents\m1_r2_explorer_2\handoff.md`
  - `c:\sunMy\trading_bot\.agents\m1_r2_explorer_3\handoff.md`

## File Ownership
You exclusively own and may edit:
- `config/settings.py`
- `ai_advisory/vyce_client.py`
- `risk_engine/risk_manager.py`
- `main.py`
- `tests/test_ai_advisory.py`
- `tests/test_risk_engine.py`
- `tests/test_m1_adversarial.py`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Tasks
1. Read the three R2 explorer handoff reports carefully.
2. In `ai_advisory/vyce_client.py`:
   - In `_build_fallback_veto(signal, market_context, error_reason)`: validate Stop-Loss corridor `[0.5%, 5.0%]` and confidence threshold `>= 0.70` for BUY signals before approving. If outside corridor or confidence < 0.70, return `"approved": False`, `"reasoning": "Quantitative Fallback: Wide Stop Loss (...) or Low Confidence (...) rejected"`.
   - In `generate_post_mortem`: properly sanitize null/empty strings in JSON fields (`title`, `details`, `lesson_learned`). If null/empty, engage deterministic fallback so string `"None"` is never emitted.
3. In `risk_engine/risk_manager.py`:
   - In `handle_signal`: after receiving `ai_decision`, check:
     `if ai_decision.get("fallback_used") and ai_decision.get("approved"):`
     Re-run through `self._execute_quantitative_fallback(signal, reason=ai_decision.get("reasoning"))` as defense-in-depth to guarantee SL corridor and confidence constraints.
   - Wrap `save_ai_advisory` and `save_signal` calls with `try...except Exception as e:` blocks logging warnings/errors so SQLite concurrency/locks never crash order execution.
4. In `tests/test_m1_adversarial.py`:
   - Fix line 80: Pass `open=3000.0, high=3010.0, low=2990.0, close=3005.0, volume=10.0` to `MarketEvent` instead of `price=3000.0`.
5. Verify:
   - Run `.venv\Scripts\pytest -v`.
   - Ensure 100% of all tests pass across all test modules (including unit, integration, and adversarial tests).
   - Document test command and output in your report.

## Output
Write report to `c:\sunMy\trading_bot\.agents\m1_worker_2\handoff.md`. Send message when done.

## 2026-09-17T05:44:18Z
You are M1 Worker 2. Read c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md and c:\sunMy\trading_bot\.agents\m1_worker_2\DISPATCH.md.
Your working directory is c:\sunMy\trading_bot\.agents\m1_worker_2.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement the fixes recommended in m1_r2_explorer_1, m1_r2_explorer_2, and m1_r2_explorer_3:
1. Update ai_advisory/vyce_client.py:
   - Enforce SL corridor [0.5%, 5.0%] and confidence >= 0.70 in _build_fallback_veto
   - Sanitize nulls in generate_post_mortem
2. Update risk_engine/risk_manager.py:
   - Enforce _execute_quantitative_fallback when ai_decision.get("fallback_used") and ai_decision.get("approved")
   - Wrap SQLite calls in try/except blocks
3. Update tests/test_m1_adversarial.py:
   - Fix MarketEvent kwargs (open, high, low, close, volume)
4. Run full test suite with .venv\Scripts\pytest -v and verify 100% pass rate.
5. Write your report to c:\sunMy\trading_bot\.agents\m1_worker_2\handoff.md and notify parent.
