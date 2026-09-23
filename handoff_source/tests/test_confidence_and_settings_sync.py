import asyncio
from datetime import datetime, timezone
import httpx
import pytest
import aiosqlite
import pandas as pd

from config.settings import settings
from core.constants import MarketRegime, OrderSide
from core.events import AIAdvisoryEvent, SignalEvent
from core.event_bus import EventBus
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
from risk_engine.risk_manager import RiskManager
from ai_advisory.regime_classifier import MarketRegimeClassifier
from web.app import create_web_app


@pytest.mark.asyncio
async def test_confidence_storage_and_status_endpoint(tmp_path):
    """
    Verifies:
    1. save_ai_advisory persists confidence into SQLite.
    2. get_latest_ai_advisory retrieves confidence.
    3. GET /api/v1/status exposes confidence in latest_ai_advisory.
    """
    db_file = str(tmp_path / "test_confidence.db")
    db = Database(db_file)
    await db.connect()

    cb = CircuitBreaker()
    app = create_web_app(db=db, circuit_breaker=cb)

    now = datetime.now(timezone.utc)
    # Save advisory with confidence 0.85
    await db.save_ai_advisory(
        symbol="BTC/USDT",
        regime="bull_trend",
        risk_score=2,
        trade_allowed=True,
        size_multiplier=0.9,
        reasoning="Strong upward momentum confirmed",
        dt=now,
        confidence=0.85
    )

    # 1. Direct query from DB
    latest = await db.get_latest_ai_advisory("BTC/USDT")
    assert latest is not None
    assert "confidence" in latest
    assert latest["confidence"] == pytest.approx(0.85)

    # 2. Query through GET /api/v1/status
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/status")
        assert res.status_code == 200
        data = res.json()
        assert "latest_ai_advisory" in data
        ai = data["latest_ai_advisory"]
        assert ai is not None
        assert "confidence" in ai
        assert ai["confidence"] == pytest.approx(0.85)
        assert ai["regime"] == "bull_trend"
        assert ai["risk_score"] == 2
        assert ai["trade_allowed"] == 1

    await db.close()


@pytest.mark.asyncio
async def test_safe_schema_migration_for_existing_db(tmp_path):
    """
    Verifies that an existing database without confidence column
    is safely upgraded via ALTER TABLE in _init_schema.
    """
    db_file = str(tmp_path / "test_migration.db")
    # Manually create legacy schema without confidence column
    async with aiosqlite.connect(db_file) as conn:
        await conn.execute("""
            CREATE TABLE ai_advisory_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                regime TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                trade_allowed INTEGER NOT NULL,
                size_multiplier REAL NOT NULL,
                reasoning TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        await conn.execute("""
            INSERT INTO ai_advisory_logs (symbol, regime, risk_score, trade_allowed, size_multiplier, reasoning, timestamp)
            VALUES ('BTC/USDT', 'ranging', 3, 1, 1.0, 'Legacy entry', '2026-09-17T00:00:00Z')
        """)
        await conn.commit()

    # Now open with Database class which runs _init_schema with migration
    db = Database(db_file)
    await db.connect()

    # Verify legacy entry gets default confidence 1.0
    legacy = await db.get_latest_ai_advisory("BTC/USDT")
    assert legacy is not None
    assert "confidence" in legacy
    assert legacy["confidence"] == pytest.approx(1.0)

    # Save new record with custom confidence
    now = datetime.now(timezone.utc)
    await db.save_ai_advisory(
        symbol="BTC/USDT",
        regime="bull_trend",
        risk_score=1,
        trade_allowed=True,
        size_multiplier=1.0,
        reasoning="Post migration entry",
        dt=now,
        confidence=0.92
    )

    updated = await db.get_latest_ai_advisory("BTC/USDT")
    assert updated["confidence"] == pytest.approx(0.92)

    await db.close()


@pytest.mark.asyncio
async def test_risk_manager_propagates_confidence(tmp_path):
    """
    Verifies RiskManager extracts confidence from AI decision,
    passes it to AIAdvisoryEvent, and persists it into Database.
    """
    db_file = str(tmp_path / "test_rm_confidence.db")
    db = Database(db_file)
    await db.connect()

    event_bus = EventBus()
    event_bus.start()
    cb = CircuitBreaker()

    class MockVyceClientConfidence:
        async def evaluate_signal_veto(self, signal, market_context):
            return {
                "approved": True,
                "regime": "BULL_TREND",
                "risk_score": 2,
                "confidence": 0.88,
                "size_multiplier": 0.8,
                "reasoning": "Strong trend confidence",
                "model": "claude-sonnet-4-6",
                "fallback_used": False
            }

    rm = RiskManager(
        event_bus=event_bus,
        circuit_breaker=cb,
        db=db,
        vyce_client=MockVyceClientConfidence()
    )

    received_events = []
    async def capture_event(ev):
        received_events.append(ev)

    event_bus.subscribe(AIAdvisoryEvent, capture_event)

    sig = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        timestamp=datetime.now(timezone.utc),
        confidence=1.0
    )

    order = await rm.handle_signal(sig)
    assert order is not None

    # Verify latest_ai_advisory on RiskManager
    assert rm.latest_ai_advisory is not None
    assert rm.latest_ai_advisory.confidence == pytest.approx(0.88)

    # Allow event bus to deliver event
    await asyncio.sleep(0.05)
    assert len(received_events) >= 1
    assert received_events[-1].confidence == pytest.approx(0.88)

    # Verify database persistence
    db_record = await db.get_latest_ai_advisory("BTC/USDT")
    assert db_record is not None
    assert db_record["confidence"] == pytest.approx(0.88)

    await event_bus.stop()
    await db.close()


@pytest.mark.asyncio
async def test_regime_classifier_propagates_confidence(tmp_path, monkeypatch):
    """
    Verifies MarketRegimeClassifier evaluates market, extracts confidence,
    persists it into Database, and publishes AIAdvisoryEvent.
    """
    db_file = str(tmp_path / "test_regime_confidence.db")
    db = Database(db_file)
    await db.connect()

    event_bus = EventBus()
    event_bus.start()

    monkeypatch.setattr(settings, "ENABLE_AI_ADVISORY", True)

    class MockVyceClientRegime:
        async def chat_completion(self, system_prompt: str, user_content: str) -> str:
            return '{"regime": "bull_trend", "risk_score": 2, "trade_allowed": true, "size_multiplier": 0.9, "reasoning": "High confidence trend", "confidence": 0.95}'

    classifier = MarketRegimeClassifier(event_bus, db, client=MockVyceClientRegime())

    df = pd.DataFrame({
        "close": [50000 + i * 50 for i in range(20)],
        "volume": [100.0] * 20
    })

    # Test via evaluate_market
    advisory = await classifier.evaluate_market(df, "BTC/USDT")
    assert advisory.confidence == pytest.approx(0.95)

    db_record = await db.get_latest_ai_advisory("BTC/USDT")
    assert db_record is not None
    assert db_record["confidence"] == pytest.approx(0.95)

    # Test via classify_and_broadcast alias
    advisory_alias = await classifier.classify_and_broadcast(df, "BTC/USDT")
    assert advisory_alias.confidence == pytest.approx(0.95)

    await event_bus.stop()
    await db.close()


@pytest.mark.asyncio
async def test_startup_settings_sync_restores_vyce_model_and_timeout(tmp_path, monkeypatch):
    """
    Verifies that main.py startup synchronization loop restores
    VYCE_MODEL and AI_TIMEOUT_SECONDS from SQLite.
    """
    db_file = str(tmp_path / "test_sync.db")
    db = Database(db_file)
    await db.connect()

    # Save custom VYCE_MODEL and AI_TIMEOUT_SECONDS to SQLite
    await db.set_setting("VYCE_MODEL", "claude-sonnet-custom-v2", "string", "Custom model")
    await db.set_setting("AI_TIMEOUT_SECONDS", "4.2", "float", "Custom timeout")

    cb = CircuitBreaker()

    # Simulate startup loop from main.py
    db_settings = await db.get_all_settings()
    for s in db_settings:
        k, v = s["key"], s["value"]
        if k == "TRADING_MODE": settings.TRADING_MODE = v
        elif k == "SYMBOL": settings.SYMBOL = v
        elif k == "TIMEFRAME": settings.TIMEFRAME = v
        elif k == "DAILY_MAX_DRAWDOWN_PERCENT":
            settings.DAILY_MAX_DRAWDOWN_PERCENT = float(v)
            cb.max_daily_drawdown = float(v)
        elif k == "ENABLE_AI_ADVISORY":
            settings.ENABLE_AI_ADVISORY = v.lower() in ("true", "1")
        elif k == "VYCE_MODEL":
            settings.VYCE_MODEL = str(v)
        elif k == "AI_TIMEOUT_SECONDS":
            settings.AI_TIMEOUT_SECONDS = float(v)

    assert settings.VYCE_MODEL == "claude-sonnet-custom-v2"
    assert settings.AI_TIMEOUT_SECONDS == pytest.approx(4.2)

    # Reset back to default
    settings.VYCE_MODEL = "claude-sonnet-4-6"
    settings.AI_TIMEOUT_SECONDS = 3.0

    await db.close()
