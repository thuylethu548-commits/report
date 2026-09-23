# 01. CÂY CẤU TRÚC THƯ MỤC DỰ ÁN (PROJECT DIRECTORY TREE)
**Độ sâu hiển thị:** 4 cấp  
**Đã loại trừ:** `node_modules`, `.venv`, `.git`, `__pycache__`, `.pytest_cache`, logs, secrets, database binaries, và media cache.

```text
c:\sunMy\trading_bot\
├── 📁 .agents/
│   ├── 📁 auditor_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 auditor_r2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 challenger_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 challenger_2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 challenger_r2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 explorer_survey_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 explorer_survey_2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 explorer_survey_3/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_auditor_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_auton_explorer_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 context.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_auton_explorer_2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 context.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_auton_spec_miner_3/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 context.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_challenger_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_challenger_2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_explorer_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_explorer_2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_explorer_3/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_r2_explorer_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_r2_explorer_2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_r2_explorer_3/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_reviewer_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_reviewer_2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_worker_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m1_worker_2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 m2_explorer_1/
│   │   ├── 📄 .gitkeep
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 m2_explorer_2/
│   │   ├── 📄 .gitkeep
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 m2_explorer_3/
│   │   ├── 📄 .gitkeep
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 m2_m3_worker_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 m2_worker_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 progress.md
│   ├── 📁 remediation_worker_2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 reviewer_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 reviewer_2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 reviewer_r2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 sentinel/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 handoff.md
│   ├── 📁 survey_explorer_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 context.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 survey_explorer_2/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 context.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 survey_spec_miner_3/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 context.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 teamwork_preview_orchestrator_1/
│   │   ├── 📄 .gitkeep
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 GATE_STATUS.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 teamwork_preview_orchestrator_2/
│   │   ├── 📄 .gitkeep
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 plan.md
│   │   ├── 📄 progress.md
│   ├── 📁 teamwork_preview_orchestrator_3/
│   │   ├── 📄 .gitkeep
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 GATE_STATUS.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   ├── 📁 teamwork_preview_orchestrator_4/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 context.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 progress.md
│   ├── 📁 teamwork_preview_victory_auditor_1/
│   │   ├── 📄 .gitkeep
│   │   ├── 📄 benchmark_latency.py
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 handoff.md
│   │   ├── 📄 progress.md
│   │   ├── 📄 test_live_scenario.py
│   │   ├── 📄 test_pipeline.py
│   │   ├── 📄 verify_live_api.py
│   ├── 📁 test_writer_1/
│   │   ├── 📄 BRIEFING.md
│   │   ├── 📄 context.md
│   │   ├── 📄 DISPATCH.md
│   │   ├── 📄 progress.md
│   ├── 📄 ORIGINAL_REQUEST.md
│   ├── 📄 PROJECT.md
│   ├── 📄 TEST_INFRA.md
│   ├── 📄 TEST_READY.md
├── 📁 ai_advisory/
│   ├── 📄 __init__.py
│   ├── 📄 adversarial_debater.py
│   ├── 📄 gemini_pool.py
│   ├── 📄 groq_pool.py
│   ├── 📄 regime_classifier.py
│   ├── 📄 vyce_client.py
├── 📁 config/
│   ├── 📄 __init__.py
│   ├── 📄 settings.py
│   ├── 📄 trading_safety_rules.md
├── 📁 core/
│   ├── 📁 research_lab/
│   │   ├── 📄 agents.py
│   │   ├── 📄 continuous_loop.py
│   │   ├── 📄 knowledge_store.py
│   │   ├── 📄 scenario_engine.py
│   ├── 📄 __init__.py
│   ├── 📄 backtest_engine.py
│   ├── 📄 campaign_monitor.py
│   ├── 📄 constants.py
│   ├── 📄 event_bus.py
│   ├── 📄 events.py
│   ├── 📄 fleet_manager.py
│   ├── 📄 hyper_simulation_world.py
│   ├── 📄 macro_intelligence_bridge.py
│   ├── 📄 mkt_ai_gateway.py
│   ├── 📄 mkt_fleet.py
│   ├── 📄 quantum_5d_engine.py
│   ├── 📄 spatial_agent_brain.py
│   ├── 📄 spatial_agent_brain.py.bak_llmbrain
├── 📁 data/
│   ├── 📁 backups/
│   │   ├── 📄 trading_bot_20260923_075637.db.gz
│   │   ├── 📄 trading_bot_20260923_080244.db.gz
│   │   ├── 📄 trading_bot_20260923_081211.db.gz
│   │   ├── 📄 trading_bot_20260923_082441.db.gz
│   │   ├── 📄 trading_bot_20260923_084253.db.gz
│   │   ├── 📄 trading_bot_20260923_084338.db.gz
│   │   ├── 📄 trading_bot_20260923_085359.db.gz
│   │   ├── 📄 trading_bot_20260923_090338.db.gz
│   │   ├── 📄 trading_bot_20260923_091224.db.gz
│   │   ├── 📄 trading_bot_20260923_092927.db.gz
│   │   ├── 📄 trading_bot_20260923_094431.db.gz
│   │   ├── 📄 trading_bot_20260923_100253.db.gz
│   │   ├── 📄 trading_bot_20260923_100536.db.gz
│   │   ├── 📄 trading_bot_20260923_102520.db.gz
│   │   ├── 📄 trading_bot_20260923_102657.db.gz
│   │   ├── 📄 trading_bot_20260923_102734.db.gz
│   │   ├── 📄 trading_bot_20260923_102829.db.gz
│   │   ├── 📄 trading_bot_20260923_104326.db.gz
│   │   ├── 📄 trading_bot_20260923_115535.db.gz
│   │   ├── 📄 trading_bot_20260923_125214.db.gz
│   │   ├── 📄 trading_bot_20260923_132116.db.gz
│   │   ├── 📄 trading_bot_20260923_132654.db.gz
│   ├── 📄 __init__.py
│   ├── 📄 binance_client.py
│   ├── 📄 data_lake_manager.py
│   ├── 📄 dataset_alpha_training.jsonl
│   ├── 📄 gdrive_sheets_sync.py
│   ├── 📄 macro_news_scanner.py
│   ├── 📄 storage.py
│   ├── 📄 supabase_sync.py
│   ├── 📄 trading_bot.db  -> Cơ sở dữ liệu SQLite sản xuất (ACID Primary Storage)
│   ├── 📄 trading_platform.db
│   ├── 📄 websocket_feed.py
├── 📁 execution/
│   ├── 📄 __init__.py
│   ├── 📄 binance_executor.py
│   ├── 📄 mission_farmer.py
│   ├── 📄 multi_account_dispatcher.py
│   ├── 📄 oms.py
│   ├── 📄 paper_trader.py
│   ├── 📄 spot_executor.py
│   ├── 📄 trailing_stop.py
├── 📁 monitoring/
│   ├── 📄 __init__.py
│   ├── 📄 binance_square_publisher.py
│   ├── 📄 daily_intelligence_reporter.py
│   ├── 📄 dashboard.html
│   ├── 📄 dashboard.py
│   ├── 📄 department_telemetry.py
│   ├── 📄 email_service.py
│   ├── 📄 intelligence_council.py
│   ├── 📄 telegram_bot.py
│   ├── 📄 template.py
├── 📁 project_handoff/
│   ├── 📄 00_EXECUTIVE_SUMMARY.md
├── 📁 reports/
│   ├── 📄 daily_report_2026-09-22.md
│   ├── 📄 daily_report_2026-09-23.md
├── 📁 risk_engine/
│   ├── 📄 __init__.py
│   ├── 📄 circuit_breaker.py
│   ├── 📄 funding_sentinel.py
│   ├── 📄 risk_manager.py
│   ├── 📄 time_window_guard.py
├── 📁 scripts/
│   ├── 📄 ai_spot_sniper.py
│   ├── 📄 ai_synthetic_trainer.py
│   ├── 📄 apply_megacity.py
│   ├── 📄 audit_system.py
│   ├── 📄 autonomous_market_sweeper.py
│   ├── 📄 backup_to_telegram.py
│   ├── 📄 check_aim_22.py
│   ├── 📄 check_binance_status.py
│   ├── 📄 check_bybit_funding_ake.py
│   ├── 📄 check_live_plan.py
│   ├── 📄 check_open_trades.py
│   ├── 📄 check_vyce_connectivity.py
│   ├── 📄 clean_settings_page.py
│   ├── 📄 community_agent_farm.py
│   ├── 📄 consult_models.py
│   ├── 📄 extract_all_tiktok_comments.py
│   ├── 📄 gen_ai_orch.py
│   ├── 📄 gen_pixel_floor_v2.py
│   ├── 📄 gen_pixel_floor_v3.py
│   ├── 📄 ingest_community_lessons.py
│   ├── 📄 init_cohort_benchmarks.py
│   ├── 📄 live_position_guardian.py
│   ├── 📄 market_analysis.py
│   ├── 📄 miner_daemon.py
│   ├── 📄 parse_tiktok_comments.py
│   ├── 📄 reconcile_trades.py
│   ├── 📄 record_real_lessons.py
│   ├── 📄 research_ake_contract.py
│   ├── 📄 run_hyper_simulation.py
│   ├── 📄 run_research_lab.py
│   ├── 📄 seed_clients_audit.py
│   ├── 📄 send_live_alert.py
│   ├── 📄 simulate_trading.py
│   ├── 📄 sync_data_lake_gdrive.py
│   ├── 📄 test_pos_api.py
│   ├── 📄 testnet_preflight.py
│   ├── 📄 verify_pixel_floor.py
│   ├── 📄 verify_pixel_floor_v3.py
├── 📁 strategies/
│   ├── 📄 __init__.py
│   ├── 📄 base_strategy.py
│   ├── 📄 ema_trend.py
│   ├── 📄 multi_timeframe.py
│   ├── 📄 rsi_bollinger.py
│   ├── 📄 spot_dca_strategy.py
├── 📁 tests/
│   ├── 📄 test_admin_security.py
│   ├── 📄 test_affiliate_ledger.py
│   ├── 📄 test_ai_advisory.py
│   ├── 📄 test_antigravity_canvas.py
│   ├── 📄 test_auto_post_mortem.py
│   ├── 📄 test_autonomous_fleet.py
│   ├── 📄 test_backtest_engine.py
│   ├── 📄 test_client_portal.py
│   ├── 📄 test_confidence_and_settings_sync.py
│   ├── 📄 test_funding_and_square.py
│   ├── 📄 test_golden_audit.py
│   ├── 📄 test_google_auth_and_email.py
│   ├── 📄 test_m1_adversarial.py
│   ├── 📄 test_m1_adversarial_stress.py
│   ├── 📄 test_m2_m3_adversarial_challenger.py
│   ├── 📄 test_macro_news_scanner.py
│   ├── 📄 test_market_perception.py
│   ├── 📄 test_multi_timeframe.py
│   ├── 📄 test_paper_trader.py
│   ├── 📄 test_paper_trailing.py
│   ├── 📄 test_pixel_floor_and_performance.py
│   ├── 📄 test_quantum_5d_engine.py
│   ├── 📄 test_quantum_5d_routes.py
│   ├── 📄 test_risk_engine.py
│   ├── 📄 test_settings_and_lessons.py
│   ├── 📄 test_spatial_agent_brain.py
│   ├── 📄 test_spot_pyramid_dca.py
│   ├── 📄 test_strategies.py
│   ├── 📄 test_supabase_sync.py
│   ├── 📄 test_telegram_notifier.py
│   ├── 📄 test_time_window_guard.py
│   ├── 📄 test_trailing_stop.py
│   ├── 📄 test_v4_pillars.py
│   ├── 📄 test_var_council.py
├── 📁 web/
│   ├── 📁 routes/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 admin_routes.py
│   │   ├── 📄 api_routes.py
│   │   ├── 📄 canvas_routes.py
│   │   ├── 📄 client_routes.py
│   ├── 📁 static/
│   │   ├── 📁 css/
│   │   │   ├── 📄 admin.css
│   │   │   ├── 📄 antigravity_canvas.css
│   │   │   ├── 📄 client.css
│   │   │   ├── 📄 client.css.bak_audit
│   │   │   ├── 📄 common.css
│   │   │   ├── 📄 cultivation_floor.before-animation.css
│   │   │   ├── 📄 cultivation_floor.css
│   │   │   ├── 📄 nro_pixel_engine.css
│   │   │   ├── 📄 orchestration.css
│   │   │   ├── 📄 pixel_floor.css
│   │   │   ├── 📄 pixel_floor.css.bak_master
│   │   │   ├── 📄 pixel_floor.css.bak_ui_redesign
│   │   │   ├── 📄 portal_dashboard.css
│   │   │   ├── 📄 quantum.css
│   │   │   ├── 📄 responsive.css
│   │   ├── 📁 images/
│   │   │   ├── 📁 avatars/
│   │   │   ├── 📁 dept_scenes/
│   │   │   ├── 📁 office_sprites/
│   │   │   ├── 📁 rooms/
│   │   │   ├── 📁 sprites/
│   │   ├── 📁 img/
│   │   │   ├── 📄 astra_logo.svg
│   │   ├── 📁 js/
│   │   │   ├── 📄 admin_app.js
│   │   │   ├── 📄 agent_rpg_registry.js
│   │   │   ├── 📄 antigravity_canvas.js
│   │   │   ├── 📄 chart_engine.js
│   │   │   ├── 📄 client_app.js
│   │   │   ├── 📄 cultivation_animation.js
│   │   │   ├── 📄 cultivation_floor.before-animation.js
│   │   │   ├── 📄 cultivation_floor.js
│   │   │   ├── 📄 liquidity_vector_field.js
│   │   │   ├── 📄 nro_pixel_engine.js
│   │   │   ├── 📄 OrbitControls.js
│   │   │   ├── 📄 orchestration.js
│   │   │   ├── 📄 performance_app.js
│   │   │   ├── 📄 performance_app.js.bak_tabs
│   │   │   ├── 📄 pixel_floor.js
│   │   │   ├── 📄 pixel_floor.js.bak_master
│   │   │   ├── 📄 pixel_floor.js.bak_megacity
│   │   │   ├── 📄 pixel_floor.js.bak_tpp_fix
│   │   │   ├── 📄 pixel_floor.js.bak_ui_redesign
│   │   │   ├── 📄 portal_dashboard.js
│   │   │   ├── 📄 quantum_engine.js
│   │   │   ├── 📄 theme.js
│   │   │   ├── 📄 three.min.js
│   │   │   ├── 📄 three_world_engine.js
│   │   ├── 📁 vendor/
│   │   │   ├── 📄 OrbitControls.js
│   │   │   ├── 📄 three.min.js
│   │   │   ├── 📄 tween.umd.js
│   │   ├── 📄 favicon.svg
│   ├── 📁 templates/
│   │   ├── 📁 admin/
│   │   │   ├── 📄 ai_orchestration.html
│   │   │   ├── 📄 antigravity_canvas.html
│   │   │   ├── 📄 audit_logs.html
│   │   │   ├── 📄 campaign.html
│   │   │   ├── 📄 clients.html
│   │   │   ├── 📄 cockpit.html
│   │   │   ├── 📄 lessons.html
│   │   │   ├── 📄 login.html
│   │   │   ├── 📄 mkt_floor.html
│   │   │   ├── 📄 performance.html
│   │   │   ├── 📄 performance.html.bak_tabs
│   │   │   ├── 📄 pixel_floor.html
│   │   │   ├── 📄 pixel_floor.html.bak_master
│   │   │   ├── 📄 pixel_floor.html.bak_ui_redesign
│   │   │   ├── 📄 quantum_cockpit.html
│   │   │   ├── 📄 research_lab.html
│   │   │   ├── 📄 settings.html
│   │   │   ├── 📄 settings.html.bak_dual_pages
│   │   │   ├── 📄 trade_analysis.html
│   │   │   ├── 📄 trader_demo.html
│   │   │   ├── 📄 trades_history.html
│   │   │   ├── 📄 workflows.html
│   │   ├── 📁 client/
│   │   │   ├── 📄 home.html
│   │   │   ├── 📄 home.html.bak_audit
│   │   │   ├── 📄 portal_api_settings.html
│   │   │   ├── 📄 portal_dashboard.html
│   │   │   ├── 📄 portal_dashboard.html.bak_portal_redesign
│   │   │   ├── 📄 portal_login.html
│   │   │   ├── 📄 portal_login.html.bak_audit
│   │   │   ├── 📄 portal_register.html
│   │   │   ├── 📄 portal_register.html.bak_audit
│   │   │   ├── 📄 privacy.html
│   │   │   ├── 📄 privacy.html.bak_audit
│   │   │   ├── 📄 risk_warning.html
│   │   │   ├── 📄 risk_warning.html.bak_audit
│   │   │   ├── 📄 terms.html
│   │   │   ├── 📄 terms.html.bak_audit
│   │   │   ├── 📄 track_record.html
│   │   ├── 📁 layouts/
│   │   │   ├── 📄 admin_base.html
│   │   │   ├── 📄 base.html
│   │   │   ├── 📄 portal_base.html
│   ├── 📄 __init__.py
│   ├── 📄 app.py
├── 📄 .env.example
├── 📄 .gitignore
├── 📄 =
├── 📄 AGENTS.md
├── 📄 debug_pf.html
├── 📄 main.py  -> Điểm khởi động hệ thống giao dịch, quản lý EventBus, Web Server và tác vụ nền
├── 📄 pytest.ini  -> Cấu hình thực thi bộ kiểm thử PyTest (asyncio mode auto, pythonpath)
├── 📄 RELEASE_MANIFEST.json  -> Tập tin kê khai các phiên bản phát hành và mốc kiểm định an toàn
├── 📄 requirements.txt  -> Khai báo các thư viện phụ thuộc của Python (CCXT, FastAPI, Pandas, DuckDB...)
├── 📄 scratch_grok_eval.txt
├── 📄 setup_npm.py
├── 📄 SYSTEM_ARCHITECTURE_MANUAL.md  -> Sổ tay kiến trúc hệ thống và hướng dẫn vận hành phiên bản 3.0
├── 📄 tiktok_comments_digest.md
├── 📄 trading_bot.db  -> Cơ sở dữ liệu SQLite sản xuất (ACID Primary Storage)
├── 📄 trading_bot_schema.sql  -> Tệp định nghĩa cấu trúc cơ sở dữ liệu SQLite ban đầu (DDL schema)
```
