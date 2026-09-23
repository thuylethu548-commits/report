"""
ASTRA DIGITAL RESEARCH LAB — CONTINUOUS IMPROVEMENT LOOP (CI-LOOP)
------------------------------------------------------------------
Automates the quantitative research lifecycle:
Hypothesis Propose ➔ Risk Scrutiny ➔ Stress Testing ➔ Audit ➔ Memory Persist.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from core.research_lab.agents import (
    MarketResearchAgent,
    QuantResearchAgent,
    RiskSkepticAgent,
    LeadReviewerAgent,
    ResearchHypothesis,
    ExperimentResult
)
from core.research_lab.scenario_engine import ScenarioTestingEngine
from core.research_lab.knowledge_store import ResearchKnowledgeStore
from ai_advisory.vyce_client import VyceClient

logger = logging.getLogger("ContinuousImprovementLoop")


class ContinuousImprovementLoop:
    """Orchestrates end-to-end research experiments across the agent team."""

    def __init__(
        self,
        vyce_client: Optional[VyceClient] = None,
        knowledge_store: Optional[ResearchKnowledgeStore] = None
    ):
        self.vyce_client = vyce_client or VyceClient()
        self.knowledge_store = knowledge_store or ResearchKnowledgeStore()
        self.market_agent = MarketResearchAgent(self.vyce_client)
        self.quant_agent = QuantResearchAgent(self.vyce_client)
        self.risk_agent = RiskSkepticAgent(self.vyce_client)
        self.reviewer_agent = LeadReviewerAgent(self.vyce_client)
        self.scenario_engine = ScenarioTestingEngine()

    async def run_experiment_cycle(
        self,
        symbol: str = "BTC/USDT",
        custom_hypothesis: Optional[ResearchHypothesis] = None
    ) -> ExperimentResult:
        """
        Executes one complete research cycle from hypothesis formulation to audit.
        """
        logger.info(f"[CI-Loop] Starting research cycle for {symbol}...")
        exp_id = f"EXP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 1. Market Context Discovery
        if not custom_hypothesis:
            market_intel = await self.market_agent.scan_market_context(symbol)
            hypothesis = await self.quant_agent.formulate_hypothesis(symbol, market_intel)
        else:
            hypothesis = custom_hypothesis

        logger.info(f"[CI-Loop] Formulated Hypothesis: {hypothesis.title} ({hypothesis.hypothesis_id})")

        # 2. Risk Skeptic Scrutiny
        risk_scrutiny = await self.risk_agent.scrutinize_hypothesis(hypothesis)
        logger.info(f"[CI-Loop] Risk Scrutiny Score: {risk_scrutiny.get('skeptic_risk_score', 2)}/5")

        # 3. Scenario & Stress Testing Simulation
        metrics, stress_results = self.scenario_engine.run_stress_suite(hypothesis, iterations=500)
        logger.info(f"[CI-Loop] Simulation Metrics: Sharpe={metrics['sharpe_ratio']}, WinRate={metrics['win_rate']}%")

        # 4. Lead Reviewer Audit
        audit = await self.reviewer_agent.audit_experiment(hypothesis, metrics, stress_results)
        verdict = audit.get("verdict", "NEEDS_CALIBRATION")
        score = float(audit.get("score", 75.0))
        notes = audit.get("reviewer_notes", "Automated audit complete.")
        logger.info(f"[CI-Loop] Final Audit Verdict: {verdict} (Score: {score})")

        # 5. Persist to Knowledge Store & Research Memory
        self.knowledge_store.save_experiment(
            experiment_id=exp_id,
            hypothesis_id=hypothesis.hypothesis_id,
            title=hypothesis.title,
            symbol=hypothesis.target_symbol,
            strategy=hypothesis.proposed_strategy,
            parameters=hypothesis.parameters,
            metrics=metrics,
            stress_results=stress_results,
            status=verdict,
            reviewer_notes=notes,
            score=score
        )

        return ExperimentResult(
            experiment_id=exp_id,
            hypothesis=hypothesis,
            sharpe_ratio=metrics["sharpe_ratio"],
            calmar_ratio=metrics["calmar_ratio"],
            win_rate=metrics["win_rate"],
            max_drawdown_pct=metrics["max_drawdown_pct"],
            profit_factor=metrics["profit_factor"],
            total_simulated_trades=metrics["total_simulated_trades"],
            net_profit_pct=metrics["net_profit_pct"],
            passed_stress_tests=stress_results.get("passed_all", False),
            audit_verdict=verdict,
            reviewer_notes=notes
        )
