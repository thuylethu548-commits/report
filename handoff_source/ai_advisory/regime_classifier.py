import json
import logging
from datetime import datetime, timezone
import pandas as pd
from config.settings import settings
from core.constants import MarketRegime
from core.events import AIAdvisoryEvent, MarketEvent
from core.event_bus import EventBus
from data.storage import Database
from .vyce_client import VyceClient

logger = logging.getLogger("RegimeClassifier")

SYSTEM_PROMPT = """You are a quantitative market regime classifier for an automated cryptocurrency trading system.
Analyze the provided market statistics (asset, price action, volatility, volume trend) and classify the regime.
You MUST output strictly valid JSON with no markdown tags, matching this exact schema:
{
  "regime": "bull_trend" | "bear_trend" | "ranging" | "extreme_volatility",
  "risk_score": 1 to 5,
  "trade_allowed": true | false,
  "size_multiplier": 0.0 to 1.0,
  "reasoning": "brief explanation under 30 words",
  "confidence": 0.0 to 1.0
}
If volatility is abnormal or market is chaotic, set regime="extreme_volatility", trade_allowed=false, and size_multiplier=0.0."""


class MarketRegimeClassifier:
    def __init__(self, event_bus: EventBus, db: Database, client: VyceClient | None = None):
        self.event_bus = event_bus
        self.db = db
        self.client = client or VyceClient()
        self.current_advisory: AIAdvisoryEvent = AIAdvisoryEvent(
            symbol=settings.SYMBOL,
            timestamp=datetime.now(timezone.utc),
            regime=MarketRegime.RANGING,
            risk_score=2,
            trade_allowed=True,
            size_multiplier=1.0,
            reasoning="Default baseline initialization.",
            confidence=1.0
        )

    async def evaluate_market(self, df: pd.DataFrame, symbol: str) -> AIAdvisoryEvent:
        if not settings.ENABLE_AI_ADVISORY:
            return self.current_advisory

        if len(df) < 15:
            return self.current_advisory

        # Calculate statistics
        latest_close = float(df["close"].iloc[-1])
        pct_change_24h = float((df["close"].iloc[-1] / df["close"].iloc[0] - 1.0) * 100)
        volatility = float(df["close"].pct_change().std() * 100)
        avg_volume = float(df["volume"].mean())
        curr_volume = float(df["volume"].iloc[-1])
        vol_ratio = curr_volume / (avg_volume + 1e-9)

        user_content = f"""Market Snapshot for {symbol}:
- Current Close: {latest_close:.2f}
- 24-Period Price Change: {pct_change_24h:.2f}%
- 24-Period Return Volatility: {volatility:.3f}%
- Current Volume vs Avg: {vol_ratio:.2f}x
Determine market regime and risk level."""

        raw_response = await self.client.chat_completion(SYSTEM_PROMPT, user_content)
        if raw_response:
            try:
                # Clean any backticks if present
                clean_json = raw_response.strip().strip("```json").strip("```").strip()
                parsed = json.loads(clean_json)

                regime_str = parsed.get("regime", "ranging").lower()
                regime = MarketRegime(regime_str) if regime_str in MarketRegime._value2member_map_ else MarketRegime.RANGING
                confidence = float(parsed.get("confidence", 1.0))

                advisory = AIAdvisoryEvent(
                    symbol=symbol,
                    timestamp=datetime.now(timezone.utc),
                    regime=regime,
                    risk_score=int(parsed.get("risk_score", 3)),
                    trade_allowed=bool(parsed.get("trade_allowed", True)),
                    size_multiplier=float(parsed.get("size_multiplier", 1.0)),
                    reasoning=str(parsed.get("reasoning", "")),
                    confidence=confidence
                )
                self.current_advisory = advisory
                await self.db.save_ai_advisory(
                    symbol=symbol,
                    regime=advisory.regime.value,
                    risk_score=advisory.risk_score,
                    trade_allowed=advisory.trade_allowed,
                    size_multiplier=advisory.size_multiplier,
                    reasoning=advisory.reasoning,
                    dt=advisory.timestamp,
                    confidence=confidence
                )
                await self.event_bus.publish(advisory)
                logger.info(f"[AI Advisory] Regime: {advisory.regime.value} | Risk: {advisory.risk_score}/5 | TradeAllowed: {advisory.trade_allowed}")
                return advisory

            except Exception as e:
                logger.warning(f"Error parsing AI Advisory response: {e}. Keeping current regime.")

        return self.current_advisory

    # Alias for API compatibility
    classify_and_broadcast = evaluate_market
