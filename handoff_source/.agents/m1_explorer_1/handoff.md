# Handoff Report — M1 Explorer 1: Vyce AI Client, Key Resolution & Advisory Veto Engine

**Date**: 2026-09-17T05:28:00Z  
**Author**: M1 Explorer 1 (Vyce Client & Model Resolver Specialist)  
**Target Repository**: `c:\sunMy\trading_bot`  
**Working Directory**: `c:\sunMy\trading_bot\.agents\m1_explorer_1`  
**Recipient**: Lead Orchestrator (`4a1d31f3-0188-4bb2-b5c1-ff9c51dda848`) and M1 Worker  

---

## 1. Observation

### 1.1. Existing Configuration & Environment State
- **File `.env` (`c:\sunMy\trading_bot\.env`)**:
  - Lines 16-19:
    ```ini
    VYCE_API_KEY=mock_vyce_key
    VYCE_BASE_URL=https://vyceai.com/v1
    VYCE_MODEL=deepseek-chat
    ENABLE_AI_ADVISORY=False
    ```
- **VPS OS Environment Variables (`os.environ`)**:
  - `ANTHROPIC_API_KEY`: `"***REDACTED***"`
  - `ANTHROPIC_BASE_URL`: `"https://vyceai.com"`
  - `VYCE_API_KEY`: `None` (Not defined in OS environment)
  - `VYCE_BASE_URL`: `None` (Not defined in OS environment)
- **File `config/settings.py` (`c:\sunMy\trading_bot\config\settings.py`)**:
  - Lines 6-7:
    ```python
    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    ```
  - Lines 29-35:
    ```python
    # Vyce AI Proxy
    VYCE_API_KEY: str = "mock_vyce_key"
    VYCE_BASE_URL: str = "https://vyceai.com/v1"
    VYCE_MODEL: str = "deepseek-chat"
    ENABLE_AI_ADVISORY: bool = False
    AI_TIMEOUT_SECONDS: float = 3.0
    ```
- **Critical Pydantic Discovery**:
  - Because `env_file=".env"` is loaded by `BaseSettings`, setting `VYCE_API_KEY: str = Field(default_factory=...)` fails to resolve `ANTHROPIC_API_KEY` when `.env` contains `VYCE_API_KEY=mock_vyce_key`.
  - Pydantic assigns the value `"mock_vyce_key"` from `.env` directly, completely bypassing `default_factory`.
  - Similarly, `.env` contains `VYCE_MODEL=deepseek-chat`, which overrides any field default like `VYCE_MODEL: str = "claude-sonnet-4-6"`.
  - Verification test in Python proved that a Pydantic `@model_validator(mode="after")` is required to inspect `self.VYCE_API_KEY` and fallback to `os.getenv("ANTHROPIC_API_KEY")`.

### 1.2. Existing `ai_advisory/vyce_client.py` Implementation
- Lines 10-20:
  ```python
  class VyceClient:
      def __init__(self):
          self.api_key = settings.VYCE_API_KEY
          self.base_url = settings.VYCE_BASE_URL.rstrip("/")
          self.model = settings.VYCE_MODEL
          self.timeout = settings.AI_TIMEOUT_SECONDS
          self._headers = {
              "Authorization": f"Bearer {self.api_key}",
              "Content-Type": "application/json"
          }
  ```
- Lines 37-53:
  - Inside `chat_completion`:
    ```python
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(url, headers=self._headers, json=payload)
    ```
  - Every HTTP call opens a brand new TCP connection, negotiates TLS 1.3 handshake, sends one request, and tears down the socket.
  - No connection pooling (`httpx.Limits`) is configured.
  - No model alias remapping is performed.
  - No `evaluate_signal_veto` method exists.
  - No `close()` method exists.
  - Latency impact directly verified on live VPS:
    - Fresh connection: **3.10s** (TLS handshake latency alone ~1.5s).
    - Persistent keep-alive reuse: **1.21s - 2.09s**.
    - Sporadic timeout observed: Upstream proxy can occasionally exceed 5.0s/10.0s causing `httpx.ReadTimeout`.

### 1.3. Live Vyce AI Proxy API Response Characteristics
- Model Catalog (`GET https://vyceai.com/v1/models`):
  - Model `claude-3-5-sonnet` -> Returns **HTTP 400 Bad Request** (`{"error":{"message":"Invalid request...","code":"invalid_request"}}`).
  - Model `claude-sonnet-4-6` -> Returns **HTTP 200 OK** with Claude Sonnet completions.
- Live Probe Execution on VPS (`test_probe.py` with `ANTHROPIC_API_KEY`):
  - When given an EMA Golden Cross BUY signal, `claude-sonnet-4-6` returned:
    ```json
    {
      "approved": true,
      "regime": "BULL_TREND",
      "risk_score": 2,
      "confidence": 0.85,
      "size_multiplier": 0.9,
      "reasoning": "Strong bullish confirmation: golden cross, positive 24h return, and above-average volume align with EMA_Trend BUY signal, supporting approval with standard sizing."
    }
    ```
  - When given a panic sell crash with extreme volatility, `claude-sonnet-4-6` returned:
    ```json
    {
      "approved": false,
      "regime": "BEAR_TREND",
      "risk_score": 5,
      "confidence": 0.15,
      "size_multiplier": 0.2,
      "reasoning": "VETO: Extreme volatility regime, death cross, panic sell volume. RSI collapse signals weak hands capitulation. Insufficient bounce confirmation. Risk/reward compromised. Defer until stabilization."
    }
    ```
  - Exact match with the contract schema defined in `PROJECT.md` §Interface Contracts.

### 1.4. Current Event Pipeline & Risk Engine Integration
- `core/events.py`:
  - `SignalEvent`: `strategy_name`, `symbol`, `side` (`OrderSide.BUY`/`SELL`), `price`, `timestamp`, `stop_loss`, `take_profit`, `confidence`.
  - `AIAdvisoryEvent`: `symbol`, `timestamp`, `regime` (`MarketRegime`), `risk_score`, `trade_allowed`, `size_multiplier`, `reasoning`.
- `risk_engine/risk_manager.py`:
  - Lines 38-50 currently check `self.latest_ai_advisory.trade_allowed` passively against a cached event.
  - It does not actively call `VyceClient.evaluate_signal_veto(signal, market_context)` per signal.
- Existing Test Suite (`pytest`):
  - All 10 existing tests pass in 4.03s:
    `tests\test_ai_advisory.py ..`
    `tests\test_paper_trader.py .`
    `tests\test_risk_engine.py ....`
    `tests\test_settings_and_lessons.py .`
    `tests\test_strategies.py ..`

---

## 2. Logic Chain

1. **Premise 1 (R1 & Feature 1)**: The system must use Claude Sonnet via Vyce AI proxy with key fallback (`ANTHROPIC_API_KEY` / `VYCE_API_KEY`), model alias resolution (`claude-3-5-sonnet` -> `claude-sonnet-4-6`), and persistent keep-alive `httpx.AsyncClient`.
2. **Observation 1.1**: VPS has `ANTHROPIC_API_KEY` while `.env` has `VYCE_API_KEY=mock_vyce_key` and `VYCE_MODEL=deepseek-chat`. Pydantic's `env_file` loader prioritizes `.env` values over field `default_factory`.
3. **Inference 1**: In `config/settings.py`, a `@model_validator(mode="after")` must be implemented to check if `self.VYCE_API_KEY` is empty or `"mock_vyce_key"`, and if so, bind `os.getenv("ANTHROPIC_API_KEY")`. It must also normalize `VYCE_BASE_URL` to include `/v1` and remap `VYCE_MODEL` (`deepseek-chat`, `claude-3-5-sonnet` -> `claude-sonnet-4-6`).
4. **Observation 1.2**: Ephemeral `httpx.AsyncClient` instantiation per request adds ~1.5s TLS handshake overhead, pushing total response time past the strict 3.0s budget (up to 3.10s-4.00s). Reusing a pooled persistent client reduces round-trip time to ~1.2s-2.0s.
5. **Inference 2**: `VyceClient` must maintain a persistent `httpx.AsyncClient` with `httpx.Limits(max_keepalive_connections=5, max_connections=10, keepalive_expiry=30.0)` and `httpx.Timeout(self.timeout, connect=2.0)`. Connection initialization should be lazy (`_get_client()`) to ensure binding to the active event loop, and provide `close()` for graceful shutdown.
6. **Observation 1.2 & 1.3**: Vyce AI proxy occasionally encounters upstream read timeouts (>5.0s / >10.0s) during high traffic.
7. **Inference 3**: In `evaluate_signal_veto`, any network failure, timeout, or JSON parsing error must immediately fall back to deterministic quantitative rules (`fallback_used=True`, conservative sizing, no crash, no event bus freezing).

---

## 3. Caveats

1. **Read-Only Scope**: This report is produced by M1 Explorer 1. No code changes have been committed to `config/settings.py` or `ai_advisory/vyce_client.py`. The implementations below are prepared for immediate application by M1 Worker.
2. **VPS Credential Precedence**: In VPS production, `ANTHROPIC_API_KEY` is the live key. If a user later adds a real `VYCE_API_KEY` (not starting with `mock_`), the validator will prioritize the explicit `VYCE_API_KEY`.
3. **Async Event Loop Lifecycle**: In Python 3.12, instantiating `httpx.AsyncClient` before `asyncio.run()` (e.g. at module import time) can attach to a dummy loop. The design uses lazy instantiation in `_get_client()` to guarantee attachment to the running event loop.

---

## 4. Conclusion & Complete Implementation Design

### 4.1. Exact Specification for `config/settings.py`

#### Changes:
1. Change `VYCE_MODEL` default to `"claude-sonnet-4-6"`.
2. Change `ENABLE_AI_ADVISORY` default to `True`.
3. Add Pydantic `@model_validator(mode="after")` method `resolve_vyce_ai_configuration` to:
   - Resolve `VYCE_API_KEY`: Check `os.getenv("VYCE_API_KEY")` then `os.getenv("ANTHROPIC_API_KEY")` if current key is empty or `"mock_vyce_key"`.
   - Resolve `VYCE_BASE_URL`: Check `os.getenv("VYCE_BASE_URL")` then `os.getenv("ANTHROPIC_BASE_URL")`, ensuring standard `/v1` suffix.
   - Resolve `VYCE_MODEL`: Remap `deepseek-chat`, `claude-3-5-sonnet`, `claude-3.5-sonnet`, `claude-3-5-sonnet-20241022` to `claude-sonnet-4-6`.

#### Full Code Replacement for `config/settings.py`:
```python
import os
from typing import Literal, Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Trading Environment
    TRADING_MODE: Literal["paper", "testnet", "live"] = "paper"

    # Binance API
    BINANCE_API_KEY: str = "mock_key"
    BINANCE_API_SECRET: str = "mock_secret"
    BINANCE_USE_TESTNET: bool = True

    # Trading Pairs & Timeframe
    SYMBOL: str = "BTC/USDT"
    TIMEFRAME: str = "15m"

    # Risk Management Rules
    STARTING_BALANCE_USDT: float = 100.0
    MAX_POSITION_PERCENT: float = 0.20  # Max 20% of portfolio per trade
    DAILY_MAX_DRAWDOWN_PERCENT: float = 0.02  # 2% daily loss lock
    STOP_LOSS_PERCENT: float = 0.015  # 1.5% hard stop
    TAKE_PROFIT_PERCENT: float = 0.03  # 3% target
    MAX_OPEN_POSITIONS: int = 2

    # Vyce AI Proxy (OpenAI Compatible)
    VYCE_API_KEY: str = "mock_vyce_key"
    VYCE_BASE_URL: str = "https://vyceai.com/v1"
    VYCE_MODEL: str = "claude-sonnet-4-6"
    ENABLE_AI_ADVISORY: bool = True
    AI_TIMEOUT_SECONDS: float = 3.0

    # Telegram (Optional)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    ENABLE_TELEGRAM: bool = False

    # Dashboard Server
    DASHBOARD_HOST: str = "127.0.0.1"
    DASHBOARD_PORT: int = 8386
    DATABASE_PATH: str = "trading_bot.db"

    @model_validator(mode="after")
    def resolve_vyce_ai_configuration(self) -> "Settings":
        """
        Seamlessly resolves Vyce AI credentials, base URL, and model aliases:
        1. API Key: Prioritizes explicit VYCE_API_KEY (if non-mock); falls back to ANTHROPIC_API_KEY.
        2. Base URL: Normalizes ANTHROPIC_BASE_URL or VYCE_BASE_URL ensuring '/v1' path.
        3. Model: Remaps legacy/convenience aliases ('deepseek-chat', 'claude-3-5-sonnet', etc.)
           to 'claude-sonnet-4-6'.
        """
        # 1. Key Resolution
        env_vyce = os.getenv("VYCE_API_KEY", "").strip()
        env_anthropic = os.getenv("ANTHROPIC_API_KEY", "").strip()

        if not self.VYCE_API_KEY or self.VYCE_API_KEY == "mock_vyce_key":
            if env_vyce and env_vyce != "mock_vyce_key":
                self.VYCE_API_KEY = env_vyce
            elif env_anthropic and env_anthropic != "mock_vyce_key":
                self.VYCE_API_KEY = env_anthropic

        # 2. Base URL Resolution
        env_vyce_url = os.getenv("VYCE_BASE_URL", "").strip()
        env_anthropic_url = os.getenv("ANTHROPIC_BASE_URL", "").strip()

        candidate_url = env_vyce_url or env_anthropic_url or self.VYCE_BASE_URL
        if candidate_url:
            candidate_url = candidate_url.rstrip("/")
            if not candidate_url.endswith("/v1"):
                candidate_url = f"{candidate_url}/v1"
            self.VYCE_BASE_URL = candidate_url

        # 3. Model Alias Resolution
        model_aliases = {
            "deepseek-chat": "claude-sonnet-4-6",
            "claude-3-5-sonnet": "claude-sonnet-4-6",
            "claude-3.5-sonnet": "claude-sonnet-4-6",
            "claude-3-5-sonnet-20241022": "claude-sonnet-4-6",
            "claude-3-sonnet": "claude-sonnet-4-6",
        }
        self.VYCE_MODEL = model_aliases.get(self.VYCE_MODEL, self.VYCE_MODEL)

        return self


settings = Settings()
```

---

### 4.2. Exact Specification for `ai_advisory/vyce_client.py`

#### Key Architectural Highlights:
1. **Persistent Pool**: `httpx.Limits(max_keepalive_connections=5, max_connections=10, keepalive_expiry=30.0)` reduces TCP+TLS handshake latency from ~1.5s to 0ms for subsequent requests.
2. **Lazy Initialization**: `_get_client()` dynamically initializes on first call within the running event loop.
3. **Graceful Shutdown**: `close()` safely shuts down the persistent HTTP client.
4. **Context Manager**: Implements `async with VyceClient() as client:`.
5. **Model Resolution**: Classmethod `resolve_model_alias` remaps `claude-3-5-sonnet` -> `claude-sonnet-4-6`.
6. **Active Veto Engine**: `evaluate_signal_veto(signal, market_context)` formats prompt, parses JSON output strictly, and enforces the contract defined in `PROJECT.md`.
7. **Quantitative Fallback**: `_build_fallback_veto` triggers instantly on timeout (< 3.0s), network failure, or bad response, returning deterministic decisions with `fallback_used: True`.
8. **Forensic Post-Mortem Hook**: `generate_post_mortem(trade_info)` is included to support Milestone 2.

#### Full Code Replacement for `ai_advisory/vyce_client.py`:
```python
import json
import logging
from typing import Optional, Dict, Any
import httpx
from config.settings import settings
from core.events import SignalEvent
from core.constants import OrderSide

logger = logging.getLogger("VyceClient")

MODEL_ALIASES = {
    "claude-3-5-sonnet": "claude-sonnet-4-6",
    "claude-3.5-sonnet": "claude-sonnet-4-6",
    "claude-3-5-sonnet-20241022": "claude-sonnet-4-6",
    "claude-3-sonnet": "claude-sonnet-4-6",
    "deepseek-chat": "claude-sonnet-4-6",
}

VETO_SYSTEM_PROMPT = """You are the Supreme AI Risk Advisory Gatekeeper for an automated quantitative cryptocurrency trading desk.
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
5. If regime is EXTREME_VOLATILITY or market conditions strongly contradict the signal, set approved=false, risk_score=4 or 5, size_multiplier=0.2.
6. For BUY signals in healthy uptrends or high-quality pullbacks, set approved=true.
7. For SELL/Exit signals, approve to facilitate disciplined risk management unless anomalous.
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
        timeout: Optional[float] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.api_key = api_key or settings.VYCE_API_KEY
        raw_base = (base_url or settings.VYCE_BASE_URL).rstrip("/")
        self.base_url = raw_base if raw_base.endswith("/v1") else f"{raw_base}/v1"
        raw_model = model or settings.VYCE_MODEL
        self.model = self.resolve_model_alias(raw_model)
        self.timeout = float(timeout or settings.AI_TIMEOUT_SECONDS)

        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Persistent HTTP client with connection pooling
        self._external_client = http_client is not None
        self._client: Optional[httpx.AsyncClient] = http_client

    @classmethod
    def resolve_model_alias(cls, model_name: str) -> str:
        """Remaps model aliases to the live proxy model ID (e.g. claude-sonnet-4-6)."""
        return MODEL_ALIASES.get(model_name, model_name)

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

    async def chat_completion(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 300,
        temperature: float = 0.1
    ) -> Optional[str]:
        """
        Sends chat completion request to Vyce AI proxy with strict timeout and keep-alive reuse.
        Returns raw text response or None on failure/timeout.
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            client = await self._get_client()
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
            else:
                logger.warning(
                    f"Vyce AI responded with status {response.status_code}: {response.text[:200]}"
                )
                return None
        except httpx.TimeoutException:
            logger.warning(f"Vyce AI request timed out after {self.timeout}s. Engaging Non-AI fallback.")
            return None
        except Exception as e:
            logger.warning(f"Vyce AI request failed: {e}. Engaging Non-AI fallback.")
            return None

    async def evaluate_signal_veto(
        self,
        signal: SignalEvent,
        market_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Supreme AI Advisory Gatekeeper: Evaluates a technical trading signal against macro/market context.
        Returns structured decision: approved, regime, risk_score, confidence, size_multiplier, reasoning.
        Engages deterministic quantitative fallback if AI call fails or exceeds timeout.
        """
        user_content = self._format_signal_prompt(signal, market_context)
        raw_response = await self.chat_completion(
            system_prompt=VETO_SYSTEM_PROMPT,
            user_content=user_content,
            max_tokens=250,
            temperature=0.1
        )

        if raw_response:
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
                    "model": self.model,
                    "fallback_used": False
                }
            except Exception as e:
                logger.warning(f"Failed to parse Vyce AI response: {e}. Raw: {raw_response[:150]}")

        # Non-blocking quantitative fallback
        return self._build_fallback_veto(signal, market_context, "AI unreachable or invalid output")

    async def generate_post_mortem(self, trade_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Queries Claude Sonnet for forensic analysis on a stopped-out trade.
        Returns structured post-mortem dictionary ready for SQLite storage.
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

        raw_response = await self.chat_completion(
            system_prompt=POST_MORTEM_SYSTEM_PROMPT,
            user_content=user_content,
            max_tokens=350,
            temperature=0.2
        )

        if raw_response:
            try:
                parsed = self._clean_and_parse_json(raw_response)
                return {
                    "category": str(parsed.get("category", "STOP_LOSS")),
                    "title": str(parsed.get("title", f"Cắt lỗ {trade_info.get('symbol')} tại {trade_info.get('exit_price')}")),
                    "details": str(parsed.get("details", f"Lệnh đóng do chạm Stop Loss tại {trade_info.get('exit_price')}.")),
                    "capital_impact": abs(float(parsed.get("capital_impact", abs(pnl)))),
                    "lesson_learned": str(parsed.get("lesson_learned", "Tuân thủ kỷ luật dừng lỗ và điều chỉnh biên độ ATR phù hợp.")),
                    "operator": str(parsed.get("operator", "Claude-3.5-Sonnet"))
                }
            except Exception as e:
                logger.warning(f"Failed to parse post-mortem response: {e}")

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

        return (
            f"Signal to Evaluate:\n"
            f"- Strategy: {signal.strategy_name}\n"
            f"- Symbol: {signal.symbol}\n"
            f"- Action: {signal.side.value}\n"
            f"- Price: {signal.price:.2f}\n"
            f"- Stop Loss: {signal.stop_loss:.2f}\n"
            f"- Take Profit: {signal.take_profit:.2f}\n"
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
        """Deterministic quantitative fallback rule when AI service is unavailable."""
        rsi = market_context.get("rsi") or market_context.get("rsi_14")
        if signal.side == OrderSide.BUY and rsi is not None and float(rsi) > 75:
            return {
                "approved": False,
                "regime": "EXTREME_VOLATILITY",
                "risk_score": 4,
                "confidence": 0.50,
                "size_multiplier": 0.20,
                "reasoning": f"Quantitative Fallback Veto: RSI ({float(rsi):.1f}) is overbought. ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

        return {
            "approved": True,
            "regime": str(market_context.get("market_regime", "RANGING")),
            "risk_score": 3,
            "confidence": 0.50,
            "size_multiplier": 0.50,
            "reasoning": f"Quantitative Fallback: Order approved with conservative sizing. ({error_reason})",
            "model": self.model,
            "fallback_used": True
        }
```

---

### 4.3. Recommendations & Implementation Plan for M1 Worker

1. **Step 1 — Update `config/settings.py`**:
   - Replace file content with the full implementation from Section 4.1.
   - Run python validation check to verify `settings.VYCE_API_KEY` resolves to `ANTHROPIC_API_KEY` and `settings.VYCE_MODEL` resolves to `claude-sonnet-4-6`.

2. **Step 2 — Update `.env` and `.env.example`**:
   - Update `VYCE_MODEL=claude-sonnet-4-6` and `ENABLE_AI_ADVISORY=True`.

3. **Step 3 — Update `ai_advisory/vyce_client.py`**:
   - Replace file content with the full implementation from Section 4.2.

4. **Step 4 — Wire `RiskManager` in `risk_engine/risk_manager.py`**:
   - Add `vyce_client: Optional[VyceClient] = None` to `RiskManager.__init__`.
   - In `handle_signal(signal: SignalEvent)`:
     - When `settings.ENABLE_AI_ADVISORY` is active, call `ai_eval = await self.vyce_client.evaluate_signal_veto(signal, context)`.
     - Publish updated `AIAdvisoryEvent`.
     - If `not ai_eval["approved"]`: record rejection in `signals` table with `reason=f"AI Advisory Veto: {ai_eval['reasoning']}"` and return `None`.
     - If approved: scale position size using `ai_eval["size_multiplier"]`.
     - If fallback was used: log `logger.warning(f"[AI Fallback Engaged] {ai_eval['reasoning']}")`.

5. **Step 5 — Add Unit Test Suite `tests/test_vyce_client.py`**:
   - Create unit tests verifying key resolution, model alias remapping, persistent client reuse, approved decision, veto decision, timeout fallback (< 3.0s), and invalid JSON fallback.

6. **Step 6 — Create Connectivity Script `scripts/check_vyce_connectivity.py`**:
   - Standalone executable script that uses `VyceClient` to verify live VPS connectivity to `https://vyceai.com/v1` with Claude Sonnet.

---

## 5. Verification Method

### 5.1. Automated Unit Testing
Run pytest from the repository root:
```powershell
.venv\Scripts\pytest.exe -v
```
**Expected Outcome**: All existing 10 tests pass + all new tests in `tests/test_vyce_client.py` pass with 100% pass rate.

### 5.2. Settings Resolution Verification Command
```powershell
.venv\Scripts\python.exe -c "
from config.settings import settings
assert settings.VYCE_API_KEY.startswith('sk-'), f'Expected sk- key, got {settings.VYCE_API_KEY}'
assert settings.VYCE_MODEL == 'claude-sonnet-4-6', f'Expected claude-sonnet-4-6, got {settings.VYCE_MODEL}'
assert settings.VYCE_BASE_URL.endswith('/v1'), f'Expected /v1 suffix, got {settings.VYCE_BASE_URL}'
print('Settings resolution verification passed!')
"
```

### 5.3. Live Connectivity Verification Script
Run the standalone connectivity check:
```powershell
.venv\Scripts\python.exe -c "
import asyncio
from ai_advisory.vyce_client import VyceClient
from core.events import SignalEvent
from core.constants import OrderSide
from datetime import datetime, timezone

async def test():
    client = VyceClient()
    sig = SignalEvent(
        strategy_name='EMA_Trend',
        symbol='BTC/USDT',
        side=OrderSide.BUY,
        price=65000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=64000.0,
        take_profit=67000.0,
        confidence=0.85
    )
    res = await client.evaluate_signal_veto(sig, {'rsi': 55.0, 'market_regime': 'BULL_TREND'})
    print('Veto evaluation result:', res)
    assert 'approved' in res
    assert 'regime' in res
    await client.close()

asyncio.run(test())
"
```

### 5.4. Invalidation Conditions
1. Vyce AI proxy removes support for model `claude-sonnet-4-6`.
2. The VPS environment revokes or alters `ANTHROPIC_API_KEY`.
3. Pydantic changes the behavior of `@model_validator(mode="after")`.
