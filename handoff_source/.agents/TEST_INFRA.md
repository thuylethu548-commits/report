# E2E Test Infra: Astra Quant Desk Autonomous Multi-Agent Trading System

## Test Philosophy
- Opaque-box, requirement-driven derived strictly from `ORIGINAL_REQUEST.md` (Sections 2026-09-22T02:15:20Z and 2026-09-22T02:33:12Z).
- Methodology: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinations + Real-World Workload Scenarios + White-Box Adversarial Hardening.
- Benchmark Integrity: Zero mock cheating, authentic mathematical calculations, deterministic execution, and live parity.

## Feature Inventory Coverage Map
| # | Feature | Milestone | Tier 1 (Coverage) | Tier 2 (Boundary) | Tier 3 (Pairwise) | Tier 4 (Real-World) |
|---|---------|:---------:|:-----------------:|:-----------------:|:-----------------:|:-------------------:|
| F1.1-F1.4 | Multi-Timeframe Perception & Alert Synthesis | M1 | 5 | 5 | ✓ | ✓ |
| F2.1-F2.5 | Adversarial VAR Council & Consensus Engine | M2 | 5 | 5 | ✓ | ✓ (Bull trap & Liquidity hunt) |
| F3.1-F3.5 | Dynamic Holding ("Thế gồng coin") & House Money | M3 | 5 | 5 | ✓ | ✓ (1.2% BE, 2% Trail, 3% TP) |
| F4.1-F4.4 | Psychology & Community Lessons Grounding | M1, M2 | 5 | 5 | ✓ | ✓ (4 core traps) |
| F5.1-F5.5 | Deterministic Risk Engine & 50u Account Guard | M4 | 5 | 5 | ✓ | ✓ (-$3.50 breaker, 2 positions) |

## Test Architecture & Tier Structure
- **Runner**: Pytest (`.venv\Scripts\pytest -v`)
- **Tier 1 (Feature Coverage)**: Happy path tests for all 23 atomic features in isolation.
- **Tier 2 (Boundary & Corner Cases)**: Exact thresholds (+1.19% vs +1.20% BE, +1.99% vs +2.00% Trail, -$3.49 vs -$3.50 Breaker, 2-position cap, 1/symbol cap, SL corridor [0.5%, 5.0%]).
- **Tier 3 (Cross-Feature Combinations)**: Asynchronous interaction between VAR Council, Trailing Stop, Circuit Breaker, and Database.
- **Tier 4 (Real-World Scenarios)**: Realistic trading scenarios:
  * Bull Trap Rally at 4H resistance.
  * Liquidity Hunt Wick stop run.
  * Sprint to House Money Mode (+10 USDT daily profit / +3% position gain).
  * Dead-Trade resolution after 2 hours.
- **Tier 5 (Adversarial Coverage Hardening)**: White-box stress tests against latency spikes, corrupted LLM payloads, network outages, and rapid SL bursts.

## Coverage Goals
- 100% pass on automated tests with zero regressions.
- >= 85% trap veto rate on adversarial VAR council scenarios.
- Quantitative fallback latency < 100ms.
