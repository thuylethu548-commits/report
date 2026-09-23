import pytest
from datetime import datetime, timezone, timedelta
from risk_engine.time_window_guard import TimeWindowRiskGuard, VN_TIMEZONE


def test_funding_rate_red_flag():
    guard = TimeWindowRiskGuard()

    # 14:58 VN time -> 2 mins before 15:00 funding rate settlement -> MUST BE RED FLAG
    dt_vn_1458 = datetime(2026, 9, 18, 14, 58, tzinfo=VN_TIMEZONE)
    is_rf, reason = guard.is_red_flag_window(dt_vn_1458)
    assert is_rf is True
    assert "Funding Rate" in reason

    # 15:10 VN time -> safely past funding transition -> NOT RED FLAG
    dt_vn_1510 = datetime(2026, 9, 18, 15, 10, tzinfo=VN_TIMEZONE)
    is_rf2, _ = guard.is_red_flag_window(dt_vn_1510)
    assert is_rf2 is False


def test_golden_window_detection():
    guard = TimeWindowRiskGuard()

    # 16:15 VN time on Friday -> London Open -> Golden Window
    dt_vn_london = datetime(2026, 9, 18, 16, 15, tzinfo=VN_TIMEZONE)
    is_gw, session = guard.is_golden_window(dt_vn_london)
    assert is_gw is True
    assert "CHÂU ÂU" in session

    # 20:45 VN time on Friday -> New York Peak -> Golden Window
    dt_vn_ny = datetime(2026, 9, 18, 20, 45, tzinfo=VN_TIMEZONE)
    is_gw2, session2 = guard.is_golden_window(dt_vn_ny)
    assert is_gw2 is True
    assert "PHIÊN MỸ" in session2


def test_weekend_chop_red_flag():
    guard = TimeWindowRiskGuard()

    # Saturday 16:00 VN time (weekday = 5) -> Weekend chop
    dt_sat = datetime(2026, 9, 19, 16, 0, tzinfo=VN_TIMEZONE)
    is_rf, reason = guard.is_red_flag_window(dt_sat)
    assert is_rf is True
    assert "Weekend" in reason


def test_get_window_status():
    guard = TimeWindowRiskGuard()
    status = guard.get_window_status()
    assert "current_time_vn" in status
    assert "recommendation" in status
