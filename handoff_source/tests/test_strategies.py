import pytest
from datetime import datetime, timezone
from core.constants import OrderSide
from core.events import MarketEvent
from core.event_bus import EventBus
from strategies.ema_trend import EMATrendStrategy
from strategies.rsi_bollinger import RSIBollingerStrategy


@pytest.mark.asyncio
async def test_ema_trend_strategy_warmup_and_golden_cross():
    event_bus = EventBus()
    strategy = EMATrendStrategy(symbol="BTC/USDT", event_bus=event_bus, fast_period=3, slow_period=5, atr_period=3)

    # Feed 10 declining candles then 5 sharp rising candles to trigger golden cross
    prices = [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 95, 102, 110, 120]
    last_signal = None
    for i, p in enumerate(prices):
        event = MarketEvent(
            symbol="BTC/USDT",
            timestamp=datetime.now(timezone.utc),
            open=p - 1,
            high=p + 1,
            low=p - 2,
            close=p,
            volume=50.0,
            is_candle_closed=True
        )
        sig = await strategy.on_market_event(event)
        if sig:
            last_signal = sig

    assert last_signal is not None
    assert last_signal.side == OrderSide.BUY
    assert last_signal.stop_loss < last_signal.price
    assert last_signal.take_profit > last_signal.price


@pytest.mark.asyncio
async def test_rsi_bollinger_strategy_oversold():
    event_bus = EventBus()
    strategy = RSIBollingerStrategy(symbol="BTC/USDT", event_bus=event_bus, bb_period=5, rsi_period=5)

    # Feed 10 flat candles then sharp crash to trigger oversold
    prices = [100, 100, 100, 100, 100, 100, 100, 90, 75, 60]
    last_signal = None
    for p in prices:
        event = MarketEvent(
            symbol="BTC/USDT",
            timestamp=datetime.now(timezone.utc),
            open=p + 1,
            high=p + 2,
            low=p - 2,
            close=p,
            volume=100.0,
            is_candle_closed=True
        )
        sig = await strategy.on_market_event(event)
        if sig:
            last_signal = sig

    assert last_signal is not None
    assert last_signal.side == OrderSide.BUY
    assert last_signal.stop_loss < last_signal.price


@pytest.mark.asyncio
async def test_ema_trend_pullback_continuation():
    event_bus = EventBus()
    strategy = EMATrendStrategy(symbol="ETH/USDT", event_bus=event_bus, fast_period=3, slow_period=6, atr_period=3)

    # Establish an uptrend where fast > slow
    prices = [100, 105, 110, 115, 120, 125, 130]
    for p in prices:
        event = MarketEvent(
            symbol="ETH/USDT",
            timestamp=datetime.now(timezone.utc),
            open=p - 2,
            high=p + 2,
            low=p - 3,
            close=p,
            volume=100.0,
            is_candle_closed=True
        )
        await strategy.on_market_event(event)

    # Reset position side to simulate having flat position and waiting for pullback
    strategy.position_side = None
    strategy.last_signal_candle = 0

    # Pullback candle: dip close to EMA then bounce green
    dip_event = MarketEvent(
        symbol="ETH/USDT",
        timestamp=datetime.now(timezone.utc),
        open=122,
        high=131,
        low=120,  # dips deep near fast EMA
        close=128,  # bounces green close > open
        volume=120.0,
        is_candle_closed=True
    )
    sig = await strategy.on_market_event(dip_event)
    assert sig is not None
    assert sig.side == OrderSide.BUY
    assert sig.stop_loss < sig.price
    assert sig.take_profit > sig.price


@pytest.mark.asyncio
async def test_rsi_bollinger_extreme_oversold():
    event_bus = EventBus()
    strategy = RSIBollingerStrategy(symbol="SOL/USDT", event_bus=event_bus, bb_period=5, rsi_period=5)

    # Crash price so RSI <= 30
    prices = [100, 95, 90, 80, 70, 60, 50]
    last_signal = None
    for p in prices:
        event = MarketEvent(
            symbol="SOL/USDT",
            timestamp=datetime.now(timezone.utc),
            open=p + 2,
            high=p + 3,
            low=p - 2,
            close=p,
            volume=200.0,
            is_candle_closed=True
        )
        sig = await strategy.on_market_event(event)
        if sig:
            last_signal = sig

    assert last_signal is not None
    assert last_signal.side == OrderSide.BUY

