import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import ccxt
from config.settings import settings
from ai_advisory.vyce_client import VyceClient
from risk_engine.funding_sentinel import FundingSentinel

logger = logging.getLogger("BinanceSquarePublisher")


class BinanceSquarePublisher:
    """
    Automated Market Intelligence Generator for Binance Square & Social Media.
    Synthesizes live multi-pair market feeds, funding rates, and AI quantitative models
    to craft high-value, educational market insights to build audience and attract copy-traders.
    """
    def __init__(
        self,
        vyce_client: Optional[VyceClient] = None,
        funding_sentinel: Optional[FundingSentinel] = None,
        exchange: Optional[Any] = None
    ):
        self.vyce = vyce_client or VyceClient()
        self.sentinel = funding_sentinel or FundingSentinel()
        self.exchange = exchange
        self._last_post: Optional[Dict[str, Any]] = None

    def _get_exchange(self):
        if self.exchange:
            return self.exchange
        return ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})

    async def fetch_market_snapshot(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Collects live price, 24h change, and funding rate for core pairs."""
        target_symbols = symbols or settings.SYMBOLS
        snapshots = []
        ex = self._get_exchange()

        for s in target_symbols:
            try:
                if asyncio.iscoroutinefunction(getattr(ex, "fetch_ticker", None)):
                    ticker = await ex.fetch_ticker(s)
                else:
                    ticker = await asyncio.to_thread(ex.fetch_ticker, s)

                fr = await self.sentinel.get_funding_rate(s)
                snapshots.append({
                    "symbol": s,
                    "last_price": ticker.get("last", 0.0),
                    "change_24h_pct": ticker.get("percentage", 0.0),
                    "high_24h": ticker.get("high", 0.0),
                    "low_24h": ticker.get("low", 0.0),
                    "volume_usdt": ticker.get("quoteVolume", 0.0),
                    "funding_rate_pct": fr if fr is not None else 0.01
                })
            except Exception as e:
                logger.warning(f"Failed to fetch ticker for {s}: {e}")
        return snapshots

    async def generate_post(self, focus_symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Synthesizes live data into a viral, professional Binance Square post using fast AI.
        """
        snapshots = await self.fetch_market_snapshot()
        now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

        # Build prompt context
        market_summary = ""
        for snap in snapshots:
            market_summary += (
                f"- {snap['symbol']}: Giá ${snap['last_price']:,.2f} "
                f"(24h: {snap['change_24h_pct']:+.2f}%), "
                f"Funding Rate: {snap['funding_rate_pct']:.4f}%\n"
            )

        system_prompt = (
            "Bạn là Giám đốc Nghiên cứu Định lượng (Head of Quant Research) tại Astra Quant Labs. "
            "Nhiệm vụ của bạn là viết một bài nhận định thị trường chuẩn phong cách chuyên gia quỹ trên Binance Square (tiếng Việt). "
            "Yêu cầu:\n"
            "1. Phong cách chuyên nghiệp, khách quan, súc tích (khoảng 180 - 250 từ).\n"
            "2. Cấu trúc rõ ràng: Tiêu đề cuốn hút (có icon), Tóm tắt dòng tiền & Funding Rate, Kịch bản giá then chốt, Lời khuyên quản trị rủi ro bảo toàn vốn.\n"
            "3. Nhấn mạnh nguyên tắc sống còn: Cắt lỗ kỷ luật, không gồng lệnh, tuyệt đối không dùng đòn bẩy cao (>5x).\n"
            "4. Thêm các hashtag chuẩn: #BinanceSquare #Bitcoin #CryptoTrading #AstraQuant #RiskManagement"
        )

        user_prompt = (
            f"Dữ liệu thị trường thời gian thực lúc {now_str}:\n"
            f"{market_summary}\n"
            f"Hãy viết bài nhận định thị trường hấp dẫn cho độc giả Binance Square."
        )

        # Use deepseek-v4.1 for fast 2-3s generation; fallback to claude-sonnet-4-6
        content = await self.vyce.chat_completion(
            system_prompt=system_prompt,
            user_content=user_prompt,
            max_tokens=450,
            temperature=0.4,
            timeout=12.0,
            model=getattr(settings, "VYCE_FAST_MODEL", "deepseek-v4.1"),
            action="BINANCE_SQUARE_REPORT"
        )

        if not content:
            # Fallback template if AI call is unavailable
            content = (
                f"📊 [ASTRA QUANT DESK] CẬP NHẬT THỊ TRƯỜNG {now_str}\n\n"
                f"Thị trường đang trong giai đoạn nén biên độ sideway tích lũy. "
                f"Funding rate các cặp chính (BTC, ETH, SOL) duy trì ở mức thấp, chưa có tín hiệu gom hàng săn thanh lý cực đoan.\n\n"
                f"🛡️ LỜI KHUYÊN QUẢN TRỊ VỐN:\n"
                f"1. Kiên nhẫn đứng ngoài khi chưa có nến xác nhận phá vỡ kháng cự/hỗ trợ.\n"
                f"2. Tuyệt đối không dùng đòn bẩy cao (giữ dưới 3x-5x).\n"
                f"3. Luôn đặt Hard Stop-Loss cho mọi vị thế để bảo toàn vốn sống còn.\n\n"
                f"#BinanceSquare #Bitcoin #AstraQuant #RiskManagement"
            )

        referral_footer = (
            "\n\n🎁 Nhận ưu đãi tiền thưởng lên đến 50 - 400 USDC khi đăng ký sàn Binance tại:\n"
            "https://www.binance.com/referral/earn-together/refer2earn-usdc/claim?hl=vi&ref=GRO_28502_O41DR\n"
            "(Mã giới thiệu: GRO_28502_O41DR)"
        )
        if "GRO_28502_O41DR" not in content:
            content += referral_footer

        import urllib.parse
        encoded_content = urllib.parse.quote(content)
        square_intent_url = f"https://www.binance.com/vi/square/post/new?text={encoded_content}"

        result = {
            "title": f"Báo Cáo Phân Tích Định Lượng {now_str}",
            "generated_at": now_str,
            "content": content,
            "snapshots": snapshots,
            "referral_code": "GRO_28502_O41DR",
            "square_intent_url": square_intent_url
        }
        self._last_post = result
        return result

    async def publish_post(self, content: Optional[str] = None, channel: str = "auto") -> Dict[str, Any]:
        """
        Publishes market insight post to Binance Square or dispatches to Digital Team review flow.
        - Option A: Direct Binance Creator Open API (if BINANCE_SQUARE_API_KEY configured).
        - Option B: Telegram Broadcast to Marketing Channel with 1-click Binance Square publish button.
        """
        import os
        import aiohttp

        post = self._last_post
        if not post or content:
            if not content:
                post = await self.generate_post()
            else:
                import urllib.parse
                post = {
                    "title": f"Báo Cáo Phân Tích Định Lượng {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}",
                    "generated_at": datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC'),
                    "content": content,
                    "referral_code": "GRO_28502_O41DR",
                    "square_intent_url": f"https://www.binance.com/vi/square/post/new?text={urllib.parse.quote(content)}"
                }

        body_text = post.get("content", "")
        square_api_key = os.getenv("BINANCE_SQUARE_API_KEY")

        # 1. Direct Binance Square API Posting (If API credentials provided)
        if square_api_key and channel in ("auto", "api"):
            try:
                headers = {
                    "X-MBX-APIKEY": square_api_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "content": body_text,
                    "title": post.get("title", "Astra Quant Intelligence")
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.binance.com/sapi/v1/feed/post",
                        headers=headers,
                        json=payload,
                        timeout=10.0
                    ) as resp:
                        if resp.status in (200, 201):
                            res_json = await resp.json()
                            logger.info(f"Published to Binance Square API successfully: {res_json}")
                            return {
                                "status": "SUCCESS",
                                "method": "DIRECT_API",
                                "details": res_json,
                                "post": post
                            }
                        else:
                            err_txt = await resp.text()
                            logger.warning(f"Binance Square API returned {resp.status}: {err_txt}")
            except Exception as e:
                logger.error(f"Failed to post via Binance Square API: {e}")

        # 2. Dispatch to Telegram for Human-in-the-Loop 1-Click Publishing
        try:
            tg_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
            tg_chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)
            if tg_token and tg_chat_id:
                tele_msg = (
                    f"📢 <b>[BAN DIGITAL & MKT NIVER] ĐỀ XUẤT BÀI ĐĂNG BINANCE SQUARE</b>\n\n"
                    f"{body_text}\n\n"
                    f"👉 <a href='{post.get('square_intent_url')}'>🚀 BẤM VÀO ĐÂY ĐỂ ĐĂNG LÊN BINANCE SQUARE (1-CLICK)</a>"
                )
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        f"https://api.telegram.org/bot{tg_token}/sendMessage",
                        json={
                            "chat_id": tg_chat_id,
                            "text": tele_msg,
                            "parse_mode": "HTML",
                            "disable_web_page_preview": True
                        },
                        timeout=8.0
                    )
                logger.info("Dispatched Binance Square draft to Telegram successfully.")
        except Exception as e:
            logger.warning(f"Failed to send Square post to Telegram: {e}")

        return {
            "status": "SUCCESS",
            "method": "INTENT_URL_AND_TELEGRAM",
            "square_intent_url": post.get("square_intent_url"),
            "post": post
        }


binance_square_publisher = BinanceSquarePublisher()
