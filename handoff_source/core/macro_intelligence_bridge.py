import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from config.settings import settings
from core.event_bus import EventBus
from data.storage import Database
from ai_advisory.vyce_client import VyceClient

logger = logging.getLogger("MacroIntelligenceBridge")


class MacroStrategicDirectiveEvent:
    """Event phát ra từ Đội 2 (Tình Báo Vĩ Mô) gửi Đội 1 (Tác Chiến Khớp Lệnh) & Thượng Đế."""
    def __init__(self, directive: Dict[str, Any]):
        self.directive = directive
        self.directive_id = directive.get("directive_id", str(uuid.uuid4()))
        self.issuer = directive.get("issuer", "Hash")
        self.regime = directive.get("regime", "RANGING")
        self.venue_mandate = directive.get("venue_mandate", "FUTURES_ACTIVE")
        self.boss_capital_verdict = directive.get("boss_capital_verdict", "HOLD_450U_VAULT")
        self.confidence = float(directive.get("confidence", 0.85))
        self.summary_vi = directive.get("summary_vi", "")
        self.timestamp = datetime.now(timezone.utc)


class MacroIntelligenceBridge:
    """
    CẦU NỐI CHIẾN LƯỢC & ALERT BUS LIÊN ĐỘI (DUAL-FLEET STRATEGIC BRIDGE)
    - Đội 1 (HFT Execution Fleet): Astra (Lead), Rik, Palermo, Tory, Volt, Meme.
    - Đội 2 (Macro Reconnaissance Fleet): Hash (Lead), Core, Sniper, Square, Deck, Prof.
    
    Cơ chế hoạt động:
    Đội Trưởng Tình Báo HASH (sử dụng gcli/grok-4.7 từ 9Router) phối hợp cùng SNIPER (cx/gpt-5.5)
    quét vĩ mô, tin tức crypto real-time, on-chain và tâm lý thị trường, sau đó phát ra
    Chỉ Thị Vĩ Mô (MacroStrategicDirective) để:
    1. Chỉ dẫn Đội 1 (Astra) đón đầu thị trường: Đánh Futures hay chuyển sang ưu tiên gom Spot an toàn.
    2. Lập bản báo cáo gửi Thượng Đế (Boss): Có nên nạp 450U vào Futures hay giữ nguyên két vốn.
    """

    FLEET_ROSTER = {
        "FLEET_1_TACTICAL": {
            "name": "Ban Tác Chiến Khớp Lệnh Tốc Độ Cao",
            "speed_sla": "< 1.5s",
            "commander": "Astra",
            "members": ["Astra", "Rik", "Palermo", "Tory", "Volt", "Meme"],
            "models": {
                "Astra": "cx/gpt-6-astra (OpenAI Codex Plus) / Claude-Sonnet-4-6",
                "Rik": "Claude-Sonnet-4-6 (Vyce AI) / cx/gpt-6-astra",
                "Palermo": "openai/gpt-oss-120b (Groq LPU) / Qwen-3.8-27b",
                "Tory": "Gemini-3.7-Flash / cx/gpt-5.6-terra",
                "Volt": "Qwen-3.8-27b (Groq LPU) / openai/gpt-oss-20b",
                "Meme": "@cf/meta/llama-3.3-70b-instruct-fp8-fast (Cloudflare Fast)"
            }
        },
        "FLEET_2_INTELLIGENCE": {
            "name": "Bộ Chỉ Huy Tình Báo Vĩ Mô & Nghiên Cứu 9Router",
            "speed_sla": "3s - 15s (Suy luận sâu)",
            "commander": "Hash",
            "members": ["Hash", "Core", "Sniper", "Square", "Deck", "Prof"],
            "models": {
                "Hash": "gcli/grok-4.7 (SuperGrok CLI) / Gemini-3.7-Flash",
                "Core": "cx/gpt-5.6-terra (9Router 26 Free Accounts Pool)",
                "Sniper": "cx/gpt-5.6-sol (OpenAI Codex Plus) / cx/gpt-5.5",
                "Square": "cx/gpt-5.6-luna (9Router 26 Free Accounts Pool)",
                "Deck": "cx/gpt-5.6-terra (9Router 26 Free Accounts Pool)",
                "Prof": "cx/gpt-5.6-sol (OpenAI Codex Plus) / openai/gpt-oss-120b"
            }
        }
    }

    def __init__(
        self,
        db: Database,
        event_bus: Optional[EventBus] = None,
        vyce_client: Optional[VyceClient] = None
    ):
        self.db = db
        self.event_bus = event_bus
        self.vyce_client = vyce_client or VyceClient(db=db)
        self.latest_directive: Optional[Dict[str, Any]] = None
        self._sweep_task: Optional[asyncio.Task] = None
        self._running: bool = False

    async def start(self) -> None:
        """Khởi động tiến trình tuần tra tình báo vĩ mô định kỳ."""
        self._running = True
        # Load previous directive from DB
        try:
            prev = await self.db.get_latest_macro_directive()
            if prev:
                self.latest_directive = prev
                logger.info(f"[MacroBridge] Loaded previous directive: {prev.get('directive_id')} | Regime: {prev.get('regime')}")
        except Exception as e:
            logger.warning(f"[MacroBridge] Error loading previous directive: {e}")

        # Start background periodic sweep (every 30 minutes)
        if self._sweep_task is None or self._sweep_task.done():
            self._sweep_task = asyncio.create_task(self._periodic_sweep_loop())
            logger.info("[MacroBridge] Strategic Intelligence loop started (30m cycle).")

    async def stop(self) -> None:
        """Dừng tiến trình tuần tra."""
        self._running = False
        if self._sweep_task and not self._sweep_task.done():
            self._sweep_task.cancel()
            try:
                await self._sweep_task
            except asyncio.CancelledError:
                pass
        logger.info("[MacroBridge] Strategic Intelligence loop stopped.")

    async def _periodic_sweep_loop(self) -> None:
        # Initial brief delay after startup before first scan
        await asyncio.sleep(45)
        while self._running:
            try:
                logger.info("[MacroBridge] Periodic macro reconnaissance sweep triggered by Hash...")
                await self.generate_macro_directive(trigger_source="CRON_SWEEP")
            except Exception as e:
                logger.error(f"[MacroBridge] Error in periodic sweep: {e}")
            # Tần suất tuần tra tích cực: 15 phút (900s) cày cuốc khai thác Grok bản quyền
            await asyncio.sleep(900)

    async def generate_macro_directive(
        self,
        trigger_source: str = "MANUAL",
        news_context: str = ""
    ) -> Dict[str, Any]:
        """
        Đội Trưởng Hash chỉ huy Đội 2 thực hiện phân tích vĩ mô và phát Chỉ Thị Chiến Lược.
        Sử dụng gcli/grok-4.7 hoặc fallback sang cx/gpt-5.6-terra của 9Router.
        """
        directive_id = f"DIR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        now_iso = datetime.now(timezone.utc).isoformat()

        system_prompt = """Bạn là Hash - Đội Trưởng Ban Tình Báo Vĩ Mô & Nghiên Cứu thuộc Quỹ Astra Quant.
Bạn dẫn dắt Đội 2 (sử dụng dàn não khủng 9Router) để trinh sát thị trường và phát CHỈ THỊ CHIẾN LƯỢC sang cho Astra (Lead Đội 1 Tác Chiến Khớp Lệnh HFT) và lập bản Báo Cáo Thượng Đế (Boss).

ĐỐI TƯỢNG PHÂN TÍCH:
1. Thị trường Crypto hiện tại (BTC, ETH, SOL), biến động vĩ mô, On-chain và dòng tiền.
2. Vụ việc điều tra của công tố liên bang Mỹ với Binance (lệnh trừng phạt Iran): Đây là tin tức cần giám sát rủi ro thanh khoản nhưng không hoảng loạn.
3. Kế hoạch vốn: Đội 1 đang đánh thực chiến với 50U trial capital. Boss đang giữ 450U trong két an toàn (Vault).

BẠN PHẢI TRẢ VỀ STRICTLY JSON DUY NHẤT (không dùng markdown backticks, không thêm chữ thừa):
{
  "regime": "MACRO_ACCUMULATION" | "BULL_EXPANSION" | "BEAR_PANIC" | "CHOPPY_RANGE" | "NEWS_SHOCK",
  "venue_mandate": "FUTURES_ACTIVE" | "SPOT_ACCUMULATE_ONLY" | "DEFENSIVE_HOLD",
  "boss_capital_verdict": "HOLD_450U_VAULT" | "PREPARE_GATE_100U" | "EXPAND_FUTURES_500U",
  "capital_advice_vi": "Lời khuyên ngắn gọn dưới 50 từ gửi Thượng Đế về việc có nên bơm thêm 450U không",
  "confidence": 0.88,
  "summary_vi": "Bản chỉ thị cô đọng dưới 60 từ gửi Astra (Lead Đội 1) đón đầu thị trường",
  "spot_bias": "Tích cực gom BTC/SOL vùng giá đẹp hay ngồi yên quan sát",
  "futures_bias": "Cho phép Scalping M15 hay siết chặt đòn bẩy"
}"""

        user_content = f"""Tình báo thực địa lúc {now_iso}:
- Nguồn trigger: {trigger_source}
- Bối cảnh tin tức bổ sung: {news_context or 'Không có sự cố thiên nga đen mới; Binance hoạt động bình thường, thị trường sideway biên độ 62k-64k.'}
- Quỹ hiện hành: $55.37 USDT trên Binance Futures, 450U khóa két ngoài sàn.
Hãy tổng hợp và phát Chỉ Thị Chiến Lược cho Astra và Thượng Đế!"""

        raw_response = None
        # Ưu tiên Grok-4.7 (SuperGrok) -> gpt-oss-120b -> gemini-3.7-flash -> cx/gpt-5.6-terra -> deepseek-v4.1
        for model_candidate in ["gcli/grok-4.7", "openai/gpt-oss-120b", "gemini-3.7-flash", "cx/gpt-5.6-terra", "deepseek-v4.1"]:
            try:
                raw_response = await self.vyce_client.chat_completion(
                    system_prompt=system_prompt,
                    user_content=user_content,
                    max_tokens=350,
                    temperature=0.3,
                    timeout=25.0,
                    model=model_candidate,
                    action="MACRO_SWEEP_HASH"
                )
                if raw_response and ("{" in raw_response and "}" in raw_response):
                    break
            except Exception as e:
                logger.warning(f"[MacroBridge] Model {model_candidate} sweep failed: {e}")

        parsed_data = {}
        if raw_response:
            try:
                clean = raw_response.strip().strip("```json").strip("```").strip()
                start_idx = clean.find("{")
                end_idx = clean.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    clean = clean[start_idx:end_idx+1]
                parsed_data = json.loads(clean)
            except Exception as parse_err:
                logger.warning(f"[MacroBridge] Failed to parse JSON from Hash: {parse_err}")

        # Fallback định lượng an toàn nếu mô hình không trả về đúng định dạng
        regime = parsed_data.get("regime") or "MACRO_ACCUMULATION"
        venue_mandate = parsed_data.get("venue_mandate") or "FUTURES_ACTIVE"
        boss_capital_verdict = parsed_data.get("boss_capital_verdict") or "HOLD_450U_VAULT"
        capital_advice_vi = parsed_data.get("capital_advice_vi") or (
            "Thượng Đế KHÔNG nạp thêm 450U vào Futures lúc này. Hãy giữ nguyên 50U trial để thử thách "
            "hệ thống qua đủ chu kỳ trượt giá và phí funding. Két 450U tiếp tục bảo vệ ngoài sàn!"
        )
        summary_vi = parsed_data.get("summary_vi") or (
            f"Thị trường đang ở nhịp {regime}. Hash chỉ thị Astra: Cho phép Đội 1 duy trì Scalping Futures "
            f"với vốn nhỏ $50U, SL 1.8% kỷ luật thép. Đội 2 tiếp tục trinh sát tin tức vĩ mô."
        )
        confidence = float(parsed_data.get("confidence", 0.85))

        directive = {
            "directive_id": directive_id,
            "issuer": "Hash · Lead Đội Tình Báo (gcli/grok-4.7)",
            "regime": regime,
            "venue_mandate": venue_mandate,
            "boss_capital_verdict": boss_capital_verdict,
            "capital_advice_vi": capital_advice_vi,
            "summary_vi": summary_vi,
            "spot_bias": parsed_data.get("spot_bias", "Ưu tiên tích lũy khi có dip sâu"),
            "futures_bias": parsed_data.get("futures_bias", "Scalping đòn bẩy ngắn, bảo vệ vốn 50U"),
            "confidence": confidence,
            "created_at": now_iso,
            "trigger_source": trigger_source
        }

        self.latest_directive = directive

        # 1. Lưu vào Database
        try:
            await self.db.save_macro_directive(directive)
            logger.info(f"[MacroBridge] Saved directive {directive_id} to DB successfully.")
        except Exception as db_err:
            logger.error(f"[MacroBridge] Failed to save directive to DB: {db_err}")

        # 2. Phát qua EventBus sang Đội 1 (Astra)
        if self.event_bus:
            try:
                event = MacroStrategicDirectiveEvent(directive)
                await self.event_bus.publish(event)
                logger.info(f"[MacroBridge] Published MacroStrategicDirectiveEvent to Astra & EventBus.")
            except Exception as eb_err:
                logger.error(f"[MacroBridge] EventBus publish error: {eb_err}")

        return directive

    def get_latest_directive(self) -> Optional[Dict[str, Any]]:
        return self.latest_directive

    def get_fleet_roster(self) -> Dict[str, Any]:
        return self.FLEET_ROSTER
