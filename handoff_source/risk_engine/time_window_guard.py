import logging
from datetime import datetime, timezone, timedelta
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger("TimeWindowRiskGuard")

# Vietnam Timezone is UTC+7
VN_TIMEZONE = timezone(timedelta(hours=7))


class TimeWindowRiskGuard:
    """
    Time Window & Market Session Risk Engine for Vietnamese & Global Crypto Markets.
    - Identifies Red Flag windows (Funding Rate transitions, High-impact CPI/FOMC, Weekend chop).
    - Identifies Golden Trading Windows (London Open, New York Peak Liquidity).
    """

    def __init__(
        self,
        enable_funding_guard: bool = True,
        enable_weekend_guard: bool = True,
        enable_golden_boost: bool = True
    ):
        self.enable_funding_guard = enable_funding_guard
        self.enable_weekend_guard = enable_weekend_guard
        self.enable_golden_boost = enable_golden_boost

    def to_vietnam_time(self, dt: Optional[datetime] = None) -> datetime:
        """Converts UTC or naive datetime to Vietnam Time (UTC+7)."""
        now_dt = dt or datetime.now(timezone.utc)
        if now_dt.tzinfo is None:
            now_dt = now_dt.replace(tzinfo=timezone.utc)
        return now_dt.astimezone(VN_TIMEZONE)

    def is_red_flag_window(self, dt: Optional[datetime] = None) -> Tuple[bool, str]:
        """
        Checks whether the current time falls inside a dangerous high-risk 'Red Flag' window.
        Returns: (is_red_flag, reason)
        """
        vn_time = self.to_vietnam_time(dt)
        hour = vn_time.hour
        minute = vn_time.minute
        weekday = vn_time.weekday()  # Monday is 0, Sunday is 6

        # 1. Funding Rate Transition Window (06:55-07:05, 14:55-15:05, 22:55-23:05 VN time)
        # Arbitrage bots rebalance aggressively, creating flash wicks and spreads.
        if self.enable_funding_guard:
            for funding_hour in (7, 15, 23):
                # 5 mins before funding hour (e.g. 06:55 to 06:59)
                if hour == (funding_hour - 1) and minute >= 55:
                    return True, f"RED FLAG: Mốc giao điểm Funding Rate sàn Binance ({funding_hour:02d}:00 VN). Bot tạm dừng tránh râu quét."
                # 5 mins after funding hour (e.g. 07:00 to 07:05)
                if hour == funding_hour and minute <= 5:
                    return True, f"RED FLAG: Mốc vừa chốt Funding Rate sàn Binance ({funding_hour:02d}:00 VN). Chờ thanh khoản ổn định."

        # 2. Weekend Low-Liquidity Chop (Saturday 14:00 to Sunday 20:00 VN time)
        # Wall Street is closed, thin liquidity allows easy manipulation/stop-hunts.
        if self.enable_weekend_guard:
            if weekday == 5 and hour >= 14:  # Saturday afternoon
                return True, "RED FLAG: Phiên cuối tuần thanh khoản mỏng (Weekend Low-Liquidity Chop). Nguy cơ bẫy giá cao."
            if weekday == 6 and hour < 20:   # Sunday morning/afternoon
                return True, "RED FLAG: Phiên Chủ Nhật chờ phiên Mỹ mở cửa. Tránh vào lệnh khi thị trường đi ngang."

        # 3. High-impact Macro News Storm Windows (19:25 - 19:40 on weekdays)
        # Common release time for US CPI, Core PCE, and NFP (Vietnam Time)
        if weekday < 5 and hour == 19 and (25 <= minute <= 40):
            return True, "RED FLAG: Khung giờ tin tức vĩ mô bão giật (CPI / NFP 19:30 VN). Tạm dừng mở vị thế mới."

        return False, ""

    def is_golden_window(self, dt: Optional[datetime] = None) -> Tuple[bool, str]:
        """
        Checks whether the current time falls inside a high-probability 'Golden Window'.
        Returns: (is_golden, session_name)
        """
        vn_time = self.to_vietnam_time(dt)
        hour = vn_time.hour
        minute = vn_time.minute
        weekday = vn_time.weekday()

        if weekday >= 5:  # Weekends generally don't have golden sessions
            return False, ""

        # 1. New York Peak Liquidity Window (19:30 - 22:30 VN time)
        if (hour == 19 and minute >= 30) or (20 <= hour <= 22) or (hour == 22 and minute <= 30):
            return True, "KHUNG GIỜ VÀNG PHIÊN MỸ (19:30 - 22:30 VN): Thanh khoản cực đại, sóng Breakout chuẩn xác nhất."

        # 2. London Open Session (15:00 - 17:30 VN time)
        if (15 <= hour <= 16) or (hour == 17 and minute <= 30):
            return True, "KHUNG GIỜ VÀNG PHIÊN CHÂU ÂU (15:00 - 17:30 VN): Dòng tiền London mở cửa, xu hướng rõ nét."

        # 3. Asia Early Morning Reaction Window (07:30 - 09:00 VN time)
        if (hour == 7 and minute >= 30) or (hour == 8):
            return True, "KHUNG GIỜ PHIÊN CHÂU Á (07:30 - 09:00 VN): Phản ứng sau khi phiên Mỹ đóng cửa."

        return False, ""

    def get_window_status(self, dt: Optional[datetime] = None) -> Dict[str, Any]:
        """Returns structured status for dashboard and risk engine telemetry."""
        vn_time = self.to_vietnam_time(dt)
        is_rf, rf_reason = self.is_red_flag_window(dt)
        is_gw, gw_session = self.is_golden_window(dt)

        return {
            "current_time_vn": vn_time.strftime("%Y-%m-%d %H:%M:%S (UTC+7)"),
            "is_red_flag": is_rf,
            "red_flag_reason": rf_reason,
            "is_golden_window": is_gw,
            "golden_window_name": gw_session,
            "recommendation": "HALT_NEW_TRADES" if is_rf else ("BOOST_CONVICTION" if is_gw else "STANDARD_TRADING")
        }
