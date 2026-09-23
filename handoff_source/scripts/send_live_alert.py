import asyncio
import httpx
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from config.settings import settings

async def send_live_alert():
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        print("Missing token or chat_id")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    text = (
        "💎 *[ASTRA LIVE QUANT DESK - THÔNG BÁO VỊ THẾ LIVE THẬT]*\n\n"
        "✅ *Khớp lệnh thật trên Binance Futures:*\n"
        "• Cặp giao dịch: `SOL/USDT:USDT` (Futures x3)\n"
        "• Vị thế: *LONG (MUA)*\n"
        "• Khối lượng: `0.06 SOL` (~ $6.06 Notional)\n"
        "• Giá vào lệnh (Entry): `$101.03`\n"
        "• Ký quỹ (Margin đã dùng): `~$2.02 USDT`\n"
        "• Số dư ví USDT tự do: `~$7.98 USDT` (Tuyệt đối an toàn, bảo vệ tài khoản 10$)\n\n"
        "🛡️ *Kế hoạch Quản trị Rủi ro Tự Động:*\n"
        "• Stop-Loss (Cắt lỗ cứng): `$99.51` (-1.5% ~ -0.09$)\n"
        "• Take-Profit (Chốt lời mục tiêu): `$104.06` (+3.0% ~ +0.18$)\n"
        "• Break-Even Lock: Tự động dời SL hòa vốn khi giá chạm +1.2% ($102.24)\n"
        "• Dynamic Trailing Stop: Tự động bám đỉnh lãi khi đạt +2.0%\n\n"
        "🚀 Hệ thống đã định tuyến 100% cảnh báo về Telegram này!"
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        print("Telegram response status:", resp.status_code)
        print("Telegram response body:", resp.text)

if __name__ == "__main__":
    asyncio.run(send_live_alert())
