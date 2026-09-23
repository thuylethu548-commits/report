import pytest
from core.constants import OrderSide
from execution.trailing_stop import TrailingStopManager


def test_trailing_stop_break_even_lock():
    mgr = TrailingStopManager()
    state = mgr.register_position(
        order_id="TEST-BE-001",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        entry_price=60000.0,
        initial_stop_loss=59000.0,
        initial_take_profit=63000.0,
        quantity=0.01,
        break_even_threshold_pct=0.012
    )

    # 1. Price moves up +0.5% (60300) -> Break-even should NOT trigger
    res1 = mgr.update_price("TEST-BE-001", current_price=60300.0)
    assert res1 is None
    assert state.break_even_triggered is False
    assert state.current_stop_loss == 59000.0

    # 2. Price moves up +1.3% (60780) -> Break-even SHOULD trigger
    res2 = mgr.update_price("TEST-BE-001", current_price=60780.0)
    assert res2 is not None
    assert res2["action"] == "BREAK_EVEN_LOCK"
    assert res2["new_sl"] == round(60000.0 * 1.002, 2)
    assert state.break_even_triggered is True
    assert state.current_stop_loss == 60120.0


def test_dynamic_trailing_stop_advancement():
    mgr = TrailingStopManager()
    state = mgr.register_position(
        order_id="TEST-TS-002",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        entry_price=60000.0,
        initial_stop_loss=59000.0,
        initial_take_profit=66000.0,
        quantity=0.01,
        trailing_activation_pct=0.020, # 2.0%
        atr_multiplier=1.0
    )

    # 1. Price climbs to +2.5% (61500), with ATR = 300
    res = mgr.update_price("TEST-TS-002", current_price=61500.0, current_atr=300.0)
    assert res is not None
    # Candidate SL = 61500 - 300 = 61200 > 59000
    assert state.current_stop_loss == 61200.0
    assert res["new_sl"] == 61200.0

    # 2. Price jumps to 62500, with ATR = 300
    res2 = mgr.update_price("TEST-TS-002", current_price=62500.0, current_atr=300.0)
    assert res2 is not None
    # Candidate SL = 62500 - 300 = 62200
    assert state.current_stop_loss == 62200.0
    assert res2["new_sl"] == 62200.0

    # 3. Price pulls back to 62300 -> SL should stay at 62200 (never loosen!)
    res3 = mgr.update_price("TEST-TS-002", current_price=62300.0, current_atr=300.0)
    assert res3 is None
    assert state.current_stop_loss == 62200.0


def test_dead_trade_timer_profit_lock():
    from datetime import datetime, timezone, timedelta
    mgr = TrailingStopManager()
    past_time = datetime.now(timezone.utc) - timedelta(hours=2, minutes=5) # 2h 5m ago

    state = mgr.register_position(
        order_id="TEST-DEAD-003",
        symbol="ETH/USDT",
        side=OrderSide.BUY,
        entry_price=2480.0,
        initial_stop_loss=2440.0,
        initial_take_profit=2550.0,
        quantity=0.01,
        entry_time=past_time
    )

    # If position has stalled for 2h and is slightly green (2490.0, +0.4%), dead trade timer locks in profit
    now_time = datetime.now(timezone.utc)
    res = mgr.check_dead_trade_timer("TEST-DEAD-003", current_price=2490.0, current_time=now_time)
    assert res is not None
    assert res["action"] == "DEAD_TRADE_PROFIT_LOCK"
    assert res["new_sl"] == round(2480.0 * 1.001, 2)
    assert state.break_even_triggered is True
    assert state.current_stop_loss == 2482.48

