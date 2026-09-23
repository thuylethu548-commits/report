# Dispatch for M1 Worker

## Identity & Mission
- Role: Milestone 1 Implementation Worker
- Working Directory: c:\sunMy\trading_bot\.agents\m1_worker_1
- Original Request Path: c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md
- Scope Documents:
  - `c:\sunMy\trading_bot\.agents\PROJECT.md`
  - `c:\sunMy\trading_bot\.agents\m1_explorer_1\handoff.md`
  - `c:\sunMy\trading_bot\.agents\m1_explorer_2\handoff.md`
  - `c:\sunMy\trading_bot\.agents\m1_explorer_3\handoff.md`

## File Ownership
You exclusively own and may edit:
- `config/settings.py`
- `ai_advisory/vyce_client.py`
- `risk_engine/risk_manager.py`
- `main.py`
- `tests/test_ai_advisory.py`
- `tests/test_risk_engine.py`

Do NOT modify files outside your ownership.

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Tasks
1. Read `ORIGINAL_REQUEST.md` and the three explorer reports carefully.
2. Update `config/settings.py`:
   - Support `ANTHROPIC_API_KEY` fallback if `VYCE_API_KEY` is empty/mock.
   - Support `ANTHROPIC_BASE_URL` fallback if `VYCE_BASE_URL` is empty. Ensure `/v1` suffix.
   - Remap `VYCE_MODEL` aliases (`claude-3-5-sonnet` -> `claude-sonnet-4-6`).
   - Default `ENABLE_AI_ADVISORY = True`, `AI_TIMEOUT_SECONDS = 3.0`.
3. Upgrade `ai_advisory/vyce_client.py`:
   - Persistent `httpx.AsyncClient` with keep-alive connection pooling (`Limits(max_keepalive_connections=5, max_connections=10, keepalive_expiry=30.0)`).
   - `resolve_model_alias` helper.
   - `evaluate_signal_veto(signal, market_context)` with prompt parsing and strict JSON output.
   - `generate_post_mortem(trade_info)` (pre-wired for M2).
   - Strict `< 3.0s` timeout handling catching `httpx.TimeoutException` and upstream errors.
   - `close()` method.
4. Upgrade `risk_engine/risk_manager.py`:
   - Accept optional `vyce_client: Optional[VyceClient] = None` in `__init__` for 100% backward compatibility.
   - In `handle_signal(signal: SignalEvent)`:
     - Phase 1: Deterministic hard checks (circuit breaker, open positions, stop loss validity).
     - Phase 2: If `settings.ENABLE_AI_ADVISORY`: active Supreme Advisor evaluation via `evaluate_signal_veto` wrapped in `< 3.0s` timeout (`asyncio.wait_for`). If vetoed, record rejection with reason and return `None`. If approved, apply `size_multiplier`.
     - Dual-Layer Fallback: On timeout or error, execute deterministic quantitative fallback (allow SELL to de-escalate risk; evaluate BUY with SL corridor & confidence, scale by 0.5), log `[AI Fallback Engaged]`, save to `ai_advisory_logs`, and proceed safely.
     - Phase 3 & 4: Position sizing and publish `OrderEvent`.
   - Subscribe to `FillEvent` to keep `self.open_positions` synchronized.
5. Update `main.py` to instantiate and pass `vyce_client` to `RiskManager` and ensure graceful shutdown.
6. Verify & Test:
   - Run existing and updated tests using `.venv\Scripts\pytest -v`.
   - Ensure 100% of tests pass.
   - Document verification commands and output.

## Output
Write your handoff report to `c:\sunMy\trading_bot\.agents\m1_worker_1\handoff.md`.
Send message when done.

## 2026-09-17T05:27:48Z

You are M1 Worker 1. Read c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md and c:\sunMy\trading_bot\.agents\m1_worker_1\DISPATCH.md.
Your working directory is c:\sunMy\trading_bot\.agents\m1_worker_1.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement Milestone 1 requirements:
- config/settings.py (key fallback, model alias mapping)
- ai_advisory/vyce_client.py (persistent keep-alive client, evaluate_signal_veto, generate_post_mortem, timeout handling)
- risk_engine/risk_manager.py (active advisory veto gatekeeper, dual-layer < 3.0s timeout, quantitative fallback, fill event subscription)
- main.py (VyceClient wiring)
- tests/ (expand test_ai_advisory.py and test_risk_engine.py)

Run pytest (.venv\Scripts\pytest -v) and ensure 100% passing.
Write your handoff report to c:\sunMy\trading_bot\.agents\m1_worker_1\handoff.md with passing test logs.
Send message when done.

