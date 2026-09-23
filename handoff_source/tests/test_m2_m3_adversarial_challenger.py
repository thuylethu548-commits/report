import asyncio
import json
import time
import pytest
import pytest_asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

from config.settings import settings
from core.constants import OrderSide, OrderType
from core.events import OrderEvent, MarketEvent, FillEvent
from core.event_bus import EventBus
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
from execution.paper_trader import PaperTrader
from execution.binance_executor import BinanceExecutor
from ai_advisory.vyce_client import VyceClient


@pytest_asyncio.fixture
async def env(tmp_path):
    """Provides an isolated database, event bus, circuit breaker, and audit logs."""
    db_file = str(tmp_path / "test_adversarial_challenger.db")
    db = Database(db_path=db_file)
    await db.connect()

    event_bus = EventBus()
    event_bus.start()

    cb = CircuitBreaker(max_daily_drawdown_percent=0.10)
    cb.reset_daily_metrics(1000.0)

    audit_logs: List[Dict[str, Any]] = []

    yield db, event_bus, cb, audit_logs

    await event_bus.stop()
    await db.close()


# =============================================================================
# SECTION 1: EMPIRICAL NON-BLOCKING SLA VERIFICATION (< 5.0ms under 1s AI delay)
# =============================================================================

@pytest.mark.asyncio
async def test_empirical_close_position_non_blocking_sla_benchmark(env):
    """
    Stress-test the non-blocking execution SLA of _close_position.
    Runs 50 sequential stop-loss closures with a 1,000ms simulated network delay.
    Asserts:
      - Min, Max, p50, p95, p99 latencies are recorded.
      - STRICT ASSERTION: EVERY iteration MUST finish in < 5.0ms.
      - Background tasks are spawned and complete asynchronously.
    """
    db, event_bus, cb, audit_logs = env

    async def slow_network_call(trade_info):
        await asyncio.sleep(1.0)  # 1,000ms artificial delay
        return {
            "category": "STOP_LOSS",
            "title": f"Delayed Post-Mortem {trade_info['order_id']}",
            "details": "Simulated slow LLM response",
            "capital_impact": abs(trade_info.get("pnl_usdt", 1.0)),
            "lesson_learned": "Non-blocking dispatch verified",
            "operator": "Claude-3.5-Sonnet"
        }

    mock_vyce = MagicMock(spec=VyceClient)
    mock_vyce.generate_post_mortem = AsyncMock(side_effect=slow_network_call)

    trader = PaperTrader(
        event_bus=event_bus,
        db=db,
        circuit_breaker=cb,
        vyce_client=mock_vyce,
        audit_logs=audit_logs
    )

    latencies_ms = []
    num_trials = 50

    for i in range(num_trials):
        pos_key = f"Strategy_TEST_{i}"
        order_id = f"ORD-BENCH-{i:03d}"
        trader.open_positions[pos_key] = {
            "order_id": order_id,
            "strategy_name": "Benchmark_Strategy",
            "symbol": "BTC/USDT",
            "side": OrderSide.BUY,
            "entry_price": 60000.0,
            "quantity": 0.001,
            "stop_loss": 59000.0,
            "take_profit": 62000.0,
            "entry_time": datetime.now(timezone.utc),
            "fee": 0.06
        }

        # Measure high-precision wall clock time of _close_position
        t_start = time.perf_counter()
        await trader._close_position(pos_key, exit_price=58800.0, reason="STOP_LOSS")
        t_elapsed = (time.perf_counter() - t_start) * 1000.0

        latencies_ms.append(t_elapsed)
        # Immediate strict check per iteration
        assert t_elapsed < 5.0, f"Iteration {i} exceeded 5.0ms threshold: {t_elapsed:.3f}ms"
        assert pos_key not in trader.open_positions

    # Compute statistical benchmarks
    latencies_sorted = sorted(latencies_ms)
    min_lat = latencies_sorted[0]
    max_lat = latencies_sorted[-1]
    p50_lat = latencies_sorted[int(len(latencies_sorted) * 0.50)]
    p95_lat = latencies_sorted[int(len(latencies_sorted) * 0.95)]
    p99_lat = latencies_sorted[int(len(latencies_sorted) * 0.99)]

    print(f"\n--- NON-BLOCKING SLA BENCHMARK (50 iterations) ---")
    print(f"Min: {min_lat:.3f}ms | p50: {p50_lat:.3f}ms | p95: {p95_lat:.3f}ms | p99: {p99_lat:.3f}ms | Max: {max_lat:.3f}ms")

    assert max_lat < 5.0, f"Max latency {max_lat:.3f}ms violated strict < 5.0ms SLA"

    # Ensure background tasks are still running or draining
    assert len(trader._background_tasks) > 0

    # Wait for all background tasks to finish
    await trader.close(timeout=5.0)
    assert len(trader._background_tasks) == 0

    # Verify all 50 benchmark lessons were successfully recorded in SQLite (plus 3 seeded defaults)
    lessons = await db.get_lessons(limit=100)
    bench_lessons = [l for l in lessons if "ORD-BENCH-" in l["title"]]
    assert len(bench_lessons) == num_trials


@pytest.mark.asyncio
async def test_empirical_handle_market_tick_sla_under_stop_loss(env):
    """
    Verify handle_market_tick Stop-Loss detection and dispatch finishes in < 5.0ms
    when triggering a position exit with a 1,000ms delayed background post-mortem.
    """
    db, event_bus, cb, audit_logs = env

    async def slow_post_mortem(trade_info):
        await asyncio.sleep(1.0)
        return {
            "category": "STOP_LOSS",
            "title": "Delayed SL Tick",
            "details": "Triggered via market tick",
            "capital_impact": 5.0,
            "lesson_learned": "Tick handler is non-blocking",
            "operator": "Claude-3.5-Sonnet"
        }

    mock_vyce = MagicMock(spec=VyceClient)
    mock_vyce.generate_post_mortem = AsyncMock(side_effect=slow_post_mortem)

    trader = PaperTrader(
        event_bus=event_bus,
        db=db,
        circuit_breaker=cb,
        vyce_client=mock_vyce,
        audit_logs=audit_logs
    )

    pos_key = "EMA_Trend_ETH/USDT"
    trader.open_positions[pos_key] = {
        "order_id": "ORD-TICK-001",
        "strategy_name": "EMA_Trend",
        "symbol": "ETH/USDT",
        "side": OrderSide.BUY,
        "entry_price": 3000.0,
        "quantity": 0.01,
        "stop_loss": 2900.0,
        "take_profit": 3200.0,
        "entry_time": datetime.now(timezone.utc),
        "fee": 0.03
    }

    tick = MarketEvent(
        symbol="ETH/USDT",
        open=2950.0,
        high=2950.0,
        low=2880.0,
        close=2890.0,  # Below stop_loss of 2900.0
        volume=50.0,
        timestamp=datetime.now(timezone.utc)
    )

    t_start = time.perf_counter()
    await trader.handle_market_tick(tick)
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    print(f"\n--- handle_market_tick SL execution time: {elapsed_ms:.3f}ms ---")
    assert elapsed_ms < 5.0, f"handle_market_tick took {elapsed_ms:.3f}ms, exceeding 5.0ms SLA"
    assert pos_key not in trader.open_positions
    assert len(trader._background_tasks) == 1

    await trader.close(timeout=2.0)


# =============================================================================
# SECTION 2: ADVERSARIAL NETWORK & LLM CONDITIONS (TIMEOUT, 500, MALFORMED, FENCES)
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.parametrize("scenario,transport_handler", [
    (
        "timeout_exceeding_5s",
        lambda req: asyncio.sleep(6.0)  # > 5.0s timeout
    ),
    (
        "http_500_internal_error",
        lambda req: httpx.Response(500, text="Internal Server Error: AI upstream gateway failure")
    ),
    (
        "http_502_bad_gateway",
        lambda req: httpx.Response(502, text="<html><body>502 Bad Gateway</body></html>")
    ),
    (
        "http_503_service_unavailable",
        lambda req: httpx.Response(503, text="Service Unavailable: overloaded")
    ),
    (
        "http_504_gateway_timeout",
        lambda req: httpx.Response(504, text="Gateway Timeout")
    ),
    (
        "malformed_plain_text",
        lambda req: httpx.Response(200, json={
            "choices": [{"message": {"content": "I am sorry, but as an AI I cannot generate financial advice."}}]
        })
    ),
    (
        "malformed_truncated_json",
        lambda req: httpx.Response(200, json={
            "choices": [{"message": {"content": '{"category": "STOP_LOSS", "title": "Truncated json...'}}]
        })
    ),
    (
        "malformed_json_array",
        lambda req: httpx.Response(200, json={
            "choices": [{"message": {"content": '[{"title": "Not a dict"}]'}}]
        })
    ),
    (
        "missing_title",
        lambda req: httpx.Response(200, json={
            "choices": [{"message": {"content": '{"category": "STOP_LOSS", "details": "Det", "lesson_learned": "Les"}'}}]
        })
    ),
    (
        "empty_string_fields",
        lambda req: httpx.Response(200, json={
            "choices": [{"message": {"content": '{"category": "STOP_LOSS", "title": "   ", "details": "", "lesson_learned": "\t"}'}}]
        })
    ),
    (
        "null_fields",
        lambda req: httpx.Response(200, json={
            "choices": [{"message": {"content": '{"category": null, "title": null, "details": null, "lesson_learned": null}'}}]
        })
    ),
    (
        "non_numeric_capital_impact",
        lambda req: httpx.Response(200, json={
            "choices": [{"message": {"content": '{"category": "STOP_LOSS", "title": "Valid Title", "details": "Valid Details", "lesson_learned": "Valid Lesson", "capital_impact": "UNMEASURABLE"}'}}]
        })
    ),
])
async def test_adversarial_vyce_client_generate_post_mortem_fallback(scenario, transport_handler):
    """
    Direct unit verification of VyceClient.generate_post_mortem under hostile network/LLM conditions.
    Asserts:
      - VyceClient NEVER raises an uncaught exception.
      - Produces a valid, deterministic fallback dictionary.
      - Operator is 'Deterministic-Fallback'.
      - All essential fields (title, details, lesson_learned, capital_impact) are populated.
    """
    class AdversarialTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            res = transport_handler(request)
            if asyncio.iscoroutine(res):
                res = await res
                return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})
            return res

    mock_client = httpx.AsyncClient(transport=AdversarialTransport(), timeout=httpx.Timeout(5.0, connect=2.0))
    vyce = VyceClient(http_client=mock_client)

    trade_info = {
        "order_id": f"ORD-ADV-{scenario[:10]}",
        "symbol": "BTC/USDT",
        "strategy_name": "EMA_Trend",
        "entry_price": 60000.0,
        "exit_price": 58500.0,
        "pnl_usdt": -15.0,
        "pnl_percent": -2.5,
        "hold_duration_seconds": 90.0,
        "reason": "STOP_LOSS"
    }

    result = await vyce.generate_post_mortem(trade_info)

    assert isinstance(result, dict)
    assert result["operator"] == "Deterministic-Fallback"
    assert result["category"] == "STOP_LOSS"
    assert "BTC/USDT" in result["title"]
    assert len(result["details"]) > 0
    assert len(result["lesson_learned"]) > 0
    assert result["capital_impact"] == 15.0
    await mock_client.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize("fence_payload", [
    (
        "```json\n"
        "{\n"
        '  "category": "STOP_LOSS",\n'
        '  "title": "Clean Fence Title",\n'
        '  "details": "Clean Fence Details",\n'
        '  "capital_impact": 12.5,\n'
        '  "lesson_learned": "Clean Fence Lesson",\n'
        '  "operator": "Claude-3.5-Sonnet"\n'
        "}\n"
        "```"
    ),
    (
        "```\n"
        "{\n"
        '  "category": "SLIPPAGE",\n'
        '  "title": "No Tag Fence Title",\n'
        '  "details": "No Tag Fence Details",\n'
        '  "capital_impact": 8.0,\n'
        '  "lesson_learned": "No Tag Fence Lesson",\n'
        '  "operator": "Claude-3.5-Sonnet"\n'
        "}\n"
        "```"
    ),
    (
        "Here is your forensic analysis:\n```json\n"
        "{\n"
        '  "category": "STOP_LOSS",\n'
        '  "title": "Surrounded Fence Title",\n'
        '  "details": "Surrounded Fence Details",\n'
        '  "capital_impact": 10.0,\n'
        '  "lesson_learned": "Surrounded Fence Lesson"\n'
        "}\n"
        "```\nHope this helps!"
    )
])
async def test_adversarial_markdown_fences_handling(fence_payload):
    """
    Verify markdown code fences parsing or safe fallback degradation.
    If the markdown fence starts with text before the fence, it must safely fall back
    to deterministic output without crashing.
    """
    class FenceTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(200, json={
                "choices": [{"message": {"content": fence_payload}}]
            })

    mock_client = httpx.AsyncClient(transport=FenceTransport(), timeout=httpx.Timeout(5.0))
    vyce = VyceClient(http_client=mock_client)

    trade_info = {
        "order_id": "ORD-FENCE-001",
        "symbol": "SOL/USDT",
        "strategy_name": "RSI_BB",
        "entry_price": 140.0,
        "exit_price": 135.0,
        "pnl_usdt": -5.0,
        "pnl_percent": -3.57,
        "hold_duration_seconds": 120.0,
        "reason": "STOP_LOSS"
    }

    result = await vyce.generate_post_mortem(trade_info)

    assert isinstance(result, dict)
    assert len(result["title"]) > 0
    assert len(result["details"]) > 0
    assert len(result["lesson_learned"]) > 0
    assert result["capital_impact"] in (12.5, 8.0, 5.0)  # Either parsed or fallback abs(pnl)
    await mock_client.aclose()


@pytest.mark.asyncio
async def test_end_to_end_paper_trader_adversarial_fallback_and_sqlite_persistence(env):
    """
    Full End-to-End test:
    When PaperTrader triggers Stop-Loss under a severe HTTP 500 network failure:
      1. Position is immediately closed and removed from open_positions.
      2. Trade is recorded in SQLite 'trades'.
      3. FillEvent is published on EventBus.
      4. Auto post-mortem background task engages deterministic fallback.
      5. Deterministic lesson is successfully inserted into SQLite 'trading_lessons'.
      6. Audit log warning/critical message is recorded.
      7. Entire bot pipeline remains active and error-free.
    """
    db, event_bus, cb, audit_logs = env

    class Failing500Transport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(500, text="Internal Server Error: AI service offline")

    failing_client = httpx.AsyncClient(transport=Failing500Transport(), timeout=httpx.Timeout(5.0))
    vyce = VyceClient(http_client=failing_client)

    trader = PaperTrader(
        event_bus=event_bus,
        db=db,
        circuit_breaker=cb,
        vyce_client=vyce,
        audit_logs=audit_logs
    )
    trader.balance_usdt = 1000.0  # Ensure plenty of balance for order

    # Place buy order
    buy_order = OrderEvent(
        order_id="ORD-ADV-E2E-001",
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        price=60000.0,
        quantity=0.001,
        stop_loss=58500.0,
        take_profit=63000.0,
        timestamp=datetime.now(timezone.utc)
    )
    await trader.handle_order(buy_order)
    assert len(trader.open_positions) == 1

    # Market crash triggers Stop Loss
    crash_tick = MarketEvent(
        symbol="BTC/USDT",
        open=59000.0,
        high=59000.0,
        low=58000.0,
        close=58400.0,
        volume=100.0,
        timestamp=datetime.now(timezone.utc)
    )
    await trader.handle_market_tick(crash_tick)
    assert len(trader.open_positions) == 0

    # Wait for post-mortem background task
    await trader.close(timeout=3.0)

    # 1. Verify SQLite trades table has closed trade
    async with db._conn.cursor() as cursor:
        await cursor.execute("SELECT status, exit_price, pnl_usdt FROM trades WHERE order_id = ?", ("ORD-ADV-E2E-001",))
        trade_row = await cursor.fetchone()
        assert trade_row is not None
        assert trade_row["status"] == "CLOSED"
        assert trade_row["pnl_usdt"] < 0

    # 2. Verify SQLite trading_lessons table contains deterministic fallback record
    lessons = await db.get_lessons(limit=10)
    assert len(lessons) >= 1
    fallback_lesson = lessons[0]
    assert fallback_lesson["operator"] == "Deterministic-Fallback"
    assert fallback_lesson["category"] == "STOP_LOSS"
    assert "BTC/USDT" in fallback_lesson["title"]
    assert "Bảo toàn vốn là ưu tiên số 1" in fallback_lesson["lesson_learned"]
    assert fallback_lesson["capital_impact"] > 0

    # 3. Verify audit log entry
    assert any("Deterministic-Fallback" in log["msg"] or "Auto Post-Mortem" in log["msg"] for log in audit_logs)

    await failing_client.aclose()


# =============================================================================
# SECTION 3: CONCURRENT STOP-LOSS EXITS STRESS HARNESS
# =============================================================================

@pytest.mark.asyncio
async def test_concurrent_stop_loss_exits_stress_harness(env):
    """
    Stress-test concurrent Stop-Loss exits across 20 distinct trading pairs simultaneously.
    Simulates a flash crash where 20 positions hit stop-loss concurrently.
    Asserts:
      - All 20 positions are cleanly closed.
      - All 20 post-mortem background tasks execute concurrently.
      - SQLite handles concurrent writes to trading_lessons without locking errors.
      - All 20 lessons are safely persisted and retrieved.
      - trader.close() drains all tasks gracefully within timeout.
    """
    db, event_bus, cb, audit_logs = env

    symbols = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "ADA/USDT",
        "XRP/USDT", "DOGE/USDT", "AVAX/USDT", "DOT/USDT", "LINK/USDT",
        "NEAR/USDT", "MATIC/USDT", "UNI/USDT", "ATOM/USDT", "LTC/USDT",
        "FTM/USDT", "ALGO/USDT", "ICP/USDT", "APT/USDT", "SUI/USDT"
    ]

    # Mock VyceClient with slight variable latency (50ms to 200ms) to induce concurrent racing writes
    async def concurrent_generate(trade_info):
        delay = 0.05 + (hash(trade_info["symbol"]) % 15) * 0.01  # 50ms - 200ms
        await asyncio.sleep(delay)
        return {
            "category": "STOP_LOSS",
            "title": f"Stop-Loss {trade_info['symbol']} flash crash",
            "details": f"Exit price: {trade_info['exit_price']}, PnL: {trade_info['pnl_usdt']}",
            "capital_impact": abs(trade_info["pnl_usdt"]),
            "lesson_learned": f"Enforce SL discipline on {trade_info['symbol']}",
            "operator": "Claude-3.5-Sonnet"
        }

    mock_vyce = MagicMock(spec=VyceClient)
    mock_vyce.generate_post_mortem = AsyncMock(side_effect=concurrent_generate)

    trader = PaperTrader(
        event_bus=event_bus,
        db=db,
        circuit_breaker=cb,
        vyce_client=mock_vyce,
        audit_logs=audit_logs
    )

    # 1. Populate 20 open positions
    for sym in symbols:
        pos_key = f"EMA_Trend_{sym}"
        trader.open_positions[pos_key] = {
            "order_id": f"ORD-CONCUR-{sym.replace('/', '_')}",
            "strategy_name": "EMA_Trend",
            "symbol": sym,
            "side": OrderSide.BUY,
            "entry_price": 100.0,
            "quantity": 1.0,
            "stop_loss": 95.0,
            "take_profit": 110.0,
            "entry_time": datetime.now(timezone.utc),
            "fee": 0.1
        }

    assert len(trader.open_positions) == 20

    # 2. Trigger concurrent exits simultaneously via asyncio.gather
    t0 = time.perf_counter()
    exit_coros = [
        trader._close_position(f"EMA_Trend_{sym}", exit_price=94.0, reason="STOP_LOSS")
        for sym in symbols
    ]
    await asyncio.gather(*exit_coros)
    dispatch_time_ms = (time.perf_counter() - t0) * 1000.0

    print(f"\n--- CONCURRENT EXIT DISPATCH TIME (20 positions): {dispatch_time_ms:.3f}ms ---")

    # All positions must be removed immediately from open_positions
    assert len(trader.open_positions) == 0

    # 20 background tasks must have been spawned
    assert len(trader._background_tasks) == 20

    # 3. Gracefully await completion of all background tasks
    await trader.close(timeout=5.0)
    assert len(trader._background_tasks) == 0

    # 4. Verify all 20 lessons are persisted in SQLite without locking issues
    lessons = await db.get_lessons(limit=50)
    crash_lessons = [l for l in lessons if "flash crash" in l["title"]]
    assert len(crash_lessons) == 20

    # Verify each symbol is present in lessons
    persisted_symbols = [l["title"] for l in crash_lessons]
    for sym in symbols:
        assert any(sym in title for title in persisted_symbols), f"Symbol {sym} missing from lessons!"


@pytest.mark.asyncio
async def test_binance_executor_concurrent_stop_loss_and_fallback(env, monkeypatch):
    """
    Verify BinanceExecutor handles concurrent stop-loss fill events with fallback and SQLite persistence
    when running in live trading mode.
    """
    db, event_bus, cb, audit_logs = env
    monkeypatch.setattr(settings, "TRADING_MODE", "live")

    class FailingTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            await asyncio.sleep(0.05)
            return httpx.Response(500, text="AI Error")

    mock_client = httpx.AsyncClient(transport=FailingTransport(), timeout=httpx.Timeout(5.0))
    vyce = VyceClient(http_client=mock_client)

    mock_binance = MagicMock()
    # Mock Binance create_order returning filled order response
    async def mock_create_order(symbol, order_type, side, amount):
        return {
            "id": f"BIN-{symbol.replace('/', '_')}",
            "average": 188.0,
            "filled": amount,
            "cost": 188.0 * amount
        }
    mock_binance.create_order = AsyncMock(side_effect=mock_create_order)

    executor = BinanceExecutor(
        event_bus=event_bus,
        binance_client=mock_binance,
        db=db,
        vyce_client=vyce,
        audit_logs=audit_logs
    )

    # Setup open positions in BinanceExecutor
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "AVAX/USDT"]
    for sym in symbols:
        pos_key = f"Strategy_{sym}"
        executor.open_positions[pos_key] = {
            "order_id": f"ORD-BIN-{sym.replace('/', '_')}",
            "strategy_name": "Strategy",
            "symbol": sym,
            "side": OrderSide.BUY,
            "entry_price": 200.0,
            "quantity": 1.0,
            "stop_loss": 190.0,
            "take_profit": 220.0,
            "entry_time": datetime.now(timezone.utc),
            "fee": 0.2
        }

    # Simulate 5 concurrent STOP_LOSS sell orders submitted
    fill_orders = [
        OrderEvent(
            order_id=f"ORD-BIN-{sym.replace('/', '_')}",
            strategy_name="Strategy",
            symbol=sym,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            price=188.0,  # Below stop loss (190.0)
            quantity=1.0,
            stop_loss=0.0,
            take_profit=0.0,
            timestamp=datetime.now(timezone.utc)
        )
        for sym in symbols
    ]

    await asyncio.gather(*[executor.handle_order(ord_evt) for ord_evt in fill_orders])

    # All positions closed
    assert len(executor.open_positions) == 0
    assert len(executor._background_tasks) == 5

    # Drain tasks
    await executor.close(timeout=5.0)
    assert len(executor._background_tasks) == 0

    # Verify lessons persisted with Deterministic-Fallback
    lessons = await db.get_lessons(limit=10)
    fallback_lessons = [l for l in lessons if l["operator"] == "Deterministic-Fallback"]
    assert len(fallback_lessons) == 5

    await mock_client.aclose()


# =============================================================================
# SECTION 4: UNHANDLED EXCEPTION RESILIENCE (STORAGE FAILURE / CORRUPTION)
# =============================================================================

@pytest.mark.asyncio
async def test_trigger_auto_post_mortem_resilient_to_storage_exception(env):
    """
    Verify that if db.add_lesson raises an OperationalError (e.g. disk full / table lock),
    _trigger_auto_post_mortem catches the exception, logs it, and returns None,
    preventing any crash of the background task or the bot.
    """
    db, event_bus, cb, audit_logs = env

    mock_vyce = MagicMock(spec=VyceClient)
    mock_vyce.generate_post_mortem = AsyncMock(return_value={
        "category": "STOP_LOSS",
        "title": "Valid Post-Mortem",
        "details": "Details",
        "capital_impact": 5.0,
        "lesson_learned": "Lesson",
        "operator": "Claude-3.5-Sonnet"
    })

    # Mock db.add_lesson raising OperationalError
    failing_db = MagicMock(spec=Database)
    failing_db.add_lesson = AsyncMock(side_effect=RuntimeError("disk I/O error or table lock"))

    trader = PaperTrader(
        event_bus=event_bus,
        db=failing_db,
        circuit_breaker=cb,
        vyce_client=mock_vyce,
        audit_logs=audit_logs
    )

    pos = {
        "order_id": "ORD-CRASH-001",
        "symbol": "BTC/USDT",
        "strategy_name": "EMA_Trend",
        "entry_price": 60000.0,
        "quantity": 0.01,
        "entry_time": datetime.now(timezone.utc)
    }

    # Must NOT raise exception
    res = await trader._trigger_auto_post_mortem(
        pos=pos,
        exit_price=58000.0,
        pnl_usdt=-20.0,
        pnl_pct=-3.33,
        reason="STOP_LOSS"
    )

    assert res is None
    await trader.close()
