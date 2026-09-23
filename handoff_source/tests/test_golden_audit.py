import pytest
import pytest_asyncio
import os
from datetime import datetime, timezone
from data.storage import Database
from core.campaign_monitor import CampaignMonitor
from core.events import SignalEvent
from core.event_bus import EventBus
from core.constants import OrderSide
from risk_engine.circuit_breaker import CircuitBreaker
from risk_engine.risk_manager import RiskManager
from config.settings import settings


@pytest_asyncio.fixture
async def setup_test_db(tmp_path):
    db_path = str(tmp_path / "test_campaign.db")
    db = Database(db_path)
    await db.connect()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_golden_audit_crud_and_outcome_update(setup_test_db):
    db = setup_test_db
    order_id = "test-ord-001"
    symbol = "BTC/USDT"
    side = "BUY"
    strategy = "EMA_Trend"

    # 1. Save Golden Audit
    await db.save_golden_audit(
        order_id=order_id,
        symbol=symbol,
        side=side,
        strategy_name=strategy,
        why_trade="Bullish breakout with EMA 20/50 confirmation",
        why_asset="BTC has highest liquidity and clear trend structure",
        why_direction="BUY following 4H macro trend",
        why_now="15m candle close confirmed breakout above resistance",
        evidence="RSI=58, MTF EMA=Bullish, ADX=28",
        what_could_go_wrong="Sudden liquidity dump or whale sell wall",
        opposing_argument="Bear Agent flagged 4H resistance at 62k",
        opposing_verdict_reason="Tight SL (1.8%) and R:R 1:2.5 justify the risk",
        max_risk_usdt=0.90,
        what_actually_happened="Order active on exchange"
    )

    # 2. Fetch and assert
    audit = await db.get_golden_audit(order_id)
    assert audit is not None
    assert audit["order_id"] == order_id
    assert audit["symbol"] == symbol
    assert audit["max_risk_usdt"] == 0.90
    assert "Bullish breakout" in audit["why_trade"]
    assert "Bear Agent flagged" in audit["opposing_argument"]

    # 3. Update outcome (Question 10)
    await db.update_golden_audit_outcome(
        order_id=order_id,
        what_actually_happened="Take Profit hit at $62,000 (+3.5%). PnL +$1.25 USDT."
    )

    updated = await db.get_golden_audit(order_id)
    assert "Take Profit hit" in updated["what_actually_happened"]

    # 4. List recent audits
    audits = await db.get_recent_golden_audits(limit=10)
    assert len(audits) >= 1
    assert audits[0]["order_id"] == order_id


@pytest.mark.asyncio
async def test_campaign_monitor_metrics_and_daily_report(setup_test_db):
    db = setup_test_db

    # Record mock trade
    now = datetime.now(timezone.utc)
    await db.record_trade_open(
        order_id="mock-001",
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side="BUY",
        price=60000.0,
        quantity=0.0002,
        fee=0.01,
        dt=now,
        is_paper=True
    )
    await db.record_trade_close(
        order_id="mock-001",
        exit_price=62000.0,
        fee=0.01,
        exit_time=now,
        pnl_usdt=0.40,
        pnl_percent=3.33
    )

    monitor = CampaignMonitor(db)
    metrics = await monitor.get_campaign_metrics()

    assert metrics["campaign_name"] == "7-DAY ADAPTIVE TRADING TEST"
    assert metrics["initial_capital_usdt"] == 55.0
    assert metrics["closed_trades"] == 1
    assert metrics["win_trades"] == 1
    assert metrics["win_rate_percent"] == 100.0
    assert metrics["six_pillars"]["composite_evaluation_score"] > 0

    # Generate daily report
    report_md = await monitor.generate_daily_report()
    assert "BÁO CÁO NGÀY CHIẾN DỊCH" in report_md
    assert "TRADE THE MARKET, NOT THE KPI" in report_md
    assert "6 TRỤ CỘT" in report_md


@pytest.mark.asyncio
async def test_risk_manager_saves_golden_audit_on_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MAX_POSITION_PERCENT", 0.20)
    monkeypatch.setattr(settings, "MAX_OPEN_POSITIONS", 3)
    monkeypatch.setattr(settings, "STARTING_BALANCE_USDT", 100.0)

    db_path = str(tmp_path / "test_rm_golden.db")
    db = Database(db_path)
    await db.connect()
    event_bus = EventBus()
    event_bus.start()
    cb = CircuitBreaker(max_daily_drawdown_percent=0.02)
    cb.reset_daily_metrics(100.0)

    class NeutralTimeGuard:
        def is_red_flag_window(self, dt=None):
            return False, ""
        def is_golden_window(self, dt=None):
            return False, ""
        def get_window_status(self, dt=None):
            return {"is_red_flag": False, "is_golden_window": False}

    class MockApprovedVyce:
        async def evaluate_signal_veto(self, signal, market_context):
            return {
                "approved": True,
                "regime": "BULL_TREND",
                "risk_score": 1,
                "confidence": 0.92,
                "size_multiplier": 1.0,
                "reasoning": "Golden Cross confirmed by 1h/4h confluence.",
                "model": "claude-sonnet-4-6",
                "opposing_argument": "Slight overbought on 5m",
                "opposing_verdict_reason": "High higher-timeframe momentum dominates"
            }

    rm = RiskManager(event_bus, db, cb, vyce_client=MockApprovedVyce(), time_guard=NeutralTimeGuard())

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=58920.0,
        take_profit=62100.0,
        confidence=0.90
    )

    order = await rm.handle_signal(signal)
    assert order is not None

    # Verify golden audit was saved
    audit = await db.get_golden_audit(order.order_id)
    assert audit is not None
    assert audit["symbol"] == "BTC/USDT"
    assert audit["side"] == "BUY"
    assert "Golden Cross confirmed" in audit["why_trade"]
    assert audit["max_risk_usdt"] > 0
    assert audit["opposing_argument"] == "Slight overbought on 5m"

    await event_bus.stop()
    await db.close()
