"""
GEMINI MULTI-ACCOUNT KEY POOL & DAILY QUOTA MONITOR
---------------------------------------------------
Quản lý bể chứa API Key Google Gemini từ nhiều tài khoản Google khác nhau:
- Mỗi tài khoản Google miễn phí 1,500 requests/ngày (reset 00:00 UTC).
- Tự động đếm số request trong ngày của từng key.
- Tự động xoay tua (Auto-rotate) sang key tiếp theo khi key hiện tại chạm 80% (1,200 req) hoặc dính lỗi 429 (Rate Limit).
- Tự động gửi cảnh báo qua Telegram báo Admin đăng nhập tài khoản Google khác để lấy thêm key dự phòng.
"""

import os
import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import httpx
from config.settings import settings

logger = logging.getLogger("GeminiPool")

DAILY_FREE_QUOTA_LIMIT = 1500
WARNING_THRESHOLD_REQ = 1200  # 80% of daily quota


class GeminiKeyPool:
    def __init__(self):
        self._keys: List[Dict[str, Any]] = []
        self._active_index: int = 0
        self._last_reset_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._init_pool()

    def _init_pool(self):
        # Read from GEMINI_API_KEYS or GEMINI_API_KEY
        raw_keys = os.getenv("GEMINI_API_KEYS", "") or getattr(settings, "GEMINI_API_KEYS", "")
        if not raw_keys:
            single = os.getenv("GEMINI_API_KEY", "") or getattr(settings, "GEMINI_API_KEY", "")
            raw_keys = single or "AQ.REDACTED_GEMINI_KEY"

        key_list = [k.strip() for k in raw_keys.replace(";", ",").split(",") if k.strip()]
        self._keys = []
        for idx, k in enumerate(key_list):
            masked = (k[:6] + "..." + k[-4:]) if len(k) > 10 else k
            self._keys.append({
                "index": idx + 1,
                "key": k,
                "masked": masked,
                "requests_today": 0,
                "status": "ACTIVE",
                "last_error": None,
                "last_used": None
            })
        self._active_index = 0
        logger.info(f"[GeminiPool] Khởi tạo thành công với {len(self._keys)} Google Gemini API Key.")

    def _check_daily_reset(self):
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if current_date != self._last_reset_date:
            logger.info(f"[GeminiPool] Reset hạn mức ngày mới ({current_date}).")
            self._last_reset_date = current_date
            for k in self._keys:
                k["requests_today"] = 0
                k["status"] = "ACTIVE"
                k["last_error"] = None
            self._active_index = 0

    def get_active_key(self) -> str:
        self._check_daily_reset()
        if not self._keys:
            return "AQ.REDACTED_GEMINI_KEY"

        # Find first ACTIVE key
        start_idx = self._active_index
        for i in range(len(self._keys)):
            idx = (start_idx + i) % len(self._keys)
            k_info = self._keys[idx]
            if k_info["status"] in ("ACTIVE", "WARNING_80"):
                self._active_index = idx
                k_info["requests_today"] += 1
                k_info["last_used"] = datetime.now(timezone.utc).isoformat()
                
                # Check threshold warning
                if k_info["requests_today"] >= WARNING_THRESHOLD_REQ and k_info["status"] != "WARNING_80":
                    k_info["status"] = "WARNING_80"
                    asyncio.create_task(self._send_quota_warning(k_info, reason="Chạm 80% hạn mức ngày"))
                return k_info["key"]

        # All keys exhausted or rate-limited
        asyncio.create_task(self._send_all_exhausted_alert())
        return self._keys[0]["key"]

    async def mark_rate_limited(self, key: str, error_msg: str = ""):
        """Đánh dấu key bị lỗi 429 Rate Limit / Quota Exceeded và xoay tua ngay sang key kế tiếp."""
        self._check_daily_reset()
        matched = None
        for k_info in self._keys:
            if k_info["key"] == key:
                k_info["status"] = "RATE_LIMITED"
                k_info["last_error"] = error_msg
                matched = k_info
                break

        old_idx = self._active_index
        self._active_index = (self._active_index + 1) % len(self._keys)
        next_key = self._keys[self._active_index]

        logger.warning(
            f"[GeminiPool] Key #{matched['index'] if matched else '?'} dính lỗi 429/Hết Quota! "
            f"Tự động xoay tua sang Key #{next_key['index']} ({next_key['masked']})."
        )

        if matched:
            await self._send_quota_warning(matched, reason=f"Lỗi 429 Rate Limit / Quota Exceeded: {error_msg}")

    async def _send_quota_warning(self, key_info: Dict[str, Any], reason: str):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            return

        total_keys = len(self._keys)
        active_remaining = sum(1 for k in self._keys if k["status"] in ("ACTIVE", "WARNING_80"))

        msg = (
            f"⚠️ *[CẢNH BÁO QUOTA GOOGLE GEMINI]*\n"
            f"----------------------------------------\n"
            f"🔑 *Key:* #{key_info['index']} (`{key_info['masked']}`)\n"
            f"📊 *Đã dùng:* {key_info['requests_today']}/{DAILY_FREE_QUOTA_LIMIT} requests hôm nay\n"
            f"⚡ *Lý do:* {reason}\n"
            f"🔄 *Trạng thái:* Hệ thống đã tự động xoay tua sang Key tiếp theo (Còn {active_remaining}/{total_keys} keys khả dụng).\n\n"
            f"👉 *Hành động cần làm:* Bạn vui lòng đăng nhập tài khoản Google khác tại [aistudio.google.com](https://aistudio.google.com/app/apikey) lấy thêm key và thêm vào `GEMINI_API_KEYS` nhé!"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.warning(f"[GeminiPool] Lỗi gửi cảnh báo Telegram: {e}")

    async def _send_all_exhausted_alert(self):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            return

        msg = (
            f"🚨 *[KHẨN CẤP - TOÀN BỘ KEY GEMINI ĐÃ CẠN]*\n"
            f"----------------------------------------\n"
            f"Toàn bộ {len(self._keys)} API Key Google Gemini trong pool đều đã đạt hạn mức 1,500 req/ngày hoặc bị 429!\n"
            f"Hệ thống đang tự động kích hoạt fallback sang Groq / Vyce AI.\n\n"
            f"👉 *Vui lòng đăng nhập ngay tài khoản Google mới* tại [aistudio.google.com](https://aistudio.google.com/app/apikey) lấy thêm Key mới để bổ sung!"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.warning(f"[GeminiPool] Lỗi gửi cảnh báo Telegram: {e}")

    def get_pool_status(self) -> List[Dict[str, Any]]:
        self._check_daily_reset()
        return [
            {
                "index": k["index"],
                "masked": k["masked"],
                "requests_today": k["requests_today"],
                "quota_limit": DAILY_FREE_QUOTA_LIMIT,
                "status": k["status"],
                "last_used": k["last_used"]
            }
            for k in self._keys
        ]


# Singleton instance
gemini_pool = GeminiKeyPool()
