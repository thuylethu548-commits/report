"""
core/mkt_fleet.py
MKT NIVER - MARKETING DIVISION (TẦNG DƯỚI / LOWER OPERATIONS DECK)
Điều Phối Viên Đội Ngũ 12 Phòng Ban Marketing & Ads cho Hệ Thống Astra Desk
"""
import logging
import threading
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from collections import deque

logger = logging.getLogger("MktFleet")

class MktFleetCoordinator:
    """
    Điều phối viên 12 Phòng Ban MKT Niver trực thuộc Tầng Dưới của Astra Desk Citadel.
    Quản lý 22 Fanpage, Ads Engine, Thatim Seeding Booster và Chuyển Đổi Shopee Affiliate.
    """

    MKT_AGENT_METADATA = {
        "captain": {
            "name": "captain",
            "name_vi": "Tổng Chỉ Huy",
            "role_vi": "Điều Phối Toàn Đội",
            "duty_vi": "Điều phối toàn bộ 22 Fanpage & phân bổ nguồn lực chiến dịch",
            "role": "Captain",
            "full_role": "Supreme Campaign Commander",
            "model": "agnes-3.0-flash (Vyce AI · 512K)",
            "color": "#8b5cf6",
            "icon": "🎯",
            "char": "C",
            "base_latency": 15.0,
            "status": "ACTIVE",
        },
        "content_lab": {
            "name": "content_lab",
            "name_vi": "Phòng Nội Dung",
            "role_vi": "Sáng Tạo Kịch Bản & Hook",
            "duty_vi": "Viết caption, hook 3s đầu, script video cho 22 Fanpage theo ngách",
            "role": "Content",
            "full_role": "Viral Content & Hook Engine",
            "model": "claude-sonnet-4-6 (Vyce AI)",
            "color": "#22c55e",
            "icon": "✒️",
            "char": "L",
            "base_latency": 12.0,
            "status": "ACTIVE",
        },
        "video_forge": {
            "name": "video_forge",
            "name_vi": "Xưởng Video",
            "role_vi": "Render FFmpeg & Anti-ContentID",
            "duty_vi": "Sản xuất video dọc 1080x1920, TTS AI, vi chỉnh 4 điểm lách AI Meta",
            "role": "Video",
            "full_role": "FFmpeg Autonomous Studio",
            "model": "cx/gpt-5.6-terra (9Router)",
            "color": "#f59e0b",
            "icon": "🎬",
            "char": "V",
            "base_latency": 45.0,
            "status": "ACTIVE",
        },
        "ads_engine": {
            "name": "ads_engine",
            "name_vi": "Phòng Quảng Cáo",
            "role_vi": "Tối Ưu Ads & Chốt Đơn",
            "duty_vi": "Chạy Facebook Ads test Ảnh + Caption, tối ưu CPA < 50k, scale winner",
            "role": "Ads",
            "full_role": "Meta Ads & Performance Booster",
            "model": "claude-sonnet-4-6 (Vyce AI)",
            "color": "#ef4444",
            "icon": "📢",
            "char": "A",
            "base_latency": 20.0,
            "status": "ARMED",
        },
        "seeding_ops": {
            "name": "seeding_ops",
            "name_vi": "Đội Seeding",
            "role_vi": "Thatim.vn Social Proof",
            "duty_vi": "Auto-seeding qua Thatim.vn ($152.39 balance), kỹ thuật chim mồi 2 máy",
            "role": "Seeding",
            "full_role": "Social Proof & Crowd Simulator",
            "model": "deepseek-v4-flash (Vyce AI)",
            "color": "#10b981",
            "icon": "🌱",
            "char": "S",
            "base_latency": 8.0,
            "status": "ONLINE",
        },
        "trend_scout": {
            "name": "trend_scout",
            "name_vi": "Trinh Sát Xu Hướng",
            "role_vi": "Bắt Sóng Trend & Đối Thủ",
            "duty_vi": "Quét sóng Gemini 4, bóc tách format đối thủ @graperu_ trên TikTok",
            "role": "Scout",
            "full_role": "TikTok & Meta Trend Radar",
            "model": "cx/gpt-6-astra (9Router)",
            "color": "#0ea5e9",
            "icon": "📡",
            "char": "T",
            "base_latency": 18.0,
            "status": "SCANNING",
        },
        "risk_guard": {
            "name": "risk_guard",
            "name_vi": "Cảnh Sát Rủi Ro",
            "role_vi": "Anti-Checkpoint & Bảo Toàn Nick",
            "duty_vi": "Kiểm soát Zero-Burst Policy, Stagger 25-45 phút, chống bóp reach Meta",
            "role": "Risk",
            "full_role": "Compliance & Checkpoint Shield",
            "model": "claude-sonnet-4-6 (Vyce AI)",
            "color": "#0284c7",
            "icon": "🛡️",
            "char": "R",
            "base_latency": 5.0,
            "status": "ARMED",
        },
        "affiliate_desk": {
            "name": "affiliate_desk",
            "name_vi": "Bàn Affiliate",
            "role_vi": "Cookie Trap & Chuyển Đổi",
            "duty_vi": "Điều hướng Bio Beacons, kích hoạt Cookie Shopee 7 ngày, mồi tò mò",
            "role": "Affiliate",
            "full_role": "Shopee CRO & Cookie Harvester",
            "model": "cx/gpt-5.6-luna (9Router)",
            "color": "#14b8a6",
            "icon": "💰",
            "char": "M",
            "base_latency": 10.0,
            "status": "ACTIVE",
        },
        "crm_support": {
            "name": "crm_support",
            "name_vi": "Chăm Sóc Khách",
            "role_vi": "Xử Lý Đơn & Bảo Hành",
            "duty_vi": "Fulfillment tài khoản Gemini AI Premium (lãi 150k/con), bảo hành uy tín",
            "role": "CRM",
            "full_role": "Customer Success & Warranty Desk",
            "model": "deepseek-v4.1 (Vyce AI)",
            "color": "#6366f1",
            "icon": "👥",
            "char": "U",
            "base_latency": 14.0,
            "status": "ACTIVE",
        },
        "analytics_pm": {
            "name": "analytics_pm",
            "name_vi": "Phòng Phân Tích",
            "role_vi": "Đo Lường Signal & FLOP Monitor",
            "duty_vi": "Giám sát 3 phễu đề xuất Facebook Reels, bắt bệnh video FLOP hàng giờ",
            "role": "Analytics",
            "full_role": "Signal Telemetry & FLOP Forensic",
            "model": "deepseek-v4-flash (Vyce AI)",
            "color": "#3b82f6",
            "icon": "📊",
            "char": "P",
            "base_latency": 16.0,
            "status": "ACTIVE",
        },
        "page_router": {
            "name": "page_router",
            "name_vi": "Phân Luồng Page",
            "role_vi": "Điều Phối Ma Trận 22 Page",
            "duty_vi": "Phân bổ video độc bản 1-1 cho 8 Manhua, 7 Cổ Trang, 7 KOC/Gia Dụng",
            "role": "Router",
            "full_role": "Intelligent Niche Dispatcher",
            "model": "cx/gpt-5.6-terra (9Router)",
            "color": "#64748b",
            "icon": "🔀",
            "char": "O",
            "base_latency": 6.0,
            "status": "ACTIVE",
        },
        "asset_guard": {
            "name": "asset_guard",
            "name_vi": "Bảo Vệ Tài Sản",
            "role_vi": "Vân Tay Số & Chống Trùng",
            "duty_vi": "Kiểm tra SHA-256 + Perceptual Hash (pHash), tuyệt đối 0 cross-posting",
            "role": "AssetGuard",
            "full_role": "Asset Registry & Duplicate Blocker",
            "model": "Local Perceptual Hash",
            "color": "#f43f5e",
            "icon": "🔒",
            "char": "G",
            "base_latency": 2.0,
            "status": "ENFORCING",
        }
    }

    FLEET_NAMES = [
        "captain", "content_lab", "video_forge", "ads_engine",
        "seeding_ops", "trend_scout", "risk_guard", "affiliate_desk",
        "crm_support", "analytics_pm", "page_router", "asset_guard"
    ]

    DEPT_SPEECHES = {
        "captain": [
            "Hệ thống Nemark MKT Fleet trực chiến 24/7. Điều phối 22 page.",
            "Đang đồng bộ số liệu Facebook Insights & 12 phòng ban marketing..."
        ],
        "content_lab": [
            "Sẵn sàng viết caption viral cho cụm Drama, Manhua, KOC.",
            "Đã tạo 3 hook variants chuẩn A/B test cho chiến dịch Gemini AI."
        ],
        "video_forge": [
            "FFmpeg render 1080x1920 với bộ lọc Lanczos và chống bản quyền 4 điểm.",
            "Giọng đọc TTS AI vi-VN sẵn sàng. Cấu hình an toàn -threads 2 chống nghẽn VPS."
        ],
        "ads_engine": [
            "Giám sát CPA và tối ưu ngân sách 150k/ngày/page. Format Ảnh + Caption đang ra đơn ngon!",
            "Chiến lược test 1 page winner trước, sau 3 ngày mới nhân bản sang dàn page."
        ],
        "seeding_ops": [
            "Đồng bộ Thatim.vn API thành công. Số dư khả dụng $152.39 USD.",
            "Kỹ thuật chim mồi 2 máy sẵn sàng: Page phụ vào hỏi, Page chính đáp đẩy tương tác."
        ],
        "trend_scout": [
            "Bắt sóng trend Gemini 4 trên TikTok. Đối thủ @graperu_ đạt 373k view.",
            "Phát hiện nhu cầu tài khoản AI bùng nổ. Khán giả thích deal 189k bảo hành uy tín."
        ],
        "risk_guard": [
            "Kiểm soát Zero-Burst Policy. Lập lịch phát Meta giãn cách 25-45 phút.",
            "Tuyệt đối cấm spam link Shopee thô dưới 1.000 view để bảo vệ phân phối Meta."
        ],
        "affiliate_desk": [
            "Kích hoạt Cookie Shopee 7 ngày qua Beacons bio https://beacons.ai/reviewhola.",
            "Mồi tò mò kịch bản drama đẩy CTR lên bio đạt đỉnh. Chuyển đổi organic an toàn."
        ],
        "crm_support": [
            "Chiến dịch Gemini Jio arbitrage: Giá bán 189k, vốn 35k, lãi ròng 150k/con.",
            "Cổng bảo hành và cấp tài khoản sẵn sàng, cam kết 1 đổi 1 giữ uy tín thương hiệu."
        ],
        "analytics_pm": [
            "Bộ chẩn đoán FLOP 1h đang quét chỉ số. Đánh giá watch-through & share thay vì like ảo.",
            "Tỷ lệ hoàn thành video > 45% là tín hiệu thuật toán chuẩn bị đẩy vào phễu triệu view."
        ],
        "page_router": [
            "Ma trận 22 Fanpage đã phân luồng: 8 Manhua, 7 Cổ Trang, 7 KOC/Gia Dụng.",
            "Mỗi page là 1 bản sắc độc bản, 1 Hook riêng, 1 tệp khán giả không giẫm chân nhau."
        ],
        "asset_guard": [
            "Bảo vệ vân tay SHA-256 + pHash: 100% video là bản render độc bản.",
            "Tuyệt đối không cross-post 1 video cho 2 page tránh bẫy Unoriginal Content 0-view."
        ]
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._event_logs = deque(maxlen=60)
        self._agent_state = {}
        self._init_states()
        self._seed_initial_events()

    def _init_states(self):
        for code in self.FLEET_NAMES:
            meta = self.MKT_AGENT_METADATA[code]
            self._agent_state[code] = {
                "name": code,
                "name_vi": meta["name_vi"],
                "role_vi": meta["role_vi"],
                "duty_vi": meta["duty_vi"],
                "role": meta["role"],
                "full_role": meta["full_role"],
                "model": meta["model"],
                "color": meta["color"],
                "icon": meta["icon"],
                "char": meta["char"],
                "latency_ms": meta["base_latency"],
                "status": meta["status"],
                "details": "Trực chiến & đồng bộ ma trận 22 Fanpage",
                "signals_today": 0,
                "uptime": "99.9%"
            }

    def _seed_initial_events(self):
        now = datetime.now(timezone.utc).isoformat()
        sample_events = [
            ("captain", "SYSTEM_ONLINE", {"detail": "Nemark MKT Deck đã tích hợp vào Tầng Dưới Astra Desk"}),
            ("trend_scout", "TREND_RADAR", {"trend": "Sóng Gemini 4 bùng nổ TikTok", "cpm_ref": "~12,000 VND"}),
            ("ads_engine", "ADS_STRATEGY", {"format": "Ảnh + Caption (Winner)", "target_cpa": "< 50,000 VND"}),
            ("seeding_ops", "THATIM_SYNC", {"balance_usd": 152.39, "services_count": 418}),
            ("crm_support", "UNIT_ECONOMICS", {"product": "Gemini AI Premium", "net_profit": "150,000 VND/con"}),
            ("risk_guard", "SAFETY_CHECK", {"policy": "Zero-Burst Active", "min_stagger": "25m"}),
            ("asset_guard", "FINGERPRINT_AUDIT", {"scanned_pages": 22, "duplicate_rate": "0.0%"})
        ]
        for agent, ev_type, payload in sample_events:
            self.log_event(agent, ev_type, payload)

    def log_event(self, agent_name: str, event_type: str, payload: dict):
        with self._lock:
            ev = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": agent_name,
                "event_type": event_type,
                "payload": payload
            }
            self._event_logs.appendleft(ev)
            if agent_name in self._agent_state:
                self._agent_state[agent_name]["signals_today"] += 1
                if "detail" in payload:
                    self._agent_state[agent_name]["details"] = str(payload["detail"])

    def update_agent_status(self, agent_code: str, status: str, details: Optional[str] = None):
        with self._lock:
            if agent_code in self._agent_state:
                self._agent_state[agent_code]["status"] = status
                if details:
                    self._agent_state[agent_code]["details"] = details

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            active_count = sum(1 for a in self._agent_state.values() if a["status"] in ("ACTIVE", "ONLINE", "ARMED", "SCANNING", "ENFORCING"))
            return {
                "floor_name": "MKT NIVER (TẦNG DƯỚI - OPERATIONS DECK)",
                "active_count": active_count,
                "total_agents": len(self.FLEET_NAMES),
                "total_pages": 22,
                "thatim_balance_usd": 152.39,
                "gemini_profit_per_unit": "150,000 VND",
                "ads_format": "Ảnh + Caption (Verified High ROI)",
                "uptime": "99.9%",
                "total_events": len(self._event_logs),
                "agents": dict(self._agent_state),
                "recent_events": list(self._event_logs)[:20]
            }

# Singleton instance
_coordinator_instance = None
_instance_lock = threading.Lock()

def get_mkt_coordinator() -> MktFleetCoordinator:
    global _coordinator_instance
    if _coordinator_instance is None:
        with _instance_lock:
            if _coordinator_instance is None:
                _coordinator_instance = MktFleetCoordinator()
    return _coordinator_instance
