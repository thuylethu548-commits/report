# Execution Plan: Astra Quant Desk AI Upgrade

## Objective
Upgrade Astra Quant Desk multi-agent trading system with Claude-3.5-Sonnet (via Vyce AI Proxy) as Supreme Advisor (Veto/Approve signals, macro analysis), Auto Post-Mortem on Stop-Loss into SQLite `trading_lessons` and `/admin/lessons`, dynamic dashboard controls with confidence score on `/admin` and hot-reload toggle in `/admin/settings`, full automated test suite pass, live endpoint connectivity script, and E2E verification on port 8386.

## Phases

### Phase 0: Codebase Survey & Scope Mapping
- Dispatch 3 parallel Explorers:
  - Explorer 1: Strategy engine, signal generation (EMA Trend, RSI Bollinger), order execution loop, and risk management.
  - Explorer 2: Vyce AI proxy configuration, environment variables, LLM client architecture, fallback rules, and timeout mechanisms.
  - Explorer 3: SQLite database schema, positions/trades tables, FastAPI web server, WebSocket/polling feeds, admin routes (`/admin`, `/admin/settings`, `/admin/lessons`), and existing `tests/`.
- Aggregate reports into `PROJECT.md` with Feature Inventory, Architecture, Milestones, Interface Contracts, and Code Layout.

### Phase 1: Dual-Track Implementation & E2E Test Suite Design
- **Track A (Implementation)**:
  - Milestone 1: Live Vyce AI (Claude-3.5-Sonnet) Integration & Advisory Veto Engine with < 3.0s timeout fallback.
  - Milestone 2: Auto Post-Mortem on Stop-Loss, SQLite `trading_lessons` persistence, and `/admin/lessons` endpoint/template.
  - Milestone 3: Dynamic Dashboard controls, confidence score display on `/admin`, hot-reload runtime toggle on `/admin/settings`.
  - Each milestone executed via iteration cycle: Explorer -> Worker -> Reviewers (2) -> Challengers (2) -> Forensic Auditor -> Gate.
- **Track B (E2E Testing Track)**:
  - Test harness, runner, and live connectivity verification script for Vyce AI.
  - Opaque-box 4-tier test suite (Feature coverage, Boundary & Corner cases, Combinations, Real-world scenarios).
  - Publish `TEST_READY.md`.

### Phase 2: Final Milestone & Hardening
- Phase 2A: Verify 100% pass on all existing tests and new E2E tests (Tiers 1-4).
- Phase 2B: Adversarial Coverage Hardening (Tier 5) with Challenger stress testing and edge-case verification.

### Phase 3: Live Verification & Handover
- Verify full server operation on port 8386 (live signal advisory veto/approve log, stop-loss simulation with lesson generation, UI rendering, low latency).
- Assemble final handoff and report completion to Sentinel for Victory Audit.
