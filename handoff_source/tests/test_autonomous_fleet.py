import pytest
import os
import aiohttp
from datetime import datetime, timezone
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
from core.event_bus import EventBus
from core.events import SignalEvent, AIAdvisoryEvent, OrderEvent, MarketEvent
from core.constants import OrderSide, MarketRegime
from core.fleet_manager import AutonomousFleetCoordinator
from web.app import create_web_app
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def test_db(tmp_path):
    db_file = str(tmp_path / "test_fleet.db")
    db = Database(db_path=db_file)
    await db.connect()
    yield db
    await db.close()


@pytest.fixture
def circuit_breaker():
    return CircuitBreaker(max_daily_drawdown_percent=5.0)


@pytest.fixture
async def event_bus():
    eb = EventBus()
    eb.start()
    yield eb
    await eb.stop()


@pytest.fixture
def fleet_coordinator(test_db, circuit_breaker, event_bus):
    return AutonomousFleetCoordinator(
        db=test_db,
        circuit_breaker=circuit_breaker,
        event_bus=event_bus
    )


@pytest.mark.asyncio
async def test_fleet_coordinator_initialization(fleet_coordinator):
    """Verify all 10 canonical agents are registered properly."""
    fleet = await fleet_coordinator.get_fleet_telemetry()
    assert len(fleet) in (10, 12)
    names = [ag["name"] for ag in fleet]
    for expected_name in ["Palermo", "Rik", "Tory", "Hash", "Deck", "Prof", "Meme", "Volt", "Core", "Astra"]:
        assert expected_name in names

    # Check specific agent properties
    astra = next(ag for ag in fleet if ag["name"] == "Astra")
    assert astra["status"] == "SUPERVISING"

    rik = next(ag for ag in fleet if ag["name"] == "Rik")
    assert rik["status"] == "ARMED"

    meme = next(ag for ag in fleet if ag["name"] == "Meme")
    assert meme["status"] == "ONLINE"


@pytest.mark.asyncio
async def test_fleet_debate_and_signal_flow(fleet_coordinator):
    """Verify that signal events and debate logs are captured and retrieved."""
    sig = SignalEvent(
        strategy_name="Astra-Breakout",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=85000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=83725.0,
        take_profit=87550.0,
        confidence=0.88
    )
    await fleet_coordinator.record_signal_event(sig)

    debates = fleet_coordinator.get_debate_logs()
    assert len(debates) > 0
    top = debates[0]
    assert top["from_agent"] == "Tory"
    assert top["action"] == "PROPOSE"
    assert "85000.00" in top["message"]

    # Now simulate AI Advisory
    adv = AIAdvisoryEvent(
        symbol="BTC/USDT",
        timestamp=datetime.now(timezone.utc),
        regime=MarketRegime.BULL_TREND,
        risk_score=1,
        trade_allowed=True,
        size_multiplier=1.0,
        reasoning="Macro trend strongly bullish with surging volume",
        confidence=0.92
    )
    await fleet_coordinator.record_ai_advisory_event(adv)
    debates = fleet_coordinator.get_debate_logs()
    top = debates[0]
    assert top["from_agent"] == "Astra"
    assert top["action"] == "APPROVE"


@pytest.mark.asyncio
async def test_api_fleet_and_quantum_telemetry(test_db, circuit_breaker, event_bus, fleet_coordinator):
    """Verify FastAPI routes for /api/v1/fleet and /api/v1/quantum/telemetry."""
    app = create_web_app(
        db=test_db,
        circuit_breaker=circuit_breaker,
        event_bus=event_bus,
        fleet_coordinator=fleet_coordinator
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. /api/v1/fleet
        res_fleet = await client.get("/api/v1/fleet")
        assert res_fleet.status_code == 200
        fleet_data = res_fleet.json()
        assert len(fleet_data) in (10, 12)
        assert any(ag["name"] == "Astra" for ag in fleet_data)

        # 2. /api/v1/quantum/telemetry
        res_telemetry = await client.get("/api/v1/quantum/telemetry")
        assert res_telemetry.status_code == 200
        tele_data = res_telemetry.json()
        assert "fleet" in tele_data
        assert len(tele_data["fleet"]) in (10, 12)
        assert "debate_logs" in tele_data
        assert "handoff_chord" in tele_data
        assert "mission_clock" in tele_data

        # 3. /api/v1/quantum/fleet_live
        res_live = await client.get("/api/v1/quantum/fleet_live")
        assert res_live.status_code == 200
        live_data = res_live.json()
        assert live_data["status"] == "SUCCESS"
        assert live_data["active_count"] in (10, 12)
