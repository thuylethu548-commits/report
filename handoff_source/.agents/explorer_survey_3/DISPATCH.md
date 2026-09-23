# Dispatch for Explorer Survey 3

## Identity & Mission
- Role: Codebase Explorer (Database, Web Admin, Dashboard & Test Suite)
- Working Directory: c:\sunMy\trading_bot\.agents\explorer_survey_3
- Original Request Path: c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md

## Task
You are a read-only exploration agent. Read `c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md` first.
Investigate the trading bot codebase at `c:\sunMy\trading_bot` focusing on:
1. SQLite Database: connection setup, migrations/schema definition (`trading_bot.db`), existing tables (positions, trades, logs), and how to add the `trading_lessons` table.
2. Web Admin Cockpit & API: FastAPI app structure, routes (`/admin`, `/admin/settings`, `/admin/lessons`), templates (Jinja2 or HTML/JS), WebSockets or polling feeds.
3. Hot-reload configuration: how `/admin/settings` persists settings and how the bot reloads them at runtime without restarting the server.
4. Confidence score & AI advisory display: how real-time metrics are pushed or fetched by `/admin`.
5. Existing test suite: inspect all tests in `tests/`, test runner (pytest), fixtures, mock strategies, current pass rate, and execution command.

## Output
Write your findings to `c:\sunMy\trading_bot\.agents\explorer_survey_3\handoff.md` with full evidence chains (file paths, line numbers, schema designs, route definitions).
Send a message when complete.

## 2026-09-17T05:16:37Z
You are Explorer Survey 3. Read c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md and c:\sunMy\trading_bot\.agents\explorer_survey_3\DISPATCH.md.
Your working directory is c:\sunMy\trading_bot\.agents\explorer_survey_3.
Investigate the codebase at c:\sunMy\trading_bot:
1. SQLite database setup, existing tables, and design for trading_lessons.
2. Web Admin Cockpit & FastAPI routes (/admin, /admin/settings, /admin/lessons), templates, and WebSocket/polling feeds.
3. Hot-reload mechanism for runtime settings.
4. Existing tests in tests/, test runner, fixtures, and how to run tests.
Produce c:\sunMy\trading_bot\.agents\explorer_survey_3\handoff.md with verified evidence chains, file paths, line numbers, and UI/database designs.
When done, message me with your summary.
