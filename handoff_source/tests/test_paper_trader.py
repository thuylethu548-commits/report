import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone
from core.constants import OrderSide, OrderType
from core.events import OrderEvent, MarketEvent
from core.event_bus import EventBus
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
from execution.paper_trader import PaperTrader
from config.settings import settings


@pytest_asyncio.fixture
async def setup_paper(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "TRADING_MODE", "paper")
    monkeypatch.setattr(settings, "MARKET_TYPE", "spot")
    monkeypatch.setattr(settings, "STARTING_BALANCE_USDT", 100.0)
    db_path = str(tmp_path / "test_paper.db")
    db = Database(db_path)
    await db.connect()
    event_bus = EventBus()
    event_bus.start()
    cb = CircuitBreaker(max_daily_drawdown_percent=0.02)
    cb.reset_daily_metrics(100.0)
    pt = PaperTrader(event_bus, db, cb)
    yield db, event_bus, cb, pt
    await event_bus.stop()
    await db.close()


@pytest.mark.asyncio
async def test_paper_trader_execution_and_tp(setup_paper):
    db, event_bus, cb, pt = setup_paper

    # Initial balance $100
    assert pt.balance_usdt == 100.0

    # Submit BUY order: 0.001 BTC @ $60,000 (~$60 cost)
    order = OrderEvent(
        order_id="test_ord_1",
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.001,
        price=60000.0,
        stop_loss=58000.0,
        take_profit=63000.0,
        timestamp=datetime.now(timezone.utc)
    )
    await pt.handle_order(order)

    # Balance should be deducted (~$100 - $60 - fee)
    assert pt.balance_usdt < 45.0
    assert pt.base_asset_balance == 0.001
    assert "EMA_Trend_BTC/USDT" in pt.open_positions

    # Send Market tick hitting Take-Profit ($64,000 > $63,000)
    market_tick = MarketEvent(
        symbol="BTC/USDT",
        timestamp=datetime.now(timezone.utc),
        open=63500.0,
        high=64000.0,
        low=63000.0,
        close=64000.0,
        volume=10.0,
        is_candle_closed=True
    )
    await pt.handle_market_tick(market_tick)

    # Position should be closed with profit!
    assert "EMA_Trend_BTC/USDT" not in pt.open_positions
    assert pt.base_asset_balance == 0.0
    # Profit was ~$4, so balance should now be around ~$103+
    assert pt.balance_usdt > 102.0
