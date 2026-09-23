import asyncio
import pytest
import pytest_asyncio
import httpx
from datetime import datetime, timezone
from core.constants import OrderSide, MarketRegime
from core.events import SignalEvent, FillEvent
from core.event_bus import EventBus
from data.storage import Database
from config.settings import settings
from risk_engine.circuit_breaker import CircuitBreaker
from risk_engine.risk_manager import RiskManager
from ai_advisory.vyce_client import VyceClient


class MockVyceAdvisor:
    def __init__(
        self,
        approved: bool = True,
        regime: str = "BULL_TREND",
        risk_score: int = 2,
        confidence: float = 0.85,
        size_multiplier: float = 0.8,
        reasoning: str = "Mock reasoning"
    ):
        self.approved = approved
        self.regime = regime
        self.risk_score = risk_score
        self.confidence = confidence
        self.size_multiplier = size_multiplier
        self.reasoning = reasoning

    async def evaluate_signal_veto(self, signal, market_context):
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


class MockVyceTimeout:
    async def evaluate_signal_veto(self, signal, market_context):
        await asyncio.sleep(5.0)  # Exceeds timeout
        return {"approved": True}


class MockVyceNetworkError:
    async def evaluate_signal_veto(self, signal, market_context):
        raise httpx.ConnectError("Connection refused by proxy")


@pytest_asyncio.fixture
async def setup_env(tmp_path, monkeypatch):
    # Pin settings for test isolation — prevents .env changes from breaking tests
    monkeypatch.setattr(settings, "MAX_POSITION_PERCENT", 0.20)
    monkeypatch.setattr(settings, "MAX_OPEN_POSITIONS", 2)
    monkeypatch.setattr(settings, "STARTING_BALANCE_USDT", 100.0)
    monkeypatch.setattr(settings, "ENABLE_TIME_WINDOW_GUARD", False)

    db_path = str(tmp_path / "test_risk.db")
    db = Database(db_path)
    await db.connect()
    event_bus = EventBus()
    event_bus.start()
    cb = CircuitBreaker(max_daily_drawdown_percent=0.02)
    cb.reset_daily_metrics(100.0)

    class NeutralTimeGuard:
        def is_red_flag_window(self, dt=None):
            return False, ""
        def is_golden_window(self, dt=None):
            return False, ""
        def get_window_status(self, dt=None):
            return {"is_red_flag": False, "is_golden_window": False}

    rm = RiskManager(event_bus, db, cb, time_guard=NeutralTimeGuard())
    yield db, event_bus, cb, rm
    await event_bus.stop()
    await db.close()


@pytest.mark.asyncio
async def test_circuit_breaker_trip(setup_env):
    db, event_bus, cb, rm = setup_env
    assert not cb.is_tripped

    # Drop balance from 100 to 97 (3% loss > 2% limit)
    is_ok = cb.update_equity(balance=97.0, equity=97.0)
    assert not is_ok
    assert cb.is_tripped
    assert "Daily drawdown" in cb.trip_reason


@pytest.mark.asyncio
async def test_risk_manager_rejects_when_circuit_breaker_tripped(setup_env):
    db, event_bus, cb, rm = setup_env
    cb.trigger_emergency_kill("Test emergency")

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=59000.0,
        take_profit=62000.0
    )
    order = await rm.handle_signal(signal)
    assert order is None  # Must be rejected!


@pytest.mark.asyncio
async def test_risk_manager_rejects_invalid_stop_loss(setup_env):
    db, event_bus, cb, rm = setup_env

    # Stop loss above current price for a BUY order is invalid!
    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=61000.0,
        take_profit=65000.0
    )
    order = await rm.handle_signal(signal)
    assert order is None  # Must be rejected!


@pytest.mark.asyncio
async def test_risk_manager_approves_valid_signal(setup_env):
    db, event_bus, cb, rm = setup_env
    rm.vyce_client = MockVyceAdvisor(approved=True)

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=59000.0,
        take_profit=62000.0
    )
    order = await rm.handle_signal(signal)
    assert order is not None
    assert order.side == OrderSide.BUY
    assert order.quantity > 0
    assert order.stop_loss == 59000.0


# =============================================================================
# Milestone 1: Active Advisory Veto Gatekeeper & Sizing Tests
# =============================================================================

@pytest.mark.asyncio
async def test_risk_manager_ai_advisory_veto(setup_env):
    db, event_bus, cb, _ = setup_env
    mock_ai = MockVyceAdvisor(
        approved=False,
        regime="BEAR_TREND",
        risk_score=5,
        confidence=0.20,
        size_multiplier=0.20,
        reasoning="Macro bear divergence detected"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=59000.0,
        take_profit=62000.0,
        confidence=0.85
    )

    order = await rm.handle_signal(signal)
    assert order is None  # Vetoed!

    # Check SQLite persistence in signals table
    recent_signals = await db.get_recent_signals(limit=1)
    assert len(recent_signals) == 1
    assert recent_signals[0]["approved"] == 0
    assert "AI Advisory Veto" in recent_signals[0]["rejection_reason"]
    assert "Macro bear divergence" in recent_signals[0]["rejection_reason"]

    # Check SQLite persistence in ai_advisory_logs table
    async with db._conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM ai_advisory_logs ORDER BY id DESC LIMIT 1")
        row = await cursor.fetchone()
        assert row is not None
        assert row["trade_allowed"] == 0
        assert row["regime"] == "bear_trend"
        assert row["risk_score"] == 5


@pytest.mark.asyncio
async def test_risk_manager_ai_advisory_approval_with_sizing(setup_env):
    db, event_bus, cb, _ = setup_env
    mock_ai = MockVyceAdvisor(
        approved=True,
        regime="BULL_TREND",
        risk_score=1,
        confidence=0.95,
        size_multiplier=0.6,
        reasoning="Strong trend alignment"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=59000.0,
        take_profit=62000.0,
        confidence=0.90
    )

    order = await rm.handle_signal(signal)
    assert order is not None
    assert order.side == OrderSide.BUY

    # Sizing formula: 100 USDT * 0.20 max_pos * 0.6 multiplier = 12 USDT
    # Quantity: 12 / 60000 = 0.0002 BTC
    expected_qty = round((100.0 * 0.20 * 0.6) / 60000.0, 6)
    assert order.quantity == expected_qty
    assert order.quantity == 0.0002

    # Check SQLite signals table
    recent_signals = await db.get_recent_signals(limit=1)
    assert len(recent_signals) == 1
    assert recent_signals[0]["approved"] == 1

    # Check SQLite ai_advisory_logs table
    async with db._conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM ai_advisory_logs ORDER BY id DESC LIMIT 1")
        row = await cursor.fetchone()
        assert row is not None
        assert row["trade_allowed"] == 1
        assert row["size_multiplier"] == 0.6


@pytest.mark.asyncio
async def test_risk_manager_vetoes_on_extreme_volatility(setup_env):
    db, event_bus, cb, _ = setup_env
    # Even if approved=True, extreme volatility must veto
    mock_ai = MockVyceAdvisor(
        approved=True,
        regime="EXTREME_VOLATILITY",
        risk_score=5,
        confidence=0.8,
        size_multiplier=0.5,
        reasoning="Severe flash volatility"
    )
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=59000.0,
        take_profit=62000.0
    )

    order = await rm.handle_signal(signal)
    assert order is None

    recent_signals = await db.get_recent_signals(limit=1)
    assert "Extreme Market Volatility" in recent_signals[0]["rejection_reason"]


# =============================================================================
# Milestone 1: Dual-Layer Timeout & Quantitative Fallback Tests
# =============================================================================

@pytest.mark.asyncio
async def test_risk_manager_timeout_engages_quantitative_fallback(setup_env, monkeypatch):
    db, event_bus, cb, _ = setup_env
    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 0.2)

    rm = RiskManager(event_bus, db, cb, vyce_client=MockVyceTimeout())

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=59000.0,
        take_profit=62000.0,
        confidence=0.85
    )

    # Must complete safely and approve via quantitative fallback with size de-rating (0.50x)
    order = await rm.handle_signal(signal)
    assert order is not None
    # 100 * 0.20 * 0.5 = 10 USDT -> 10 / 60000 = 0.000167 BTC
    expected_qty = round((100.0 * 0.20 * 0.5) / 60000.0, 6)
    assert order.quantity == expected_qty
    assert order.quantity == 0.000167

    # Check fallback logged in SQLite
    async with db._conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM ai_advisory_logs ORDER BY id DESC LIMIT 1")
        row = await cursor.fetchone()
        assert row is not None
        assert row["trade_allowed"] == 1
        assert row["size_multiplier"] == 0.5
        assert "AI Timeout" in row["reasoning"]


@pytest.mark.asyncio
async def test_risk_manager_network_error_engages_fallback(setup_env):
    db, event_bus, cb, _ = setup_env
    rm = RiskManager(event_bus, db, cb, vyce_client=MockVyceNetworkError())

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=59000.0,
        take_profit=62000.0,
        confidence=0.80
    )

    order = await rm.handle_signal(signal)
    assert order is not None
    assert order.quantity == 0.000167


@pytest.mark.asyncio
async def test_quantitative_fallback_rejects_wide_stop_loss(setup_env, monkeypatch):
    db, event_bus, cb, _ = setup_env
    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 0.1)
    rm = RiskManager(event_bus, db, cb, vyce_client=MockVyceTimeout())

    # Stop-loss at 54000 on entry 60000 is 10% risk, exceeding the 5.0% safe corridor limit
    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=54000.0,
        take_profit=68000.0,
        confidence=0.85
    )

    order = await rm.handle_signal(signal)
    assert order is None

    recent_signals = await db.get_recent_signals(limit=1)
    assert "outside safe corridor" in recent_signals[0]["rejection_reason"]


@pytest.mark.asyncio
async def test_quantitative_fallback_rejects_low_confidence(setup_env, monkeypatch):
    db, event_bus, cb, _ = setup_env
    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 0.1)
    rm = RiskManager(event_bus, db, cb, vyce_client=MockVyceTimeout())

    # Confidence 0.60 is below fallback threshold 0.70
    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=59000.0,
        take_profit=62000.0,
        confidence=0.60
    )

    order = await rm.handle_signal(signal)
    assert order is None

    recent_signals = await db.get_recent_signals(limit=1)
    assert "below safe threshold 0.70" in recent_signals[0]["rejection_reason"]


@pytest.mark.asyncio
async def test_quantitative_fallback_approves_sell_signal_unconditionally(setup_env, monkeypatch):
    db, event_bus, cb, default_rm = setup_env
    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 0.1)
    rm = RiskManager(event_bus, db, cb, vyce_client=MockVyceTimeout(), time_guard=default_rm.time_guard)

    signal = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.SELL,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=61000.0,
        take_profit=58000.0
    )

    order = await rm.handle_signal(signal)
    assert order is not None
    assert order.side == OrderSide.SELL


# =============================================================================
# Milestone 1: FillEvent Synchronization & Max Positions Enforcement Tests
# =============================================================================

@pytest.mark.asyncio
async def test_fill_event_synchronization_and_position_limits(setup_env):
    db, event_bus, cb, _ = setup_env
    mock_ai = MockVyceAdvisor(approved=True, size_multiplier=0.8)
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai)

    assert len(rm.open_positions) == 0

    # Fill 1: BUY
    fill1 = FillEvent(
        order_id="ord-001",
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        fill_price=60000.0,
        quantity=0.0002,
        fee=0.01,
        timestamp=datetime.now(timezone.utc)
    )
    await rm.handle_fill(fill1)
    assert len(rm.open_positions) == 1
    assert "EMA_Trend_BTC/USDT" in rm.open_positions

    # Fill 2: BUY
    fill2 = FillEvent(
        order_id="ord-002",
        strategy_name="RSI_Bollinger",
        symbol="ETH/USDT",
        side=OrderSide.BUY,
        fill_price=3000.0,
        quantity=0.002,
        fee=0.01,
        timestamp=datetime.now(timezone.utc)
    )
    await rm.handle_fill(fill2)
    assert len(rm.open_positions) == 2

    # Now attempt a 3rd BUY signal -> exceeds MAX_OPEN_POSITIONS (2)
    sig3 = SignalEvent(
        strategy_name="New_Strategy",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60200.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=59200.0,
        take_profit=62000.0
    )
    order3 = await rm.handle_signal(sig3)
    assert order3 is None  # Rejected by hard position limit check

    recent_signals = await db.get_recent_signals(limit=1)
    assert "Maximum open positions reached (2/2)" in recent_signals[0]["rejection_reason"]

    # Fill 3: SELL closes pos 1
    sell_fill = FillEvent(
        order_id="ord-003",
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.SELL,
        fill_price=61000.0,
        quantity=0.0002,
        fee=0.01,
        timestamp=datetime.now(timezone.utc)
    )
    await rm.handle_fill(sell_fill)
    assert len(rm.open_positions) == 1
    assert "EMA_Trend_BTC/USDT" not in rm.open_positions

    # Now new BUY signal can proceed
    order4 = await rm.handle_signal(sig3)
    assert order4 is not None
    assert order4.side == OrderSide.BUY


@pytest.mark.asyncio
async def test_audit_logs_recording(setup_env):
    db, event_bus, cb, _ = setup_env
    audit_logs = []
    mock_ai = MockVyceAdvisor(approved=True, size_multiplier=0.7, reasoning="Audit log verification")
    rm = RiskManager(event_bus, db, cb, vyce_client=mock_ai, audit_logs=audit_logs)

    sig = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=59000.0,
        take_profit=62000.0
    )
    await rm.handle_signal(sig)

    assert len(audit_logs) == 1
    assert audit_logs[0]["level"] == "SUCCESS"
    assert "Audit log verification" in audit_logs[0]["msg"]
    assert "BTC/USDT" in audit_logs[0]["msg"]


@pytest.mark.asyncio
async def test_risk_manager_with_real_vyce_client_outage_rejects_unsafe_signals(setup_env):
    """
    Verifies that when a real VyceClient encounters a network outage, RiskManager enforces
    its quantitative corridor checks and rejects wide Stop-Loss and low-confidence BUY signals.
    """
    db, event_bus, cb, _ = setup_env

    class FailTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            raise httpx.ConnectError("Offline")

    mock_client = httpx.AsyncClient(transport=FailTransport())
    vyce_client = VyceClient(http_client=mock_client)
    rm = RiskManager(event_bus, db, cb, vyce_client=vyce_client)

    try:
        # Signal 1: Wide Stop-Loss (10% SL)
        wide_sl_signal = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=60000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=54000.0,
            take_profit=68000.0,
            confidence=0.85
        )
        order1 = await rm.handle_signal(wide_sl_signal)
        assert order1 is None, "Expected rejection for 10% Stop-Loss signal"

        # Signal 2: Low Confidence (0.50)
        low_conf_signal = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=60000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=58500.0,
            take_profit=63000.0,
            confidence=0.50
        )
        order2 = await rm.handle_signal(low_conf_signal)
        assert order2 is None, "Expected rejection for confidence < 0.70"

        # Signal 3: Safe Signal (2.5% SL, 0.85 conf)
        safe_signal = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=60000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=58500.0,
            take_profit=63000.0,
            confidence=0.85
        )
        order3 = await rm.handle_signal(safe_signal)
        assert order3 is not None, "Expected approval for safe signal in quantitative fallback"
        assert order3.quantity == 0.000167  # 50% de-rated sizing
    finally:
        await vyce_client.close()
        await mock_client.aclose()


@pytest.mark.asyncio
async def test_risk_manager_handles_sqlite_locks_gracefully(setup_env):
    """
    Verifies that transient SQLite locks during advisory or signal logging do not
    crash RiskManager.handle_signal or drop approved orders.
    """
    _, event_bus, cb, _ = setup_env

    class LockedDb:
        async def get_recent_candles(self, *args, **kwargs):
            return []
        async def save_ai_advisory(self, *args, **kwargs):
            raise RuntimeError("sqlite3.OperationalError: database is locked")
        async def save_signal(self, *args, **kwargs):
            raise RuntimeError("sqlite3.OperationalError: database is locked")

    class MockAiApproval:
        async def evaluate_signal_veto(self, signal, market_context):
            return {
                "approved": True,
                "regime": "BULL_TREND",
                "risk_score": 2,
                "confidence": 0.85,
                "size_multiplier": 0.8,
                "reasoning": "Trend solid",
                "fallback_used": False
            }

    rm = RiskManager(event_bus, LockedDb(), cb, vyce_client=MockAiApproval())

    sig = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=58500.0,
        take_profit=63000.0,
        confidence=0.85
    )

    # Must complete successfully and return OrderEvent without raising unhandled exception
    order = await rm.handle_signal(sig)
    assert order is not None
    assert order.symbol == "BTC/USDT"


@pytest.mark.asyncio
async def test_risk_manager_time_window_guard_veto(setup_env, monkeypatch):
    from config.settings import settings
    monkeypatch.setattr(settings, "TRADING_MODE", "live")
    monkeypatch.setattr(settings, "ENABLE_TIME_WINDOW_GUARD", True)
    db, event_bus, cb, rm = setup_env
    rm.vyce_client = MockVyceAdvisor(approved=True)

    class MockRedFlagGuard:
        def is_red_flag_window(self, dt=None):
            return True, "RED FLAG: Mốc giao điểm Funding Rate sàn Binance (15:00 VN). Bot tạm dừng tránh râu quét."

        def is_golden_window(self, dt=None):
            return False, ""

    rm.time_guard = MockRedFlagGuard()

    sig = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=58500.0,
        take_profit=63000.0,
        confidence=0.85
    )

    # In Red Flag window, signal must be rejected!
    order = await rm.handle_signal(sig)
    assert order is None

    # If force flag is set, it can bypass red flag guard
    sig.force = True
    forced_order = await rm.handle_signal(sig)
    assert forced_order is not None


@pytest.mark.asyncio
async def test_risk_manager_macro_emergency_defense_veto(setup_env):
    db, event_bus, cb, rm = setup_env
    rm.vyce_client = MockVyceAdvisor(approved=True)

    class MockMacroScanner:
        cached_status = {
            "state": "WAR_RISK_DEFENSIVE",
            "emergency_defense": True,
            "summary": "Cảnh báo chiến sự bùng nổ, kích hoạt phòng thủ."
        }

    rm.macro_scanner = MockMacroScanner()

    sig = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=58500.0,
        take_profit=63000.0,
        confidence=0.85
    )

    # In Emergency Defense mode, signal must be rejected!
    order = await rm.handle_signal(sig)
    assert order is None

    # Forced signal bypasses emergency defense
    sig.force = True
    forced_order = await rm.handle_signal(sig)
    assert forced_order is not None


