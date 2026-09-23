import pytest
from datetime import datetime, timezone
from core.constants import OrderSide
from execution.trailing_stop import TrailingStopManager
from data.websocket_feed import BinanceWebSocketFeed
from data.binance_client import BinanceClient


def test_trailing_stop_short_break_even():
    mgr = TrailingStopManager()
    state = mgr.register_position(
        order_id="TEST-SHORT-BE-001",
        symbol="BTC/USDT",
        side=OrderSide.SELL,
        entry_price=60000.0,
        initial_stop_loss=61000.0,
        initial_take_profit=57000.0,
        quantity=0.01,
        break_even_threshold_pct=0.012
    )

    # 1. Price drops -0.5% (59700) -> Break-even should NOT trigger
    res1 = mgr.update_price("TEST-SHORT-BE-001", current_price=59700.0)
    assert res1 is None
    assert state.break_even_triggered is False
    assert state.current_stop_loss == 61000.0

    # 2. Price drops -1.3% (59220) -> Break-even SHOULD trigger for SHORT
    res2 = mgr.update_price("TEST-SHORT-BE-001", current_price=59220.0)
    assert res2 is not None
    assert res2["action"] == "BREAK_EVEN_LOCK"
    expected_sl = round(60000.0 * 0.998, 2)  # 59880.0
    assert res2["new_sl"] == expected_sl
    assert state.break_even_triggered is True
    assert state.current_stop_loss == expected_sl


def test_dynamic_trailing_stop_short_advancement():
    mgr = TrailingStopManager()
    state = mgr.register_position(
        order_id="TEST-SHORT-TS-002",
        symbol="ETH/USDT",
        side=OrderSide.SELL,
        entry_price=3000.0,
        initial_stop_loss=3060.0,
        initial_take_profit=2700.0,
        quantity=0.1,
        trailing_activation_pct=0.020,  # 2.0%
        atr_multiplier=1.0
    )

    # 1. Price drops to -2.5% (2925.0), with ATR = 20
    res = mgr.update_price("TEST-SHORT-TS-002", current_price=2925.0, current_atr=20.0)
    assert res is not None
    assert res["action"] == "TRAILING_STOP_ADVANCE"
    # Candidate SL for short = 2925 + 20 = 2945 < 3060
    assert state.current_stop_loss == 2945.0
    assert res["new_sl"] == 2945.0

    # 2. Price drops further to 2900.0
    res2 = mgr.update_price("TEST-SHORT-TS-002", current_price=2900.0, current_atr=20.0)
    assert res2 is not None
    # Candidate SL = 2900 + 20 = 2920 < 2945
    assert state.current_stop_loss == 2920.0
    assert res2["new_sl"] == 2920.0


def test_websocket_feed_combined_streams():
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
    feed = BinanceWebSocketFeed(event_bus=None, db=None, symbols=symbols)
    assert "stream?streams=" in feed.ws_url
    assert "btcusdt@kline_15m" in feed.ws_url
    assert "ethusdt@kline_15m" in feed.ws_url
    assert "solusdt@kline_15m" in feed.ws_url
    assert "bnbusdt@kline_15m" in feed.ws_url
    assert feed.symbol_map["BTCUSDT"] == "BTC/USDT"
    assert feed.symbol_map["ETHUSDT"] == "ETH/USDT"
    assert feed.symbol_map["SOLUSDT"] == "SOL/USDT"
    assert feed.symbol_map["BNBUSDT"] == "BNB/USDT"


@pytest.mark.asyncio
async def test_binance_client_check_connection():
    client = BinanceClient(api_key="mock_key", secret="mock_secret", market_type="futures", use_testnet=True)
    assert client.market_type == "futures"
    res = await client.check_connection()
    assert "connected" in res
    await client.close()
