import asyncio
import sys
import time
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath("."))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.event_bus import EventBus
from core.events import SignalEvent, MarketEvent, OrderEvent
from core.constants import OrderSide, OrderType
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
from risk_engine.risk_manager import RiskManager
from execution.paper_trader import PaperTrader
from ai_advisory.vyce_client import VyceClient

async def test_full_pipeline():
    print("=" * 60)
    print("VICTORY AUDIT: Independent E2E Integration & Stress Test")
    print("=" * 60)

    db = Database("trading_bot.db")
    await db.connect()
    event_bus = EventBus()
    event_bus.start()

    circuit_breaker = CircuitBreaker()
    circuit_breaker.reset_daily_metrics(100.0)
    vyce_client = VyceClient()

    audit_logs = []
    risk_manager = RiskManager(event_bus, db, circuit_breaker, vyce_client=vyce_client, audit_logs=audit_logs)
    paper_trader = PaperTrader(event_bus, db, circuit_breaker, vyce_client=vyce_client, audit_logs=audit_logs)

    # 1. Test AI Advisory Veto when Stop-Loss is invalid (too wide, e.g. 10%)
    print("\n--- 1. Testing Signal Veto on Unsafe Risk (Stop Loss 10% wide) ---")
    unsafe_signal = SignalEvent(
        strategy_name="EMA_Cross",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        stop_loss=53000.0,  # 11.6% stop loss -> outside [0.5%, 5.0%] corridor
        take_profit=66000.0,
        confidence=0.85,
        timestamp=datetime.now(timezone.utc)
    )

    t0 = time.perf_counter()
    order = await risk_manager.handle_signal(unsafe_signal)
    t_elapsed = (time.perf_counter() - t0) * 1000
    print(f"RiskManager processed unsafe signal in {t_elapsed:.1f}ms: order={order}")
    assert order is None, "Expected order to be VETOED by RiskManager!"
    print("[PASS] Unsafe signal correctly VETOED by Risk Gatekeeper.")

    # 2. Test Post-Mortem Generation on Stop-Loss
    print("\n--- 2. Testing PaperTrader Stop-Loss & Auto Post-Mortem ---")
    # Open a position
    buy_order = OrderEvent(
        order_id="AUDIT-SL-001",
        strategy_name="EMA_Cross",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        price=60000.0,
        quantity=0.001,
        stop_loss=59400.0, # 1.0% stop loss
        take_profit=62000.0,
        timestamp=datetime.now(timezone.utc)
    )
    await paper_trader.handle_order(buy_order)
    assert len(paper_trader.open_positions) == 1, "Position should be open"
    print(f"[PASS] Position opened: {paper_trader.open_positions.get('AUDIT-SL-001', {}).get('symbol')}")

    # Count lessons before
    lessons_before = await db.get_lessons(limit=10)
    count_before = len(lessons_before)

    # Price drops through stop loss (59300 <= 59400)
    drop_market = MarketEvent(
        symbol="BTC/USDT",
        open=59500.0,
        high=59550.0,
        low=59200.0,
        close=59300.0,
        volume=5.0,
        timestamp=datetime.now(timezone.utc)
    )
    t_drop_start = time.perf_counter()
    await paper_trader.handle_market_tick(drop_market)
    t_drop_elapsed = (time.perf_counter() - t_drop_start) * 1000
    print(f"Position closed on Stop-Loss. Non-blocking handle_market_tick returned in {t_drop_elapsed:.2f}ms")
    assert t_drop_elapsed < 50.0, f"SLA violated: tick handling took {t_drop_elapsed:.2f}ms"
    assert len(paper_trader.open_positions) == 0, "Position should be closed"

    # Await background post-mortem task
    print("Waiting for background Post-Mortem task to complete...")
    await paper_trader.close(timeout=8.0)

    # Verify lesson in SQLite
    lessons_after = await db.get_lessons(limit=10)
    print(f"Lessons count before: {count_before}, after: {len(lessons_after)}")
    assert len(lessons_after) == count_before + 1, "Expected new lesson recorded in trading_lessons!"
    new_lesson = lessons_after[0]
    print(f"New Lesson recorded: ID={new_lesson['id']} | Category={new_lesson['category']} | Title='{new_lesson['title']}' | Operator='{new_lesson['operator']}'")
    assert new_lesson["category"] == "STOP_LOSS"
    assert "Dừng lỗ" in new_lesson["title"] or "Stop" in new_lesson["title"] or "Cắt lỗ" in new_lesson["title"]

    # 3. Clean up the audit trade & lesson
    await db.delete_lesson(new_lesson["id"])
    print("[PASS] Test lesson cleaned up.")

    await event_bus.stop()
    await vyce_client.close()
    await db.close()
    print("=" * 60)
    print("ALL INDEPENDENT PIPELINE TESTS PASSED.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
