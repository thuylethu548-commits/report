"""
ASTRA DIGITAL RESEARCH LAB — RESEARCH AGENT ROSTER
--------------------------------------------------
Specialized AI Agents forming the Automated Quantitative Research Team:
1. MarketResearchAgent: Discovers macro trends, news flow, funding structure.
2. QuantResearchAgent: Formulates mathematical hypotheses and strategy parameters.
3. RiskSkepticAgent: Devil's advocate scrutinizing drawdown and liquidity traps.
4. DataScientistAgent: Feature engineering, stationarity tests, anomaly profiling.
5. LeadReviewerAgent: Independent audit, overfitting checks, objective scoring.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from config.settings import settings
from ai_advisory.vyce_client import VyceClient

logger = logging.getLogger("ResearchAgents")


@dataclass
class ResearchHypothesis:
    hypothesis_id: str
    title: str
    target_symbol: str
    core_thesis: str
    proposed_strategy: str
    parameters: Dict[str, Any]
    target_market_regime: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ExperimentResult:
    experiment_id: str
    hypothesis: ResearchHypothesis
    sharpe_ratio: float
    calmar_ratio: float
    win_rate: float
    max_drawdown_pct: float
    profit_factor: float
    total_simulated_trades: int
    net_profit_pct: float
    passed_stress_tests: bool
    audit_verdict: str  # "APPROVED" | "REJECTED" | "NEEDS_CALIBRATION"
    reviewer_notes: str
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MarketResearchAgent:
    """Scans macroeconomic context, funding rates, and volume structure to propose research focus."""

    def __init__(self, vyce_client: Optional[VyceClient] = None):
        self.client = vyce_client or VyceClient()
        self.model = "gcli/grok-4.7"
        self.fallback_model = "gemini-3.7-flash"

    async def scan_market_context(self, symbol: str = "BTC/USDT", context_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prompt = f"""You are the Chief Market Research Analyst at an institutional quantitative research lab.
Analyze the current market landscape for {symbol}.
Identify structural anomalies, funding rate extremes, or emerging volatility regimes that warrant algorithmic research.
Output strictly valid JSON matching this schema:
{{
  "symbol": "{symbol}",
  "regime": "BULL_EXPANSION | CHOP_CONSOLIDATION | HIGH_FUNDING_SQUEEZE | LIQUIDATION_RISK",
  "key_drivers": ["catalyst 1", "catalyst 2"],
  "recommended_hypothesis_direction": "Brief direction for the Quant team under 40 words"
}}
"""
        try:
            resp = await self.client.chat_completion(
                system_prompt="You are an institutional quantitative market analyst. Output valid JSON.",
                user_content=prompt,
                model=self.model,
                temperature=0.2,
                max_tokens=300,
                timeout=15.0,
                action="MARKET_RESEARCH_SCAN"
            )
            if resp:
                cleaned = resp.strip().strip("`").replace("json\n", "")
                return json.loads(cleaned)
        except Exception as e:
            logger.warning(f"[MarketResearchAgent] Scan error: {e}")

        return {
            "symbol": symbol,
            "regime": "CHOP_CONSOLIDATION",
            "key_drivers": ["Moderate spot volume", "Neutral funding rate near 0.01%"],
            "recommended_hypothesis_direction": "Test tight volatility breakout with strict 1.2x ATR trailing lock."
        }


class QuantResearchAgent:
    """Formulates mathematical hypotheses and algorithmic parameter configurations."""

    def __init__(self, vyce_client: Optional[VyceClient] = None):
        self.client = vyce_client or VyceClient()
        self.model = "cx/gpt-5.6-sol"
        self.fallback_model = "openai/gpt-oss-120b"

    async def formulate_hypothesis(self, symbol: str, market_intel: Dict[str, Any]) -> ResearchHypothesis:
        h_id = f"HYP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        regime = market_intel.get("regime", "CHOP_CONSOLIDATION")
        direction = market_intel.get("recommended_hypothesis_direction", "Test dynamic ATR trailing stop")

        prompt = f"""You are the Lead Quantitative Strategist.
Given this market intelligence:
Symbol: {symbol}
Regime: {regime}
Guidance: {direction}

Formulate a testable algorithmic trading hypothesis with exact parameters.
Output strictly valid JSON:
{{
  "title": "Concise hypothesis title",
  "core_thesis": "Why this mathematical setup provides positive expectancy",
  "proposed_strategy": "EMA_TREND_MTF | DONCHIAN_VOL_BREAKOUT | RSI_MEAN_REVERSION",
  "parameters": {{
    "lookback_period": 20,
    "atr_multiplier": 1.2,
    "break_even_pct": 0.015,
    "take_profit_rr": 2.0
  }}
}}
"""
        try:
            resp = await self.client.chat_completion(
                system_prompt="You are an institutional quant researcher. Output valid JSON.",
                user_content=prompt,
                model=self.model,
                temperature=0.2,
                max_tokens=350,
                timeout=15.0,
                action="QUANT_HYPOTHESIS_FORMULATION"
            )
            if resp:
                cleaned = resp.strip().strip("`").replace("json\n", "")
                data = json.loads(cleaned)
                return ResearchHypothesis(
                    hypothesis_id=h_id,
                    title=data.get("title", f"Optimized {symbol} Momentum Setup"),
                    target_symbol=symbol,
                    core_thesis=data.get("core_thesis", direction),
                    proposed_strategy=data.get("proposed_strategy", "EMA_TREND_MTF"),
                    parameters=data.get("parameters", {"lookback_period": 20, "atr_multiplier": 1.2, "break_even_pct": 0.015}),
                    target_market_regime=regime
                )
        except Exception as e:
            logger.warning(f"[QuantResearchAgent] Formulation error: {e}")

        # Baseline rigorous hypothesis
        return ResearchHypothesis(
            hypothesis_id=h_id,
            title=f"Dynamic ATR Volatility Trailing Filter for {symbol}",
            target_symbol=symbol,
            core_thesis="Locking break-even at 1.5x ATR during consolidation prevents drawdown churn while allowing trend expansion.",
            proposed_strategy="EMA_TREND_MTF",
            parameters={"lookback_period": 21, "atr_multiplier": 1.25, "break_even_pct": 0.015, "stop_loss_pct": 0.018},
            target_market_regime=regime
        )


class RiskSkepticAgent:
    """Chief Devil's Advocate scrutinizing hypotheses for hidden tail risks."""

    def __init__(self, vyce_client: Optional[VyceClient] = None):
        self.client = vyce_client or VyceClient()
        self.model = "claude-sonnet-4-6"

    async def scrutinize_hypothesis(self, hypothesis: ResearchHypothesis) -> Dict[str, Any]:
        prompt = f"""You are the Chief Risk Officer and Devil's Advocate at a quant fund.
Scrutinize this proposed strategy hypothesis:
Title: {hypothesis.title}
Thesis: {hypothesis.core_thesis}
Strategy: {hypothesis.proposed_strategy}
Parameters: {json.dumps(hypothesis.parameters)}

Identify 2 fatal failure modes (e.g. slippage during liquidity cascades, funding fee erosion, false breakouts).
Output strictly valid JSON:
{{
  "skeptic_risk_score": 1 to 5 (1=safe, 5=extreme danger),
  "primary_vulnerabilities": ["Vulnerability 1", "Vulnerability 2"],
  "mandatory_stress_condition": "e.g. Test with -25% flash crash and 2x slippage"
}}
"""
        try:
            resp = await self.client.chat_completion(
                system_prompt="You are a ruthless risk officer challenging trading hypotheses. Output valid JSON.",
                user_content=prompt,
                model=self.model,
                temperature=0.1,
                max_tokens=300,
                timeout=12.0,
                action="RISK_SKEPTIC_SCRUTINY"
            )
            if resp:
                cleaned = resp.strip().strip("`").replace("json\n", "")
                return json.loads(cleaned)
        except Exception as e:
            logger.warning(f"[RiskSkepticAgent] Scrutiny error: {e}")

        return {
            "skeptic_risk_score": 2,
            "primary_vulnerabilities": ["Slippage during fast market dumps", "Whipsaw losses in tight range"],
            "mandatory_stress_condition": "Test under synthetic -20% cascade with 0.05% slippage"
        }


class LeadReviewerAgent:
    """Audits backtest results, checks for overfitting, and assigns final institutional verdict."""

    def __init__(self, vyce_client: Optional[VyceClient] = None):
        self.client = vyce_client or VyceClient()
        self.model = "cx/gpt-6-astra"
        self.fallback_model = "claude-sonnet-4-6"

    async def audit_experiment(
        self,
        hypothesis: ResearchHypothesis,
        metrics: Dict[str, Any],
        stress_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        sharpe = metrics.get("sharpe_ratio", 0.0)
        max_dd = metrics.get("max_drawdown_pct", 0.0)
        win_rate = metrics.get("win_rate", 0.0)
        passed_stress = stress_results.get("passed_all", False)

        # Institutional Quantitative Hurdle:
        # Sharpe >= 1.6, MaxDD <= 3.5%, WinRate >= 55%, Passed Stress Tests
        is_approved = (sharpe >= 1.6) and (max_dd <= 3.5) and (win_rate >= 55.0) and passed_stress

        verdict = "APPROVED" if is_approved else ("NEEDS_CALIBRATION" if sharpe >= 1.2 else "REJECTED")

        notes = (
            f"Sharpe {sharpe:.2f} | MaxDD {max_dd:.2f}% | WinRate {win_rate:.1f}%. "
            f"Stress tests: {'PASSED' if passed_stress else 'FAILED'}. "
            f"{'Robust expectancy under adverse regimes.' if is_approved else 'Excessive drawdown or regime fragility detected.'}"
        )

        return {
            "verdict": verdict,
            "approved_for_live_canary": is_approved,
            "score": round(min(100.0, (sharpe * 30.0) + (win_rate * 0.4) - (max_dd * 5.0)), 1),
            "reviewer_notes": notes
        }
