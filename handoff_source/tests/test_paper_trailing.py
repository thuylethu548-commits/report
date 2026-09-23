import pytest
import asyncio
from datetime import datetime, timezone
from core.event_bus import EventBus
from core.events import OrderEvent, MarketEvent, TrailingStopEvent
from core.constants import OrderSide, OrderType, OrderStatus
from config.settings import settings
from execution.paper_trader import PaperTrader
from risk_engine.circuit_breaker import CircuitBreaker
from data.storage import Database


@pytest.mark.asyncio
async def test_paper_trader_trailing_and_break_even(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "TRADING_MODE", "paper")
    monkeypatch.setattr(settings, "MARKET_TYPE", "spot")
    db_path = str(tmp_path / "test_paper_ts.db")
    db = Database(db_path)
    await db.connect()

    event_bus = EventBus()
    event_bus.start()

    cb = CircuitBreaker(max_daily_drawdown_percent=5.0)
    cb.reset_daily_metrics(1000.0)

    audit_logs = []
    paper = PaperTrader(event_bus, db, cb, audit_logs=audit_logs)
    paper.balance_usdt = 1000.0

    trailing_events = []
    async def on_ts_event(evt: TrailingStopEvent):
        trailing_events.append(evt)

    event_bus.subscribe(TrailingStopEvent, on_ts_event)

    # 1. Simulate BUY order execution at 10,000
    buy_order = OrderEvent(
        order_id="ts_ord_1",
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.01,
        price=10000.0,
        stop_loss=9800.0,
        take_profit=11000.0,
        timestamp=datetime.now(timezone.utc),
        status=OrderStatus.PENDING
    )
    await paper.handle_order(buy_order)

    pos_key = "EMA_Trend_BTC/USDT"
    assert pos_key in paper.open_positions
    pos = paper.open_positions[pos_key]
    assert pos["stop_loss"] == 9800.0
    entry_price = pos["entry_price"]

    # 2. Market price rises +1.3% (Break-even should trigger at +1.2%)
    be_price = round(entry_price * 1.013, 2)
    market_event_be = MarketEvent(
        symbol="BTC/USDT",
        timestamp=datetime.now(timezone.utc),
        open=entry_price,
        high=be_price,
        low=entry_price,
        close=be_price,
        volume=10.0
    )
    await paper.handle_market_tick(market_event_be)
    await asyncio.sleep(0.05)

    # Stop Loss should have moved to Entry * 1.002
    expected_be_sl = round(entry_price * 1.002, 2)
    assert pos["stop_loss"] == expected_be_sl
    assert len(trailing_events) >= 1
    assert trailing_events[0].action == "BREAK_EVEN_LOCK"

    # 3. Market price shoots up +3.0% (Trailing stop should trigger at +2.0%)
    high_price = round(entry_price * 1.030, 2)
    market_event_trail = MarketEvent(
        symbol="BTC/USDT",
        timestamp=datetime.now(timezone.utc),
        open=be_price,
        high=high_price,
        low=be_price,
        close=high_price,
        volume=10.0
    )
    await paper.handle_market_tick(market_event_trail)
    await asyncio.sleep(0.05)

    # Stop loss should be advanced higher than break-even
    assert pos["stop_loss"] > expected_be_sl
    assert any(e.action == "TRAILING_STOP_ADVANCE" for e in trailing_events)

    await event_bus.stop()
    await db.close()
