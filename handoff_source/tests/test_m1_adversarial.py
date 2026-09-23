import asyncio
import time
import pytest
import pytest_asyncio
import httpx
from datetime import datetime, timezone

from config.settings import settings
from core.constants import OrderSide, MarketRegime, OrderType
from core.events import SignalEvent, MarketEvent, FillEvent, AIAdvisoryEvent, OrderEvent
from core.event_bus import EventBus
from data.storage import Database
from ai_advisory.vyce_client import VyceClient
from risk_engine.circuit_breaker import CircuitBreaker
from risk_engine.risk_manager import RiskManager


@pytest_asyncio.fixture
async def env(tmp_path):
    db_path = str(tmp_path / "test_adversarial.db")
    db = Database(db_path)
    await db.connect()
    bus = EventBus()
    bus.start()
    cb = CircuitBreaker(max_daily_drawdown_percent=0.05)
    cb.reset_daily_metrics(1000.0)
    yield db, bus, cb
    await bus.stop()
    await db.close()


# =============================================================================
# Stress Test 1: Severe Latency (>3.0s) & EventBus Non-Blocking
# =============================================================================

@pytest.mark.asyncio
async def test_latency_spike_timeout_and_eventbus_throughput(env, monkeypatch):
    """
    Simulate severe upstream latency (5.0s delay).
    Assert:
    1. Fallback activates within <= 3.2s (does not hang 5.0s).
    2. Fallback record is created in SQLite.
    3. Other events on EventBus queued during the wait are processed promptly.
    """
    db, bus, cb = env
    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 3.0)

    # Custom transport that simulates 5.0s server lag
    class SlowTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            await asyncio.sleep(5.0)
            return httpx.Response(200, json={
                "choices": [{"message": {"content": '{"approved": true, "regime": "BULL_TREND", "risk_score": 1, "confidence": 0.9, "size_multiplier": 1.0, "reasoning": "Lagged ok"}'}}]
            })

    slow_client = httpx.AsyncClient(transport=SlowTransport(), timeout=httpx.Timeout(3.0, connect=2.0))
    vyce_client = VyceClient(http_client=slow_client, timeout=3.0)
    rm = RiskManager(bus, db, cb, vyce_client=vyce_client)

    # Track processed events on bus
    bus_processed_events = []
    async def track_market_event(evt):
        bus_processed_events.append(evt)
    bus.subscribe(MarketEvent, track_market_event)

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=58500.0, # 2.5% SL (valid corridor)
        take_profit=63000.0,
        confidence=0.85
    )

    t0 = time.perf_counter()
    # Concurrently publish a market event to verify EventBus queue handling
    await bus.publish(signal)
    await bus.publish(MarketEvent(
        symbol="ETH/USDT",
        timestamp=datetime.now(timezone.utc),
        open=3000.0,
        high=3010.0,
        low=2990.0,
        close=3005.0,
        volume=10.0
    ))

    # Wait for RiskManager to handle signal and event bus to drain
    # Since timeout is 3.0s, total time should be around 3.0s - 3.5s, definitely < 4.5s
    await bus._queue.join()
    elapsed = time.perf_counter() - t0

    await vyce_client.close()
    await slow_client.aclose()

    print(f"\n[Latency Test] Elapsed time: {elapsed:.2f}s")
    assert elapsed < 4.0, f"Fallback took {elapsed:.2f}s, exceeding 3.0s + 1.0s grace period!"
    assert elapsed >= 2.9, f"Fallback returned too early ({elapsed:.2f}s), expected ~3.0s timeout!"

    # Verify market event was not lost or dropped
    assert len(bus_processed_events) == 1
    assert bus_processed_events[0].symbol == "ETH/USDT"

    # Verify SQLite fallback log
    async with db._conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM ai_advisory_logs ORDER BY id DESC LIMIT 1")
        log_row = await cursor.fetchone()
        assert log_row is not None
        assert "Fallback" in log_row["reasoning"] or "Timeout" in log_row["reasoning"]


# =============================================================================
# Stress Test 2: Corrupted / Adversarial JSON Payloads from LLM
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.parametrize("corrupted_payload", [
    "Not a JSON string at all! Random LLM chatter.",
    '{"approved": true, "regime": "BULL_TREND", ',  # truncated JSON
    '{"approved": true, "regime": "EXTREME_VOLATILITY", "risk_score": "INVALID_INT"}',  # invalid type
    '{"approved": true, "regime": 12345, "confidence": "NONE"}',  # invalid confidence
    '[]',  # list instead of dict
    '["item1", "item2"]',
    '{}',  # empty dict
    '```',  # edge case: only backticks
    '```json\n{"invalid json inside fence\n```',
    'Here is the JSON you requested:\n```json\n{"approved": true, "regime": "BULL_TREND"}\n```',
    '{"approved": null, "regime": null, "confidence": null, "size_multiplier": null}',
    '{"approved": true, "regime": "UNKNOWN_REGIME_FOO", "risk_score": 99, "confidence": 5.5, "size_multiplier": -2.0}'
])
async def test_corrupted_json_advisory_safety(corrupted_payload):
    """
    Stress test VyceClient._clean_and_parse_json and evaluate_signal_veto
    under various corrupted/adversarial JSON payloads.
    Must never throw an unhandled exception, must return valid schema.
    """
    class MockCorruptedTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(200, json={"choices": [{"message": {"content": corrupted_payload}}]})

    mock_client = httpx.AsyncClient(transport=MockCorruptedTransport())
    client = VyceClient(http_client=mock_client)

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=58500.0,
        take_profit=63000.0,
        confidence=0.85
    )

    try:
        decision = await client.evaluate_signal_veto(signal, {})
        assert isinstance(decision, dict)
        assert "approved" in decision
        assert "regime" in decision
        assert "risk_score" in decision
        assert "confidence" in decision
        assert "size_multiplier" in decision
        assert "reasoning" in decision
        assert isinstance(decision["approved"], bool)
        assert isinstance(decision["risk_score"], int)
        assert 1 <= decision["risk_score"] <= 5
        assert isinstance(decision["confidence"], float)
        assert 0.0 <= decision["confidence"] <= 1.0
        assert isinstance(decision["size_multiplier"], float)
        assert 0.2 <= decision["size_multiplier"] <= 1.0
    finally:
        await client.close()
        await mock_client.aclose()


# =============================================================================
# Stress Test 3: Network & Upstream Exceptions
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.parametrize("network_exc", [
    httpx.ConnectError("Connection refused by peer"),
    httpx.RemoteProtocolError("Server disconnected without response"),
    httpx.ReadTimeout("Read timed out"),
    httpx.ConnectTimeout("Connect timed out"),
    httpx.WriteTimeout("Write timed out"),
    httpx.PoolTimeout("Connection pool exhausted"),
    RuntimeError("Unexpected OS socket error")
])
async def test_network_exceptions_safe_recovery(network_exc):
    """
    Assert VyceClient catches network exceptions and safely activates quantitative fallback.
    """
    class ExceptionTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            raise network_exc

    mock_client = httpx.AsyncClient(transport=ExceptionTransport())
    client = VyceClient(http_client=mock_client)

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=58500.0,
        take_profit=63000.0,
        confidence=0.85
    )

    try:
        decision = await client.evaluate_signal_veto(signal, {})
        assert isinstance(decision, dict)
        assert decision["fallback_used"] is True
        assert "Quantitative Fallback" in decision["reasoning"]
    finally:
        await client.close()
        await mock_client.aclose()


# =============================================================================
# Stress Test 4: HTTP Upstream Error Status Codes (429, 500, 502, 503)
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [429, 500, 502, 503])
async def test_http_error_statuses_safe_recovery(status_code):
    class ErrorStatusTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(status_code, text=f"Error {status_code}")

    mock_client = httpx.AsyncClient(transport=ErrorStatusTransport())
    client = VyceClient(http_client=mock_client)

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=58500.0,
        take_profit=63000.0,
        confidence=0.85
    )

    try:
        decision = await client.evaluate_signal_veto(signal, {})
        assert decision["fallback_used"] is True
    finally:
        await client.close()
        await mock_client.aclose()


# =============================================================================
# Stress Test 5: Post-Mortem Forensic Analysis Adversarial Testing
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.parametrize("corrupted_payload", [
    "Non-JSON explanation of trade failure",
    '{"category": "STOP_LOSS", "capital_impact": "UNQUANTIFIABLE"}',
    '{"category": null, "title": null, "details": null, "lesson_learned": null}',
    '[]',
    '```json\n{"invalid json\n```'
])
async def test_post_mortem_corrupted_payloads_fallback(corrupted_payload):
    """
    Assert VyceClient.generate_post_mortem falls back gracefully to deterministic
    Vietnamese risk lesson when LLM output is malformed.
    """
    class MockCorruptedTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(200, json={"choices": [{"message": {"content": corrupted_payload}}]})

    mock_client = httpx.AsyncClient(transport=MockCorruptedTransport())
    client = VyceClient(http_client=mock_client)

    trade_info = {
        "order_id": "test_ord_1",
        "symbol": "BTC/USDT",
        "strategy_name": "EMA_Trend",
        "entry_price": 60000.0,
        "exit_price": 58500.0,
        "quantity": 0.01,
        "pnl_usdt": -15.0,
        "pnl_percent": -2.5,
        "hold_duration_seconds": 120.0,
        "reason": "STOP_LOSS"
    }

    try:
        lesson = await client.generate_post_mortem(trade_info)
        assert isinstance(lesson, dict)
        assert lesson["category"] == "STOP_LOSS"
        assert "BTC/USDT" in lesson["title"]
        assert lesson["capital_impact"] == 15.0
        assert "Bảo toàn vốn" in lesson["lesson_learned"] or "kỷ luật" in lesson["lesson_learned"]
        assert lesson["operator"] == "Deterministic-Fallback"
    finally:
        await client.close()
        await mock_client.aclose()


# =============================================================================
# Stress Test 6: Fallback Quantitative Safety Rules in RiskManager with Real VyceClient
# =============================================================================

@pytest.mark.asyncio
async def test_fallback_with_real_vyce_client_enforces_safety_limits(env):
    """
    CRITICAL ARCHITECTURAL SAFETY CHECK:
    When VyceClient encounters network failure or timeout:
    1. If BUY signal has wide stop-loss (e.g. 10%, violating the [0.5%, 5.0%] corridor)
       or low confidence (< 0.70), DOES THE SYSTEM REJECT IT?
    2. Or does VyceClient._build_fallback_veto bypass RiskManager's quantitative checks
       and approve unsafe trades?
    """
    db, bus, cb = env

    class FailTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            raise httpx.ConnectError("Simulated network down")

    mock_client = httpx.AsyncClient(transport=FailTransport())
    vyce_client = VyceClient(http_client=mock_client)
    rm = RiskManager(bus, db, cb, vyce_client=vyce_client)

    # Signal 1: Wide Stop-Loss (10% SL, price=60000, sl=54000)
    wide_sl_signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=54000.0,  # 10% risk! Exceeds 5.0% safe corridor limit!
        take_profit=68000.0,
        confidence=0.85
    )

    # Signal 2: Low Confidence (0.50, below 0.70 threshold)
    low_conf_signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=58500.0,  # 2.5% SL
        take_profit=63000.0,
        confidence=0.50    # Low confidence! Below 0.70 safe threshold!
    )

    order_wide_sl = await rm.handle_signal(wide_sl_signal)
    order_low_conf = await rm.handle_signal(low_conf_signal)

    await vyce_client.close()
    await mock_client.aclose()

    # Empirical check:
    print(f"\n[Fallback Check] order_wide_sl result: {order_wide_sl}")
    print(f"[Fallback Check] order_low_conf result: {order_low_conf}")

    # Under safety rules: Unsafe signals during AI outage MUST be rejected to preserve capital!
    assert order_wide_sl is None, f"DEFECT: Wide SL signal (10% SL) was APPROVED during AI network error! Order: {order_wide_sl}"
    assert order_low_conf is None, f"DEFECT: Low confidence signal (0.50) was APPROVED during AI network error! Order: {order_low_conf}"


# =============================================================================
# Stress Test 7: Multi-Signal Concurrency under AI Proxy Latency
# =============================================================================

@pytest.mark.asyncio
async def test_concurrent_signals_under_ai_latency(env, monkeypatch):
    """
    Stress-test EventBus behavior when 3 signals arrive simultaneously
    while the upstream AI proxy experiences 1.0s latency.
    Asserts that all signals are processed without dropped events, race conditions,
    or deadlocks.
    """
    db, bus, cb = env
    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 2.0)

    class LaggedTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            await asyncio.sleep(0.5)
            return httpx.Response(200, json={
                "choices": [{"message": {"content": '{"approved": true, "regime": "BULL_TREND", "risk_score": 2, "confidence": 0.85, "size_multiplier": 0.8, "reasoning": "Lagged batch ok"}'}}]
            })

    client = httpx.AsyncClient(transport=LaggedTransport())
    vyce_client = VyceClient(http_client=client, timeout=2.0)
    rm = RiskManager(bus, db, cb, vyce_client=vyce_client)

    approved_orders = []
    async def track_order(evt):
        approved_orders.append(evt)
    bus.subscribe(OrderEvent, track_order)

    # Publish 3 signals concurrently
    signals = [
        SignalEvent(
            strategy_name=f"Strategy_{i}",
            symbol=f"SYM_{i}/USDT",
            side=OrderSide.BUY,
            price=100.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=98.0, # 2% SL
            take_profit=105.0,
            confidence=0.85
        )
        for i in range(3)
    ]

    t0 = time.perf_counter()
    for s in signals:
        await bus.publish(s)

    await bus._queue.join()
    elapsed = time.perf_counter() - t0

    await vyce_client.close()
    await client.aclose()

    print(f"\n[Concurrency Test] 3 concurrent signals processed in {elapsed:.2f}s")
    assert len(approved_orders) == 3, f"Expected 3 approved orders, got {len(approved_orders)}"
    assert elapsed < 5.0, f"Processing 3 signals took {elapsed:.2f}s, exceeding 5.0s!"


