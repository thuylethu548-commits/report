## 2026-09-22T02:23:08Z

You are survey_explorer_2, an exploration agent specializing in quantitative algorithms and trading mechanics.
Your identity: teamwork_preview_explorer
Your working directory: c:\sunMy\trading_bot\.agents\survey_explorer_2
Project root: c:\sunMy\trading_bot

MANDATORY: Read c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md (specifically section ## 2026-09-22T02:15:20Z) before starting work.
Also read c:\sunMy\trading_bot\.agents\PROJECT.md.

Objective:
Investigate and detail the algorithmic, mathematical, and state machine specifications for the new multi-agent trading requirements:
1. R1: Multi-Timeframe Perception & Indicator Synthesis:
   - 15m, 1h, 4h data alignment and technical indicator calculations (EMA 9/21, RSI 14, Bollinger Bands 20, 2 std).
   - Volume anomaly detection, liquidity hunt wick detection, alert synthesis data structures.
2. R2: Adversarial 3-Tier VAR Council & Consensus Engine:
   - Bull Thesis Agent: evaluates trend momentum, market structure, support levels.
   - Bear Devil's Advocate Agent: searches for bull/bear traps, false breakouts, liquidity grabs, divergence, high-risk scenarios.
   - Supreme Arbiter: quantitative consensus arbiter, weighing evidence, computing confidence score (approve if >= 0.80), risk score (1-5), and Size Multiplier (e.g. 0.2x to 1.0x).
   - Trap detection scenarios (fakeout, wick hunts) and how to evaluate >= 85% trap veto rate.
3. R3: Dynamic Position Holding & Trailing Protocol ("Thế gồng coin"):
   - Break-Even state transition: trigger at >= +1.2% unrealized profit, adjust stop_loss = entry_price + estimated roundtrip fees (slippage + taker fee allowance).
   - Dynamic Trailing Stop: activation and step logic bám sát local high/low (swing points or ATR-based trailing distance).
   - House Money Mode: partial take-profit at +3.0% target or when cumulative daily profit reaches +10 USDT; reduce remaining position to 0.2x size runner to ride macro wave risk-free.
4. R4: Market Psychology & Lessons Grounding:
   - SQLite integration with trading_lessons or dedicated psychology lessons database.
   - Querying past lessons (gồng lỗ buông xuôi, chốt non, FOMO đu đỉnh, bẫy đòn bẩy cao) and injecting relevant lessons into the VAR council context before entry.
5. R5: Deterministic Hard Risk Bounds & Circuit Breaker:
   - Daily max loss threshold: -$3.50 USDT hard circuit breaker shutting down further entries for the day.
   - Max concurrent positions: <= 2 across entire portfolio, <= 1 per trading pair.
   - Quantitative fallback: < 100ms deterministic rule if AI council times out or encounters network degradation.

Scope boundaries:
- READ-ONLY exploration. DO NOT modify any code or files outside your working directory.
- Write your comprehensive findings to c:\sunMy\trading_bot\.agents\survey_explorer_2\handoff.md.
- Maintain c:\sunMy\trading_bot\.agents\survey_explorer_2\progress.md.
- When complete, call send_message to report your completion and provide the handoff path.
