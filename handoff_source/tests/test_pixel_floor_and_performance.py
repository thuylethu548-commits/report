import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from data.storage import Database
from web.app import create_web_app
from risk_engine.circuit_breaker import CircuitBreaker
from web.routes.admin_routes import get_expected_admin_token


@pytest_asyncio.fixture
async def test_db(tmp_path):
    db_file = str(tmp_path / "test_pixel_perf.db")
    db = Database(db_file)
    await db.connect()
    yield db
    await db.close()


@pytest.fixture
def test_app(test_db):
    cb = CircuitBreaker()
    app = create_web_app(db=test_db, circuit_breaker=cb)
    return app


@pytest.mark.asyncio
async def test_database_agent_telemetry(test_db):
    telemetry = await test_db.get_agent_telemetry_detailed()
    assert "departments" in telemetry
    depts = telemetry["departments"]
    assert len(depts) == 12

    expected_keys = [
        "lead_pm",
        "risk_council",
        "news_scout",
        "quant_lab",
        "breakout_hunter",
        "volatility_lab",
        "execution_oms",
        "spot_dca",
        "arbitrage_desk",
        "accounting_pm",
        "community_affiliate",
        "cvar_stress"
    ]
    for key in expected_keys:
        assert key in depts
        d = depts[key]
        assert "title" in d
        assert "officer" in d
        assert "role" in d
        assert "status" in d
        assert "bubble" in d
        assert "ai_model" in d
        assert "ai_provider" in d


@pytest.mark.asyncio
async def test_database_performance_scorecard(test_db):
    # Record a token usage to verify telemetry integration
    now_str = datetime.now(timezone.utc).isoformat()
    await test_db.record_token_usage(
        model="claude-3-5-sonnet",
        action="TEST_ADVISORY",
        prompt_tokens=150,
        completion_tokens=50,
        total_tokens=200,
        estimated_cost_usd=0.001
    )

    scorecard = await test_db.get_agent_performance_scorecard()
    assert "performance" in scorecard
    assert "veto_protection" in scorecard
    assert "token_telemetry" in scorecard

    perf = scorecard["performance"]
    assert "win_rate_pct" in perf
    assert "total_pnl_usdt" in perf

    veto = scorecard["veto_protection"]
    assert "total_vetoes" in veto
    assert "estimated_saved_usdt" in veto

    token = scorecard["token_telemetry"]
    assert token["total_tokens"] >= 200
    assert token["estimated_cost_usd"] > 0


@pytest.mark.asyncio
async def test_api_telemetry_endpoints(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Pixel Floor Telemetry API
        res_pixel = await client.get("/api/v1/telemetry/pixel-floor")
        assert res_pixel.status_code == 200
        p_json = res_pixel.json()
        assert "departments" in p_json
        assert "balance_usdt" in p_json

        # 2. Performance Telemetry API
        res_perf = await client.get("/api/v1/telemetry/performance")
        assert res_perf.status_code == 200
        score_json = res_perf.json()
        assert "performance" in score_json
        assert "token_telemetry" in score_json


@pytest.mark.asyncio
async def test_admin_routes_auth_and_rendering(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Unauthorized redirection
        res_p_unauth = await client.get("/admin/pixel-floor", follow_redirects=False)
        assert res_p_unauth.status_code == 303
        assert "/admin/login?next=/admin/pixel-floor" in res_p_unauth.headers["location"]

        res_perf_unauth = await client.get("/admin/performance", follow_redirects=False)
        assert res_perf_unauth.status_code == 303
        assert "/admin/login?next=/admin/performance" in res_perf_unauth.headers["location"]

        res_orch_unauth = await client.get("/admin/ai-orchestration", follow_redirects=False)
        assert res_orch_unauth.status_code == 303
        assert "/admin/login?next=/admin/ai-orchestration" in res_orch_unauth.headers["location"]

        # 2. Authorized access with admin cookie
        valid_token = get_expected_admin_token()
        client.cookies.set("admin_session_token", valid_token)

        res_p_auth = await client.get("/admin/pixel-floor")
        assert res_p_auth.status_code == 200
        assert "TRADING FLOOR" in res_p_auth.text.upper()
        assert "Phòng Ban Pixel" in res_p_auth.text

        res_perf_auth = await client.get("/admin/performance")
        assert res_perf_auth.status_code == 200
        assert "HIỆU SUẤT & TOKEN AI" in res_perf_auth.text
        assert "Claude-3.5-Sonnet" in res_perf_auth.text

        res_orch_auth = await client.get("/admin/ai-orchestration")
        assert res_orch_auth.status_code == 200
        assert "Trung Tâm Điều Phối AI" in res_orch_auth.text
        assert "7 Nguồn API" in res_orch_auth.text
        assert "OpenRouter" in res_orch_auth.text
        assert "9Router" in res_orch_auth.text

        res_settings_auth = await client.get("/admin/settings")
        assert res_settings_auth.status_code == 200
        assert "Cài Đặt Giao Dịch Binance" in res_settings_auth.text
        assert "/admin/ai-orchestration" in res_settings_auth.text

        # 3. API endpoint for orchestration overview
        res_orch_api = await client.get("/api/v1/orchestration/overview")
        assert res_orch_api.status_code == 200
        data_orch = res_orch_api.json()
        assert "providers" in data_orch
        assert "overview" in data_orch
        assert data_orch["overview"]["total_providers"] >= 6
