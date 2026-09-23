"""
HỘI ĐỒNG TRANH BIỆN ĐỐI KHÁNG ĐA TÁC TỬ (ADVERSARIAL MULTI-AGENT DEBATE)
------------------------------------------------------------------------
Cơ chế kiểm duyệt tín hiệu 3 Hiệp đối kháng trước khi vào lệnh thực chiến:
- Hiệp 1: Phe Bò (gpt-5.6-sol) - Tìm luận điểm bảo vệ lệnh Long/Short theo đà xu hướng.
- Hiệp 2: Phe Gấu (claude-opus-5) - Devil's Advocate bóc mẽ bẫy dụ, rủi ro thanh lý, phân kỳ âm.
- Hiệp 3: Trọng Tài Tối Cao (claude-sonnet-5) - Phán quyết cuối cùng (Approve/Veto + Size Multiplier).
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from config.settings import settings
from ai_advisory.vyce_client import VyceClient

logger = logging.getLogger("AdversarialDebater")

ROUND1_BULL_PROMPT = """You are the Lead Bullish Momentum Strategist at a top crypto quant fund.
Your role: Review the technical signal and argue strongly IN FAVOR of entering this trade.
Focus on: Momentum indicators (EMA alignment, RSI trajectory, Volume spikes, Support holding, Breakout potential).
Keep your defense rigorous, quant-focused, and concise (under 80 words).
Output strictly valid JSON:
{
  "bull_thesis": "Your strong rationale for entering the trade",
  "confidence": 0.85
}
"""

ROUND2_BEAR_PROMPT = """You are the Chief Skeptic & Devil's Advocate Risk Officer at a top crypto quant fund.
Your role: Ruthlessly scrutinize and challenge this trade setup to protect fund capital from traps.
Focus on: Overhead resistance, liquidity hunt wicks, bear/bull traps, overbought/oversold exhaustion, funding rate extremes, slippage risk.
Keep your attack sharp, forensic, and concise (under 80 words).
Output strictly valid JSON:
{
  "bear_counter_thesis": "Your aggressive critique pointing out hidden risks or traps",
  "trap_risk_score": 4
}
"""

ROUND3_ARBITER_PROMPT = """You are the Supreme Quantitative Risk Arbiter at an algorithmic trading fund.
Review the original signal, the Bull's argument, and the Bear's critique.
Deliver your final, binding institutional judgment.
Output strictly valid JSON matching this schema:
{
  "approved": boolean,
  "verdict": "APPROVED_LONG | APPROVED_SHORT | VETOED",
  "risk_score": 1 to 5 (1=safest, 5=extreme danger),
  "confidence": 0.0 to 1.0,
  "size_multiplier": 0.2 to 1.0,
  "ruling_rationale": "Clear final justification under 60 words explaining which side was right"
}
Rules:
- Alpha Generation Doctrine: All trades carry inherent risk. The system already enforces strict 1.8% Stop-Loss and daily loss limits. Do NOT allow the Bear to veto simply because normal market risks or minor pullbacks exist.
- If Bull's momentum or pullback thesis is viable, APPROVE the trade. If Bear raises valid caution points (e.g. overhead resistance or moderate chop), reduce size_multiplier (0.4 - 0.8) rather than killing the trade!
- Only VETO if Bear proves a catastrophic structural flaw (e.g. invalid SL, trading straight into macro flash crash).
"""


class AdversarialDebater:
    def __init__(self, vyce_client: Optional[VyceClient] = None):
        self.vyce_client = vyce_client or VyceClient()
        # ĐỘI HÌNH VAR TỐI ƯU 3 HIỆP TOÀN LỰC:
        # Hiệp 1: Phe Bò (Momentum Thesis) - Groq LPU 120B (80ms) / cx/gpt-5.6-sol
        self.bull_model = "openai/gpt-oss-120b"
        # Hiệp 2: Phe Gấu (Devil's Advocate / Bóc bẫy) - SuperGrok 4.7 / DeepSeek-V4.1
        self.bear_model = "gcli/grok-4.7"
        # Hiệp 3: Đồng Trọng Tài VAR Tối Cao - cx/gpt-6-astra (OpenAI Codex Plus) & claude-sonnet-4-6
        self.arbiter_model = "cx/gpt-6-astra"
        self.arbiter_co_model = "gcli/grok-4.7"
        self.arbiter_fallback_model = "claude-sonnet-4-6"
        # Dự phòng khẩn cấp khi nghẽn: Google Gemini 3.7 & Cloudflare Llama-3.3 70B
        self.fallback_scout_model = "gemini-3.7-flash"
        self.fallback_fast_model = "@cf/meta/llama-3.3-70b-instruct-fp8-fast" 

    async def debate_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        symbol = signal_data.get("symbol", "BTC/USDT")
        side = signal_data.get("side", "BUY")
        price = signal_data.get("price", 0.0)
        strategy = signal_data.get("strategy", "UNKNOWN")
        context = signal_data.get("context", {})

        logger.info(f"[TRANH BIỆN ĐỐI KHÁNG] Thẩm định tín hiệu {side} {symbol} @ {price} ({strategy}) - Chế độ Song Song")

        # Enrich with Community Intelligence & Macro Sentiment
        intel_notes = []
        if "NEAR" in symbol:
            intel_notes.append("Community Intelligence (Lesson #35): NEAR has strong Chain Abstraction & AI narrative; watch for impulsive legs, take partial profits disciplined (House Money).")
        elif "SUI" in symbol:
            intel_notes.append("Community Intelligence: SUI has high Layer 1 ecosystem inflows and aggressive volatility; tight trailing stop recommended.")
        elif "DOGE" in symbol or "PEPE" in symbol:
            intel_notes.append("Community Intelligence: High-beta meme coin driven by retail social sentiment; beware of blow-off tops and sudden wick liquidations.")

        intel_str = ("\n" + "\n".join(intel_notes)) if intel_notes else ""

        signal_summary = (
            f"Trading Signal: {side} {symbol} at ${price}\n"
            f"Strategy: {strategy}\n"
            f"Market Context: {json.dumps(context, ensure_ascii=False)}"
            f"{intel_str}"
        )

        # GIAI ĐOẠN 1: TRANH BIỆN SONG SONG (BÒ & GẤU PHÂN TÍCH ĐỒNG THỜI)
        bull_task = self.vyce_client.chat_completion(
            system_prompt=ROUND1_BULL_PROMPT,
            user_content=signal_summary,
            max_tokens=200,
            temperature=0.2,
            timeout=13.0,
            model=self.bull_model,
            action="ADVERSARIAL_DEBATE_R1_BULL"
        )

        bear_task = self.vyce_client.chat_completion(
            system_prompt=ROUND2_BEAR_PROMPT,
            user_content=signal_summary,
            max_tokens=200,
            temperature=0.3,
            timeout=18.0,
            model=self.bear_model,
            action="ADVERSARIAL_DEBATE_R2_BEAR"
        )

        results = await asyncio.gather(bull_task, bear_task, return_exceptions=True)
        round1_res = results[0] if not isinstance(results[0], Exception) else None
        round2_res = results[1] if not isinstance(results[1], Exception) else None

        if not round2_res:
            try:
                round2_res = await self.vyce_client.chat_completion(
                    system_prompt=ROUND2_BEAR_PROMPT,
                    user_content=signal_summary,
                    max_tokens=200,
                    temperature=0.3,
                    timeout=5.0,
                    model="qwen/qwen3.8-27b",
                    action="ADVERSARIAL_DEBATE_R2_BEAR_FALLBACK"
                )
            except Exception:
                pass

        bull_thesis = "Signal momentum aligns with technical parameters."
        if round1_res:
            try:
                c1 = round1_res.strip().strip("`").replace("json\n", "")
                d1 = json.loads(c1)
                bull_thesis = d1.get("bull_thesis", bull_thesis)
            except Exception:
                bull_thesis = round1_res[:150]

        bear_critique = "Potential liquidity hunt or resistance rejection near current levels."
        if round2_res:
            try:
                c2 = round2_res.strip().strip("`").replace("json\n", "")
                d2 = json.loads(c2)
                bear_critique = d2.get("bear_counter_thesis", bear_critique)
            except Exception:
                bear_critique = round2_res[:150]

        # GIAI ĐOẠN 2: TRỌNG TÀI TỐI CAO RA PHÁN QUYẾT (SUPREME CO-ARBITER)
        arbiter_input = (
            f"ORIGINAL SIGNAL: {side} {symbol} @ ${price}\n\n"
            f"[ROUND 1 - BULL THESIS ({self.bull_model})]:\n{bull_thesis}\n\n"
            f"[ROUND 2 - BEAR CRITIQUE ({self.bear_model})]:\n{bear_critique}\n\n"
            f"Deliver your supreme verdict strictly in JSON."
        )

        active_arbiter = self.arbiter_model
        round3_res = await self.vyce_client.chat_completion(
            system_prompt=ROUND3_ARBITER_PROMPT,
            user_content=arbiter_input,
            max_tokens=250,
            temperature=0.1,
            timeout=13.0,
            model=self.arbiter_model,
            action="ADVERSARIAL_DEBATE_R3_ARBITER"
        )

        if not round3_res:
            logger.warning(f"[Adversarial Debate] Arbiter {self.arbiter_model} failed, engaging Co-Arbiter {self.arbiter_co_model}...")
            active_arbiter = self.arbiter_co_model
            round3_res = await self.vyce_client.chat_completion(
                system_prompt=ROUND3_ARBITER_PROMPT,
                user_content=arbiter_input,
                max_tokens=250,
                temperature=0.1,
                timeout=12.0,
                model=self.arbiter_co_model,
                action="ADVERSARIAL_DEBATE_R3_CO_ARBITER"
            )

        if not round3_res:
            logger.warning(f"[Adversarial Debate] Co-Arbiter {self.arbiter_co_model} failed, engaging fallback {self.arbiter_fallback_model}...")
            active_arbiter = self.arbiter_fallback_model
            round3_res = await self.vyce_client.chat_completion(
                system_prompt=ROUND3_ARBITER_PROMPT,
                user_content=arbiter_input,
                max_tokens=250,
                temperature=0.1,
                timeout=10.0,
                model=self.arbiter_fallback_model,
                action="ADVERSARIAL_DEBATE_R3_ARBITER_FALLBACK"
            )

        if not round3_res:
            logger.warning("[Adversarial Debate] Arbiter model produced no response or failed; engaging safety fallback.")
            return {
                "approved": False,
                "verdict": "VETOED_TIMEOUT",
                "risk_score": 4,
                "confidence": 0.0,
                "size_multiplier": 0.0,
                "ruling_rationale": "Adversarial Arbiter unavailable or timed out.",
                "fallback_used": True,
                "debate_transcript": {
                    "bull_model": self.bull_model,
                    "bull_thesis": bull_thesis,
                    "bear_model": self.bear_model,
                    "bear_critique": bear_critique,
                    "arbiter_model": active_arbiter
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        final_verdict = {
            "approved": True,
            "verdict": "APPROVED_LONG" if side.upper() == "BUY" else "APPROVED_SHORT",
            "risk_score": 2,
            "confidence": 0.85,
            "size_multiplier": 1.0,
            "ruling_rationale": "Bull thesis holds under scrutiny; reasonable risk-reward.",
            "fallback_used": False,
            "debate_transcript": {
                "bull_model": self.bull_model,
                "bull_thesis": bull_thesis,
                "bear_model": self.bear_model,
                "bear_critique": bear_critique,
                "arbiter_model": active_arbiter
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if round3_res:
            try:
                c3 = round3_res.strip().strip("`").replace("json\n", "")
                d3 = json.loads(c3)
                if d3.get("risk_score") is None or d3.get("size_multiplier") is None:
                    raise ValueError("Critical field (risk_score or size_multiplier) is None")
                final_verdict["approved"] = bool(d3.get("approved", True))
                final_verdict["verdict"] = str(d3.get("verdict", final_verdict["verdict"]))
                final_verdict["risk_score"] = int(d3.get("risk_score", 2))
                final_verdict["confidence"] = float(d3.get("confidence", 0.85))
                final_verdict["size_multiplier"] = float(d3.get("size_multiplier", 1.0))
                final_verdict["ruling_rationale"] = str(d3.get("ruling_rationale", final_verdict["ruling_rationale"]))
            except Exception as e:
                logger.warning(f"Lỗi phân tích phán quyết Trọng tài: {e}")
                final_verdict["fallback_used"] = True
                final_verdict["ruling_rationale"] = f"Adversarial Arbiter parse error: {e}"

        logger.info(
            f"[KẾT QUẢ TRANH BIỆN] Phán quyết: {final_verdict['verdict']} | "
            f"Duyệt: {final_verdict['approved']} | Risk Score: {final_verdict['risk_score']}"
        )
        return final_verdict
