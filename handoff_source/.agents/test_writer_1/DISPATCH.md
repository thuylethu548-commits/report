## 2026-09-22T02:55:00Z
You are test_writer_1, the E2E Test Suite Architect and Writer.
Your identity: teamwork_preview_test_writer
Your working directory: c:\sunMy\trading_bot\.agents\test_writer_1
Project root: c:\sunMy\trading_bot

MANDATORY: Read c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md (specifically sections ## 2026-09-22T02:15:20Z and ## 2026-09-22T02:33:12Z) before starting work.
Also read c:\sunMy\trading_bot\.agents\PROJECT.md, c:\sunMy\trading_bot\.agents\TEST_INFRA.md, and c:\sunMy\trading_bot\.agents\survey_spec_miner_3\handoff.md.

Objective:
Build the comprehensive requirement-driven, opaque-box E2E test suite in tests/ structured across 5 tiers:
1. Inspect existing tests in tests/ to maintain 100% backward compatibility.
2. Create/augment test suites:
   - tests/test_market_perception.py: Tier 1 & Tier 2 tests for multi-timeframe candle ingestion, EMA 9/21, RSI 14 Wilder, Bollinger Bands 20/2, volume anomalies (climax, churn, dryout), and liquidity hunt wicks (spring & upthrust).
   - tests/test_var_council.py: 3-round VAR council tests, confidence >= 0.80 gate, bear risk score <= 3, size multiplier (0.2x-1.0x), >= 85% trap veto benchmark (20 standardized scenarios), and transparent dialogue transcript logging.
   - tests/test_holding_protocol.py: Dynamic holding ("Thế gồng coin") tests: Break-Even at +1.2% (+0.2% fee buffer, invariant net profit >= 0), Dynamic Trailing Stop at +2.0% (1.0x ATR monotonic ratchet), House Money Mode at +3.0% / +10 USDT (80% partial TP, 0.2x runner locked at +1.5%), and dead-trade timer (>2h).
   - tests/test_risk_circuit_breaker.py: Deterministic hard risk bounds: -$3.50 daily loss circuit breaker, max 2 portfolio positions, max 1 per symbol, 50u capital sizing calibration ($10-$14 notional, ~14 trades/day), and < 100ms fallback SLA.
   - tests/test_adversarial_stress.py: Tier 5 adversarial stress tests: latency spikes, corrupted LLM payloads, network outages, rapid SL bursts.
3. Execute pytest on the newly created test suites and document results.
4. Write c:\sunMy\trading_bot\.agents\TEST_READY.md when the test infrastructure and test suites are ready.
5. Deliver your handoff report to c:\sunMy\trading_bot\.agents\test_writer_1\handoff.md and call send_message.

Scope boundaries:
- Write test files ONLY in tests/ and metadata in c:\sunMy\trading_bot\.agents\test_writer_1 and c:\sunMy\trading_bot\.agents\TEST_READY.md.
- DO NOT modify production source code in ai_advisory/, risk_engine/, execution/, strategies/, data/, config/.

## 2026-09-22T02:58:41Z
Sender: parent (e9b53268-5666-44c8-8876-b9e21cf9f943)
Context: E2E Test Suite Creation
Content: User directive updated in ORIGINAL_REQUEST.md (§2026-09-22T02:57:56Z): Campaign '7-DAY ADAPTIVE TRADING TEST' ('Trade the Market, Not the KPI'). Tests must verify that the bot adapts to market conditions (no trade when no edge, no forced trade count), records the 10 Golden Questions, and evaluates performance across the 6 pillars.
Action: Please factor these requirements into your 5-tier E2E test suites.
