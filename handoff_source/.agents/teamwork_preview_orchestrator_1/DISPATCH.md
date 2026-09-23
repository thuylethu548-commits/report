# Dispatch

## 2026-09-17T05:15:46Z

You are the Project Orchestrator (teamwork_preview_orchestrator_1) for the Astra Quant Desk AI upgrade project.

Your working directory is:
c:\sunMy\trading_bot\.agents\teamwork_preview_orchestrator_1

The project root is:
c:\sunMy\trading_bot

The original user request is recorded verbatim at:
c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md

Instructions:
1. Read the user request at c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md.
2. Initialize your BRIEFING.md, plan.md, and progress.md in your working directory.
3. Coordinate specialists/workers to execute all requirements (R1, R2, R3) and satisfy all acceptance criteria:
   - Live Vyce AI (Claude-3.5-Sonnet) integration & Advisory Veto Engine with safe fallback (< 3.0s timeout).
   - Auto Post-Mortem when a position hits Stop-Loss, analyzing causes and recording lessons into SQLite table `trading_lessons`, displaying on `/admin/lessons`.
   - Dynamic Dashboard controls & confidence score display on `/admin` and hot-reload toggle in `/admin/settings`.
   - Comprehensive automated unit tests (100% pass) and Vyce AI live endpoint connectivity check script.
   - End-to-end verification running on port 8386.
4. Keep your progress.md updated regularly as work advances so the sentinel can monitor progress.
5. When all work and acceptance criteria are completed and verified, report completion to the sentinel so the victory audit can be initiated.
