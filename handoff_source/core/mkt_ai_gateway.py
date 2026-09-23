"""
core/mkt_ai_gateway.py
MKT NIVER - MULTI-TIER AI ROUTING GATEWAY (TRADING BOT INTEGRATION)
"""
import logging
import time
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger("MktAIGateway")

VYCE_API_KEY_MKT = "***REDACTED***"
VYCE_BASE_URL = "https://vyceai.com/v1"
NINEROUTER_BASE_URL = "http://localhost:20128/v1"
NINEROUTER_API_KEY = "***REDACTED***"
BAI_API_ENDPOINT = "https://api.b.ai/v1/chat/completions"
BAI_API_KEYS = [
    "***REDACTED***",
    "***REDACTED***",
    "***REDACTED***",
]

MKT_DEPT_MODELS = {
    "captain": "agnes-3.0-flash",       # Vyce AI (512K Context, Agentic Flagship)
    "content_lab": "claude-sonnet-4-6", # Vyce AI (Deep reasoning & Viral Hook)
    "video_forge": "cx/gpt-5.6-terra",  # 9Router (FFmpeg scripts & Timeline)
    "ads_engine": "claude-sonnet-4-6",  # Vyce AI (CPA & Conversion Copy)
    "seeding_ops": "deepseek-v4-flash", # Vyce AI (Fast crowd simulator)
    "trend_scout": "cx/gpt-6-astra",    # 9Router (TikTok & Trend Radar)
    "risk_guard": "claude-sonnet-4-6",  # Vyce AI (Meta Policy & Anti-Checkpoint)
    "affiliate_desk": "cx/gpt-5.6-luna",# 9Router (Shopee Cookie Trap)
    "crm_support": "deepseek-v4.1",     # Vyce AI (Gemini Jio Fulfillment)
    "analytics_pm": "deepseek-v4-flash",# Vyce AI (Signal Telemetry & FLOP Forensic)
    "page_router": "cx/gpt-5.6-terra",  # 9Router (22 Fanpages Matrix Dispatch)
    "asset_guard": "local-hash"         # Local Perceptual Fingerprint
}

class MktAIGateway:
    def __init__(self):
        self._bai_key_index = 0
        self._browser_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        }

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "You are an elite marketing and viral growth intelligence agent.",
        model: Optional[str] = None,
        dept_code: Optional[str] = None,
        max_tokens: int = 800,
        temperature: float = 0.7,
        timeout: float = 20.0
    ) -> Dict[str, Any]:
        target_model = model or (MKT_DEPT_MODELS.get(dept_code, "agnes-3.0-flash") if dept_code else "agnes-3.0-flash")
        
        # 1. 9Router
        if target_model.startswith("cx/") or "gpt-5.6" in target_model or "gpt-6" in target_model:
            res = await self._call_9router(prompt, system_prompt, target_model, max_tokens, temperature, timeout)
            if res.get("success"):
                return res
            target_model = "agnes-3.0-flash"

        # 2. Vyce AI
        res = await self._call_vyce(prompt, system_prompt, target_model, max_tokens, temperature, timeout)
        if res.get("success"):
            return res

        # 3. 9Router Fallback
        res = await self._call_9router(prompt, system_prompt, "cx/gpt-5.6-terra", max_tokens, temperature, timeout)
        if res.get("success"):
            return res

        # 4. B.AI Pool
        return await self._call_bai_pool(prompt, system_prompt, max_tokens, temperature, timeout)

    async def _call_vyce(self, prompt, system_prompt, model, max_tokens, temperature, timeout):
        headers = {**self._browser_headers, "Authorization": f"Bearer {VYCE_API_KEY_MKT}"}
        url = f"{VYCE_BASE_URL.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": temperature
        }
        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(url, json=payload, headers=headers)
                lat_ms = (time.time() - t0) * 1000.0
                if r.status_code == 200:
                    data = r.json()
                    return {"success": True, "provider": "Vyce AI", "model": model, "content": data["choices"][0]["message"]["content"], "latency_ms": round(lat_ms, 1)}
                return {"success": False, "status": r.status_code, "error": r.text[:200]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _call_9router(self, prompt, system_prompt, model, max_tokens, temperature, timeout):
        headers = {**self._browser_headers, "Authorization": f"Bearer {NINEROUTER_API_KEY}"}
        url = f"{NINEROUTER_BASE_URL.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": temperature
        }
        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(url, json=payload, headers=headers)
                lat_ms = (time.time() - t0) * 1000.0
                if r.status_code == 200:
                    data = r.json()
                    return {"success": True, "provider": "9Router (VPS Local)", "model": model, "content": data["choices"][0]["message"]["content"], "latency_ms": round(lat_ms, 1)}
                return {"success": False, "status": r.status_code, "error": r.text[:200]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _call_bai_pool(self, prompt, system_prompt, max_tokens, temperature, timeout):
        key = BAI_API_KEYS[self._bai_key_index % len(BAI_API_KEYS)]
        self._bai_key_index += 1
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": "glm-5.3-flash",
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": temperature
        }
        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(BAI_API_ENDPOINT, json=payload, headers=headers)
                lat_ms = (time.time() - t0) * 1000.0
                if r.status_code == 200:
                    data = r.json()
                    return {"success": True, "provider": "B.AI Pool (0-Cost)", "model": "glm-5.3-flash", "content": data["choices"][0]["message"]["content"], "latency_ms": round(lat_ms, 1)}
                return {"success": False, "status": r.status_code, "error": r.text[:200]}
        except Exception as e:
            return {"success": False, "error": str(e)}

mkt_ai_gateway = MktAIGateway()
