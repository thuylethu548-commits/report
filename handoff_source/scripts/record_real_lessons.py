import asyncio
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_advisory.vyce_client import VyceClient
from data.storage import Database

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

async def extract_and_save_lessons():
    db = Database('trading_bot.db')
    await db.connect()
    client = VyceClient(model='claude-sonnet-4-6', fast_model='deepseek-v4-flash', timeout=8.0, fast_timeout=8.0)

    # Real loss trade 1: ETH 10u
    trade_1 = {
        'symbol': 'ETH/USDT',
        'strategy_name': 'EMA_Trend',
        'entry_price': 2495.7,
        'exit_price': 2458.3,
        'pnl_usdt': -0.44,
        'pnl_percent': -1.5,
        'hold_duration_seconds': 3600.0,
        'reason': 'STOP_LOSS'
    }
    print('[1/2] Đang gọi AI Council phân tích lệnh thua ETH (10u)...')
    pm_1 = await client.generate_post_mortem(trade_1)
    print('Kết quả phân tích ETH:')
    print(f"   Tiêu đề:  {pm_1.get('title')}")
    print(f"   Chi tiết: {pm_1.get('details')}")
    print(f"   Bài học:  {pm_1.get('lesson_learned')}")
    print(f"   Tác giả:  {pm_1.get('operator')}")
    
    await db.save_trading_lesson(
        category=pm_1.get('category', 'STOP_LOSS'),
        title=pm_1.get('title', 'Cắt lỗ ETH bảo toàn vốn'),
        details=pm_1.get('details', ''),
        capital_impact=pm_1.get('capital_impact', 0.44),
        lesson_learned=pm_1.get('lesson_learned', ''),
        operator=pm_1.get('operator', 'Claude-Sonnet-4.6')
    )

    # Real loss trade 2: BTC 10u
    trade_2 = {
        'symbol': 'BTC/USDT',
        'strategy_name': 'EMA_Trend',
        'entry_price': 77903.8,
        'exit_price': 79072.4,
        'pnl_usdt': -0.38,
        'pnl_percent': -1.5,
        'hold_duration_seconds': 7200.0,
        'reason': 'STOP_LOSS'
    }
    print('[2/2] Đang gọi AI Council phân tích lệnh thua BTC (10u)...')
    pm_2 = await client.generate_post_mortem(trade_2)
    print('Kết quả phân tích BTC:')
    print(f"   Tiêu đề:  {pm_2.get('title')}")
    print(f"   Chi tiết: {pm_2.get('details')}")
    print(f"   Bài học:  {pm_2.get('lesson_learned')}")
    print(f"   Tác giả:  {pm_2.get('operator')}")
    
    await db.save_trading_lesson(
        category=pm_2.get('category', 'STOP_LOSS'),
        title=pm_2.get('title', 'Cắt lỗ BTC bảo toàn vốn'),
        details=pm_2.get('details', ''),
        capital_impact=pm_2.get('capital_impact', 0.38),
        lesson_learned=pm_2.get('lesson_learned', ''),
        operator=pm_2.get('operator', 'Claude-Sonnet-4.6')
    )

    await db.close()
    print('>>> ĐÃ LƯU THÀNH CÔNG TẤT CẢ BÀI HỌC VÀO CƠ SỞ DỮ LIỆU SQL!')

if __name__ == '__main__':
    asyncio.run(extract_and_save_lessons())
