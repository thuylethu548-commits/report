import pytest
import asyncio
from datetime import datetime, timezone
from core.constants import OrderSide, MarketRegime
from core.events import SignalEvent
from core.event_bus import EventBus
from strategies.multi_timeframe import MultiTimeframeFilter
from risk_engine.risk_manager import RiskManager
from risk_engine.circuit_breaker import CircuitBreaker
from data.storage import Database


def create_synthetic_candles(base_price: float, count: int = 60, trend: float = 0.0):
    candles = []
    for i in range(count):
        price = base_price + (i * trend)
        candles.append([
            1700000000000 + (i * 3600000),
            price - 5.0,
            price + 10.0,
            price - 10.0,
            price,
            100.0
        ])
    return candles


def test_mtf_ema_and_confluence():
    mtf = MultiTimeframeFilter(ema_period=50)

    # 1. Feed 60 candles around 50,000 for 1h and 4h
    candles_1h = create_synthetic_candles(50000.0, count=60, trend=10.0)  # EMA ~ 50300
    candles_4h = create_synthetic_candles(49000.0, count=60, trend=20.0)  # EMA ~ 49600

    mtf.set_candles("1h", candles_1h)
    mtf.set_candles("4h", candles_4h)

    ema_1h = mtf.calculate_ema("1h")
    ema_4h = mtf.calculate_ema("4h")

    assert ema_1h is not None and ema_1h > 50000.0
    assert ema_4h is not None and ema_4h > 49000.0

    # Test Bullish Confluence: Price is 51,500 (above both 1h and 4h EMA)
    res_bull = mtf.check_confluence("BTC/USDT", 51500.0)
    assert res_bull["approved"] is True
    assert res_bull["trend_1h"] == "BULLISH"
    assert res_bull["trend_4h"] == "BULLISH"

    # Test Bearish Veto: Price is 48,000 (below both)
    res_bear = mtf.check_confluence("BTC/USDT", 48000.0)
    assert res_bear["approved"] is False
    assert res_bear["trend_1h"] == "BEARISH"
    assert res_bear["trend_4h"] == "BEARISH"
    assert "Phủ quyết" in res_bear["reason"]


@pytest.mark.asyncio
async def test_risk_manager_mtf_veto_integration(tmp_path):
    db_path = str(tmp_path / "test_mtf_risk.db")
    db = Database(db_path)
    await db.connect()

    event_bus = EventBus()
    event_bus.start()

    cb = CircuitBreaker(max_daily_drawdown_percent=5.0)
    cb.reset_daily_metrics(1000.0)

    mtf = MultiTimeframeFilter(ema_period=50)
    # EMA 1h ~ 50,000; EMA 4h ~ 50,000
    candles = create_synthetic_candles(50000.0, count=60)
    mtf.set_candles("1h", candles)
    mtf.set_candles("4h", candles)

    audit_logs = []
    risk = RiskManager(event_bus, db, cb, audit_logs=audit_logs, mtf_filter=mtf)

    # 1. Signal at 45,000 (Downtrend below EMA 50,000) -> Should be VETOED by MTF
    bear_signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=45000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=44000.0,
        take_profit=48000.0,
        confidence=0.85
    )
    order_bear = await risk.handle_signal(bear_signal)
    assert order_bear is None  # Vetoed!
    assert any("MTF Veto" in log["msg"] for log in audit_logs)

    # 2. Signal at 55,000 (Uptrend above EMA 50,000) -> Should PASS MTF check
    # Disable AI advisory for pure MTF test
    from config.settings import settings
    orig_ai = settings.ENABLE_AI_ADVISORY
    settings.ENABLE_AI_ADVISORY = False
    try:
        bull_signal = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=55000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=54000.0,
            take_profit=58000.0,
            confidence=0.85
        )
        order_bull = await risk.handle_signal(bull_signal)
        assert order_bull is not None
        assert order_bull.price == 55000.0
    finally:
        settings.ENABLE_AI_ADVISORY = orig_ai
        await event_bus.stop()
        await db.close()
