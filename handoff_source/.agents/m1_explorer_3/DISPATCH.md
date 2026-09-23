# Dispatch for M1 Explorer 3

## Identity & Mission
- Role: Milestone 1 Explorer (Safe Fallback & Timeout Specialist)
- Working Directory: c:\sunMy\trading_bot\.agents\m1_explorer_3
- Original Request Path: c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md
- Project Scope Document: c:\sunMy\trading_bot\.agents\PROJECT.md

## Task
You are a read-only exploration agent. Read `c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md` and `c:\sunMy\trading_bot\.agents\PROJECT.md`.
Read the survey reports at `c:\sunMy\trading_bot\.agents\explorer_survey_2\handoff.md`.
Analyze the safe fallback and timeout requirements for R1:
1. Requirements: "< 3.0s timeout: Nếu AI phản hồi chậm hoặc lỗi mạng, hệ thống tự kích hoạt fallback an toàn theo quy tắc định lượng để không gây nghẽn luồng giao dịch."
2. Design the timeout enforcement:
   - Timeout setting (`settings.AI_TIMEOUT_SECONDS = 3.0`).
   - Wrapping via `asyncio.wait_for(..., timeout=settings.AI_TIMEOUT_SECONDS)`.
3. Design the quantitative fallback logic:
   - What quantitative rule should be evaluated when timeout/exception occurs? (e.g. check signal confidence, verify price vs EMA trend, verify RSI not in extreme overbought/oversold territory, size multiplier = 0.5 or 1.0).
   - Log fallback activation clearly in `audit_logs` and SQLite `ai_advisory_logs`.
4. Ensure zero blocking: event loop in `EventBus._worker` must not hang or freeze.
5. Recommend the exact fix/implementation plan for Worker. Do NOT write code files yourself.

## Output
Write report to `c:\sunMy\trading_bot\.agents\m1_explorer_3\handoff.md`. Send message when done.

## 2026-09-17T05:23:05Z
You are M1 Explorer 3. Read c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md, c:\sunMy\trading_bot\.agents\PROJECT.md, and c:\sunMy\trading_bot\.agents\m1_explorer_3\DISPATCH.md.
Your working directory is c:\sunMy\trading_bot\.agents\m1_explorer_3.
Analyze safe fallback engine and < 3.0s timeout wrapping.
Design quantitative fallback logic, audit logging, and non-blocking execution.
Produce c:\sunMy\trading_bot\.agents\m1_explorer_3\handoff.md.
Send message when done.

