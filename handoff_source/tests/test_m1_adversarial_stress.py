import asyncio
import pytest
import pytest_asyncio
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from core.constants import OrderSide, MarketRegime
from core.events import SignalEvent, OrderEvent, AIAdvisoryEvent, FillEvent
from core.event_bus import EventBus
from data.storage import Database
from config.settings import settings
from risk_engine.circuit_breaker import CircuitBreaker
from risk_engine.risk_manager import RiskManager
from ai_advisory.vyce_client import VyceClient


class MockConfigurableVyceAdvisor:
    """Mock advisor that allows granular control over return values and call count tracking."""
    def __init__(
        self,
        approved: bool = True,
        regime: str = "BULL_TREND",
        risk_score: int = 2,
        confidence: float = 0.85,
        size_multiplier: float = 0.8,
        reasoning: str = "Configurable mock reasoning",
        raw_dict: Optional[Dict[str, Any]] = None,
        raise_exception: Optional[Exception] = None
    ):
        self.approved = approved
        self.regime = regime
        self.risk_score = risk_score
        self.confidence = confidence
        self.size_multiplier = size_multiplier
        self.reasoning = reasoning
        self.raw_dict = raw_dict
        self.raise_exception = raise_exception
        self.call_count = 0

    async def evaluate_signal_veto(self, signal, market_context):
        self.call_count += 1
        if self.raise_exception:
            raise self.raise_exception
        if self.raw_dict is not None:
            return self.raw_dict
        return {
            "approved": self.approved,
            "regime": self.regime,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "size_multiplier": self.size_multiplier,
            "reasoning": self.reasoning,
            "model": "claude-sonnet-4-6",
            "fallback_used": False
        }


@pytest_asyncio.fixture
async def env(tmp_path, monkeypatch):
    """Clean isolated test environment fixture."""
    monkeypatch.setattr(settings, "MAX_POSITION_PERCENT", 0.20)
    monkeypatch.setattr(settings, "MAX_OPEN_POSITIONS", 2)
    monkeypatch.setattr(settings, "STARTING_BALANCE_USDT", 100.0)
    monkeypatch.setattr(settings, "ENABLE_TIME_WINDOW_GUARD", False)

    db_path = str(tmp_path / "adversarial_risk.db")
    db = Database(db_path)
    await db.connect()
    event_bus = EventBus()
    event_bus.start()
    cb = CircuitBreaker(max_daily_drawdown_percent=0.02)
    cb.reset_daily_metrics(100.0)
    yield db, event_bus, cb
    await event_bus.stop()
    await db.close()


def make_buy_signal(price=60000.0, sl=59000.0, tp=62000.0, confidence=0.85):
    return SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=price,
        timestamp=datetime.now(timezone.utc),
        stop_loss=sl,
        take_profit=tp,
        confidence=confidence
    )


def make_sell_signal(price=60000.0, sl=61000.0, tp=58000.0):
    return SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.SELL,
        price=price,
        timestamp=datetime.now(timezone.utc),
        stop_loss=sl,
        take_profit=tp,
        confidence=0.85
    )


# =============================================================================
# Test Suite 1: Signal Veto vs Approval Gatekeeper Integrity
# =============================================================================

@pytest.mark.asyncio
async def test_ai_veto_strictly_blocks_order_and_persists_rejection(env):
    db, event_bus, cb = env
    received_orders = []
    event_bus.subscribe(OrderEvent, lambda e: received_orders.append(e))

    mock_ai = MockConfigurableVyceAdvisor(
        approved=False,
        regime="BEAR_TREND",
        risk_score=5,
        confidence=0.25,
        size_multiplier=0.20,
        reasoning="Macro bear divergence detected"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    sig = make_buy_signal()
    result = await rm.handle_signal(sig)

    # 1. Result must be None
    assert result is None, "AI veto must return None from handle_signal"

    # 2. EventBus must NOT have received any OrderEvent
    await asyncio.sleep(0.05)
    assert len(received_orders) == 0, "No OrderEvent should be published when AI vetoes"

    # 3. SQLite signals table must record rejection
    signals = await db.get_recent_signals(limit=10)
    assert len(signals) == 1
    assert signals[0]["approved"] == 0
    assert "AI Advisory Veto" in signals[0]["rejection_reason"]
    assert "Macro bear divergence" in signals[0]["rejection_reason"]

    # 4. SQLite ai_advisory_logs must record veto
    async with db._conn.cursor() as cur:
        await cur.execute("SELECT * FROM ai_advisory_logs ORDER BY id DESC LIMIT 1")
        log = await cur.fetchone()
        assert log is not None
        assert log["trade_allowed"] == 0
        assert log["risk_score"] == 5


@pytest.mark.asyncio
async def test_ai_approval_creates_order_and_persists_approval(env):
    db, event_bus, cb = env
    received_orders = []
    event_bus.subscribe(OrderEvent, lambda e: received_orders.append(e))

    mock_ai = MockConfigurableVyceAdvisor(
        approved=True,
        regime="BULL_TREND",
        risk_score=1,
        confidence=0.92,
        size_multiplier=0.75,
        reasoning="Strong multi-timeframe EMA alignment"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    sig = make_buy_signal(price=60000.0)
    result = await rm.handle_signal(sig)

    # 1. Order returned
    assert result is not None
    assert isinstance(result, OrderEvent)
    assert result.side == OrderSide.BUY

    # 2. Expected quantity: 100 USDT equity * 0.20 max_pos * 0.75 multiplier = 15 USDT
    # 15 / 60000 = 0.00025 BTC
    assert result.quantity == 0.00025

    # 3. EventBus received order
    await asyncio.sleep(0.05)
    assert len(received_orders) == 1
    assert received_orders[0].order_id == result.order_id

    # 4. SQLite records approval
    signals = await db.get_recent_signals(limit=10)
    assert len(signals) == 1
    assert signals[0]["approved"] == 1
    assert signals[0]["rejection_reason"] == ""


@pytest.mark.asyncio
async def test_ai_veto_on_sell_signal(env):
    db, event_bus, cb = env
    mock_ai = MockConfigurableVyceAdvisor(
        approved=False,
        regime="BEAR_TREND",
        reasoning="Anomalous sell signal"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    sig = make_sell_signal()
    result = await rm.handle_signal(sig)
    assert result is None

    signals = await db.get_recent_signals(limit=1)
    assert len(signals) == 1
    assert signals[0]["approved"] == 0
    assert "AI Advisory Veto" in signals[0]["rejection_reason"]


# =============================================================================
# Test Suite 2: Extreme Volatility Regime Veto Override
# =============================================================================

@pytest.mark.asyncio
async def test_extreme_volatility_vetoes_despite_ai_approved_true(env):
    db, event_bus, cb = env
    mock_ai = MockConfigurableVyceAdvisor(
        approved=True,  # AI says approved=True!
        regime="EXTREME_VOLATILITY",  # But regime is extreme volatility
        risk_score=5,
        confidence=0.80,
        size_multiplier=0.5,
        reasoning="Flash crash volatility detected"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    sig = make_buy_signal()
    result = await rm.handle_signal(sig)

    # Must be vetoed!
    assert result is None, "Extreme volatility must overrule approved=True"

    signals = await db.get_recent_signals(limit=1)
    assert len(signals) == 1
    assert signals[0]["approved"] == 0
    assert "Extreme Market Volatility" in signals[0]["rejection_reason"]


@pytest.mark.asyncio
@pytest.mark.parametrize("regime_input", [
    "EXTREME_VOLATILITY",
    "extreme_volatility",
    "Extreme_Volatility",
    "Extreme_volatility"
])
async def test_extreme_volatility_casing_resilience(env, regime_input):
    db, event_bus, cb = env
    mock_ai = MockConfigurableVyceAdvisor(
        approved=True,
        regime=regime_input,
        reasoning=f"Testing casing: {regime_input}"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    sig = make_buy_signal()
    result = await rm.handle_signal(sig)
    assert result is None, f"Regime '{regime_input}' failed to trigger extreme volatility veto"


@pytest.mark.asyncio
@pytest.mark.parametrize("safe_regime", [
    "BULL_TREND",
    "BEAR_TREND",
    "RANGING",
    "bull_trend",
    "bear_trend",
    "ranging"
])
async def test_safe_regimes_with_approved_true_pass(env, safe_regime):
    db, event_bus, cb = env
    mock_ai = MockConfigurableVyceAdvisor(
        approved=True,
        regime=safe_regime,
        size_multiplier=0.8,
        reasoning=f"Safe regime: {safe_regime}"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    sig = make_buy_signal()
    result = await rm.handle_signal(sig)
    assert result is not None, f"Regime '{safe_regime}' should not be vetoed when approved=True"
    assert result.side == OrderSide.BUY


# =============================================================================
# Test Suite 3: Position Sizing Multiplier Bounds & Clamping [0.2, 1.0]
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.parametrize("sub_lower_mult", [0.05, 0.0, -0.5, 0.19, 0.001])
async def test_position_sizing_sub_lower_bound_clamping(env, sub_lower_mult):
    """Values below 0.2 must be strictly clamped to 0.2."""
    db, event_bus, cb = env
    mock_ai = MockConfigurableVyceAdvisor(
        approved=True,
        regime="BULL_TREND",
        size_multiplier=sub_lower_mult,
        reasoning="Sub lower multiplier test"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    sig = make_buy_signal(price=60000.0)
    result = await rm.handle_signal(sig)
    assert result is not None

    # Expected: 100 * 0.20 * 0.20 = 4 USDT -> 4 / 60000 = 0.000067 BTC
    expected_qty = round((100.0 * 0.20 * 0.20) / 60000.0, 6)
    assert result.quantity == expected_qty
    assert result.quantity == 0.000067


@pytest.mark.asyncio
@pytest.mark.parametrize("upper_mult", [1.01, 1.50, 2.0, 10.0, 100.0])
async def test_position_sizing_upper_bound_clamping(env, upper_mult):
    """Values above 1.0 must be strictly clamped to 1.0."""
    db, event_bus, cb = env
    mock_ai = MockConfigurableVyceAdvisor(
        approved=True,
        regime="BULL_TREND",
        size_multiplier=upper_mult,
        reasoning="Upper multiplier test"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    sig = make_buy_signal(price=60000.0)
    result = await rm.handle_signal(sig)
    assert result is not None

    # Expected: 100 * 0.20 * 1.0 = 20 USDT -> 20 / 60000 = 0.000333 BTC
    expected_qty = round((100.0 * 0.20 * 1.0) / 60000.0, 6)
    assert result.quantity == expected_qty
    assert result.quantity == 0.000333


@pytest.mark.asyncio
@pytest.mark.parametrize("exact_mult,expected_qty", [
    (0.20, 0.000067),
    (0.50, 0.000167),
    (0.80, 0.000267),
    (1.00, 0.000333)
])
async def test_position_sizing_proportional_accuracy(env, exact_mult, expected_qty):
    db, event_bus, cb = env
    mock_ai = MockConfigurableVyceAdvisor(
        approved=True,
        regime="BULL_TREND",
        size_multiplier=exact_mult,
        reasoning="Proportional sizing test"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    sig = make_buy_signal(price=60000.0)
    result = await rm.handle_signal(sig)
    assert result is not None
    assert result.quantity == expected_qty


@pytest.mark.asyncio
async def test_vyce_client_clean_and_parse_clamping():
    """Verify that VyceClient internally clamps LLM returned size_multiplier to [0.2, 1.0]."""
    client = VyceClient()

    # Case A: LLM returns 0.01 (too low)
    raw_json_low = '{"approved": true, "regime": "BULL_TREND", "risk_score": 1, "confidence": 0.9, "size_multiplier": 0.01, "reasoning": "ok"}'
    parsed_low = client._clean_and_parse_json(raw_json_low)
    size_mult_low = max(0.2, min(1.0, float(parsed_low.get("size_multiplier", 1.0))))
    assert size_mult_low == 0.2

    # Case B: LLM returns 5.0 (too high)
    raw_json_high = '{"approved": true, "regime": "BULL_TREND", "risk_score": 1, "confidence": 0.9, "size_multiplier": 5.0, "reasoning": "ok"}'
    parsed_high = client._clean_and_parse_json(raw_json_high)
    size_mult_high = max(0.2, min(1.0, float(parsed_high.get("size_multiplier", 1.0))))
    assert size_mult_high == 1.0


# =============================================================================
# Test Suite 4: Toggle Off Behavior (ENABLE_AI_ADVISORY = False)
# =============================================================================

@pytest.mark.asyncio
async def test_toggle_off_completely_bypasses_ai(env, monkeypatch):
    """When ENABLE_AI_ADVISORY is False, VyceClient must NEVER be called."""
    db, event_bus, cb = env
    monkeypatch.setattr(settings, "ENABLE_AI_ADVISORY", False)

    # Poison the advisor: if it is called, it will raise an AssertionError
    mock_ai = MockConfigurableVyceAdvisor(
        raise_exception=AssertionError("AI advisory was called while ENABLE_AI_ADVISORY is False!")
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    sig = make_buy_signal(price=60000.0)
    result = await rm.handle_signal(sig)

    # 1. Must approve cleanly without calling AI
    assert result is not None
    assert mock_ai.call_count == 0, "VyceClient was called despite ENABLE_AI_ADVISORY=False!"

    # 2. Sizing must use default 1.0x (100 * 0.20 * 1.0 / 60000 = 0.000333 BTC)
    assert result.quantity == 0.000333

    # 3. Signals table records approval
    signals = await db.get_recent_signals(limit=1)
    assert len(signals) == 1
    assert signals[0]["approved"] == 1

    # 4. ai_advisory_logs must have 0 rows
    async with db._conn.cursor() as cur:
        await cur.execute("SELECT COUNT(*) as cnt FROM ai_advisory_logs")
        row = await cur.fetchone()
        assert row["cnt"] == 0, "No ai_advisory_logs should be saved when AI is disabled"


@pytest.mark.asyncio
async def test_toggle_off_preserves_deterministic_hard_rules(env, monkeypatch):
    """When ENABLE_AI_ADVISORY is False, deterministic risk rules (Phase 1) remain 100% active."""
    db, event_bus, cb = env
    monkeypatch.setattr(settings, "ENABLE_AI_ADVISORY", False)

    mock_ai = MockConfigurableVyceAdvisor(
        raise_exception=AssertionError("AI should not be called!")
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    # Check 1: Circuit breaker tripped
    cb.trigger_emergency_kill("Emergency manual stop")
    sig = make_buy_signal()
    res1 = await rm.handle_signal(sig)
    assert res1 is None, "Tripped circuit breaker must reject even when AI is off"

    cb.reset_daily_metrics(100.0)

    # Check 2: Invalid Stop Loss (SL >= Price)
    invalid_sl_sig = make_buy_signal(price=60000.0, sl=60500.0)
    res2 = await rm.handle_signal(invalid_sl_sig)
    assert res2 is None, "Invalid SL must reject even when AI is off"

    # Check 3: Max open positions reached
    # Add 2 open positions
    fill1 = FillEvent("o1", "S1", "BTC/USDT", OrderSide.BUY, 60000.0, 0.0002, 0.0, datetime.now(timezone.utc))
    fill2 = FillEvent("o2", "S2", "BTC/USDT", OrderSide.BUY, 60000.0, 0.0002, 0.0, datetime.now(timezone.utc))
    await rm.handle_fill(fill1)
    await rm.handle_fill(fill2)
    assert len(rm.open_positions) == 2

    res3 = await rm.handle_signal(sig)
    assert res3 is None, "Max open positions must reject even when AI is off"
    assert mock_ai.call_count == 0


@pytest.mark.asyncio
async def test_runtime_hot_toggle_transitions(env, monkeypatch):
    """Simulate switching ENABLE_AI_ADVISORY from True -> False -> True dynamically."""
    db, event_bus, cb = env
    mock_ai = MockConfigurableVyceAdvisor(
        approved=True,
        regime="BULL_TREND",
        size_multiplier=0.60,
        reasoning="Hot toggle test"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    # Turn 1: ENABLE_AI_ADVISORY = True
    monkeypatch.setattr(settings, "ENABLE_AI_ADVISORY", True)
    res1 = await rm.handle_signal(make_buy_signal(price=60000.0))
    assert res1 is not None
    assert mock_ai.call_count == 1
    # Multiplier 0.60 -> 100 * 0.20 * 0.60 / 60000 = 0.0002 BTC
    assert res1.quantity == 0.0002

    # Clear position so next order isn't blocked by position limits
    rm.open_positions.clear()

    # Turn 2: ENABLE_AI_ADVISORY = False
    monkeypatch.setattr(settings, "ENABLE_AI_ADVISORY", False)
    res2 = await rm.handle_signal(make_buy_signal(price=60000.0))
    assert res2 is not None
    assert mock_ai.call_count == 1, "Call count should remain 1 because AI was disabled"
    # Multiplier default 1.0x -> 100 * 0.20 * 1.0 / 60000 = 0.000333 BTC
    assert res2.quantity == 0.000333

    rm.open_positions.clear()

    # Turn 3: ENABLE_AI_ADVISORY = True again
    monkeypatch.setattr(settings, "ENABLE_AI_ADVISORY", True)
    res3 = await rm.handle_signal(make_buy_signal(price=60000.0))
    assert res3 is not None
    assert mock_ai.call_count == 2, "Call count should increment to 2 when re-enabled"
    assert res3.quantity == 0.0002


# =============================================================================
# Test Suite 5: Adversarial Boundary & Underflow Stress
# =============================================================================

@pytest.mark.asyncio
async def test_micro_equity_quantity_underflow(env):
    """When capital is tiny and calculated quantity rounds to 0.0, must reject cleanly."""
    db, event_bus, cb = env
    cb.reset_daily_metrics(0.01, force=True)  # 0.01 USDT account equity
    mock_ai = MockConfigurableVyceAdvisor(
        approved=True,
        size_multiplier=0.20
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    sig = make_buy_signal(price=60000.0)
    # 0.01 * 0.20 * 0.20 = 0.0004 USDT -> 0.0004 / 60000 = 0.000000006 -> rounds to 0.0
    result = await rm.handle_signal(sig)
    assert result is None, "Underflow quantity <= 0 must be rejected"

    signals = await db.get_recent_signals(limit=1)
    assert len(signals) == 1
    assert signals[0]["approved"] == 0
    assert "Calculated order quantity too small" in signals[0]["rejection_reason"]


@pytest.mark.asyncio
async def test_rapid_burst_signal_throughput(env):
    """Stress test: 50 sequential signals processed through RiskManager without leakage."""
    db, event_bus, cb = env
    mock_ai = MockConfigurableVyceAdvisor(
        approved=True,
        regime="BULL_TREND",
        size_multiplier=0.70
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    # Process 50 signals
    approved_count = 0
    rejected_count = 0
    for i in range(50):
        sig = make_buy_signal(price=60000.0 + i)
        # Alternate between approved and rejected scenarios by adjusting positions
        if i % 2 == 0:
            rm.open_positions.clear()
            order = await rm.handle_signal(sig)
            if order:
                approved_count += 1
        else:
            # Overfill positions
            rm.open_positions["P1"] = {"quantity": 0.01}
            rm.open_positions["P2"] = {"quantity": 0.01}
            order = await rm.handle_signal(sig)
            if order is None:
                rejected_count += 1

    assert approved_count == 25
    assert rejected_count == 25
    assert mock_ai.call_count == 25  # Only called when Phase 1 checks passed!


@pytest.mark.asyncio
async def test_vyce_client_handles_surrounding_text_gracefully():
    """When LLM returns conversational text with JSON, VyceClient catches JSONDecodeError and engages fallback."""
    client = VyceClient()
    sig = make_buy_signal()
    ctx = {"symbol": "BTC/USDT", "price": 60000.0}

    # Simulate LLM returning conversational text + JSON
    malformed_response = "Certainly! Here is the JSON:\n```json\n{\"approved\": true, \"regime\": \"BULL_TREND\"}\n```"
    
    # We patch chat_completion to return malformed_response
    client.chat_completion = lambda *args, **kwargs: asyncio.sleep(0.01, result=malformed_response)

    decision = await client.evaluate_signal_veto(sig, ctx)
    assert decision is not None
    assert decision["fallback_used"] is True
    assert decision["model"] == client.model or "fallback" in decision.get("reasoning", "").lower()


@pytest.mark.asyncio
async def test_vyce_client_handles_none_values_in_json():
    """When LLM returns None for size_multiplier or risk_score, fallback handles it safely."""
    client = VyceClient()
    sig = make_buy_signal()
    ctx = {"symbol": "BTC/USDT", "price": 60000.0}

    # Payload with None for size_multiplier
    payload_none = '{"approved": true, "regime": "BULL_TREND", "risk_score": null, "size_multiplier": null}'
    client.chat_completion = lambda *args, **kwargs: asyncio.sleep(0.01, result=payload_none)

    decision = await client.evaluate_signal_veto(sig, ctx)
    assert decision is not None
    assert decision["fallback_used"] is True
    assert decision["size_multiplier"] == 0.50  # From quantitative fallback

