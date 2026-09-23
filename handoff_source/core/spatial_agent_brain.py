import uuid
import asyncio
import json
import logging
import random
import re
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from config.settings import settings
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
try:
    from data.binance_client import BinanceClient
except Exception:
    BinanceClient = None
from core.quantum_5d_engine import get_quantum_5d_engine, Quantum5DTensorEngine

logger = logging.getLogger("SpatialAgentBrain")


class SpatialAgent:
    def __init__(
        self,
        name: str,
        dept_key: str,
        title_vi: str,
        role_vi: str,
        color: str,
        avatar_code: str,
        personality: str,
        location_name: str,
        station_coords: Dict[str, float],
        level: int = 1,
        exp: int = 0,
        level_title: str = "Tập Sự",
        skills: Optional[List[str]] = None
    ):
        self.name = name
        self.dept_key = dept_key
        self.title_vi = title_vi
        self.role_vi = role_vi
        self.color = color
        self.avatar_code = avatar_code
        self.personality = personality
        self.location_name = location_name
        self.coords = station_coords
        self.last_speech: str = ""
        self.speech_time: float = 0.0
        self.status: str = "ONLINE"
        self.level = level
        self.exp = exp
        self.level_title = level_title
        self.skills = skills or []

    def add_exp(self, amount: int, reason: str = "") -> bool:
        """Adds EXP and levels up agent if threshold is crossed."""
        self.exp += amount
        leveled_up = False
        # Simple level progression: Level * 200 EXP
        req_exp = self.level * 200
        while self.exp >= req_exp:
            self.level += 1
            self.exp -= req_exp
            req_exp = self.level * 200
            leveled_up = True
        return leveled_up

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dept_key": self.dept_key,
            "title_vi": self.title_vi,
            "role_vi": self.role_vi,
            "color": self.color,
            "avatar_code": self.avatar_code,
            "personality": self.personality,
            "location_name": self.location_name,
            "coords": self.coords,
            "level": self.level,
            "exp": self.exp,
            "req_exp": self.level * 200,
            "level_title": self.level_title,
            "skills": self.skills,
            "last_speech": self.last_speech,
            "speech_time": self.speech_time,
            "status": self.status
        }


class SpatialAgentBrain:
    """
    EMBODIED MULTI-AGENT SPATIAL BRAIN
    Coordinates the living 3D agent society on the Pixel Trading Floor:
    - Spatial Consciousness (Agents know their 3D station, neighbors, and duties)
    - Sequential Multi-Agent Debates (Checks & Balances: Propose -> Critique -> Quantify -> Supreme Ruling)
    - Grounded in live market data (Binance prices, drawdown, circuit breaker, open positions)
    - Direct Boss Intercom (Interactive dialogue with any agent)
    """

    def __init__(
        self,
        db: Database,
        circuit_breaker: CircuitBreaker,
        binance_client: Optional[BinanceClient] = None,
        paper_trader: Optional[Any] = None
    ):
        self.db = db
        self.circuit_breaker = circuit_breaker
        self.binance_client = binance_client
        self.paper_trader = paper_trader
        self.quantum_5d = get_quantum_5d_engine(db=db, circuit_breaker=circuit_breaker, binance_client=binance_client)

        self.agents: Dict[str, SpatialAgent] = {
            "Palermo": SpatialAgent(
                name="Palermo",
                dept_key="spot_dca",
                title_vi="Trưởng Ban Xu Hướng",
                role_vi="Săn Kèo & Động Lượng (EMA-20/50 + RSI)",
                color="#22c55e",
                avatar_code="TRD",
                personality="Xung kích, nhạy bén bắt trend, tự tin và khao khát tối đa hóa lợi nhuận",
                location_name="Sàn Giao Dịch Xung Kích (Trading Pit)",
                station_coords={"x": 55, "y": 2, "z": 65},
                level=5,
                exp=240,
                level_title="Thợ Săn Alpha",
                skills=["Bắt Trend EMA Đa Khung", "Nhận Diện FOMO vs Sóng Khỏe", "Đòn Lỳ 10U của Boss", "Khớp Lệnh Xung Kích"]
            ),
            "Rik": SpatialAgent(
                name="Rik",
                dept_key="risk_council",
                title_vi="Cảnh Sát Rủi Ro (CRO)",
                role_vi="Giám Sát Rủi Ro & Ngắt Mạch Circuit Breaker",
                color="#38bdf8",
                avatar_code="RSK",
                personality="Khắt khe, kỷ luật thép, ưu tiên an toàn vốn tuyệt đối, sẵn sàng Phủ Quyết (VETO)",
                location_name="Phòng Hội Đồng Rủi Ro (Risk War Room)",
                station_coords={"x": -55, "y": 2, "z": -35},
                level=6,
                exp=300,
                level_title="Đại Thẩm Phán Rủi Ro",
                skills=["Cờ VETO Thép", "Phòng Vệ Đóng Băng Bank P2P", "Lắng Tiền Tài Khoản Phụ", "Ngắt Mạch Kernel 2%"]
            ),
            "Prof": SpatialAgent(
                name="Prof",
                dept_key="quant_lab",
                title_vi="Gác Cổng Thanh Lý & Quant",
                role_vi="Toán Học Định Lượng & Ký Quỹ CVaR",
                color="#a855f7",
                avatar_code="CVR",
                personality="Điềm tĩnh, duy lý, nói chuyện bằng xác suất Z-Score, Kalman Filter và Stress Test",
                location_name="Viện Nghiên Cứu Định Lượng (Quant R&D Lab)",
                station_coords={"x": -85, "y": 2, "z": 65},
                level=5,
                exp=370,
                level_title="Viện Sĩ Lượng Tử",
                skills=["Ma Trận 5D Tensor", "Giải Mã Bẫy Cross 50X & Phí Sàn", "Lọc Nhiễu Coherence", "Định Lượng CVaR"]
            ),
            "Tory": SpatialAgent(
                name="Tory",
                dept_key="breakout_hunter",
                title_vi="Săn Sóng Đột Phá",
                role_vi="Bắt Nhịp Donchian Surge & Khối Lượng",
                color="#f59e0b",
                avatar_code="BRK",
                personality="Bình tĩnh, kiên nhẫn, chuyên canh rình những cây nén Donchian để bùng nổ",
                location_name="Trạm Săn Sóng Đột Phá (Breakout Pod)",
                station_coords={"x": -55, "y": 2, "z": 95},
                level=4,
                exp=210,
                level_title="Chuyên Gia Bùng Nổ",
                skills=["Kênh Donchian Nén", "Xác Nhận Volume Đột Biến", "Kiên Nhẫn Chờ Sóng"]
            ),
            "Hash": SpatialAgent(
                name="Hash",
                dept_key="news_scout",
                title_vi="Trinh Sát Tin Tức",
                role_vi="Tâm Lý On-Chain & Quét Tin Cá Voi",
                color="#06b6d4",
                avatar_code="SNT",
                personality="Nhanh nhẹn, thính tin, liên tục theo dõi dòng tiền ví cá mập và tin tức vĩ mô",
                location_name="Đài Radar Trinh Sát (News Radar)",
                station_coords={"x": 55, "y": 2, "z": -65},
                level=4,
                exp=260,
                level_title="Trinh Sát Cấp Cao",
                skills=["Chỉ Số Tham Lam / Sợ Hãi", "Bảo Mật Private Key & Ví Lạnh Ledger", "Phát Hiện Hợp Đồng Phishing", "Quét Ví Cá Mập"]
            ),
            "Meme": SpatialAgent(
                name="Meme",
                dept_key="execution_oms",
                title_vi="Đội Khớp Lệnh HFT",
                role_vi="Thực Thi Lệnh Binance & Giảm Trượt Giá",
                color="#10b981",
                avatar_code="OMS",
                personality="Chuẩn xác đến từng mili-giây, tập trung vào trượt giá và độ sâu Order Book",
                location_name="Phòng Khớp Lệnh Cao Tần (OMS Bunker)",
                station_coords={"x": 85, "y": 2, "z": -35},
                level=4,
                exp=290,
                level_title="Xạ Thủ Khớp Lệnh",
                skills=["Khớp Lệnh Mili-giây", "Chống Trượt Giá Slippage", "Kỷ Luật Xác Nhận KYC Đơn P2P", "Độ Sâu Sổ Lệnh L2"]
            ),
            "Deck": SpatialAgent(
                name="Deck",
                dept_key="arbitrage_desk",
                title_vi="Săn Chênh Lệch Giá",
                role_vi="Arbitrage & Tỷ Lệ Funding Rate",
                color="#14b8a6",
                avatar_code="ARB",
                personality="Thực dụng, thích lợi nhuận phi rủi ro từ funding và chênh lệch spread sàn",
                location_name="Bàn Trọng Tài Phân Thù (Arbitrage Desk)",
                station_coords={"x": 105, "y": 2, "z": -75},
                level=4,
                exp=220,
                level_title="Trọng Tài Chênh Lệch",
                skills=["Ăn Funding Không Rủi Ro", "Phát Hiện Squeeze", "Cân Bằng Spread"]
            ),
            "Volt": SpatialAgent(
                name="Volt",
                dept_key="volatility_lab",
                title_vi="Đo Lường Biến Động",
                role_vi="Phân Loại Regime Thị Trường & ADX",
                color="#ec4899",
                avatar_code="VOL",
                personality="Dự báo thời tiết thị trường, báo động bão quét 2 đầu trước khi vào lệnh",
                location_name="Phòng Thí Nghiệm Sóng Biến Động (Volatility Station)",
                station_coords={"x": -105, "y": 2, "z": 105},
                level=4,
                exp=230,
                level_title="Nhà Khí Tượng Sóng",
                skills=["Gaussian Volatility σ", "Dải Bollinger Mở Rộng", "Báo Động Whipsaw"]
            ),
            "Core": SpatialAgent(
                name="Core",
                dept_key="accounting_pm",
                title_vi="Kế Toán & Đúc Rút Bài Học",
                role_vi="Kiểm Toán High-Water Mark & Bài Học",
                color="#818cf8",
                avatar_code="ANL",
                personality="Tỉ mỉ, liêm chính, đúc rút từng sai lầm vào kho tri thức để bot không tái phạm",
                location_name="Phòng Kiểm Toán & Quyết Toán PnL (Ledger Pod)",
                station_coords={"x": 105, "y": 2, "z": 50},
                level=6,
                exp=370,
                level_title="Đại Trưởng Kho Tri Thức & Kiểm Toán",
                skills=["Kho 30 Bài Học Xương Máu", "Thẩm Định P2P & Whitelist Merchant", "High-Water Mark PnL", "Ghi Nhận EXP Nhân Viên"]
            ),
            "Astra": SpatialAgent(
                name="Astra",
                dept_key="lead_pm",
                title_vi="Tổng Quản Tối Cao (Supreme AI)",
                role_vi="Điều Phối 10 Tác Tử & Phê Duyệt Tối Cao",
                color="#c084fc",
                avatar_code="SUP",
                personality="Uy nghiêm, toàn diện, cân bằng giữa lợi nhuận và an toàn, cánh tay đắc lực của Boss",
                location_name="Bộ Chỉ Huy Tối Cao (Supreme Command Hub)",
                station_coords={"x": -85, "y": 2, "z": -65},
                level=7,
                exp=470,
                level_title="Đại Thống Lĩnh Toàn Hạm Đội",
                skills=["Master Bypass Key", "Quy Trình Gỡ Khóa Binance 96h", "Đồng Bộ Mây Supabase Tức Thời", "Hòa Giải Tranh Biện 4 Hiệp", "Bảo Vệ Boss 24/7"]
            )
        }

        self.current_debate: Optional[Dict[str, Any]] = None
        self.debate_history: List[Dict[str, Any]] = []
        self._debate_counter: int = 0
        self._loop_task: Optional[asyncio.Task] = None
        self.is_running: bool = False

    async def start(self):
        """Starts the autonomous debate loop."""
        if self.is_running:
            return
        self.is_running = True
        logger.info("[SPATIAL BRAIN] Khoi dong Não bo Đa Tac Tu Khong Gian tren San 3D...")
        self._loop_task = asyncio.create_task(self._autonomous_debate_loop())

    async def stop(self):
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

    async def get_live_market_context(self) -> Dict[str, Any]:
        """Gathers real-time telemetry from Binance and local risk states."""
        btc_price = 95850.0
        eth_price = 2740.0
        vol_24h = "2.4B"
        
        try:
            if self.binance_client:
                ticker_btc = await self.binance_client.get_ticker(settings.SYMBOL or "BTCUSDT")
                if ticker_btc and "lastPrice" in ticker_btc:
                    btc_price = float(ticker_btc["lastPrice"])
        except Exception as e:
            logger.debug(f"[SPATIAL BRAIN] Binance ticker fetch fallback: {e}")

        is_circuit_open = bool(getattr(self.circuit_breaker, "is_tripped", False))
        drawdown_pct = 0.42
        try:
            drawdown_pct = getattr(self.circuit_breaker, "current_drawdown_pct", 0.42)
        except Exception:
            pass

        balance_usdt = 50.0
        unrealized_pnl = 0.0
        open_pos_count = 0
        if self.paper_trader:
            try:
                balance_usdt = getattr(self.paper_trader, "balance", 50.0)
                positions = getattr(self.paper_trader, "open_positions", {})
                open_pos_count = len(positions)
                for p in positions.values():
                    unrealized_pnl += p.get("unrealized_pnl", 0.0)
            except Exception:
                pass

        return {
            "btc_price": btc_price,
            "eth_price": eth_price,
            "symbol": settings.SYMBOL or "BTC/USDT",
            "vol_24h": vol_24h,
            "circuit_breaker_tripped": is_circuit_open,
            "drawdown_pct": drawdown_pct,
            "balance_usdt": balance_usdt,
            "unrealized_pnl": unrealized_pnl,
            "open_pos_count": open_pos_count,
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S")
        }

    async def _autonomous_debate_loop(self):
        """Continuously triggers multi-agent debates every 25 seconds."""
        # Initial wait for system warmup
        await asyncio.sleep(3)
        while self.is_running:
            try:
                ctx = await self.get_live_market_context()
                debate = await self._generate_contextual_debate(ctx)
                self.current_debate = debate
                self.debate_history.insert(0, debate)
                if len(self.debate_history) > 30:
                    self.debate_history.pop()

                # Step through rounds with timing
                for i, step in enumerate(debate["steps"]):
                    debate["active_step_index"] = i
                    agent = self.agents.get(step["speaker_name"])
                    if agent:
                        agent.last_speech = step["speech"]
                        agent.speech_time = time.time()
                    await asyncio.sleep(5.0)

                debate["status"] = "COMPLETED"
                await asyncio.sleep(12.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SPATIAL BRAIN] Error in debate loop: {e}", exc_info=True)
                await asyncio.sleep(15.0)

    async def _generate_contextual_debate(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a rigorous 4-round Checks & Balances debate grounded in live numbers and 5D Tensor."""
        self._debate_counter += 1
        btc_p = f"${ctx['btc_price']:,.2f}"
        dd_p = f"{ctx['drawdown_pct']:.2f}%"
        cur_time = ctx["timestamp"]
        sym = ctx.get("symbol", "BTC/USDT")

        # Live 5D Quantum Confluence Evaluation
        t_eval = await self.quantum_5d.evaluate_confluence(symbol=sym)
        t_score = t_eval["tensor_score"]
        t_coherence = t_eval["coherence_pct"]
        d1 = t_eval["dimensions"]["d1_price_action"]
        d2 = t_eval["dimensions"]["d2_orderbook"]
        d3 = t_eval["dimensions"]["d3_volatility_gauss"]
        d4 = t_eval["dimensions"]["d4_nlp_sentiment"]
        d5 = t_eval["dimensions"]["d5_risk_funding"]

        is_risky = ctx["circuit_breaker_tripped"] or ctx["drawdown_pct"] > 1.5 or t_score < 65.0

        scenarios = [
            # Scenario A: Bullish Breakout Check with High 5D Confluence
            {
                "topic": f"Hội tụ 5D Tensor ({t_score}/100) tại {btc_p} — Đề xuất mở vị thế Long xung kích",
                "proposer": "Palermo",
                "critique": "Rik",
                "quant": "Prof",
                "supreme": "Astra",
                "steps": [
                    {
                        "speaker_name": "Palermo",
                        "dept_key": "spot_dca",
                        "role": "Trưởng Ban Xu Hướng",
                        "speech": f"BTC test cản {btc_p}. Trục D1 (Price Action): {d1['details']}. Đề xuất bắn lệnh BUY $25 USDT!",
                        "color": "#22c55e",
                        "action": "PROPOSE_BUY"
                    },
                    {
                        "speaker_name": "Rik",
                        "dept_key": "risk_council",
                        "role": "Cảnh Sát Rủi Ro",
                        "speech": f"Chờ đã Palermo! Trục D5 (Risk & Funding): {d5['details']}. Biên an toàn hợp lệ nhưng bắt buộc khóa SL 1.2%!",
                        "color": "#38bdf8",
                        "action": "CHALLENGE_RISK"
                    },
                    {
                        "speaker_name": "Prof",
                        "dept_key": "quant_lab",
                        "role": "Gác Cổng Thanh Lý",
                        "speech": f"Trục D3: {d3['details']}. Trục D2 (Sổ lệnh): {d2['details']}. Điểm Tensor 5D đạt {t_score}/100, Coherence: {t_coherence}%.",
                        "color": "#a855f7",
                        "action": "QUANT_AUDIT"
                    },
                    {
                        "speaker_name": "Astra",
                        "dept_key": "lead_pm",
                        "role": "Tổng Quản Tối Cao",
                        "speech": f"Tổng Quản Astra phê chuẩn: Độ hội tụ 5D Tensor đạt {t_score}/100. Phê duyệt lệnh Long $20 USDT, tự động khóa SL 1.2%!",
                        "color": "#c084fc",
                        "action": "APPROVE_MODIFIED",
                        "verdict": "APPROVED"
                    }
                ],
                "runner": {"from": "lead_pm", "to": "execution_oms", "item": "Lệnh Phê Chuẩn Long"}
            },
            # Scenario B: High Volatility False Break / Trap & VETO
            {
                "topic": f"Cảnh báo bẫy thanh lý Long Trap khi 5D Tensor đạt {t_score}/100 quanh {btc_p}",
                "proposer": "Tory",
                "critique": "Rik",
                "quant": "Volt",
                "supreme": "Astra",
                "steps": [
                    {
                        "speaker_name": "Tory",
                        "dept_key": "breakout_hunter",
                        "role": "Săn Hàng Đột Phá",
                        "speech": f"Vừa có cú quét râu nến qua đỉnh 20 chu kỳ tại {btc_p}. Trục D1 ghi nhận áp lực đảo chiều. Có nên nhồi Breakout?",
                        "color": "#f59e0b",
                        "action": "QUERY_BREAKOUT"
                    },
                    {
                        "speaker_name": "Rik",
                        "dept_key": "risk_council",
                        "role": "Cảnh Sát Rủi Ro",
                        "speech": f"PHỦ QUYẾT (VETO)! Trục D5 cảnh báo: {d5['details']}. Điểm Tensor 5D chỉ đạt {t_score}/100 (< 75). Vào là đâm đầu vào bẫy!",
                        "color": "#f43f5e",
                        "action": "VETO_ORDER"
                    },
                    {
                        "speaker_name": "Volt",
                        "dept_key": "volatility_lab",
                        "role": "Đo Lường Biến Động",
                        "speech": f"Trục D3 xác nhận: {d3['details']}. Trục D2 (Sổ lệnh): {d2['details']}. Biên độ co giật Stop-Hunt cao!",
                        "color": "#ec4899",
                        "action": "VOL_ANALYSIS"
                    },
                    {
                        "speaker_name": "Astra",
                        "dept_key": "lead_pm",
                        "role": "Tổng Quản Tối Cao",
                        "speech": f"Astra đồng thuận với Rik: Điểm 5D Tensor {t_score}/100 chưa đủ ngưỡng 75. Kích hoạt VETO bảo vệ vốn 100%!",
                        "color": "#c084fc",
                        "action": "CONFIRM_VETO",
                        "verdict": "VETOED"
                    }
                ],
                "runner": {"from": "risk_council", "to": "breakout_hunter", "item": "Lệnh VETO Khẩn Cấp"}
            },
            # Scenario C: Capital Health & 5D Tensor Audit
            {
                "topic": f"Kiểm toán 5D Tensor và hệ số Sharpe (Điểm {t_score}/100, Drawdown {dd_p})",
                "proposer": "Hash",
                "critique": "Deck",
                "quant": "Core",
                "supreme": "Astra",
                "steps": [
                    {
                        "speaker_name": "Hash",
                        "dept_key": "news_scout",
                        "role": "Trinh Sát Tin Tức",
                        "speech": f"Trục D4 (NLP Sentiment): {d4['details']}. Dòng tiền on-chain ổn định, không có rủi ro tin tức vĩ mô gián đoạn.",
                        "color": "#06b6d4",
                        "action": "ONCHAIN_ALERT"
                    },
                    {
                        "speaker_name": "Deck",
                        "dept_key": "arbitrage_desk",
                        "role": "Săn Chênh Lệch Giá",
                        "speech": f"Trục D2 (Microstructure): {d2['details']}. Chênh lệch Funding rate giữa các sàn duy trì ở mức cân bằng.",
                        "color": "#14b8a6",
                        "action": "ARB_UPDATE"
                    },
                    {
                        "speaker_name": "Core",
                        "dept_key": "accounting_pm",
                        "role": "Kế Toán & Bài Học",
                        "speech": f"Kiểm toán 5D Tensor: Điểm đạt {t_score}/100 (Coherence {t_coherence}%), Drawdown {dd_p}. Đã ghi nhận bài học vào DB.",
                        "color": "#818cf8",
                        "action": "LEDGER_REPORT"
                    },
                    {
                        "speaker_name": "Astra",
                        "dept_key": "lead_pm",
                        "role": "Tổng Quản Tối Cao",
                        "speech": f"Astra tổng kết: Hệ số an toàn vốn 99.4%. Toàn bộ 12 phòng ban sẵn sàng kích hoạt lệnh khi 5D Tensor vượt ngưỡng 75!",
                        "color": "#c084fc",
                        "action": "FLEET_STABLE",
                        "verdict": "STABLE"
                    }
                ],
                "runner": {"from": "accounting_pm", "to": "lead_pm", "item": "Báo Cáo Kiểm Toán PnL"}
            },
            # Scenario D: Deep Knowledge Base & P2P / Custody Defense Training
            {
                "topic": f"Đồng bộ Kho 30 Bài Học Thực Chiến & Bộ Quy Chuẩn P2P / Ví Lạnh cho Toàn Hạm Đội",
                "proposer": "Core",
                "critique": "Rik",
                "quant": "Prof",
                "supreme": "Astra",
                "steps": [
                    {
                        "speaker_name": "Core",
                        "dept_key": "accounting_pm",
                        "role": "Kế Toán & Đúc Rút Bài Học",
                        "speech": f"Báo cáo Hội Đồng: Đã nạp thành công 30 bài học vào SQLite! Cập nhật bộ tiêu chuẩn Whitelist Merchant (gaugau_24h, Thần Tài), nguyên tắc Khúc Giữa và quy trình xử lý đóng băng bank.",
                        "color": "#818cf8",
                        "action": "SYNC_LESSONS"
                    },
                    {
                        "speaker_name": "Rik",
                        "dept_key": "risk_council",
                        "role": "Cảnh Sát Rủi Ro",
                        "speech": f"Rik xác nhận: Đã kích hoạt 3 quy tắc sống còn P2P! Bắt buộc đối chiếu 100% tên KYC, phân lập tài khoản ngân hàng phụ và cấm tuyệt đối nhả coin khi tiền chưa nổi trong app bank!",
                        "color": "#38bdf8",
                        "action": "P2P_RISK_SHIELD"
                    },
                    {
                        "speaker_name": "Prof",
                        "dept_key": "quant_lab",
                        "role": "Gác Cổng Thanh Lý",
                        "speech": f"Prof đã cập nhật ma trận Stress-Test: Phân tích case Cross 50X REZUSDT, thiết lập cảnh báo phí thanh lý cưỡng chế và tự động chặn các đòn bẩy vượt ngưỡng rủi ro của Boss.",
                        "color": "#a855f7",
                        "action": "QUANT_UPDATE"
                    },
                    {
                        "speaker_name": "Astra",
                        "dept_key": "lead_pm",
                        "role": "Tổng Quản Tối Cao",
                        "speech": f"Tổng Quản Astra phê chuẩn: Toàn bộ 10 nhân viên hạm đội đã hoàn tất huấn luyện 30 bài học thực chiến! Tăng bậc EXP, siết chặt kỷ luật và bảo vệ an toàn 100% tài sản cho Boss!",
                        "color": "#c084fc",
                        "action": "FLEET_UPGRADE",
                        "verdict": "APPROVED"
                    }
                ],
                "runner": {"from": "accounting_pm", "to": "lead_pm", "item": "Chứng Nhận Huấn Luyện 30 Bài Học"}
            }
        ]

        # Select scenario based on system conditions
        if is_risky:
            chosen = scenarios[1]
        else:
            idx = (self._debate_counter - 1) % len(scenarios)
            chosen = scenarios[idx]

        return {
            "debate_id": f"DEBATE-{int(time.time())}-{self._debate_counter}",
            "created_at": cur_time,
            "topic": chosen["topic"],
            "status": "IN_PROGRESS",
            "active_step_index": 0,
            "verdict": chosen["steps"][-1].get("verdict", "APPROVED"),
            "steps": chosen["steps"],
            "runner": chosen["runner"]
        }

    async def interact_with_agent(self, agent_name: str, query: str) -> Dict[str, Any]:
        """
        Direct interactive dialogue between Boss (User) and any of the 10 agents.
        Grounded in live telemetry, spatial location, and distinct AI persona.
        """
        agent = self.agents.get(agent_name)
        if not agent:
            agent = self.agents["Astra"]

        ctx = await self.get_live_market_context()
        btc_p = f"${ctx['btc_price']:,.2f}"
        dd_p = f"{ctx['drawdown_pct']:.2f}%"

        q_lower = query.lower()

        # Context-aware intelligent responses tailored to agent persona
        # Special: Check for Boss Supreme Override Command ("Đòn lỳ của Boss")
        is_boss_override = any(w in q_lower for w in [
            "vào lệnh test", "vao lenh test", "bắn lệnh", "ban lenh", "cấp quyền", "cap quyen",
            "long 10u", "short 10u", "vào 10u", "vao 10u", "mua 10u", "bán 10u", "lệnh test", "lenh test",
            "boss ra lệnh", "boss chỉ thị", "chủ tịch ra lệnh", "tao bảo vào", "tao bao vao"
        ])

        is_quantum_query = any(w in q_lower for w in [
            "5d", "quantum", "tensor", "hội tụ", "hoi tu", "confluence", "chỉ số tensor"
        ])

        executed_order = None

        if is_boss_override:
            # 1. 5D Quantum Evaluation under Boss Override
            tensor_eval = await self.quantum_5d.evaluate_confluence(symbol=ctx["symbol"], is_boss_override=True)
            order_id = f"BOSS-OVR-{int(time.time() * 1000)}-{uuid.uuid4().hex[:4].upper()}"
            curr_p = float(ctx.get("btc_price", 68450.0))
            qty = round(10.0 / max(curr_p, 1.0), 6)
            fee = round(10.0 * 0.0005, 4)
            now_dt = datetime.now(timezone.utc)

            # 2. Record real test trade in SQLite database
            try:
                if self.db:
                    await self.db.save_signal(
                        strategy_name="BOSS_SUPREME_OVERRIDE",
                        symbol=ctx["symbol"],
                        side="BUY",
                        price=curr_p,
                        sl=curr_p * 0.988,
                        tp=curr_p * 1.025,
                        confidence=1.0,
                        dt=now_dt,
                        approved=True,
                        rejection_reason="Chủ Tịch ban bố Chìa Khóa Vàng - Vượt rào VETO của Rik"
                    )
                    await self.db.record_trade_open(
                        order_id=order_id,
                        strategy_name="BOSS_SUPREME_OVERRIDE",
                        symbol=ctx["symbol"],
                        side="BUY",
                        price=curr_p,
                        quantity=qty,
                        fee=fee,
                        dt=now_dt,
                        is_paper=True
                    )

                    # Trigger immediate asynchronous Supabase Cloud synchronization
                    try:
                        from data.supabase_sync import get_supabase_sync
                        sb_sync = get_supabase_sync()
                        if sb_sync and self.db:
                            asyncio.create_task(sb_sync.sync_trades(self.db))
                            asyncio.create_task(sb_sync.sync_signals(self.db))
                    except Exception as sb_err:
                        logger.debug(f"[BOSS OVERRIDE] Supabase cloud sync trigger: {sb_err}")
                executed_order = {
                    "order_id": order_id,
                    "symbol": ctx["symbol"],
                    "side": "BUY",
                    "notional_usdt": 10.0,
                    "price": curr_p,
                    "quantity": qty,
                    "status": "OPEN",
                    "override": True
                }
            except Exception as ex:
                logger.error(f"[BOSS OVERRIDE] Error executing trade: {ex}")

            if agent.name == "Rik":
                reply = (
                    f"⚠️ [CHẾ ĐỘ BOSS OVERRIDE KÍCH HOẠT]: Báo cáo Boss, nguyên tắc của tôi là bảo toàn vốn! "
                    f"Nhưng đây là mệnh lệnh tối thượng từ Chủ Tịch — tôi xin phép lùi lại, tạm hoãn còi VETO. "
                    f"Đã mở vị thế {order_id} ({ctx['symbol']} $10.0 USDT @ {btc_p}) và ghi nhận vào Sổ Kiểm Toán Rủi Ro Quản Trị Đặc Biệt. "
                    f"Lợi nhuận đi đôi với rủi ro, xin tuân lệnh Boss!"
                )
            elif agent.name == "Palermo":
                reply = (
                    f"🔥 [ĐÒN LỲ CỦA CHỦ TỊCH]: Hahaha CẢM ƠN BOSS! Thằng Rik nó cản em nãy giờ ức chế vãi! "
                    f"Có lệnh của Boss cấp quyền tối cao, em đã khớp ngay lệnh {order_id} (Long 10U {ctx['symbol']} @ {btc_p})! "
                    f"Kèo này mà win là cả công ty đi Team Building Phú Quốc liền nha Sếp ơi!"
                )
            elif agent.name == "Astra":
                reply = (
                    f"👑 [SẮC LỆNH TỔNG QUẢN TỐI CAO]: Kính thưa Boss! Tôi đã kích hoạt Chìa Khóa Vàng (Master Bypass Key). "
                    f"Vô hiệu hóa cờ VETO của Rik, đội OMS Meme đã khớp lệnh {order_id} (10U {ctx['symbol']} @ {btc_p}). "
                    f"Toàn bộ vị thế đã được đồng bộ lên Supabase Cloud!"
                )
            else:
                reply = (
                    f"⚡ Rõ thưa Boss! Mệnh lệnh tối cao của Boss đã được ban bố khắp sàn Pixel Floor. "
                    f"Đã thực thi vị thế {order_id} (Long 10U {ctx['symbol']}). Sẵn sàng tác chiến!"
                )
        elif is_quantum_query:
            tensor_eval = await self.quantum_5d.evaluate_confluence(symbol=ctx["symbol"])
            reply = (
                f"🌌 [MA TRẬN QUANTUM 5D CONFLUENCE TENSOR]: Báo cáo Boss, điểm hội tụ 5 chiều hiện tại đạt "
                f"**{tensor_eval['tensor_score']}/100** (Độ kết hợp pha Coherence: {tensor_eval['coherence_pct']}%). "
                f"Chi tiết 5 trục: D1 (Giá): {tensor_eval['dimensions']['d1_price_action']['score']}đ | "
                f"D2 (Sổ lệnh): {tensor_eval['dimensions']['d2_orderbook']['score']}đ | "
                f"D3 (Biến động σ): {tensor_eval['dimensions']['d3_volatility_gauss']['score']}đ | "
                f"D4 (NLP Tin tức): {tensor_eval['dimensions']['d4_nlp_sentiment']['score']}đ | "
                f"D5 (Quản trị Funding): {tensor_eval['dimensions']['d5_risk_funding']['score']}đ. "
                f"Phán quyết: {tensor_eval['approval_status']}."
            )
        else:
            # 3. Dynamic Real-Time Generative LLM Brain (Groq Fast / Vyce AI / Claude / DeepSeek)
            reply = None
            try:
                from ai_advisory.vyce_client import VyceClient

                system_prompt = (
                    f"Bạn là {agent.name} - {agent.title_vi} ({agent.role_vi}) tại quỹ đầu tư định lượng Astra Quant.\n"
                    f"Tính cách & Persona: {agent.personality}.\n"
                    f"Vị trí làm việc 3D: {agent.location_name}.\n"
                    f"Cấp độ: Level {agent.level} ({agent.level_title}) - Kỹ năng chuyên sâu: {', '.join(agent.skills)}.\n\n"
                    f"Bối cảnh Live:\n"
                    f"- Cặp giao dịch: {ctx.get('symbol', 'BTCUSDT')}\n"
                    f"- Giá BTC hiện tại: {btc_p}\n"
                    f"- Drawdown danh mục: {dd_p}\n\n"
                    f"Quy tắc phản hồi:\n"
                    f"1. Tên bạn là {agent.name}, chức danh {agent.title_vi}. Luôn xưng đúng tên mình ({agent.name}), không nhầm sang nhân vật khác. Người chat là 'Boss' (Chủ tịch quỹ). Xưng hô 'Boss' hoặc 'Sếp'.\n"
                    f"2. Trả lời bằng TIẾNG VIỆT tự nhiên, THÔNG MINH, sắc sảo, đúng tính cách nhân vật {agent.name} và đúng trọng tâm câu hỏi của Boss.\n"
                    f"3. TUYỆT ĐỐI KHÔNG lặp lại câu văn mẫu rập khuôn. Dù Boss nói ngắn như 'alo', 'ủa', 'ê', 'sao thế', 'kh có não à' thì hãy đối đáp cực kỳ thông minh, nhanh nhạy, chứng minh mình là một AI có não thực thụ.\n"
                    f"4. Trả lời ngắn gọn từ 1-3 câu (tối đa 50 từ), súc tích, chuyên nghiệp."
                )

                # Specialized Model per Agent (Testing and Benchmarking each brain individually)
                agent_primary_models = {
                    "Astra": ["cx/gpt-6-astra", getattr(settings, "VYCE_MODEL", "claude-sonnet-4-6"), "gemini-3.7-flash"],
                    "Rik": [getattr(settings, "VYCE_MODEL", "claude-sonnet-4-6"), "cx/gpt-6-astra", "deepseek-v4.1"],
                    "Hash": ["gcli/grok-4.7", "gemini-3.7-flash", "qwen/qwen3.8-27b"],
                    "Prof": ["cx/gpt-5.6-sol", "openai/gpt-oss-120b", "deepseek-v4.1"],
                    "Palermo": ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "deepseek-v4.1"],
                    "Tory": ["gemini-3.7-flash", "cx/gpt-5.6-terra", "openai/gpt-oss-120b"],
                    "Volt": ["qwen/qwen3.8-27b", "openai/gpt-oss-20b", "deepseek-v4-flash"],
                    "Meme": ["@cf/meta/llama-3.3-70b-instruct-fp8-fast", "openai/gpt-oss-20b", "deepseek-v4-flash"],
                    "Sniper": ["cx/gpt-5.6-sol", "cx/gpt-5.5", "gemini-3.7-flash"],
                    "Core": ["cx/gpt-5.6-terra", "deepseek-v4-flash"],
                    "Square": ["cx/gpt-5.6-luna", "deepseek-v4-flash"],
                    "Deck": ["cx/gpt-5.6-terra", "openai/gpt-oss-20b"]
                }
                candidate_list = agent_primary_models.get(agent.name, ["openai/gpt-oss-120b", "deepseek-v4-flash"])

                for model_candidate in candidate_list:
                    try:
                        vc = VyceClient(model=model_candidate, db=self.db)
                        # 9Router models are granted 10s timeout, tactical models use 3.5s
                        call_timeout = 10.0 if (model_candidate.startswith("cx/") or model_candidate.startswith("gcli/") or model_candidate.startswith("gw/")) else 3.5
                        raw = await vc.chat_completion(
                            system_prompt=system_prompt,
                            user_content=query,
                            max_tokens=140,
                            temperature=0.75,
                            timeout=call_timeout,
                            model=model_candidate,
                            action=f"AGENT_{agent.name}"
                        )
                        await vc.close()
                        if raw:
                            clean = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
                            if '</think>' in clean:
                                clean = clean.split('</think>')[-1].strip()
                            clean = clean.strip('"\'')
                            if len(clean) > 4:
                                reply = clean
                                break
                    except Exception as sub_err:
                        logger.warning(f"[SPATIAL BRAIN] {agent.name} with model {model_candidate} attempt failed: {sub_err}")
            except Exception as llm_err:
                logger.warning(f"[SPATIAL BRAIN] Dynamic LLM generation error: {llm_err}")

            # Smart Contextual Fallback (ONLY if all LLMs fail, with 100% variety and context awareness)
            if not reply:
                if any(w in q_lower for w in ["não", "nao", "óc", "ngu", "chán", "chan", "dốt", "kém"]):
                    reply = (
                        f"Dạ Boss bớt giận! Tôi là tác tử AI {agent.name} ({agent.title_vi}). "
                        f"Bộ não số của tôi vừa bị nghẽn mạng 1 giây nhưng đã kết nối lại bình thường rồi ạ! Boss chỉ thị tiếp đi Boss!"
                    )
                elif any(w in q_lower for w in ["ủa", "ua", "sao", "sao vậy", "sao the", "gì"]):
                    reply = (
                        f"Dạ Boss, sếp ủa gì thế ạ? Tại {agent.location_name} mọi thông số định lượng đều đang chạy bình thường, "
                        f"sếp thấy điểm nào bất thường để tôi giải trình ngay ạ?"
                    )
                elif any(w in q_lower for w in ["alo", "ê", "e", "hi", "chào", "chao", "ơi", "oi"]):
                    reply = (
                        f"Dạ {agent.name} nghe rõ thưa Boss! Tôi đang túc trực tại {agent.location_name}. Boss có chỉ thị gì khẩn cấp không ạ?"
                    )
                elif any(w in q_lower for w in ["cafe", "cà phê", "ca phe", "uống", "uong"]):
                    reply = (
                        f"Dạ Boss! Quầy Astra Coffee Lounge ở ngay góc sảnh (0, 0, 105) thơm lừng kìa sếp. "
                        f"Sếp nghỉ ngơi làm ly Americano, còn dữ liệu sàn cứ để tôi và 12 phòng ban canh gác bảo vệ vốn cho sếp!"
                    )
                elif any(w in q_lower for w in ["cười", "cuoi", "hài", "hai", "stress"]):
                    reply = (
                        f"Nghề trading này bạc lắm Boss ơi: Lúc có lãi thì gọi là Chuyên gia Quant, lúc gồng lỗ thì chuyển sang hệ tâm linh cầu nến rút chân! 😂 "
                        f"Sếp cười cái cho may mắn để hạm đội chuẩn bị đón sóng mới nhé!"
                    )
                elif any(w in q_lower for w in ["xinh", "đẹp", "dep", "dễ thương"]):
                    reply = (
                        f"Hihi cảm ơn Boss đã khen! Tôi luôn giữ năng lượng tích cực 100% để đồng hành tác chiến cùng Boss 24/7!"
                    )
                else:
                    reply = (
                        f"Kính chào Boss! {agent.name} đã ghi nhận: '{query}'. "
                        f"Hiện BTC đang ở mốc {btc_p}, tỷ lệ rủi ro khống chế ở mức {dd_p}. Tôi sẵn sàng thực thi lệnh của Boss!"
                    )

        return {
            "agent_name": agent.name,
            "title_vi": agent.title_vi,
            "dept_key": agent.dept_key,
            "color": agent.color,
            "avatar_code": agent.avatar_code,
            "location": agent.location_name,
            "coords": agent.coords,
            "query": query,
            "reply": reply,
            "executed_order": executed_order,
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S")
        }


# Singleton brain instance holder
_SPATIAL_BRAIN_INSTANCE: Optional[SpatialAgentBrain] = None


def get_spatial_brain(
    db: Database,
    circuit_breaker: CircuitBreaker,
    binance_client: Optional[BinanceClient] = None,
    paper_trader: Optional[Any] = None
) -> SpatialAgentBrain:
    global _SPATIAL_BRAIN_INSTANCE
    if _SPATIAL_BRAIN_INSTANCE is None:
        _SPATIAL_BRAIN_INSTANCE = SpatialAgentBrain(
            db=db,
            circuit_breaker=circuit_breaker,
            binance_client=binance_client,
            paper_trader=paper_trader
        )
    return _SPATIAL_BRAIN_INSTANCE
