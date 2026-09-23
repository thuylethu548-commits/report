# Dispatch for Explorer Survey 1

## Identity & Mission
- Role: Codebase Explorer (Strategy, Signals, Execution & Risk Pipeline)
- Working Directory: c:\sunMy\trading_bot\.agents\explorer_survey_1
- Original Request Path: c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md

## Task
You are an read-only exploration agent. Read `c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md` first.
Investigate the trading bot codebase at `c:\sunMy\trading_bot` focusing on:
1. Signal generation: where and how EMA Trend, RSI Bollinger, and any other technical signals are calculated.
2. Order lifecycle & execution: how signals transition into orders/positions, how trades are dispatched and tracked.
3. Risk management & Stop-Loss: where stop-loss conditions are evaluated and executed when a position hits SL or experiences slippage.
4. Gatekeeper hook points: where the Advisory Veto Engine (Claude-3.5-Sonnet gatekeeper) should intercept signals before order execution.
5. Identify exact files, classes, methods, data structures, and existing behavior.

## Output
Write your findings to `c:\sunMy\trading_bot\.agents\explorer_survey_1\handoff.md` with full evidence chains (file paths, line numbers, function signatures, data flow analysis).
Send a message when complete.
