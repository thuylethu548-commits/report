import os
from typing import Literal, List
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Trading Environment
    TRADING_MODE: Literal["paper", "testnet", "live"] = "paper"
    LIVE_SAFETY_RELEASE_APPROVED: bool = False

    # Binance API
    BINANCE_API_KEY: str = "mock_key"
    BINANCE_API_SECRET: str = "mock_secret"
    BINANCE_USE_TESTNET: bool = True

    # Public referral/creator links only; never put API secrets here.
    BINANCE_REFERRAL_URL: str = ""
    OKX_REFERRAL_URL: str = "https://okx.com/join/79650738"

    # Trading Pairs & Timeframe
    SYMBOL: str = "BTC/USDT"
    SYMBOLS: List[str] = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "DOGE/USDT", "1000PEPE/USDT", "NEAR/USDT", "SUI/USDT"]
    TIMEFRAME: str = "15m"

    # Multi-Pair & Auto-Trade Engine
    AUTO_TRADE_ENABLED: bool = True
    COOLDOWN_MINUTES: int = 15

    # Futures Market & Leverage
    MARKET_TYPE: Literal["spot", "futures"] = "futures"
    FUTURES_LEVERAGE: int = 3
    DEFAULT_LEVERAGE: int = 3
    LIVE_MAX_USDT_PER_ORDER: float = 25.0
    DEFAULT_POSITION_SIZE_USD: float = 25.0

    # Risk Management & Daily Target Rules (Full Luc Sprint)
    STARTING_BALANCE_USDT: float = 55.43
    TARGET_DAILY_PROFIT_USD: float = 18.0
    MAX_DAILY_LOSS_USD: float = 5.0
    HOUSE_MONEY_MODE_ENABLED: bool = True
    MAX_POSITION_PERCENT: float = 0.45  # Max 45% of portfolio per trade (~$25)
    DAILY_MAX_DRAWDOWN_PERCENT: float = 0.09  # ~9% daily loss lock (-$5.0)
    STOP_LOSS_PERCENT: float = 0.025  # 2.5% hard stop
    MAX_OPEN_POSITIONS: int = 2
    MAX_POSITIONS_PER_SYMBOL: int = 1

    # Multi-Timeframe Confluence (15m + 1h + 4h)
    ENABLE_MULTI_TIMEFRAME: bool = True
    MTF_EMA_PERIOD: int = 50

    # Time Window & Vietnam Market Session Guard
    ENABLE_TIME_WINDOW_GUARD: bool = True

    # ETFBit AI Gateway (OpenAI Compatible)
    ETFBIT_API_KEY: str = "***REDACTED***"
    ETFBIT_BASE_URL: str = "https://api.etfbit.net/v1"
    ETFBIT_MODEL_SUPREME: str = "gpt-5.6-sol"
    ETFBIT_MODEL_SENTIMENT: str = "gpt-5.6-terra"
    ETFBIT_MODEL_FAST: str = "gpt-5.6-luna"

    # Google Gemini Multi-Account Key Pool (1,500 req/day per Google account free)
    GEMINI_API_KEY: str = "AQ.REDACTED_GEMINI_KEY"
    GEMINI_API_KEYS: str = ""

    # Spot Trading Engine Integration (Dedicated 500U BTC Desk)
    ENABLE_SPOT_ENGINE: bool = True
    SPOT_STARTING_BALANCE_USDT: float = 500.0
    SPOT_SYMBOLS: List[str] = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    SPOT_BTC_PYRAMID_DCA: bool = True
    SPOT_BTC_TIER1_RATIO: float = 0.30  # 30% = 150 USDT (Market anchor entry ~$85.5k-$86.5k)
    SPOT_BTC_TIER2_RATIO: float = 0.40  # 40% = 200 USDT (Dip support accumulation ~$82.8k-$83.8k)
    SPOT_BTC_TIER3_RATIO: float = 0.30  # 30% = 150 USDT (Flash crash reserve ~$80k-$81.5k)
    SPOT_BTC_TP1_PRICE: float = 90000.0 # Step 1: Sell 33% at $90k
    SPOT_BTC_TP2_PRICE: float = 93000.0 # Step 2: Sell 33% at $93k
    SPOT_BTC_TP3_PRICE: float = 95000.0 # Step 3: Sell remaining 34% at $95k+
    SPOT_DCA_STEP_PERCENT: float = 0.03
    SPOT_TAKE_PROFIT_PERCENT: float = 0.05

    # Vyce AI Proxy (OpenAI Compatible)
    VYCE_API_KEY: str = "mock_vyce_key"
    VYCE_BASE_URL: str = "https://vyceai.com/v1"
    VYCE_MODEL: str = "claude-sonnet-4-6"
    VYCE_FAST_MODEL: str = "deepseek-v4-flash"
    AI_COUNCIL_MODE: str = "consensus"  # "consensus" | "failover" | "single" | "adversarial"
    ENABLE_ADVERSARIAL_DEBATE: bool = True
    ENABLE_AI_ADVISORY: bool = True
    AI_TIMEOUT_SECONDS: float = 25.0
    AI_FAST_TIMEOUT_SECONDS: float = 12.0

    # Groq Cloud AI Engine (Ultra-Fast LPU Inference Multi-Key Pool)
    GROQ_API_KEY: str = "gsk_REDACTED_FOR_SECURITY"
    GROQ_API_KEYS: str = "gsk_REDACTED_FOR_SECURITY,gsk_REDACTED_FOR_SECURITY,gsk_REDACTED_FOR_SECURITY,gsk_REDACTED_FOR_SECURITY"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    # GuRouter (Vietnamese MMO Admin 5B Token / Community Proxy)
    GUROUTER_API_KEY: str = "***REDACTED***"
    GUROUTER_BASE_URL: str = "https://gurouter.com/v1"
    GUROUTER_MODEL: str = "gpt-6-luna"

    # Cloudflare Workers AI Gateway
    CLOUDFLARE_AI_TOKEN: str = "cfut_REDACTED_CLOUDFLARE_TOKEN"
    CLOUDFLARE_ACCOUNT_ID: str = "6fd41a30a94276205d7c2378180a2bec"
    CLOUDFLARE_MODEL: str = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"

    # 9Router Local VPS Proxy (ChatGPT Plus & Codex Pool)
    NINEROUTER_API_KEY: str = "***REDACTED***"
    NINEROUTER_BASE_URL: str = "http://localhost:20128/v1"

    # Telegram (Optional)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    ENABLE_TELEGRAM: bool = False

    # Google OAuth
    GOOGLE_CLIENT_ID: str = "REDACTED_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: str = "GOCSPX-REDACTED_CLIENT_SECRET"

    # SMTP Email Service
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "thuylethu548@gmail.com"
    SMTP_PASSWORD: str = "REDACTED_APP_PASSWORD"
    ENABLE_EMAIL_ALERTS: bool = True

    # Admin Security Gate
    ADMIN_PASSWORD: str = "AstraAdmin@2026"
    ADMIN_SESSION_SECRET: str = "astra_quantum_admin_auth_token_secret_key_2026"

    # Dashboard Server
    DASHBOARD_HOST: str = "127.0.0.1"
    DASHBOARD_PORT: int = 8386
    DATABASE_PATH: str = "trading_bot.db"

    # Supabase Cloud Hybrid Database
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_PAT: str = ""

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

        # 3. Model Alias Resolution (Synchronized with Vyce AI live endpoint)
        model_aliases = {
            "deepseek-chat": "deepseek-v4.1",
            "deepseek-r1": "deepseek-v4.1",
            "deepseek-v4": "deepseek-v4.1",
            "claude-3-5-sonnet": "claude-sonnet-4-6",
            "claude-3.5-sonnet": "claude-sonnet-4-6",
            "claude-3-5-sonnet-20241022": "claude-sonnet-4-6",
            "claude-3-sonnet": "claude-sonnet-4-6",
            "claude-3-opus": "claude-sonnet-4-6",
            "claude-opus-5": "claude-sonnet-4-6",
            "claude-sonnet-5": "claude-sonnet-4-6",
            "qwen3.8-flash": "qwen3.8-flash",
            "qwen-3.8-flash": "qwen3.8-flash",
        }
        self.VYCE_MODEL = model_aliases.get(self.VYCE_MODEL.strip().lower(), self.VYCE_MODEL)

        # 4. Default AI Advisory Enablement & Timeout
        env_ai_adv = os.getenv("ENABLE_AI_ADVISORY")
        if env_ai_adv is not None:
            self.ENABLE_AI_ADVISORY = env_ai_adv.strip().lower() in ("true", "1", "yes")
        env_timeout = os.getenv("AI_TIMEOUT_SECONDS")
        if env_timeout:
            try:
                self.AI_TIMEOUT_SECONDS = float(env_timeout)
            except ValueError:
                self.AI_TIMEOUT_SECONDS = 3.0

        env_fast_model = os.getenv("VYCE_FAST_MODEL")
        if env_fast_model:
            self.VYCE_FAST_MODEL = env_fast_model.strip()

        env_council_mode = os.getenv("AI_COUNCIL_MODE")
        if env_council_mode:
            self.AI_COUNCIL_MODE = env_council_mode.strip().lower()
        env_adv_deb = os.getenv("ENABLE_ADVERSARIAL_DEBATE")
        if env_adv_deb is not None:
            self.ENABLE_ADVERSARIAL_DEBATE = env_adv_deb.strip().lower() in ("true", "1", "yes")

        env_fast_timeout = os.getenv("AI_FAST_TIMEOUT_SECONDS")
        if env_fast_timeout:
            try:
                self.AI_FAST_TIMEOUT_SECONDS = float(env_fast_timeout)
            except ValueError:
                self.AI_FAST_TIMEOUT_SECONDS = 2.0

        return self



settings = Settings()
