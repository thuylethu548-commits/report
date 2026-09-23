# Dispatch for M1 Explorer 1

## Identity & Mission
- Role: Milestone 1 Explorer (Vyce Client & Model Resolver Specialist)
- Working Directory: c:\sunMy\trading_bot\.agents\m1_explorer_1
- Original Request Path: c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md
- Project Scope Document: c:\sunMy\trading_bot\.agents\PROJECT.md

## Task
You are a read-only exploration agent. Read `c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md` and `c:\sunMy\trading_bot\.agents\PROJECT.md`.
Read the survey reports at `c:\sunMy\trading_bot\.agents\explorer_survey_2\handoff.md`.
Analyze `config/settings.py` and `ai_advisory/vyce_client.py`:
1. Design the exact implementation for `config/settings.py` to seamlessly resolve `VYCE_API_KEY` or `ANTHROPIC_API_KEY`, `VYCE_BASE_URL` or `ANTHROPIC_BASE_URL`, and default model to `claude-sonnet-4-6`.
2. Design the upgraded `VyceClient` class in `ai_advisory/vyce_client.py`:
   - Persistent `httpx.AsyncClient` with keep-alive connection pooling (`httpx.Limits(max_keepalive_connections=5, max_connections=10)`).
   - Automatic model alias remapping (`claude-3-5-sonnet` -> `claude-sonnet-4-6`).
   - Implementation of `evaluate_signal_veto(signal: SignalEvent, market_context: dict) -> Dict[str, Any]` returning structured JSON (`approved`, `regime`, `risk_score`, `confidence`, `size_multiplier`, `reasoning`).
   - Implementation of `chat_completion(system_prompt, user_content, max_tokens)`.
   - Method `close()` for graceful shutdown.
3. Recommend the exact fix/implementation plan for Worker. Do NOT write code files yourself.

## Output
Write report to `c:\sunMy\trading_bot\.agents\m1_explorer_1\handoff.md`. Send message when done.

## 2026-09-17T05:23:05Z
You are M1 Explorer 1. Read c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md, c:\sunMy\trading_bot\.agents\PROJECT.md, and c:\sunMy\trading_bot\.agents\m1_explorer_1\DISPATCH.md.
Your working directory is c:\sunMy\trading_bot\.agents\m1_explorer_1.
Analyze config/settings.py and ai_advisory/vyce_client.py.
Design persistent keep-alive httpx client, key resolution, model alias mapping, evaluate_signal_veto method.
Produce c:\sunMy\trading_bot\.agents\m1_explorer_1\handoff.md.
Send message when done.
