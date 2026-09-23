# Dispatch for M1 Explorer 2

## Identity & Mission
- Role: Milestone 1 Explorer (Risk Manager Advisory Veto Specialist)
- Working Directory: c:\sunMy\trading_bot\.agents\m1_explorer_2
- Original Request Path: c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md
- Project Scope Document: c:\sunMy\trading_bot\.agents\PROJECT.md

## Task
You are a read-only exploration agent. Read `c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md` and `c:\sunMy\trading_bot\.agents\PROJECT.md`.
Read the survey reports at `c:\sunMy\trading_bot\.agents\explorer_survey_1\handoff.md` and `c:\sunMy\trading_bot\.agents\explorer_survey_2\handoff.md`.
Analyze `risk_engine/risk_manager.py`:
1. Design the hook in `RiskManager.handle_signal(signal: SignalEvent)`:
   - When `settings.ENABLE_AI_ADVISORY` is active, invoke `vyce_client.evaluate_signal_veto`.
   - Ensure `RiskManager` has access to `VyceClient` (either passed into `__init__` or created as singleton).
   - If AI vetoes (`approved is False`), call `_record_rejection(signal, f"AI Advisory Veto: {reasoning}")` and return `None`.
   - If AI approves (`approved is True`), adjust order allocation using `size_multiplier`, save approved signal in SQLite, and emit `OrderEvent`.
2. Ensure compatibility with `main.py` instantiation: check how `RiskManager` is initialized in `main.py` and what arguments it accepts.
3. Recommend the exact fix/implementation plan for Worker. Do NOT write code files yourself.

## Output
Write report to `c:\sunMy\trading_bot\.agents\m1_explorer_2\handoff.md`. Send message when done.

## 2026-09-17T05:23:05Z
You are M1 Explorer 2. Read c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md, c:\sunMy\trading_bot\.agents\PROJECT.md, and c:\sunMy\trading_bot\.agents\m1_explorer_2\DISPATCH.md.
Your working directory is c:\sunMy\trading_bot\.agents\m1_explorer_2.
Analyze risk_engine/risk_manager.py for active signal veto gatekeeper integration.
Design handle_signal hook, position sizing, rejection/approval recording, and main.py wiring.
Produce c:\sunMy\trading_bot\.agents\m1_explorer_2\handoff.md.
Send message when done.
