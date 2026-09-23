import os
import json
import pytest
import httpx
from datetime import datetime, timezone
import pandas as pd
from core.constants import MarketRegime, OrderSide
from core.events import SignalEvent
from core.event_bus import EventBus
from data.storage import Database
from config.settings import Settings, settings
from ai_advisory.vyce_client import VyceClient
from ai_advisory.regime_classifier import MarketRegimeClassifier


class MockVyceClientSuccess:
    async def chat_completion(self, system_prompt: str, user_content: str) -> str:
        return '{"regime": "bull_trend", "risk_score": 2, "trade_allowed": true, "size_multiplier": 0.8, "reasoning": "Strong upward momentum"}'


class MockVyceClientTimeout:
    async def chat_completion(self, system_prompt: str, user_content: str):
        return None  # Simulates timeout or network failure


@pytest.mark.asyncio
async def test_ai_advisory_successful_parsing(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_ai.db")
    db = Database(db_path)
    await db.connect()
    event_bus = EventBus()
    event_bus.start()

    monkeypatch.setattr(settings, "ENABLE_AI_ADVISORY", True)

    classifier = MarketRegimeClassifier(event_bus, db, client=MockVyceClientSuccess())

    # Create dummy 20 candles
    df = pd.DataFrame({
        "close": [50000 + i * 100 for i in range(20)],
        "volume": [100.0] * 20
    })

    advisory = await classifier.evaluate_market(df, "BTC/USDT")
    assert advisory.regime == MarketRegime.BULL_TREND
    assert advisory.risk_score == 2
    assert advisory.trade_allowed is True
    assert advisory.size_multiplier == 0.8
    assert "upward momentum" in advisory.reasoning

    await event_bus.stop()
    await db.close()


@pytest.mark.asyncio
async def test_ai_advisory_fallback_on_failure(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_ai_fail.db")
    db = Database(db_path)
    await db.connect()
    event_bus = EventBus()
    event_bus.start()

    monkeypatch.setattr(settings, "ENABLE_AI_ADVISORY", True)

    classifier = MarketRegimeClassifier(event_bus, db, client=MockVyceClientTimeout())

    df = pd.DataFrame({
        "close": [50000 + i * 100 for i in range(20)],
        "volume": [100.0] * 20
    })

    # Should fall back cleanly without raising any exception
    advisory = await classifier.evaluate_market(df, "BTC/USDT")
    assert advisory is not None
    assert advisory.trade_allowed is True  # Safe default

    await event_bus.stop()
    await db.close()


# =============================================================================
# Milestone 1: Settings Resolution Tests
# =============================================================================

def test_settings_vyce_key_and_url_fallback(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "***REDACTED***")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://vyceai.com")
    monkeypatch.setenv("VYCE_API_KEY", "mock_vyce_key")
    monkeypatch.delenv("VYCE_BASE_URL", raising=False)

    s = Settings()
    assert s.VYCE_API_KEY == "***REDACTED***"
    assert s.VYCE_BASE_URL == "https://vyceai.com/v1"


def test_settings_model_alias_remapping():
    assert Settings.resolve_vyce_ai_configuration is not None
    s = Settings()
    # Model should have remapped from deepseek-chat to claude-sonnet-4-6
    assert s.VYCE_MODEL == "claude-sonnet-4-6"


# =============================================================================
# Milestone 1: VyceClient Model Alias Resolution & Lifecycle Tests
# =============================================================================

def test_vyce_client_model_alias_resolution():
    assert VyceClient.resolve_model_alias("claude-3-5-sonnet") == "claude-sonnet-4-6"
    assert VyceClient.resolve_model_alias("Claude-3.5-Sonnet") == "claude-sonnet-4-6"
    assert VyceClient.resolve_model_alias("claude-3-5-sonnet-20241022") == "claude-sonnet-4-6"
    assert VyceClient.resolve_model_alias("deepseek-chat") == "deepseek-v4.1"
    assert VyceClient.resolve_model_alias("custom-model-id") == "custom-model-id"


@pytest.mark.asyncio
async def test_vyce_client_keepalive_pool_and_close():
    client = VyceClient()
    http_client = await client._get_client()
    assert isinstance(http_client, httpx.AsyncClient)
    assert not http_client.is_closed

    # Second call returns identical client instance (keep-alive pool reuse)
    http_client_2 = await client._get_client()
    assert http_client_2 is http_client

    await client.close()
    assert http_client.is_closed


# =============================================================================
# Milestone 1: VyceClient evaluate_signal_veto Tests
# =============================================================================

@pytest.mark.asyncio
async def test_vyce_client_evaluate_signal_veto_approved():
    expected_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "approved": True,
                    "regime": "BULL_TREND",
                    "risk_score": 2,
                    "confidence": 0.88,
                    "size_multiplier": 0.9,
                    "reasoning": "Golden cross confirmed with strong volume."
                })
            }
        }]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=expected_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = VyceClient(http_client=mock_http)
        sig = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=65000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=64000.0,
            take_profit=67000.0,
            confidence=0.85
        )
        res = await client.evaluate_signal_veto(sig, {"rsi": 55.0, "market_regime": "BULL_TREND"})
        assert res["approved"] is True
        assert res["regime"] == "BULL_TREND"
        assert res["risk_score"] == 2
        assert res["confidence"] == 0.88
        assert res["size_multiplier"] == 0.9
        assert "Golden cross confirmed" in res["reasoning"]
        assert res["fallback_used"] is False


@pytest.mark.asyncio
async def test_vyce_client_evaluate_signal_veto_rejection():
    expected_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "approved": False,
                    "regime": "EXTREME_VOLATILITY",
                    "risk_score": 5,
                    "confidence": 0.15,
                    "size_multiplier": 0.2,
                    "reasoning": "VETO: Extreme flash crash volatility detected."
                })
            }
        }]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=expected_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = VyceClient(http_client=mock_http)
        sig = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=60000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=58000.0,
            take_profit=64000.0,
            confidence=0.85
        )
        res = await client.evaluate_signal_veto(sig, {"rsi": 25.0, "market_regime": "EXTREME_VOLATILITY"})
        assert res["approved"] is False
        assert res["regime"] == "EXTREME_VOLATILITY"
        assert res["risk_score"] == 5
        assert res["size_multiplier"] == 0.2
        assert "VETO" in res["reasoning"]
        assert res["fallback_used"] is False


@pytest.mark.asyncio
async def test_vyce_client_evaluate_signal_veto_markdown_stripping():
    # Proxies sometimes return ```json ... ``` markdown code fences
    raw_content = "```json\n{\n  \"approved\": true,\n  \"regime\": \"RANGING\",\n  \"risk_score\": 3,\n  \"confidence\": 0.75,\n  \"size_multiplier\": 0.8,\n  \"reasoning\": \"Ranging bounce setup.\"\n}\n```"
    expected_response = {"choices": [{"message": {"content": raw_content}}]}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=expected_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = VyceClient(http_client=mock_http)
        sig = SignalEvent(
            strategy_name="RSI_Bollinger",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=62000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=61000.0,
            take_profit=64000.0,
            confidence=0.75
        )
        res = await client.evaluate_signal_veto(sig, {"rsi": 32.0})
        assert res["approved"] is True
        assert res["regime"] == "RANGING"
        assert res["risk_score"] == 3
        assert res["fallback_used"] is False


@pytest.mark.asyncio
async def test_vyce_client_evaluate_signal_veto_timeout_fallback():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Mock upstream read timeout")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = VyceClient(http_client=mock_http)
        sig = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=60000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=59000.0,
            take_profit=62000.0,
            confidence=0.80
        )
        # Should cleanly return deterministic quantitative fallback without raising
        res = await client.evaluate_signal_veto(sig, {"rsi": 50.0, "market_regime": "RANGING"})
        assert res["approved"] is True
        assert res["fallback_used"] is True
        assert res["size_multiplier"] == 0.50
        assert "Quantitative Fallback" in res["reasoning"]


@pytest.mark.asyncio
async def test_vyce_client_evaluate_signal_veto_invalid_json_fallback():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "Not valid JSON response"}}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = VyceClient(http_client=mock_http)
        sig = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=60000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=59000.0,
            take_profit=62000.0,
            confidence=0.80
        )
        res = await client.evaluate_signal_veto(sig, {"rsi": 80.0})
        # Overbought RSI triggers quantitative veto in fallback mode
        assert res["approved"] is False
        assert res["fallback_used"] is True
        assert res["regime"] == "EXTREME_VOLATILITY"


# =============================================================================
# Milestone 1: VyceClient generate_post_mortem Tests
# =============================================================================

@pytest.mark.asyncio
async def test_vyce_client_generate_post_mortem_success():
    expected_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "category": "STOP_LOSS",
                    "title": "Cắt lỗ BTC do trượt giá",
                    "details": "Vị thế bị quét stop loss khi nến thủng hỗ trợ mạnh.",
                    "capital_impact": 15.5,
                    "lesson_learned": "Nâng khoảng dừng lỗ khi thị trường biến động mạnh.",
                    "operator": "Claude-3.5-Sonnet"
                })
            }
        }]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=expected_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = VyceClient(http_client=mock_http)
        trade_info = {
            "symbol": "BTC/USDT",
            "strategy_name": "EMA_Trend",
            "entry_price": 65000.0,
            "exit_price": 64000.0,
            "pnl_usdt": -15.5,
            "pnl_percent": -1.54,
            "hold_duration_seconds": 120.0,
            "reason": "STOP_LOSS"
        }
        res = await client.generate_post_mortem(trade_info)
        assert res["category"] == "STOP_LOSS"
        assert "Cắt lỗ" in res["title"]
        assert res["capital_impact"] == 15.5
        assert res["operator"] == "Claude-3.5-Sonnet"


@pytest.mark.asyncio
async def test_vyce_client_generate_post_mortem_fallback():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Proxy offline")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = VyceClient(http_client=mock_http)
        trade_info = {
            "symbol": "BTC/USDT",
            "entry_price": 65000.0,
            "exit_price": 64000.0,
            "pnl_usdt": -20.0,
            "pnl_percent": -1.5,
            "reason": "STOP_LOSS"
        }
        res = await client.generate_post_mortem(trade_info)
        assert res["category"] == "STOP_LOSS"
        assert res["capital_impact"] == 20.0
        assert res["operator"] == "Deterministic-Fallback"


# =============================================================================
# Milestone 2: Multi-Model AI Council & Smart Failover Tests
# =============================================================================

@pytest.mark.asyncio
async def test_vyce_client_council_consensus_success():
    """Both Claude 4.6 and DeepSeek V4 approve -> synthesized council decision."""
    def handler(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.read())
        m = data.get("model")
        if "claude" in m:
            content = json.dumps({
                "approved": True, "regime": "BULL_TREND", "risk_score": 2,
                "confidence": 0.90, "size_multiplier": 1.0,
                "reasoning": "Strong macro trend aligned."
            })
        else:
            content = json.dumps({
                "approved": True, "regime": "BULL_TREND", "risk_score": 1,
                "confidence": 0.86, "size_multiplier": 0.9,
                "reasoning": "Volume breakout confirmed."
            })
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = VyceClient(http_client=mock_http, council_mode="consensus", fast_model="deepseek-v4.1")
        sig = SignalEvent(
            strategy_name="EMA_Trend", symbol="BTC/USDT", side=OrderSide.BUY,
            price=65000.0, timestamp=datetime.now(timezone.utc),
            stop_loss=64000.0, take_profit=67000.0, confidence=0.85
        )
        res = await client.evaluate_signal_veto(sig, {"rsi": 52.0})
        assert res["approved"] is True
        assert res["confidence"] == 0.88
        assert res["risk_score"] == 2
        assert "Council Consensus" in res["reasoning"]
        assert "Claude" in res["reasoning"]
        assert "claude-sonnet-4-6" in res["model"]
        assert "deepseek" in res["model"]


@pytest.mark.asyncio
async def test_vyce_client_council_claude_veto_overrides():
    """If Claude vetoes for macro risk, the trade is strictly rejected."""
    def handler(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.read())
        m = data.get("model")
        if "claude" in m:
            content = json.dumps({
                "approved": False, "regime": "BEAR_TREND", "risk_score": 4,
                "confidence": 0.40, "size_multiplier": 0.2,
                "reasoning": "Macro resistance rejection at 66k."
            })
        else:
            content = json.dumps({
                "approved": True, "regime": "RANGING", "risk_score": 2,
                "confidence": 0.80, "size_multiplier": 0.8,
                "reasoning": "Local bounce."
            })
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = VyceClient(http_client=mock_http, council_mode="consensus")
        sig = SignalEvent(
            strategy_name="EMA_Trend", symbol="BTC/USDT", side=OrderSide.BUY,
            price=65000.0, timestamp=datetime.now(timezone.utc),
            stop_loss=64000.0, take_profit=67000.0, confidence=0.85
        )
        res = await client.evaluate_signal_veto(sig, {"rsi": 60.0})
        assert res["approved"] is False
        assert res["risk_score"] == 4
        assert "Council Veto" in res["reasoning"]


@pytest.mark.asyncio
async def test_vyce_client_smart_failover_when_primary_times_out():
    """If Claude times out, DeepSeek V4 seamlessly takes over without blocking."""
    def handler(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.read())
        m = data.get("model")
        if "claude" in m:
            raise httpx.ReadTimeout("Claude timed out")
        content = json.dumps({
            "approved": True, "regime": "BULL_TREND", "risk_score": 2,
            "confidence": 0.82, "size_multiplier": 0.85,
            "reasoning": "Fast scout approved pullback."
        })
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = VyceClient(http_client=mock_http, council_mode="consensus", fast_model="deepseek-v4.1")
        sig = SignalEvent(
            strategy_name="EMA_Trend", symbol="BTC/USDT", side=OrderSide.BUY,
            price=65000.0, timestamp=datetime.now(timezone.utc),
            stop_loss=64000.0, take_profit=67000.0, confidence=0.85
        )
        res = await client.evaluate_signal_veto(sig, {"rsi": 48.0})
        assert res["approved"] is True
        assert "Smart Failover" in res["reasoning"]
        assert "deepseek" in res["model"]


