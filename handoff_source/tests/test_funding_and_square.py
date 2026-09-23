import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from risk_engine.funding_sentinel import FundingSentinel
from monitoring.binance_square_publisher import BinanceSquarePublisher
from core.events import SignalEvent
from core.constants import OrderSide
from core.event_bus import EventBus
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
from risk_engine.risk_manager import RiskManager


@pytest.mark.asyncio
async def test_funding_sentinel_normal_rates():
    mock_exchange = MagicMock()
    mock_exchange.fetch_funding_rate.return_value = {"fundingRate": 0.0001}  # 0.01%
    sentinel = FundingSentinel(exchange=mock_exchange)

    rate = await sentinel.get_funding_rate("BTC/USDT")
    assert rate == 0.01

    eval_buy = await sentinel.evaluate_squeeze_risk("BTC/USDT", "BUY")
    assert eval_buy["safe"] is True
    assert eval_buy["warning"] is None

    eval_sell = await sentinel.evaluate_squeeze_risk("BTC/USDT", "SELL")
    assert eval_sell["safe"] is True


@pytest.mark.asyncio
async def test_funding_sentinel_high_long_squeeze():
    mock_exchange = MagicMock()
    # 0.04% funding rate -> retail excessively long
    mock_exchange.fetch_funding_rate.return_value = {"fundingRate": 0.0004}
    sentinel = FundingSentinel(exchange=mock_exchange)

    eval_buy = await sentinel.evaluate_squeeze_risk("BTC/USDT", "BUY")
    assert eval_buy["safe"] is False
    assert eval_buy["warning"] == "HIGH_LONG_SQUEEZE_RISK"
    assert "nguy cơ bẫy Long Squeeze" in eval_buy["reason"]

    # Shorting into a crowded long market is safe from long squeeze
    eval_sell = await sentinel.evaluate_squeeze_risk("BTC/USDT", "SELL")
    assert eval_sell["safe"] is True


@pytest.mark.asyncio
async def test_funding_sentinel_high_short_squeeze():
    mock_exchange = MagicMock()
    # -0.04% funding rate -> retail excessively short
    mock_exchange.fetch_funding_rate.return_value = {"fundingRate": -0.0004}
    sentinel = FundingSentinel(exchange=mock_exchange)

    eval_sell = await sentinel.evaluate_squeeze_risk("BTC/USDT", "SELL")
    assert eval_sell["safe"] is False
    assert eval_sell["warning"] == "HIGH_SHORT_SQUEEZE_RISK"
    assert "nguy cơ Short Squeeze" in eval_sell["reason"]

    eval_buy = await sentinel.evaluate_squeeze_risk("BTC/USDT", "BUY")
    assert eval_buy["safe"] is True


@pytest.mark.asyncio
async def test_risk_manager_vetoes_on_funding_squeeze(tmp_path, monkeypatch):
    from config.settings import settings
    monkeypatch.setattr(settings, "TRADING_MODE", "live")
    monkeypatch.setattr(settings, "ENABLE_TIME_WINDOW_GUARD", False)
    db = Database(str(tmp_path / "test_rm_funding.db"))
    await db.connect()
    event_bus = EventBus()
    cb = CircuitBreaker()

    mock_exchange = MagicMock()
    mock_exchange.fetch_funding_rate.return_value = {"fundingRate": 0.0005}  # 0.05%
    sentinel = FundingSentinel(exchange=mock_exchange)

    audit_logs = []
    rm = RiskManager(
        event_bus=event_bus,
        db=db,
        circuit_breaker=cb,
        funding_sentinel=sentinel,
        audit_logs=audit_logs
    )

    sig = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=76000.0,
        stop_loss=75000.0,
        take_profit=78000.0,
        confidence=0.85,
        timestamp=datetime.now(timezone.utc)
    )

    # Should be rejected because of long squeeze risk
    order = await rm.handle_signal(sig)
    assert order is None
    assert any("Funding Sentinel Veto" in log["msg"] for log in audit_logs)

    await db.close()


@pytest.mark.asyncio
async def test_binance_square_publisher_mock():
    mock_vyce = MagicMock()
    mock_vyce.chat_completion = AsyncMock(return_value="📊 [ASTRA REPORT] Phân tích BTC & SOL hôm nay...")

    mock_sentinel = MagicMock()
    mock_sentinel.get_funding_rate = AsyncMock(return_value=0.008)

    mock_exchange = MagicMock()
    mock_exchange.fetch_ticker.return_value = {
        "last": 76500.0,
        "percentage": 2.4,
        "high": 77000.0,
        "low": 75200.0,
        "quoteVolume": 15000000.0
    }

    publisher = BinanceSquarePublisher(
        vyce_client=mock_vyce,
        funding_sentinel=mock_sentinel,
        exchange=mock_exchange
    )

    post = await publisher.generate_post()
    assert "content" in post
    assert "Phân tích BTC & SOL" in post["content"]
    assert len(post["snapshots"]) > 0
    assert post["snapshots"][0]["funding_rate_pct"] == 0.008
