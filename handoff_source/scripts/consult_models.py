import sys
from pathlib import Path

# Ensure UTF-8 output
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
from ai_advisory.vyce_client import VyceClient

ARCHITECTURE_PROMPT = """
Bạn là chuyên gia kiến trúc phần mềm và kỹ sư lượng tử cấp cao (Principal Quant Architect).
Dự án Astra Quant Desk vừa thiết kế kiến trúc cho Digital Research Lab như sau:
1. Logic điều phối, Agent layer (12 AI agents), quản trị rủi ro: Python (AsyncIO)
2. Công cụ phân tích dữ liệu lớn trên Parquet Data Lake (100k+ simulation cases): DuckDB (lõi C++) + PyArrow (lõi C++)
3. Lưu trữ trạng thái giao dịch & sổ cái thực nghiệm: SQLite / PostgreSQL
4. Lưu trữ kho dữ liệu dài hạn: 5TB Google Drive (Parquet nén Snappy)
5. Cảnh báo khẩn cấp & sao lưu DB nhanh: Telegram Bot
6. Tần số giao dịch: Nến 15m/1h trên Binance Futures, có Trailing Stop, Circuit Breaker, VAR Council.

Câu hỏi:
1. Kiến trúc dùng Python làm tầng điều phối + DuckDB/PyArrow (C++) làm tầng tính toán dữ liệu lớn có ĐỦ KHỎE và ỔN ĐỊNH cho hệ thống này không?
2. Có nhất thiết phải đập đi viết lại bằng C++ hoặc Rust toàn bộ không?
3. Ưu/nhược điểm thực tế là gì?
Hãy đưa ra đánh giá khách quan, sắc bén, súc tích dưới 250 từ.
"""

async def main():
    vc = VyceClient()
    print("==================================================")
    print("🤖 HỎI Ý KIẾN TRỰC TIẾP TỪ GPT-6 ASTRA...")
    print("==================================================")
    try:
        r_gpt = await vc.chat_completion(
            system_prompt="You are a Principal Quant System Architect. Answer authoritatively in Vietnamese under 250 words.",
            user_content=ARCHITECTURE_PROMPT,
            model="cx/gpt-6-astra",
            timeout=25.0
        )
        print(r_gpt)
    except Exception as e:
        print("Lỗi kết nối GPT-6:", e)

    print("\n==================================================")
    print("🦁 HỎI Ý KIẾN TRỰC TIẾP TỪ SUPERGROK 4.7...")
    print("==================================================")
    try:
        r_grok = await vc.chat_completion(
            system_prompt="You are a Principal Quant System Architect. Answer authoritatively and sharply in Vietnamese under 250 words.",
            user_content=ARCHITECTURE_PROMPT,
            model="gcli/grok-4.7",
            timeout=25.0
        )
        print(r_grok)
    except Exception as e:
        print("Lỗi kết nối Grok:", e)

    await vc.close()

if __name__ == "__main__":
    asyncio.run(main())
