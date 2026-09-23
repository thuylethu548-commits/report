"""
COMMUNITY AGENT FARM: 20 FANPAGES & REDDIT DISTRIBUTED INTELLIGENCE
-------------------------------------------------------------------
Mạng lưới 20 Fanpage Meta/Facebook và Reddit Subreddits:
- Phân phối mỗi nhân viên AI (Agent) phụ trách 1-2 kênh cộng đồng chuyên biệt.
- Tự động cào/thu thập các bài viết có tương tác cao (>= 30 reactions, >= 15 comments).
- Đọc sâu bình luận cộng đồng, bóc tách bài học thực chiến & bẫy tâm lý.
- Tự động nhập liệu bài học vào SQLite (trading_lessons) và cập nhật tri thức cho Hội đồng VAR.
- Tự động nâng cao trình độ học tập mỗi ngày cho từng nhân sự AI.
"""

import sys
import os
import re
import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import aiohttp
from config.settings import settings
from ai_advisory.vyce_client import VyceClient

logger = logging.getLogger("CommunityAgentFarm")

# DANH SÁCH 20 FANPAGE & KÊNH CỘNG ĐỒNG PHÂN BỔ CHO CÁC NHÂN SỰ
COMMUNITY_CHANNELS = [
    {
        "id": "fb_01",
        "name": "Followin Vietnam",
        "type": "facebook_fanpage",
        "category": "VĨ MÔ & TIN TỨC",
        "assigned_officer": "Agent Red",
        "model": "claude-sonnet-4-6",
        "focus": "Tin tức chính sách Fed, bầu cử, địa chính trị, dòng tiền toàn cầu"
    },
    {
        "id": "fb_02",
        "name": "Coin98 Insights",
        "type": "facebook_fanpage",
        "category": "RESEARCH & PHÂN TÍCH CƠ BẢN",
        "assigned_officer": "Agent Red",
        "model": "claude-sonnet-4-6",
        "focus": "Báo cáo nghiên cứu hệ sinh thái, định giá dự án, tokenomics"
    },
    {
        "id": "fb_03",
        "name": "TradeCoinVN Community",
        "type": "facebook_fanpage",
        "category": "PHÂN TÍCH KỸ THUẬT & TÂM LÝ",
        "assigned_officer": "Agent Lux",
        "model": "groq-fast",
        "focus": "Góc nhìn chart nến, kháng cự hỗ trợ, tâm lý đám đông retail"
    },
    {
        "id": "fb_04",
        "name": "MarginATM",
        "type": "facebook_fanpage",
        "category": "STRATEGY & PHÂN TÍCH PHÁI SINH",
        "assigned_officer": "Agent Lux",
        "model": "groq-fast",
        "focus": "Chiến lược đòn bẩy Futures, săn lệnh thanh lý, quản trị rủi ro"
    },
    {
        "id": "fb_05",
        "name": "Allinstation",
        "type": "facebook_fanpage",
        "category": "AIRDROP & EARLY GEMS",
        "assigned_officer": "Agent Echo",
        "model": "deepseek-v4.1",
        "focus": "Săn các dự án mới, sự kiện testnet, cơ hội airdrop"
    },
    {
        "id": "fb_06",
        "name": "TCVN Debates",
        "type": "facebook_fanpage",
        "category": "TRANH BIỆN CỘNG ĐỒNG",
        "assigned_officer": "Agent Inspector",
        "model": "claude-sonnet-4-6",
        "focus": "Phản biện đa chiều, phát hiện shill trá hình, bóc phốt dự án ảo"
    },
    {
        "id": "fb_07",
        "name": "Binance Vietnam Official",
        "type": "facebook_fanpage",
        "category": "SỰ KIỆN SÀN & CAMPAIGNS",
        "assigned_officer": "Agent Echo",
        "model": "deepseek-v4.1",
        "focus": "Chiến dịch sàn Binance, Refer2Earn, Launchpool, tính năng mới"
    },
    {
        "id": "fb_08",
        "name": "NEAR Protocol Vietnam",
        "type": "facebook_fanpage",
        "category": "HỆ SINH THÁI NEAR",
        "assigned_officer": "Agent Terra",
        "model": "deepseek-v4.1",
        "focus": "Tiến độ Chain Abstraction, User-Owned AI, tin tức hợp tác của NEAR"
    },
    {
        "id": "fb_09",
        "name": "SUI Network Vietnam",
        "type": "facebook_fanpage",
        "category": "HỆ SINH THÁI SUI",
        "assigned_officer": "Agent Terra",
        "model": "deepseek-v4.1",
        "focus": "Dòng tiền Layer 1 SUI, TVL DeFi, gameFi, sự kiện bứt phá"
    },
    {
        "id": "fb_10",
        "name": "Solana Vietnam Hub",
        "type": "facebook_fanpage",
        "category": "HỆ SINH THÁI SOLANA",
        "assigned_officer": "Agent Terra",
        "model": "deepseek-v4.1",
        "focus": "Dòng tiền Solana, khối lượng DEX, trào lưu meme trên SOL"
    },
    {
        "id": "fb_11",
        "name": "WhaleBot On-Chain Alerts",
        "type": "facebook_fanpage",
        "category": "DỮ LIỆU ON-CHAIN",
        "assigned_officer": "Agent Fin",
        "model": "deepseek-v4.1",
        "focus": "Cá voi nạp/rút ví sàn, gom hàng OTC, di chuyển ví cổ"
    },
    {
        "id": "fb_12",
        "name": "Funding Rate & Liquidation Watch",
        "type": "facebook_fanpage",
        "category": "DERIVATIVES SENTINEL",
        "assigned_officer": "Agent Fin",
        "model": "deepseek-v4.1",
        "focus": "Bản đồ thanh lý Heatmap, tỷ lệ Long/Short, funding âm/dương cực đại"
    },
    {
        "id": "fb_13",
        "name": "Kèo x10 Meme Coin Club",
        "type": "facebook_fanpage",
        "category": "MEME & RETAIL FOMO",
        "assigned_officer": "Agent Luna",
        "model": "deepseek-v4-flash",
        "focus": "Đo lường độ hưng phấn của retail trên DOGE, PEPE, cảnh báo xả hàng"
    },
    {
        "id": "fb_14",
        "name": "Crypto Panic Alerts",
        "type": "facebook_fanpage",
        "category": "EMERGENCY FUD & SCAMS",
        "assigned_officer": "Agent Red",
        "model": "claude-sonnet-4-6",
        "focus": "Tin đồn khẩn cấp, tin đồn phá sản, hack giao thức, lệnh trừng phạt"
    },
    {
        "id": "fb_15",
        "name": "CoinMarketCap VN Trends",
        "type": "facebook_fanpage",
        "category": "XU HƯỚNG TĂNG TRƯỞNG",
        "assigned_officer": "Agent Operator",
        "model": "deepseek-v4-flash",
        "focus": "Top 10 tăng mạnh nhất 24h, danh mục đồng coin có volume đột biến"
    },
    {
        "id": "fb_16",
        "name": "CoinDesk Vietnam Edition",
        "type": "facebook_fanpage",
        "category": "TỔ CHỨC TÀI CHÍNH",
        "assigned_officer": "Agent Red",
        "model": "claude-sonnet-4-6",
        "focus": "Động thái của BlackRock, Fidelity, dòng vốn ETF giao ngay"
    },
    {
        "id": "fb_17",
        "name": "TradingView Vietnam Top Ideas",
        "type": "facebook_fanpage",
        "category": "Ý TƯỞNG KỸ THUẬT PRO",
        "assigned_officer": "Agent Lux",
        "model": "groq-fast",
        "focus": "Phân tích mô hình giá Harmonic, Wyckoff, sóng Elliott từ Pro trader"
    },
    {
        "id": "fb_18",
        "name": "Crypto Whistleblower Warnings",
        "type": "facebook_fanpage",
        "category": "CẢNH BÁO RỦI RO",
        "assigned_officer": "Agent Inspector",
        "model": "claude-sonnet-4-6",
        "focus": "Thanh tra dự án xả token vào đầu cộng đồng, chiêu trò thao túng"
    },
    {
        "id": "fb_19",
        "name": "DeFi Farmers Vietnam",
        "type": "facebook_fanpage",
        "category": "DÒNG TIỀN THÔNG MINH",
        "assigned_officer": "Agent Fin",
        "model": "deepseek-v4.1",
        "focus": "Lãi suất staking, biến động thanh khoản pool, cơ hội yield"
    },
    {
        "id": "fb_20",
        "name": "Binance Square Community Pulse",
        "type": "facebook_fanpage",
        "category": "BINANCE SQUARE",
        "assigned_officer": "Agent Echo",
        "model": "deepseek-v4.1",
        "focus": "Xu hướng bài viết trên Binance Square, tương tác người theo dõi"
    },
    # REDDIT SUBREDDITS
    {
        "id": "reddit_01",
        "name": "r/CryptoCurrency",
        "type": "reddit_subreddit",
        "category": "GLOBAL CRYPTO SENTIMENT",
        "assigned_officer": "Agent Red",
        "model": "claude-sonnet-4-6",
        "focus": "Thảo luận toàn cầu, tranh luận nảy lửa giữa các phe, tin tức sớm"
    },
    {
        "id": "reddit_02",
        "name": "r/nearprotocol",
        "type": "reddit_subreddit",
        "category": "NEAR OFFICIAL REDDIT",
        "assigned_officer": "Agent Terra",
        "model": "deepseek-v4.1",
        "focus": "Nhà phát triển thảo luận về Chain Abstraction, Sharding, AI Agent"
    },
    {
        "id": "reddit_03",
        "name": "r/sui",
        "type": "reddit_subreddit",
        "category": "SUI OFFICIAL REDDIT",
        "assigned_officer": "Agent Terra",
        "model": "deepseek-v4.1",
        "focus": "Cập nhật hạ tầng mạng Move, hệ sinh thái game, nâng cấp node"
    }
]


class CommunityAgentFarm:
    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self.channels = COMMUNITY_CHANNELS
        self.vyce_client = VyceClient(model="gemini-3.6-flash")

    def get_assigned_channels_for_officer(self, officer_name: str) -> List[Dict[str, Any]]:
        return [c for c in self.channels if c["assigned_officer"].lower() == officer_name.lower()]

    async def ingest_community_post(
        self,
        channel_id: str,
        post_url: str,
        post_content: str,
        comments: List[str],
        reactions_count: int = 50,
        comments_count: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        Processes a community post + top comments, extracts structured trading wisdom using AI,
        and saves it to SQLite `trading_lessons`.
        """
        # Find channel info
        ch = next((c for c in self.channels if c["id"] == channel_id), None)
        officer = ch["assigned_officer"] if ch else "Agent Inspector"
        ch_name = ch["name"] if ch else channel_id

        comments_text = "\n".join([f"- {c}" for c in comments[:8]])
        user_prompt = f"""
Nguồn thảo luận: {ch_name} (URL: {post_url})
Tương tác: {reactions_count} reactions, {comments_count} comments
Nội dung bài viết:
{post_content}

Các bình luận hay nhất của cộng đồng:
{comments_text}

Hãy phân tích và trích xuất bài học thực chiến cô đọng:
Output STRICTLY a valid JSON with schema:
{{
  "category": "HOLDING_DISCIPLINE | RISK_MANAGEMENT | PSYCHOLOGY | NARRATIVE_ANALYSIS",
  "title": "Tiêu đề bài học dưới 12 từ tiếng Việt",
  "details": "Tóm tắt bối cảnh và diễn biến thảo luận dưới 60 từ tiếng Việt",
  "lesson_learned": "Quy tắc xương máu rút ra cho bot và trader dưới 50 từ tiếng Việt",
  "key_coin": "Mã token liên quan (ví dụ NEAR, SUI, BTC...)",
  "sentiment": "BULLISH | BEARISH | NEUTRAL",
  "takeaway": "Hành động cụ thể bot cần thực thi"
}}
"""
        try:
            res = await self.vyce_client.chat_completion(
                system_prompt="You are a senior quantitative risk and community intelligence analyst. Return strictly valid JSON.",
                user_content=user_prompt,
                max_tokens=2048,
                temperature=0.2,
                model="gemini-3.6-flash",
                action="COMMUNITY_LESSON_EXTRACTION"
            )
            if not res:
                return None

            # Robust regex extraction of JSON object
            match = re.search(r'\{.*\}', res, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                cleaned = res.strip().strip("`").replace("json\n", "")
                data = json.loads(cleaned)

            # Insert into SQLite trading_lessons
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Ensure table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    title TEXT,
                    details TEXT,
                    capital_impact REAL,
                    lesson_learned TEXT,
                    operator TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            title = data.get("title", f"Bài học từ {ch_name}")
            details = f"[{ch_name}] {data.get('details', '')} | Nguồn: {post_url}"
            lesson = data.get("lesson_learned", "")
            cat = data.get("category", "COMMUNITY_INSIGHT")

            iso_now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                INSERT INTO trading_lessons (timestamp, category, title, details, capital_impact, lesson_learned, operator)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (iso_now, cat, title, details, 0.0, lesson, officer))
            conn.commit()
            lesson_id = cursor.lastrowid
            conn.close()

            logger.info(f"🏆 [{officer}] Đã nhập bài học #{lesson_id}: {title} từ {ch_name}")
            return {
                "lesson_id": lesson_id,
                "officer": officer,
                "channel": ch_name,
                "title": title,
                "lesson": lesson,
                "category": cat
            }

        except Exception as e:
            logger.warning(f"Error extracting community lesson: {e}")
            return None


community_farm = CommunityAgentFarm()
