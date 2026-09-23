import asyncio
import time
import os
import pytest
import httpx
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from core.event_bus import EventBus
from core.events import OrderEvent, MarketEvent
from core.constants import OrderSide, OrderType
from data.storage import Database
from data.binance_client import BinanceClient
from risk_engine.circuit_breaker import CircuitBreaker
from execution.paper_trader import PaperTrader
from execution.binance_executor import BinanceExecutor
from ai_advisory.vyce_client import VyceClient
from web.app import create_web_app
from config.settings import settings


@pytest.fixture
async def test_db(tmp_path):
    db_file = str(tmp_path / "test_post_mortem.db")
    db = Database(db_path=db_file)
    await db.connect()
    yield db
    await db.close()


# =====================================================================
# 1. UNIT TESTS FOR VyceClient.generate_post_mortem
# =====================================================================

@pytest.mark.asyncio
async def test_generate_post_mortem_valid_json():
    """Verify generate_post_mortem parses clean JSON and uses timeout=5.0."""
    client = VyceClient()
    mock_json = (
        '{"category": "STOP_LOSS", "title": "Cắt lỗ BTC bảo toàn vốn", '
        '"details": "Chạm ngưỡng SL tại 58500", "capital_impact": 15.5, '
        '"lesson_learned": "Bảo vệ vốn là ưu tiên hàng đầu", "operator": "Claude-3.5-Sonnet"}'
    )
    client.chat_completion = AsyncMock(return_value=mock_json)

    trade_info = {
        "order_id": "ORD-001",
        "symbol": "BTC/USDT",
        "strategy_name": "EMA_Trend",
        "entry_price": 60000.0,
        "exit_price": 58500.0,
        "pnl_usdt": -15.5,
        "pnl_percent": -2.5,
        "hold_duration_seconds": 120.0,
        "reason": "STOP_LOSS"
    }

    result = await client.generate_post_mortem(trade_info)

    client.chat_completion.assert_called_once()
    call_kwargs = client.chat_completion.call_args.kwargs
    assert call_kwargs.get("timeout") == 5.0

    assert result["category"] == "STOP_LOSS"
    assert result["title"] == "Cắt lỗ BTC bảo toàn vốn"
    assert result["details"] == "Chạm ngưỡng SL tại 58500"
    assert result["capital_impact"] == 15.5
    assert result["lesson_learned"] == "Bảo vệ vốn là ưu tiên hàng đầu"
    assert result["operator"] == "Claude-3.5-Sonnet"


@pytest.mark.asyncio
async def test_generate_post_mortem_markdown_code_fences():
    """Verify generate_post_mortem cleanly strips markdown fences before parsing."""
    client = VyceClient()
    fenced_response = (
        "```json\n"
        "{\n"
        '  "category": "SLIPPAGE",\n'
        '  "title": "Trượt giá nghiêm trọng do thanh khoản mỏng",\n'
        '  "details": "Lệnh khớp trượt 0.8% ngoài dải Bollinger",\n'
        '  "capital_impact": 8.2,\n'
        '  "lesson_learned": "Kiểm tra spread và độ sâu sổ lệnh trước giờ tin",\n'
        '  "operator": "Claude-3.5-Sonnet"\n'
        "}\n"
        "```"
    )
    client.chat_completion = AsyncMock(return_value=fenced_response)

    trade_info = {
        "order_id": "ORD-002",
        "symbol": "ETH/USDT",
        "strategy_name": "RSI_BB",
        "entry_price": 3000.0,
        "exit_price": 2950.0,
        "pnl_usdt": -8.2,
        "pnl_percent": -1.67,
        "hold_duration_seconds": 45.0,
        "reason": "SLIPPAGE"
    }

    result = await client.generate_post_mortem(trade_info)

    assert result["category"] == "SLIPPAGE"
    assert result["title"] == "Trượt giá nghiêm trọng do thanh khoản mỏng"
    assert result["capital_impact"] == 8.2
    assert result["operator"] == "Claude-3.5-Sonnet"


@pytest.mark.asyncio
async def test_generate_post_mortem_missing_field_fallback():
    """Verify generate_post_mortem falls back to deterministic logic if essential fields are missing."""
    client = VyceClient()
    # Missing 'details' and empty 'title'
    corrupted_response = '{"category": "STOP_LOSS", "title": "", "lesson_learned": "Disciplined cut"}'
    client.chat_completion = AsyncMock(return_value=corrupted_response)

    trade_info = {
        "order_id": "ORD-003",
        "symbol": "SOL/USDT",
        "strategy_name": "EMA_Trend",
        "entry_price": 150.0,
        "exit_price": 145.0,
        "pnl_usdt": -5.0,
        "pnl_percent": -3.33,
        "hold_duration_seconds": 60.0,
        "reason": "STOP_LOSS"
    }

    result = await client.generate_post_mortem(trade_info)

    assert result["operator"] == "Deterministic-Fallback"
    assert result["category"] == "STOP_LOSS"
    assert "SOL/USDT" in result["title"]
    assert result["capital_impact"] == 5.0
    assert "ưu tiên số 1" in result["lesson_learned"]


@pytest.mark.asyncio
async def test_generate_post_mortem_timeout_fallback():
    """Verify generate_post_mortem safely triggers deterministic fallback on network timeout."""
    client = VyceClient()
    # chat_completion returns None when timing out
    client.chat_completion = AsyncMock(return_value=None)

    trade_info = {
        "order_id": "ORD-004",
        "symbol": "BTC/USDT",
        "strategy_name": "EMA_Trend",
        "entry_price": 62000.0,
        "exit_price": 60000.0,
        "pnl_usdt": -20.0,
        "pnl_percent": -3.22,
        "hold_duration_seconds": 300.0,
        "reason": "STOP_LOSS"
    }

    result = await client.generate_post_mortem(trade_info)

    assert result["operator"] == "Deterministic-Fallback"
    assert result["category"] == "STOP_LOSS"
    assert result["capital_impact"] == 20.0
    assert "Dừng lỗ tự động BTC/USDT" in result["title"]


# =====================================================================
# 2. INTEGRATION TESTS FOR STOP-LOSS TRIGGER & PERSISTENCE
# =====================================================================

@pytest.mark.asyncio
async def test_auto_post_mortem_triggered_on_stop_loss(test_db):
    event_bus = EventBus()
    circuit_breaker = CircuitBreaker(max_daily_drawdown_percent=0.05)
    circuit_breaker.reset_daily_metrics(100.0)
    
    mock_vyce = MagicMock(spec=VyceClient)
    mock_vyce.generate_post_mortem = AsyncMock(return_value={
        "category": "STOP_LOSS",
        "title": "Cắt lỗ BTC/USDT do quét thanh khoản",
        "details": "Giá quét qua mức hỗ trợ 60000 chạm Stop-Loss tại 59500.",
        "capital_impact": 1.5,
        "lesson_learned": "Tránh đặt Stop-Loss quá sát cản tâm lý khi thị trường có tin CPI.",
        "operator": "Claude-3.5-Sonnet"
    })
    
    audit_logs = []
    trader = PaperTrader(
        event_bus=event_bus,
        db=test_db,
        circuit_breaker=circuit_breaker,
        vyce_client=mock_vyce,
        audit_logs=audit_logs
    )

    # 1. Place BUY Order
    buy_order = OrderEvent(
        order_id="ORD-SL-001",
        strategy_name="EMA_Cross",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        price=60000.0,
        quantity=0.001,
        stop_loss=59000.0,
        take_profit=62000.0,
        timestamp=datetime.now(timezone.utc)
    )
    await trader.handle_order(buy_order)
    assert len(trader.open_positions) == 1

    # 2. Market drops to trigger Stop-Loss (58900 <= 59000)
    drop_tick = MarketEvent(
        symbol="BTC/USDT",
        open=59500.0,
        high=59600.0,
        low=58800.0,
        close=58900.0,
        volume=10.0,
        timestamp=datetime.now(timezone.utc)
    )
    await trader.handle_market_tick(drop_tick)
    assert len(trader.open_positions) == 0

    # Wait for background task to finish
    await asyncio.sleep(0.1)

    # 3. Verify mock_vyce was called with correct trade details
    mock_vyce.generate_post_mortem.assert_called_once()
    trade_arg = mock_vyce.generate_post_mortem.call_args[0][0]
    assert trade_arg["order_id"] == "ORD-SL-001"
    assert trade_arg["reason"] == "STOP_LOSS"
    assert trade_arg["pnl_usdt"] < 0

    # 4. Verify lesson recorded in SQLite trading_lessons table
    lessons = await test_db.get_lessons()
    assert len(lessons) >= 1
    latest_lesson = lessons[0]
    assert latest_lesson["title"] == "Cắt lỗ BTC/USDT do quét thanh khoản"
    assert latest_lesson["category"] == "STOP_LOSS"
    assert latest_lesson["operator"] == "Claude-3.5-Sonnet"
    assert "Tránh đặt Stop-Loss" in latest_lesson["lesson_learned"]

    # 5. Verify audit log entry
    assert any("Auto Post-Mortem" in log["msg"] for log in audit_logs)
    await trader.close()


@pytest.mark.asyncio
async def test_auto_post_mortem_fallback_on_ai_failure(test_db):
    event_bus = EventBus()
    circuit_breaker = CircuitBreaker()
    circuit_breaker.reset_daily_metrics(100.0)

    # Mock VyceClient raising Exception
    mock_vyce = MagicMock(spec=VyceClient)
    mock_vyce.generate_post_mortem = AsyncMock(side_effect=RuntimeError("Vyce API timeout 3.0s"))

    audit_logs = []
    trader = PaperTrader(
        event_bus=event_bus,
        db=test_db,
        circuit_breaker=circuit_breaker,
        vyce_client=mock_vyce,
        audit_logs=audit_logs
    )

    pos = {
        "order_id": "ORD-ERR-002",
        "symbol": "BTC/USDT",
        "strategy_name": "RSI_BB",
        "entry_price": 65000.0,
        "quantity": 0.001,
        "entry_time": datetime.now(timezone.utc)
    }

    # Calling trigger directly to verify non-crashing fallback
    lesson_id = await trader._trigger_auto_post_mortem(
        pos=pos,
        exit_price=64000.0,
        pnl_usdt=-1.0,
        pnl_pct=-1.54,
        reason="STOP_LOSS"
    )

    assert lesson_id is None
    await trader.close()


# =====================================================================
# 3. NON-BLOCKING LATENCY TEST (< 5.0ms under 1,000ms AI delay)
# =====================================================================

@pytest.mark.asyncio
async def test_close_position_non_blocking_latency(test_db):
    """
    Verify _close_position completes execution in strictly < 5.0ms using time.perf_counter()
    even when the post-mortem network call takes 1,000ms (simulated AI latency).
    """
    event_bus = EventBus()
    circuit_breaker = CircuitBreaker()
    circuit_breaker.reset_daily_metrics(100.0)

    async def slow_generate(trade_info):
        await asyncio.sleep(1.0)
        return {
            "category": "STOP_LOSS",
            "title": "Slow AI Post Mortem",
            "details": "Completed after 1,000ms delay",
            "capital_impact": 2.0,
            "lesson_learned": "Execution thread was never blocked",
            "operator": "Claude-3.5-Sonnet"
        }

    mock_vyce = MagicMock(spec=VyceClient)
    mock_vyce.generate_post_mortem = AsyncMock(side_effect=slow_generate)

    audit_logs = []
    trader = PaperTrader(
        event_bus=event_bus,
        db=test_db,
        circuit_breaker=circuit_breaker,
        vyce_client=mock_vyce,
        audit_logs=audit_logs
    )

    pos_key = "EMA_Trend_BTC/USDT"
    trader.open_positions[pos_key] = {
        "order_id": "ORD-LATENCY-001",
        "strategy_name": "EMA_Trend",
        "symbol": "BTC/USDT",
        "side": OrderSide.BUY,
        "entry_price": 60000.0,
        "quantity": 0.001,
        "stop_loss": 59000.0,
        "take_profit": 62000.0,
        "entry_time": datetime.now(timezone.utc),
        "fee": 0.06
    }

    t0 = time.perf_counter()
    await trader._close_position(pos_key, exit_price=58900.0, reason="STOP_LOSS")
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # 1. Strict non-blocking latency constraint: must return in < 5.0ms
    assert elapsed_ms < 5.0, f"_close_position took {elapsed_ms:.2f}ms, expected strictly < 5.0ms"

    # 2. Position is already closed
    assert pos_key not in trader.open_positions
    assert len(trader._background_tasks) == 1

    # 3. Await background post-mortem task to finish gracefully
    await asyncio.gather(*trader._background_tasks)
    assert len(trader._background_tasks) == 0

    # 4. Verify lesson recorded in database
    lessons = await test_db.get_lessons()
    assert any(l["title"] == "Slow AI Post Mortem" for l in lessons)

    await trader.close()


# =====================================================================
# 4. API ROUTE TEST FOR /api/v1/lessons ORDERING
# =====================================================================

@pytest.mark.asyncio
async def test_api_lessons_ordering_timestamp_desc(tmp_path):
    """Verify /api/v1/lessons returns records strictly ordered by timestamp DESC, id DESC."""
    db_file = str(tmp_path / "test_api_ordering.db")
    db = Database(db_file)
    await db.connect()

    # Clear existing seeded lessons for strict ordering verification
    async with db._conn.cursor() as cursor:
        await cursor.execute("DELETE FROM trading_lessons")
        # Insert lessons with distinct timestamps in non-chronological order
        await cursor.execute("""
            INSERT INTO trading_lessons (timestamp, category, title, details, capital_impact, lesson_learned, operator)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("2026-09-17T08:00:00Z", "STOP_LOSS", "Morning Stop Loss", "Details 1", 5.0, "Lesson 1", "Claude"))
        await cursor.execute("""
            INSERT INTO trading_lessons (timestamp, category, title, details, capital_impact, lesson_learned, operator)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("2026-09-17T12:00:00Z", "SLIPPAGE", "Noon Slippage", "Details 2", 10.0, "Lesson 2", "Claude"))
        await cursor.execute("""
            INSERT INTO trading_lessons (timestamp, category, title, details, capital_impact, lesson_learned, operator)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("2026-09-17T10:00:00Z", "VOLATILITY_SPIKE", "Midday Volatility", "Details 3", 7.5, "Lesson 3", "Claude"))
        await db._conn.commit()

    cb = CircuitBreaker()
    app = create_web_app(db=db, circuit_breaker=cb)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/lessons")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        timestamps = [item["timestamp"] for item in data]
        # Must be strictly descending: 12:00:00Z, 10:00:00Z, 08:00:00Z
        expected_timestamps = sorted(timestamps, reverse=True)
        assert timestamps == expected_timestamps
        assert data[0]["title"] == "Noon Slippage"
        assert data[1]["title"] == "Midday Volatility"
        assert data[2]["title"] == "Morning Stop Loss"

    await db.close()


# =====================================================================
# 5. TEST FOR close() METHOD WAITING FOR BACKGROUND TASKS
# =====================================================================

@pytest.mark.asyncio
async def test_execution_close_awaits_background_tasks(test_db):
    """Verify close() method waits for running tasks and cancels hanging tasks beyond timeout."""
    event_bus = EventBus()
    cb = CircuitBreaker()
    pt = PaperTrader(event_bus=event_bus, db=test_db, circuit_breaker=cb)

    # 1. Normal task completes within close() timeout
    completed_flag = False

    async def quick_task():
        nonlocal completed_flag
        await asyncio.sleep(0.05)
        completed_flag = True

    t1 = asyncio.create_task(quick_task())
    pt._background_tasks.add(t1)
    t1.add_done_callback(pt._background_tasks.discard)

    await pt.close(timeout=1.0)
    assert completed_flag is True
    assert t1.done() is True
    assert len(pt._background_tasks) == 0

    # 2. Hanging task is cancelled if exceeding timeout
    async def hanging_task():
        await asyncio.sleep(10.0)

    t2 = asyncio.create_task(hanging_task())
    pt._background_tasks.add(t2)
    t2.add_done_callback(pt._background_tasks.discard)

    await pt.close(timeout=0.05)
    assert t2.done() is True
    assert t2.cancelled() is True

    # 3. Verify BinanceExecutor close() works identically
    mock_binance = MagicMock(spec=BinanceClient)
    be = BinanceExecutor(event_bus=event_bus, binance_client=mock_binance, db=test_db)
    be_completed = False

    async def be_quick_task():
        nonlocal be_completed
        await asyncio.sleep(0.05)
        be_completed = True

    t3 = asyncio.create_task(be_quick_task())
    be._background_tasks.add(t3)
    t3.add_done_callback(be._background_tasks.discard)

    await be.close(timeout=1.0)
    assert be_completed is True
    assert t3.done() is True
