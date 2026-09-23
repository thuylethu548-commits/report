import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import aiohttp

logger = logging.getLogger("MacroNewsScanner")

DEFAULT_RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
]

FEAR_AND_GREED_API_URL = "https://api.alternative.me/fng/?limit=1"

# Critical Geopolitical & Market Shock Alert Keywords
WAR_KEYWORDS = [
    "war", "missile", "strike", "attack", "invasion", "military",
    "nuclear", "conflict", "bomb", "casualty", "retaliation", "martial law"
]

FINANCIAL_SHOCK_KEYWORDS = [
    "bank run", "default", "liquidity crisis", "insolvency", "sec lawsuit",
    "emergency rate hike", "depeg", "sanctions", "halt trading", "hack", "exploit"
]

BULLISH_KEYWORDS = [
    "rate cut", "etf approval", "etf inflow", "institutional adoption",
    "reserve asset", "treasury buyback", "stimulus", "all-time high"
]


class MacroNewsScanner:
    """
    Real-time Macro Intelligence & Geopolitical Conflict Monitor.
    Scans RSS news feeds, public Fear & Greed indicators, and detects high-impact black swan events.
    """

    def __init__(
        self,
        rss_urls: Optional[List[str]] = None,
        fng_url: str = FEAR_AND_GREED_API_URL,
        request_timeout: float = 4.0
    ):
        self.rss_urls = rss_urls or DEFAULT_RSS_FEEDS
        self.fng_url = fng_url
        self.request_timeout = request_timeout
        self.last_scan_time: Optional[datetime] = None
        self.cached_status: Dict[str, Any] = {
            "state": "NORMAL",
            "emergency_defense": False,
            "fear_and_greed": {"value": 50, "classification": "Neutral"},
            "active_threats": [],
            "recent_headlines": [],
            "summary": "Hệ thống vĩ mô hoạt động bình thường, chưa phát hiện biến động địa chính trị khẩn cấp."
        }

    async def fetch_fear_and_greed(self, session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
        """Fetches Crypto Fear and Greed Index with graceful fallback."""
        should_close = False
        if session is None:
            session = aiohttp.ClientSession()
            should_close = True

        try:
            async with session.get(self.fng_url, timeout=self.request_timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    item = data.get("data", [{}])[0]
                    return {
                        "value": int(item.get("value", 50)),
                        "classification": item.get("value_classification", "Neutral"),
                        "timestamp": item.get("timestamp")
                    }
        except Exception as e:
            logger.debug(f"Could not fetch Fear & Greed Index (fallback used): {e}")
        finally:
            if should_close:
                await session.close()

        return {"value": 50, "classification": "Neutral"}

    async def fetch_rss_headlines(self, session: Optional[aiohttp.ClientSession] = None) -> List[Dict[str, str]]:
        """Parses recent news headlines from configured RSS channels."""
        should_close = False
        if session is None:
            session = aiohttp.ClientSession()
            should_close = True

        headlines = []
        try:
            for url in self.rss_urls:
                try:
                    async with session.get(url, timeout=self.request_timeout) as resp:
                        if resp.status == 200:
                            content = await resp.text()
                            root = ET.fromstring(content)
                            for item in root.findall(".//item")[:10]:
                                title = item.findtext("title", "").strip()
                                link = item.findtext("link", "").strip()
                                pub_date = item.findtext("pubDate", "").strip()
                                if title:
                                    headlines.append({
                                        "title": title,
                                        "link": link,
                                        "pub_date": pub_date
                                    })
                except Exception as ex:
                    logger.debug(f"Failed to fetch RSS from {url}: {ex}")
        finally:
            if should_close:
                await session.close()

        return headlines

    def analyze_headlines(self, headlines: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyzes headline text against geopolitical war and financial shock dictionaries.
        """
        war_detected = []
        shock_detected = []
        bull_detected = []

        for h in headlines:
            title_lower = h.get("title", "").lower()
            for kw in WAR_KEYWORDS:
                if f" {kw} " in f" {title_lower} " or title_lower.startswith(f"{kw} ") or title_lower.endswith(f" {kw}"):
                    war_detected.append({"headline": h["title"], "keyword": kw, "type": "WAR"})
                    break
            for kw in FINANCIAL_SHOCK_KEYWORDS:
                if f" {kw} " in f" {title_lower} " or title_lower.startswith(f"{kw} ") or title_lower.endswith(f" {kw}"):
                    shock_detected.append({"headline": h["title"], "keyword": kw, "type": "SHOCK"})
                    break
            for kw in BULLISH_KEYWORDS:
                if f" {kw} " in f" {title_lower} " or title_lower.startswith(f"{kw} ") or title_lower.endswith(f" {kw}"):
                    bull_detected.append({"headline": h["title"], "keyword": kw, "type": "BULL"})
                    break

        all_threats = war_detected + shock_detected

        if war_detected:
            state = "WAR_RISK_DEFENSIVE"
            emergency = True
            summary = f"⚠️ CẢNH BÁO CHIẾN SỰ / ĐỊA CHÍNH TRỊ: Phát hiện {len(war_detected)} tin nóng xung đột! Kích hoạt chế độ phòng thủ."
        elif shock_detected:
            state = "FINANCIAL_SHOCK_DEFENSIVE"
            emergency = True
            summary = f"⚠️ BÃO VĨ MÔ: Phát hiện {len(shock_detected)} rủi ro chấn động tài chính! Siết chặt quản trị rủi ro."
        elif len(bull_detected) >= 2:
            state = "BULL_MACRO"
            emergency = False
            summary = f"🚀 TÍN HIỆU VĨ MÔ TÍCH CỰC: Dòng tiền và tin tức vĩ mô hỗ trợ đà tăng ({len(bull_detected)} tin tích cực)."
        else:
            state = "NORMAL"
            emergency = False
            summary = "Thị trường vĩ mô ổn định, không có biến động khẩn cấp."

        return {
            "state": state,
            "emergency_defense": emergency,
            "active_threats": all_threats,
            "bullish_signals": bull_detected,
            "summary": summary
        }

    async def scan_market_macro(self) -> Dict[str, Any]:
        """Runs a complete macro scan cycle across RSS feeds & Fear/Greed index."""
        async with aiohttp.ClientSession() as session:
            fng_task = self.fetch_fear_and_greed(session)
            rss_task = self.fetch_rss_headlines(session)
            fng, headlines = await asyncio.gather(fng_task, rss_task)

        analysis = self.analyze_headlines(headlines)
        self.last_scan_time = datetime.now(timezone.utc)

        self.cached_status = {
            "state": analysis["state"],
            "emergency_defense": analysis["emergency_defense"],
            "fear_and_greed": fng,
            "active_threats": analysis["active_threats"],
            "bullish_signals": analysis.get("bullish_signals", []),
            "recent_headlines": headlines[:15],
            "summary": analysis["summary"],
            "last_updated": self.last_scan_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        return self.cached_status
