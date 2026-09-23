import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from core.backtest_engine import BacktestEngine
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
from core.event_bus import EventBus
from web.app import create_web_app
from httpx import AsyncClient, ASGITransport


def generate_synthetic_candles(count=100, trend="bull"):
    now = datetime.now(timezone.utc)
    base_price = 50000.0
    candles = []
    for i in range(count):
        t = now - timedelta(minutes=15 * (count - i))
        if trend == "bull":
            price = base_price + i * 50.0 + (5.0 if i % 2 == 0 else -5.0)
        else:
            price = base_price - i * 50.0 + (5.0 if i % 2 == 0 else -5.0)
        candles.append([
            int(t.timestamp() * 1000),
            price - 10,
            price + 25,
            price - 15,
            price,
            100.0 + (i % 10) * 10
        ])
    return candles


class MockBinanceClient:
    async def fetch_ohlcv(self, symbol="BTC/USDT", timeframe="15m", limit=100):
        return generate_synthetic_candles(count=min(limit, 100), trend="bull")

    async def close(self):
        pass


@pytest.fixture
async def test_db(tmp_path):
    db_file = str(tmp_path / "test_bt.db")
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


@pytest.mark.asyncio
async def test_backtest_engine_compute_indicators():
    engine = BacktestEngine(candle_limit=60, binance_client=MockBinanceClient())
    df = await engine.fetch_historical_data()
    assert len(df) == 60

    df_ind = engine.compute_indicators(df)
    assert "ema_20" in df_ind.columns
    assert "ema_50" in df_ind.columns
    assert "rsi" in df_ind.columns
    assert "bb_upper" in df_ind.columns
    assert "donchian_high" in df_ind.columns


@pytest.mark.asyncio
async def test_backtest_engine_simulation_execution():
    engine = BacktestEngine(
        symbol="BTC/USDT",
        timeframe="15m",
        strategy="EMA_TREND_MTF",
        initial_balance=100.0,
        leverage=5.0,
        sl_pct=0.015,
        tp_pct=0.030,
        enable_trailing=True,
        candle_limit=100,
        binance_client=MockBinanceClient()
    )
    df = await engine.fetch_historical_data()
    df = engine.compute_indicators(df)
    res = engine.run_simulation(df)

    assert "win_rate" in res
    assert "net_pnl_usdt" in res
    assert "equity_curve" in res
    assert len(res["equity_curve"]) >= 1
    assert "distribution" in res


@pytest.mark.asyncio
async def test_api_backtest_run_endpoint(test_db, circuit_breaker, event_bus, monkeypatch):
    app = create_web_app(
        db=test_db,
        circuit_breaker=circuit_breaker,
        event_bus=event_bus,
        binance_client=MockBinanceClient()
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "symbol": "BTC/USDT",
            "timeframe": "15m",
            "strategy": "EMA_TREND_MTF",
            "candle_limit": 60,
            "initial_balance": 100.0,
            "position_pct": 0.20,
            "leverage": 5.0,
            "sl_pct": 0.015,
            "tp_pct": 0.030,
            "enable_trailing": True
        }
        res = await client.post("/api/v1/backtest/run", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert "data" in data
        assert data["data"]["symbol"] == "BTC/USDT"
        assert "equity_curve" in data["data"]
