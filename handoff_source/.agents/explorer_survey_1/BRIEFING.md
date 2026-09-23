# BRIEFING — 2026-09-17T12:19:00+07:00

## Mission
Investigate trading_bot codebase focusing on signal generation, order execution, risk management & SL triggers, and gatekeeper hook points for Claude-3.5-Sonnet Advisory Veto.

## 🔒 My Identity
- Archetype: explorer
- Roles: Codebase Explorer (Strategy, Signals, Execution & Risk Pipeline)
- Working directory: c:\sunMy\trading_bot\.agents\explorer_survey_1
- Original parent: 4a1d31f3-0188-4bb2-b5c1-ff9c51dda848
- Milestone: Exploration & Codebase Mapping

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Produce handoff.md with 5 components (Observation, Logic Chain, Caveats, Conclusion, Verification Method)
- Evidence chain completeness: exact file paths, line numbers, data structures

## Current Parent
- Conversation ID: 4a1d31f3-0188-4bb2-b5c1-ff9c51dda848
- Updated: 2026-09-17T12:19:00+07:00

## Investigation State
- **Explored paths**:
  - `main.py` (wiring, startup, warmup, shutdown)
  - `config/settings.py` (configuration, env vars, defaults)
  - `core/constants.py` & `core/events.py` & `core/event_bus.py` (event-driven architecture)
  - `strategies/base_strategy.py`, `strategies/ema_trend.py`, `strategies/rsi_bollinger.py` (signal generation)
  - `risk_engine/risk_manager.py` & `risk_engine/circuit_breaker.py` (risk filtering & drawdown protection)
  - `execution/oms.py`, `execution/paper_trader.py`, `execution/binance_executor.py` (order execution & lifecycle)
  - `data/storage.py` (aiosqlite database schema, queries, seeded lessons & settings)
  - `data/binance_client.py` & `data/websocket_feed.py` (market data ingest)
  - `ai_advisory/vyce_client.py` & `ai_advisory/regime_classifier.py` (AI advisory proxy & regime classification)
  - `web/app.py`, `web/routes/admin_routes.py`, `web/routes/api_routes.py` (FastAPI endpoints, settings hot-reload, lessons)
  - `web/templates/admin/cockpit.html`, `web/templates/admin/lessons.html`, `web/templates/admin/settings.html`, `web/static/js/admin_app.js`
  - `tests/` (10 passed tests verified via pytest)
- **Key findings**:
  - Signal generation: Golden/Death Cross (EMA 9/21 with 1.5x ATR SL / 3.0x ATR TP) and RSI (14)/Bollinger (20, 2.0) mean reversion emit `SignalEvent` to `EventBus`.
  - Order lifecycle: `RiskManager` intercepts `SignalEvent`, verifies circuit breaker, stop loss, open position limit, sizes position, saves to SQLite `signals`, and emits `OrderEvent`. `PaperTrader` or `BinanceExecutor` executes `OrderEvent` and publishes `FillEvent`.
  - Risk & Stop Loss: SL is checked per tick in `PaperTrader.handle_market_tick`. If price <= SL, calls `_close_position(pos_id, price, "STOP_LOSS")`. However, the exit reason is not propagated to `FillEvent` or `trades` table, and no event is emitted to trigger auto post-mortem.
  - Gatekeeper hook: `RiskManager.handle_signal` lines 38-50 contains the passive advisory check, which currently evaluates only a stale/uninvoked `latest_ai_advisory`. It is the optimal intercept point for the active Claude-3.5-Sonnet Advisory Veto Engine with < 3.0s fallback.
- **Unexplored areas**: None for this survey scope; all 4 focus areas comprehensively traced.

## Key Decisions Made
- Identified `RiskManager.handle_signal` as the primary architectural hook for Claude-3.5-Sonnet Advisory Veto Engine.
- Identified `PaperTrader._close_position` / `FillEvent` as the trigger point for Auto Post-Mortem on Stop-Loss.

## Artifact Index
- handoff.md — Comprehensive handoff report with 5-component structure
- progress.md — Liveness & exploration tracking
