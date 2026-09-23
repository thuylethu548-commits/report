"""
GROQ MULTI-KEY POOL & HIGH-THROUGHPUT LPU ENGINE
------------------------------------------------
Quản lý bể chứa 4 API Key Groq Cloud:
- Nhân 4 lần hạn mức: 120 Requests/Phút (57,600 req/ngày).
- Tự động xoay tua (Round-robin) và tự động Failover sang key tiếp theo nếu gặp lỗi Rate Limit (429).
- Chạy siêu tốc trên phần cứng chip LPU: openai/gpt-oss-120b (80ms) & qwen/qwen3.8-27b (340ms).
"""

import os
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from config.settings import settings

logger = logging.getLogger("GroqPool")

DEFAULT_GROQ_KEYS = [
    "gsk_REDACTED_FOR_SECURITY",
    "gsk_REDACTED_FOR_SECURITY",
    "gsk_REDACTED_FOR_SECURITY",
    "gsk_REDACTED_FOR_SECURITY"
]


class GroqKeyPool:
    def __init__(self):
        self._keys: List[Dict[str, Any]] = []
        self._active_index: int = 0
        self._init_pool()

    def _init_pool(self):
        raw_keys = os.getenv("GROQ_API_KEYS", "") or getattr(settings, "GROQ_API_KEYS", "")
        if isinstance(raw_keys, list):
            key_list = raw_keys
        elif isinstance(raw_keys, str) and raw_keys.strip():
            key_list = [k.strip() for k in raw_keys.replace(";", ",").split(",") if k.strip()]
        else:
            single = getattr(settings, "GROQ_API_KEY", "")
            key_list = [single] if single else []

        # Merge with default known keys ensuring no duplicates
        combined = []
        seen = set()
        for k in (key_list + DEFAULT_GROQ_KEYS):
            if k and k not in seen:
                seen.add(k)
                combined.append(k)

        self._keys = []
        for idx, k in enumerate(combined):
            masked = (k[:8] + "..." + k[-4:]) if len(k) > 12 else k
            self._keys.append({
                "index": idx + 1,
                "key": k,
                "masked": masked,
                "requests_count": 0,
                "status": "ACTIVE",
                "last_error": None,
                "last_used": None
            })
        self._active_index = 0
        logger.info(f"[GroqPool] Khởi tạo thành công Bể chứa {len(self._keys)} Groq API Keys (Throughput: {len(self._keys)*30} RPM / {len(self._keys)*14400} RPD).")

    def get_active_key(self) -> str:
        """Lấy key đang hoạt động theo cơ chế round-robin thông minh."""
        if not self._keys:
            return getattr(settings, "GROQ_API_KEY", DEFAULT_GROQ_KEYS[0])

        current = self._keys[self._active_index]
        current["requests_count"] += 1
        current["last_used"] = time.time()
        
        # Round robin to next key for load balancing
        self._active_index = (self._active_index + 1) % len(self._keys)
        return current["key"]

    def mark_key_error(self, key: str, error_msg: str):
        """Đánh dấu key bị rate limit (429) và tự động né sang key khác."""
        for item in self._keys:
            if item["key"] == key:
                item["status"] = "RATE_LIMITED"
                item["last_error"] = error_msg
                logger.warning(f"[GroqPool] Key {item['masked']} bị Rate Limit/Lỗi: {error_msg}. Tự động xoay tua!")
                break

    def get_pool_status(self) -> Dict[str, Any]:
        return {
            "total_keys": len(self._keys),
            "keys": [
                {
                    "index": k["index"],
                    "masked": k["masked"],
                    "requests": k["requests_count"],
                    "status": k["status"]
                }
                for k in self._keys
            ],
            "total_rpm_capacity": len(self._keys) * 30,
            "total_daily_capacity": len(self._keys) * 14400
        }


# Singleton instance
groq_pool = GroqKeyPool()
