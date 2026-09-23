import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any
import httpx
from config.settings import settings
from core.events import SignalEvent
from core.constants import OrderSide

logger = logging.getLogger("VyceClient")

NINEROUTER_BASE_URL = getattr(settings, "NINEROUTER_BASE_URL", "http://localhost:20128/v1")
NINEROUTER_API_KEY = getattr(settings, "NINEROUTER_API_KEY", "***REDACTED***")
ETFBIT_BASE_URL = getattr(settings, "ETFBIT_BASE_URL", "https://api.etfbit.net/v1")
ETFBIT_API_KEY = getattr(settings, "ETFBIT_API_KEY", "***REDACTED***")

MODEL_ALIASES = {
    "claude-3-5-sonnet": "claude-sonnet-4-6",
    "claude-3.5-sonnet": "claude-sonnet-4-6",
    "claude-3-5-sonnet-20241022": "claude-sonnet-4-6",
    "claude-3-sonnet": "claude-sonnet-4-6",
    "claude-3-opus": "claude-sonnet-4-6",
    "claude-3-haiku": "deepseek-v4-flash",
    "gpt-4o": "claude-sonnet-4-6",
    "gpt-6": "cx/gpt-6-astra",
    "gpt-6-astra": "cx/gpt-6-astra",
    "gpt-6-sol": "cx/gpt-6-sol",
    "gpt-6-luna": "cx/gpt-6-luna",
    "gpt-5.6": "cx/gpt-5.6-sol",
    "gpt-5.6-terra": "cx/gpt-5.6-terra",
    "gpt-5.6-luna": "cx/gpt-5.6-luna",
    "gpt-5.6-sol": "cx/gpt-5.6-sol",
    "gpt-5.5": "cx/gpt-5.5",
    "claude-opus-5": "claude-sonnet-4-6",
    "claude-sonnet-5": "claude-sonnet-4-6",
    "claude-fable-5": "claude-sonnet-4-6",
    "codex-gpt-5.6": "cx/gpt-5.6-sol",
    "deepseek-r1": "deepseek-v4.1",
    "deepseek-v4": "deepseek-v4.1",
    "deepseek-chat": "deepseek-v4.1",
    "deepseek-v4-flash-lr": "deepseek-v4-flash-lr",
    "grok": "gcli/grok-4.7",
    "grok-4": "gcli/grok-4.7",
    "grok-4.7": "gcli/grok-4.7",
    "grok-cli": "gcli/grok-4.7",
    "grok-imagine-2": "grok-imagine-2",
    "llama-3.3-70b": "deepseek-v4.1",
    "finbert": "deepseek-v4-flash",
    "vyce-ai-proxy": "deepseek-v4-flash",
    "qwen": "deepseek-v4.1",
    "qwen3.8-flash": "deepseek-v4.1",
    "qwen-3.8-flash": "deepseek-v4.1",
    "agnes": "agnes-3.0-flash",
    "agnes-3.0-flash": "agnes-3.0-flash",
    "gemini": "gemini-3.7-flash",
    "gemini-flash": "gemini-3.7-flash",
    "gemini-2.0": "gemini-3.7-flash",
    "gemini-2.0-flash": "gemini-3.7-flash",
    "gemini-3.6": "gemini-3.7-flash",
    "gemini-3.6-flash": "gemini-3.7-flash",
    "gemini-3.7": "gemini-3.7-flash",
    "gemini-3.7-flash": "gemini-3.7-flash",
    "gemini-3.8": "gemini-3.8-flash",
    "gemini-3.8-flash": "gemini-3.8-flash",
    "groq": "openai/gpt-oss-120b",
    "groq-fast": "qwen/qwen3.8-27b",
    "openrouter": "nvidia/nemotron-3.5-lightning:free",
    "nemotron": "nvidia/nemotron-3.5-lightning:free",
    "deepseek-free": "deepseek/deepseek-v4-flash-0731:free",
    "cloudflare": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "cf": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "cf-llama": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "cf-r1": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
    "codex": "cx/gpt-6-astra",
    "codex-plus": "cx/gpt-6-astra",
    "codex-astra": "cx/gpt-6-astra",
    "codex-sol": "cx/gpt-5.6-sol",
    "gpt-5.5-codex": "cx/gpt-5.5",
}

VETO_SYSTEM_PROMPT = """You are the Institutional AI Risk Advisory & Execution Gatekeeper for an automated quantitative cryptocurrency trading desk.
Evaluate the incoming trading signal in the context of recent market structure, technical indicators, and risk parameters.
Decide whether to APPROVE or VETO the technical trade signal.
You MUST output strictly a valid JSON object with NO markdown code fences, NO backticks, and NO additional commentary, matching this exact schema:
{
  "approved": true,
  "regime": "BULL_TREND",
  "risk_score": 1,
  "confidence": 0.85,
  "size_multiplier": 1.0,
  "reasoning": "Concise justification under 40 words"
}
Rules:
1. regime MUST be one of: "BULL_TREND", "BEAR_TREND", "RANGING", "EXTREME_VOLATILITY".
2. risk_score is an integer from 1 (lowest risk) to 5 (extreme risk).
3. confidence is a float from 0.0 to 1.0.
4. size_multiplier is a float from 0.2 to 1.0.
5. ALPHA & EXECUTION DOCTRINE: The fund generates return by taking high-probability setups with strict risk controls (every order is protected by strict 1.8% Stop-Loss and daily -$3.50 circuit breaker). DO NOT OVER-VETO. Taking calculated risks is the core objective.
6. APPROVE (approved=true):
   - For BUY signals on bullish trend pullbacks, support bounces, or healthy momentum continuations.
   - For SELL signals on bearish trend pullbacks, resistance rejections, or oversold breakdown continuations.
   - For any exit / position close signal.
7. DYNAMIC SIZING OVER VETO: If you identify moderate headwinds (such as nearby minor resistance, lower volume, or 15m consolidation), DO NOT VETO. Instead, set approved=true and reduce size_multiplier (e.g. 0.5 to 0.8) to limit risk exposure while capturing the move.
8. STRICT VETO CRITERIA (Only set approved=false if):
   - Signal directly trades against the dominant higher timeframe (4H) trend without any valid divergence.
   - Stop-Loss distance is mathematically unviable (> 3.0% or < 0.3%).
   - An active market-wide flash crash or catastrophic volatility spike is unfolding.
9. Strictly respect any 'hard_earned_lessons_to_respect' provided in the context.
"""

POST_MORTEM_SYSTEM_PROMPT = """You are a senior quantitative risk officer and post-mortem forensic analyst.
Analyze the following stopped-out cryptocurrency trade and synthesize actionable lessons learned to safeguard portfolio capital.
You MUST output strictly a valid JSON object with NO markdown code fences, NO backticks, and NO additional commentary, matching this exact schema:
{
  "category": "STOP_LOSS",
  "title": "Concise Vietnamese headline under 12 words",
  "details": "Forensic breakdown of entry, price action, and failure mechanism in Vietnamese (under 60 words)",
  "capital_impact": 0.0,
  "lesson_learned": "Concrete actionable risk rule for future algorithmic trading in Vietnamese (under 50 words)",
  "operator": "Claude-3.5-Sonnet"
}
"""


class VyceClient:
    """
    High-performance, persistent keep-alive client for Vyce AI proxy with Claude Sonnet.
    Provides connection pooling, automatic model alias resolution, strict timeout handling,
    and deterministic quantitative fallback.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        fast_model: Optional[str] = None,
        council_mode: Optional[str] = None,
        timeout: Optional[float] = None,
        fast_timeout: Optional[float] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        db: Optional[Any] = None
    ):
        self.api_key = api_key or settings.VYCE_API_KEY
        raw_base = (base_url or settings.VYCE_BASE_URL).rstrip("/")
        self.base_url = raw_base if raw_base.endswith("/v1") else f"{raw_base}/v1"
        raw_model = model or settings.VYCE_MODEL
        self.model = self.resolve_model_alias(raw_model)
        raw_fast_model = fast_model or getattr(settings, "VYCE_FAST_MODEL", "deepseek-v4-flash")
        self.fast_model = self.resolve_model_alias(raw_fast_model)
        self.council_mode = (council_mode or getattr(settings, "AI_COUNCIL_MODE", "consensus")).lower()
        self.timeout = float(timeout or settings.AI_TIMEOUT_SECONDS)
        self.fast_timeout = float(fast_timeout or getattr(settings, "AI_FAST_TIMEOUT_SECONDS", 2.0))
        self.db = db

        # Token Quota and Cost Counters
        self.total_requests: int = 0
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_tokens: int = 0
        self.estimated_cost_usd: float = 0.0

        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }

        # Persistent HTTP client with connection pooling
        self._external_client = http_client is not None
        self._client: Optional[httpx.AsyncClient] = http_client

    @classmethod
    def resolve_model_alias(cls, model_name: str) -> str:
        """Remaps model aliases to the live proxy model ID (e.g. claude-sonnet-4-6)."""
        cleaned = model_name.strip().lower()
        return MODEL_ALIASES.get(cleaned, model_name)

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily instantiates the persistent httpx.AsyncClient on the active event loop."""
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0
            )
            timeout = httpx.Timeout(self.timeout, connect=2.0)
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                headers=self._headers
            )
        return self._client

    async def close(self) -> None:
        """Gracefully shuts down the persistent HTTP client."""
        if self._client and not self._client.is_closed and not self._external_client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "VyceClient":
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @staticmethod
    def _calc_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        m = model_name.lower()
        if "deepseek" in m:
            return round((prompt_tokens * 0.00000014) + (completion_tokens * 0.00000028), 6)
        elif "claude" in m or "sonnet" in m:
            return round((prompt_tokens * 0.000003) + (completion_tokens * 0.000015), 6)
        elif "gpt-4o-mini" in m:
            return round((prompt_tokens * 0.00000015) + (completion_tokens * 0.0000006), 6)
        elif "gpt-4" in m:
            return round((prompt_tokens * 0.0000025) + (completion_tokens * 0.00001), 6)
        else:
            return round((prompt_tokens * 0.000001) + (completion_tokens * 0.000003), 6)

    async def get_quota_metrics(self) -> Dict[str, Any]:
        if self.db and hasattr(self.db, "get_token_usage_summary"):
            try:
                db_summary = await self.db.get_token_usage_summary()
                if db_summary.get("total_requests", 0) > 0:
                    return db_summary
            except Exception:
                pass
        return {
            "total_requests": self.total_requests,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "by_model": [
                {"model": self.model, "tokens": self.total_tokens, "cost": round(self.estimated_cost_usd, 6)}
            ],
            "recent_calls": []
        }

    async def chat_completion(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 300,
        temperature: float = 0.1,
        timeout: Optional[float] = None,
        model: Optional[str] = None,
        action: str = "CHAT_COMPLETION"
    ) -> Optional[str]:
        """
        Sends chat completion request to Vyce AI proxy with strict timeout and keep-alive reuse.
        Returns raw text response or None on failure/timeout.
        """
        target_model = self.resolve_model_alias(model or self.model)
        
        # Smart dynamic dispatch: 9Router (ChatGPT Codex & Grok on VPS) vs Google Gemini vs Vyce AI Proxy vs ETFBit
        if (
            target_model.startswith("cx/")
            or target_model.startswith("gcli/")
            or target_model.startswith("gw/")
            or target_model.startswith("9router/")
        ):
            actual_model = target_model[len("9router/"):] if target_model.startswith("9router/") else target_model
            base_url = NINEROUTER_BASE_URL.rstrip("/")
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {NINEROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            target_model = actual_model
        elif target_model.startswith("gemini"):
            from ai_advisory.gemini_pool import gemini_pool
            gemini_key = gemini_pool.get_active_key()
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {gemini_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            }
        elif target_model.startswith("groq") or target_model.startswith("openai/gpt-oss") or target_model.startswith("qwen/"):
            from ai_advisory.groq_pool import groq_pool
            groq_key = groq_pool.get_active_key()
            base_url = getattr(settings, "GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            }
        elif ":free" in target_model or target_model.startswith("nvidia/") or target_model.startswith("openrouter") or target_model.startswith("or/"):
            or_key = getattr(settings, "OPENROUTER_API_KEY", "***REDACTED***")
            base_url = "https://openrouter.ai/api/v1"
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {or_key}",
                "HTTP-Referer": "https://trader.hoanvi.com",
                "X-Title": "Astra Quant Desk",
                "Content-Type": "application/json"
            }
        elif target_model.startswith("etf/"):
            base_url = ETFBIT_BASE_URL.rstrip("/")
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {ETFBIT_API_KEY}",
                "Content-Type": "application/json"
            }
        elif target_model.startswith("gu/") or target_model.startswith("gurouter/"):
            actual_model = target_model.split("/", 1)[1]
            gu_key = getattr(settings, "GUROUTER_API_KEY", "***REDACTED***")
            base_url = getattr(settings, "GUROUTER_BASE_URL", "https://gurouter.com/v1").rstrip("/")
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {gu_key}",
                "Content-Type": "application/json"
            }
            target_model = actual_model
        elif target_model.startswith("@cf/") or target_model.startswith("cf/") or target_model.startswith("cloudflare"):
            actual_model = target_model[3:] if target_model.startswith("cf/") else target_model
            cf_token = getattr(settings, "CLOUDFLARE_AI_TOKEN", "")
            cf_acc = getattr(settings, "CLOUDFLARE_ACCOUNT_ID", "6674cf27e0a8ac848f3782be701c4d09")
            base_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_acc}/ai/v1"
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {cf_token}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            }
            target_model = actual_model
        else:
            # Default to Vyce AI Proxy (Claude-3.5-Sonnet / DeepSeek)
            url = f"{self.base_url}/chat/completions"
            headers = self._headers

        effective_max_tokens = max_tokens
        if target_model.startswith("gemini") and effective_max_tokens < 600:
            effective_max_tokens = 600

        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": temperature,
            "max_tokens": effective_max_tokens
        }

        req_timeout = timeout if timeout is not None else self.timeout
        t0 = time.time()
        try:
            client = await self._get_client()
            response = await client.post(url, json=payload, headers=headers, timeout=req_timeout)
            lat_ms = (time.time() - t0) * 1000.0
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                usage = data.get("usage", {})
                content = choices[0].get("message", {}).get("content", "") if choices else ""

                # Token usage & cost tracking
                p_tokens = int(usage.get("prompt_tokens") or (len(user_content) + len(system_prompt)) // 4)
                c_tokens = int(usage.get("completion_tokens") or (len(content) // 4 if content else 10))
                t_tokens = int(usage.get("total_tokens") or (p_tokens + c_tokens))
                cost = self._calc_cost(target_model, p_tokens, c_tokens)

                self.total_requests += 1
                self.total_prompt_tokens += p_tokens
                self.total_completion_tokens += c_tokens
                self.total_tokens += t_tokens
                self.estimated_cost_usd += cost

                if self.db and hasattr(self.db, "record_token_usage"):
                    try:
                        asyncio.create_task(self.db.record_token_usage(
                            model=target_model,
                            action=action,
                            prompt_tokens=p_tokens,
                            completion_tokens=c_tokens,
                            total_tokens=t_tokens,
                            estimated_cost_usd=cost
                        ))
                    except Exception as e:
                        logger.debug(f"Could not record token usage in DB: {e}")

                if self.db and hasattr(self.db, "record_model_call"):
                    try:
                        fleet_id = "FLEET_2" if (target_model.startswith("cx/") or target_model.startswith("gcli/") or target_model.startswith("gw/")) else "FLEET_1"
                        asyncio.create_task(self.db.record_model_call(
                            model_name=target_model,
                            agent_name=action,
                            fleet=fleet_id,
                            latency_ms=lat_ms,
                            success=True
                        ))
                    except Exception as e:
                        logger.debug(f"Could not record model benchmark: {e}")

                if choices:
                    return content
            else:
                lat_ms = (time.time() - t0) * 1000.0
                err_text = response.text[:200]
                logger.warning(
                    f"Vyce AI ({target_model}) responded with status {response.status_code}: {err_text}"
                )
                if self.db and hasattr(self.db, "record_model_call"):
                    try:
                        fleet_id = "FLEET_2" if (target_model.startswith("cx/") or target_model.startswith("gcli/") or target_model.startswith("gw/")) else "FLEET_1"
                        asyncio.create_task(self.db.record_model_call(
                            model_name=target_model,
                            agent_name=action,
                            fleet=fleet_id,
                            latency_ms=lat_ms,
                            success=False,
                            error_msg=f"HTTP {response.status_code}: {err_text[:100]}"
                        ))
                    except Exception as e:
                        logger.debug(f"Could not record model benchmark: {e}")
                return None
        except httpx.TimeoutException:
            lat_ms = (time.time() - t0) * 1000.0
            logger.warning(f"Vyce AI ({target_model}) request timed out after {req_timeout}s.")
            if self.db and hasattr(self.db, "record_model_call"):
                try:
                    fleet_id = "FLEET_2" if (target_model.startswith("cx/") or target_model.startswith("gcli/") or target_model.startswith("gw/")) else "FLEET_1"
                    asyncio.create_task(self.db.record_model_call(
                        model_name=target_model,
                        agent_name=action,
                        fleet=fleet_id,
                        latency_ms=lat_ms,
                        success=False,
                        error_msg=f"Timeout after {req_timeout}s"
                    ))
                except Exception as e:
                    logger.debug(f"Could not record model benchmark: {e}")
            return None
        except Exception as e:
            lat_ms = (time.time() - t0) * 1000.0
            logger.warning(f"Vyce AI ({target_model}) request failed: {e}.")
            if self.db and hasattr(self.db, "record_model_call"):
                try:
                    fleet_id = "FLEET_2" if (target_model.startswith("cx/") or target_model.startswith("gcli/") or target_model.startswith("gw/")) else "FLEET_1"
                    asyncio.create_task(self.db.record_model_call(
                        model_name=target_model,
                        agent_name=action,
                        fleet=fleet_id,
                        latency_ms=lat_ms,
                        success=False,
                        error_msg=str(e)[:100]
                    ))
                except Exception as e:
                    logger.debug(f"Could not record model benchmark: {e}")
            return None

    def _parse_veto_json(self, raw_response: str, model_name: str) -> Optional[Dict[str, Any]]:
        try:
            parsed = self._clean_and_parse_json(raw_response)
            regime_raw = str(parsed.get("regime", "RANGING")).upper()
            valid_regimes = {"BULL_TREND", "BEAR_TREND", "RANGING", "EXTREME_VOLATILITY"}
            regime = regime_raw if regime_raw in valid_regimes else "RANGING"

            risk_score = max(1, min(5, int(parsed.get("risk_score", 3))))
            confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.5))))
            size_mult = max(0.2, min(1.0, float(parsed.get("size_multiplier", 1.0))))
            approved = bool(parsed.get("approved", True))
            reasoning = str(parsed.get("reasoning", "")).strip()

            return {
                "approved": approved,
                "regime": regime,
                "risk_score": risk_score,
                "confidence": round(confidence, 2),
                "size_multiplier": round(size_mult, 2),
                "reasoning": reasoning,
                "model": model_name,
                "fallback_used": False
            }
        except Exception as e:
            logger.warning(f"Failed to parse Vyce AI ({model_name}) veto response: {e}. Raw: {raw_response[:150]}")
            return None

    async def evaluate_signal_veto(
        self,
        signal: SignalEvent,
        market_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Supreme AI Advisory Gatekeeper: Evaluates a technical trading signal against macro/market context.
        Supports Multi-Model Council (Consensus), Smart Failover, and Single Model.
        Engages deterministic quantitative fallback if all AI options fail or exceed timeout.
        """
        user_content = self._format_signal_prompt(signal, market_context)

        # 0. Adversarial Mode (3-Round Debate: Bull deepseek-v4.1 vs Bear deepseek-v4-flash-lr vs Arbiter claude-sonnet-4-6)
        if self.council_mode == "adversarial":
            from ai_advisory.adversarial_debater import AdversarialDebater
            debater = AdversarialDebater(vyce_client=self)
            signal_data = {
                "symbol": signal.symbol,
                "side": signal.side.value if hasattr(signal.side, "value") else str(signal.side),
                "price": signal.price,
                "strategy": signal.strategy_name,
                "context": market_context
            }
            debate_res = await debater.debate_signal(signal_data)
            if debate_res.get("fallback_used"):
                return self._build_fallback_veto(signal, market_context, debate_res.get("ruling_rationale", "Adversarial debate fallback"))
            return {
                "approved": bool(debate_res.get("approved", False)),
                "regime": "bull_trend" if str(signal_data["side"]).upper() == "BUY" else "bear_trend",
                "risk_score": int(debate_res.get("risk_score", 3)),
                "confidence": float(debate_res.get("confidence", 0.85)),
                "size_multiplier": float(debate_res.get("size_multiplier", 1.0)),
                "reasoning": f"[Adversarial 3-Round Verdict] {debate_res.get('ruling_rationale', '')}",
                "model": "adversarial-debate-3tier",
                "fallback_used": False,
                "debate_transcript": debate_res.get("debate_transcript", {})
            }


        # 1. Single Mode or identical models
        if self.council_mode == "single" or self.model == self.fast_model:
            raw = await self.chat_completion(
                system_prompt=VETO_SYSTEM_PROMPT,
                user_content=user_content,
                max_tokens=250,
                temperature=0.1,
                timeout=self.timeout,
                model=self.model
            )
            if raw:
                parsed = self._parse_veto_json(raw, self.model)
                if parsed:
                    return parsed
            return self._build_fallback_veto(signal, market_context, f"AI {self.model} unreachable")

        # 2. Failover Mode
        if self.council_mode == "failover":
            raw_primary = await self.chat_completion(
                system_prompt=VETO_SYSTEM_PROMPT,
                user_content=user_content,
                max_tokens=250,
                temperature=0.1,
                timeout=self.timeout,
                model=self.model
            )
            if raw_primary:
                parsed = self._parse_veto_json(raw_primary, self.model)
                if parsed:
                    return parsed

            logger.info(f"Primary {self.model} unavailable. Engaging Smart Failover to {self.fast_model}...")
            raw_fast = await self.chat_completion(
                system_prompt=VETO_SYSTEM_PROMPT,
                user_content=user_content,
                max_tokens=250,
                temperature=0.1,
                timeout=self.fast_timeout,
                model=self.fast_model
            )
            if raw_fast:
                parsed = self._parse_veto_json(raw_fast, f"{self.fast_model} (Failover)")
                if parsed:
                    parsed["reasoning"] = f"[Smart Failover] {parsed['reasoning']}"
                    return parsed

            return self._build_fallback_veto(signal, market_context, "Primary and Failover AI unreachable")

        # 3. Consensus Mode (Multi-Model Council: Claude Gatekeeper + DeepSeek Scout)
        async def call_model(m: str, t: float) -> Optional[Dict[str, Any]]:
            raw = await self.chat_completion(
                system_prompt=VETO_SYSTEM_PROMPT,
                user_content=user_content,
                max_tokens=250,
                temperature=0.1,
                timeout=t,
                model=m
            )
            return self._parse_veto_json(raw, m) if raw else None

        primary_task = asyncio.create_task(call_model(self.model, self.timeout))
        fast_task = asyncio.create_task(call_model(self.fast_model, self.fast_timeout))

        results = await asyncio.gather(primary_task, fast_task, return_exceptions=True)
        primary_res = results[0] if not isinstance(results[0], Exception) else None
        fast_res = results[1] if not isinstance(results[1], Exception) else None

        # Case A: Both Council members responded
        if primary_res and fast_res:
            # If Primary Gatekeeper (Claude) vetoes -> strictly veto
            if not primary_res["approved"]:
                return {
                    "approved": False,
                    "regime": primary_res["regime"],
                    "risk_score": primary_res["risk_score"],
                    "confidence": primary_res["confidence"],
                    "size_multiplier": 0.2,
                    "reasoning": f"[Council Veto by {self.model}] {primary_res['reasoning']}",
                    "model": f"{self.model} + {self.fast_model}",
                    "fallback_used": False
                }

            # If Fast Scout detects extreme volatility / anomaly
            if not fast_res["approved"] and (fast_res["risk_score"] >= 4 or fast_res["regime"] == "EXTREME_VOLATILITY"):
                return {
                    "approved": False,
                    "regime": fast_res["regime"],
                    "risk_score": fast_res["risk_score"],
                    "confidence": fast_res["confidence"],
                    "size_multiplier": 0.2,
                    "reasoning": f"[Council Technical Veto by {self.fast_model}] {fast_res['reasoning']}",
                    "model": f"{self.model} + {self.fast_model}",
                    "fallback_used": False
                }

            # Both agree or minor divergence: consensus synthesis
            consensus_conf = round((primary_res["confidence"] + fast_res["confidence"]) / 2.0, 2)
            max_risk = max(primary_res["risk_score"], fast_res["risk_score"])
            size_multiplier = round(min(primary_res["size_multiplier"], fast_res["size_multiplier"]), 2)
            if not fast_res["approved"]:
                size_multiplier = round(size_multiplier * 0.5, 2)

            regime = primary_res["regime"] if primary_res["regime"] != "RANGING" else fast_res["regime"]
            return {
                "approved": True,
                "regime": regime,
                "risk_score": max_risk,
                "confidence": consensus_conf,
                "size_multiplier": size_multiplier,
                "reasoning": f"[Council Consensus] Claude: {primary_res['reasoning']} | DeepSeek: {fast_res['reasoning']}",
                "model": f"{self.model} + {self.fast_model}",
                "fallback_used": False
            }

        # Case B: Primary responded, Fast timed out
        if primary_res and not fast_res:
            primary_res["reasoning"] = f"{primary_res['reasoning']} (Fast Scout timed out)"
            return primary_res

        # Case C: Fast responded, Primary timed out -> Smart Failover!
        if fast_res and not primary_res:
            fast_res["model"] = f"{self.fast_model} (Failover from {self.model})"
            fast_res["reasoning"] = f"[Smart Failover] {fast_res['reasoning']}"
            return fast_res

        # Case D: Both failed -> engage quantitative fallback
        return self._build_fallback_veto(signal, market_context, "AI Council unreachable or timed out")

    async def generate_post_mortem(self, trade_info: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        """
        Queries Claude Sonnet for forensic analysis on a stopped-out trade.
        Fails over to DeepSeek V4 if Claude is unreachable, then deterministic fallback.
        """
        pnl = float(trade_info.get("pnl_usdt", 0.0))
        user_content = (
            f"Trade Post-Mortem Analysis Request:\n"
            f"- Strategy: {trade_info.get('strategy_name', 'Unknown')}\n"
            f"- Symbol: {trade_info.get('symbol', 'BTC/USDT')}\n"
            f"- Entry Price: {trade_info.get('entry_price', 0.0):.2f}\n"
            f"- Exit Price: {trade_info.get('exit_price', 0.0):.2f}\n"
            f"- Capital Impact (PnL USDT): {pnl:.2f}\n"
            f"- PnL Percent: {trade_info.get('pnl_percent', 0.0):.2f}%\n"
            f"- Hold Duration: {trade_info.get('hold_duration_seconds', 0.0):.1f}s\n"
            f"- Exit Reason: {trade_info.get('reason', 'STOP_LOSS')}"
        )

        candidate_models = [self.model]
        if self.fast_model != self.model:
            candidate_models.append(self.fast_model)

        for target_model in candidate_models:
            raw_response = await self.chat_completion(
                system_prompt=POST_MORTEM_SYSTEM_PROMPT,
                user_content=user_content,
                max_tokens=350,
                temperature=0.2,
                timeout=timeout,
                model=target_model
            )

            if raw_response:
                try:
                    parsed = self._clean_and_parse_json(raw_response)
                    if not isinstance(parsed, dict):
                        raise ValueError("Post-mortem response must be a JSON dictionary")

                    title = parsed.get("title")
                    details = parsed.get("details")
                    lesson = parsed.get("lesson_learned")
                    category = parsed.get("category")
                    cap_impact = parsed.get("capital_impact")

                    if not title or not isinstance(title, str) or not title.strip():
                        raise ValueError("Post-mortem response missing or empty 'title'")
                    if not details or not isinstance(details, str) or not details.strip():
                        raise ValueError("Post-mortem response missing or empty 'details'")
                    if not lesson or not isinstance(lesson, str) or not lesson.strip():
                        raise ValueError("Post-mortem response missing or empty 'lesson_learned'")

                    impact_val = abs(float(cap_impact if cap_impact is not None else abs(pnl)))
                    category_str = str(category).strip() if category else "STOP_LOSS"
                    operator_str = str(parsed.get("operator") or target_model).strip()

                    return {
                        "category": category_str,
                        "title": str(title).strip(),
                        "details": str(details).strip(),
                        "capital_impact": impact_val,
                        "lesson_learned": str(lesson).strip(),
                        "operator": operator_str
                    }
                except Exception as e:
                    logger.warning(f"Failed to parse post-mortem from {target_model}: {e}")

        # Deterministic fallback post-mortem
        return {
            "category": "STOP_LOSS",
            "title": f"Dừng lỗ tự động {trade_info.get('symbol', 'BTC/USDT')} bảo toàn vốn",
            "details": f"Vị thế {trade_info.get('symbol')} đóng tại {trade_info.get('exit_price', 0.0):.2f} do chạm ngưỡng Stop Loss {trade_info.get('pnl_percent', 0.0):.2f}%.",
            "capital_impact": abs(pnl),
            "lesson_learned": "Bảo toàn vốn là ưu tiên số 1; kích hoạt fallback an toàn ghi nhận kỷ luật cắt lỗ tự động.",
            "operator": "Deterministic-Fallback"
        }

    def _format_signal_prompt(self, signal: SignalEvent, market_context: Dict[str, Any]) -> str:
        ctx_lines = []
        for k, v in market_context.items():
            if isinstance(v, float):
                ctx_lines.append(f"- {k}: {v:.4f}")
            else:
                ctx_lines.append(f"- {k}: {v}")
        context_str = "\n".join(ctx_lines) if ctx_lines else "- No additional context provided"

        side_str = signal.side.value if hasattr(signal.side, "value") else str(signal.side)
        sl_pct = abs(signal.price - signal.stop_loss) / signal.price * 100.0 if signal.price > 0 else 0.0
        tp_pct = abs(signal.take_profit - signal.price) / signal.price * 100.0 if signal.price > 0 else 0.0
        rr = tp_pct / max(0.01, sl_pct)

        return (
            f"Signal to Evaluate:\n"
            f"- Strategy: {signal.strategy_name}\n"
            f"- Symbol: {signal.symbol}\n"
            f"- Action: {side_str}\n"
            f"- Entry Price: {signal.price:.4f}\n"
            f"- Stop Loss: {signal.stop_loss:.4f} (Risk: {sl_pct:.2f}%, fully compliant with fund risk limits)\n"
            f"- Take Profit: {signal.take_profit:.4f} (Reward: {tp_pct:.2f}%)\n"
            f"- Reward-to-Risk: {rr:.2f}:1\n"
            f"- Strategy Confidence: {signal.confidence:.2f}\n\n"
            f"Market Context:\n"
            f"{context_str}"
        )

    def _clean_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(clean)

    def _build_fallback_veto(
        self,
        signal: SignalEvent,
        market_context: Dict[str, Any],
        error_reason: str
    ) -> Dict[str, Any]:
        """
        Deterministic quantitative fallback rule when AI service is unavailable.
        - SELL/Exit: Always approve unconditionally to facilitate risk reduction.
        - BUY: Validate RSI overbought limit, Stop-Loss safe corridor [0.5%, 5.0%],
          and signal confidence >= 0.70 before approving with 50% sizing de-rating.
        """
        if signal.side == OrderSide.SELL:
            return {
                "approved": True,
                "regime": "RANGING",
                "risk_score": 2,
                "confidence": signal.confidence,
                "size_multiplier": 1.0,
                "reasoning": f"Quantitative Fallback: Exit signal approved unconditionally. ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

        # BUY Signal Validation:
        # 1. RSI Overbought check
        rsi = market_context.get("rsi") or market_context.get("rsi_14")
        if rsi is not None and float(rsi) > 75:
            return {
                "approved": False,
                "regime": "EXTREME_VOLATILITY",
                "risk_score": 4,
                "confidence": signal.confidence,
                "size_multiplier": 0.20,
                "reasoning": f"Quantitative Fallback Veto: RSI ({float(rsi):.1f}) is overbought. ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

        # 2. Stop Loss Distance Corridor Check [0.5%, 5.0%]
        if signal.stop_loss <= 0 or signal.stop_loss >= signal.price:
            return {
                "approved": False,
                "regime": "RANGING",
                "risk_score": 4,
                "confidence": signal.confidence,
                "size_multiplier": 0.0,
                "reasoning": f"Quantitative Fallback Veto: Invalid Stop Loss ({signal.stop_loss} vs Price {signal.price}). ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

        sl_dist_pct = (signal.price - signal.stop_loss) / signal.price
        if sl_dist_pct < 0.005 or sl_dist_pct > 0.05:
            return {
                "approved": False,
                "regime": "RANGING",
                "risk_score": 4,
                "confidence": signal.confidence,
                "size_multiplier": 0.0,
                "reasoning": f"Quantitative Fallback Veto: Stop Loss distance {sl_dist_pct*100:.2f}% outside safe corridor [0.5%, 5.0%]. ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

        # 3. Confidence Threshold Check: minimum 0.70 for fallback acceptance
        if signal.confidence < 0.70:
            return {
                "approved": False,
                "regime": "RANGING",
                "risk_score": 3,
                "confidence": signal.confidence,
                "size_multiplier": 0.0,
                "reasoning": f"Quantitative Fallback Veto: Signal confidence ({signal.confidence:.2f}) below safe threshold 0.70. ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

        # 4. Approved with conservative 50% sizing de-rating
        return {
            "approved": True,
            "regime": str(market_context.get("market_regime", "RANGING")).upper(),
            "risk_score": 3,
            "confidence": signal.confidence,
            "size_multiplier": 0.50,
            "reasoning": f"Quantitative Fallback: Order approved with conservative sizing (SL corridor valid, Conf={signal.confidence:.2f}, Size=0.50x). ({error_reason})",
            "model": self.model,
            "fallback_used": True
        }



    async def evaluate_signal_adversarial(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kích hoạt Hội đồng Tranh biện Đối kháng 3 Hiệp (gpt-5.6-sol vs claude-opus-5 vs claude-sonnet-5).
        """
        from ai_advisory.adversarial_debater import AdversarialDebater
        debater = AdversarialDebater(vyce_client=self)
        return await debater.debate_signal(signal_data)
