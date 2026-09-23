# Dispatch for M1 Round 2 Explorer 2

## Identity & Mission
- Role: Milestone 1 Round 2 Explorer (RiskManager Fallback Unification Specialist)
- Working Directory: c:\sunMy\trading_bot\.agents\m1_r2_explorer_2
- Original Request Path: c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md
- Scope Document: c:\sunMy\trading_bot\.agents\PROJECT.md

## Iteration 1 Failure Feedback
Gate Result for Iteration 1 FAILED due to:
1. `m1_reviewer_2` Finding: `VyceClient._build_fallback_veto` swallows network errors/timeouts and returns `approved=True` with conservative sizing (0.50x), completely bypassing `RiskManager._execute_quantitative_fallback` (which contains the Stop-Loss corridor `[0.5%, 5.0%]` and confidence `>= 0.70` checks). In adversarial integration tests with a real `VyceClient` on network failure, unsafe trades with 10% Stop-Loss and low confidence were approved.
2. `m1_reviewer_2` Major Finding: Calls to `save_ai_advisory` and `save_signal` in `RiskManager` lack try/except error handling against SQLite locks/concurrency.
3. `m1_challenger_1` & `m1_challenger_2` Findings: Real `VyceClient` under network outage approved unsafe trades with wide Stop-Loss.

## Task
1. Read `m1_reviewer_2/handoff.md` and `m1_challenger_2/handoff.md`.
2. Analyze `risk_engine/risk_manager.py`:
   - Design how `RiskManager.handle_signal` must enforce `_execute_quantitative_fallback(signal, ...)` whenever `ai_decision.get("fallback_used") is True` or when exceptions occur.
   - Wrap SQLite calls in try/except blocks to guard against transient database locks.
   - Ensure that with a real `VyceClient` under network outage, wide Stop-Loss (>5%) and low confidence (<0.70) BUY signals are strictly rejected.
   - Recommend exact fix specifications for the Worker.

## Output
Write report to `c:\sunMy\trading_bot\.agents\m1_r2_explorer_2\handoff.md`. Send message when done.
