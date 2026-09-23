import asyncio
import sys
import logging
from datetime import datetime, timezone

sys.path.insert(0, r'c:\sunMy\trading_bot')

import ccxt.async_support as ccxt
from config.settings import settings
from data.storage import Database
from ai_advisory.vyce_client import VyceClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [QuantSweeper] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("QuantSweeper")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

async def run_market_intelligence_sweep():
    logger.info("🔥 BẮT ĐẦU CHU KỲ PHÂN TÍCH THỊ TRƯỜNG ĐA TÁC TỬ (BULL VS BEAR COUNCIL)")
    
    db = Database('trading_bot.db')
    await db.connect()
    
    f_ex = ccxt.binance({
        'apiKey': settings.BINANCE_API_KEY,
        'secret': settings.BINANCE_API_SECRET,
        'options': {'defaultType': 'future'}
    })
    
    vyce_claude = VyceClient(model='claude-sonnet-4-6', timeout=25.0, db=db)
    vyce_deepseek = VyceClient(model='deepseek-v4.1', timeout=25.0, db=db)
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    
    try:
        for sym in symbols:
            logger.info(f"--- Đang phân tích hội đồng đa tác tử: {sym} ---")
            ticker = await f_ex.fetch_ticker(sym)
            price = ticker['last']
            change = ticker.get('percentage', 0.0)
            
            ohlcv_1h = await f_ex.fetch_ohlcv(sym, timeframe='1h', limit=25)
            closes = [c[4] for c in ohlcv_1h]
            
            # Simple RSI calculation
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            rsi = 50.0
            if len(gains) >= 14:
                ag = sum(gains[-14:]) / 14
                al = sum(losses[-14:]) / 14
                rsi = 100 - (100 / (1 + (ag / al))) if al != 0 else 100
                
            # Call Claude as Supreme Macro Evaluator
            sys_claude = (
                "You are the Lead Quantitative Strategist at Astra Quant Desk. "
                "Output strictly a JSON with keys: 'regime' (BULL_TREND/BEAR_TREND/RANGING), "
                "'signal' (BUY/SELL/HOLD), 'confidence' (0.0-1.0), 'target_price', 'stop_loss', 'rationale' (under 30 words)."
            )
            user_claude = (
                f"Asset: {sym}, Price: ${price:.2f}, 24h Change: {change:+.2f}%, 1H RSI: {rsi:.1f}. "
                f"Synthesize market structure, order book liquidity, and momentum."
            )
            
            raw_claude = await vyce_claude.chat_completion(sys_claude, user_claude, max_tokens=150, action="SWEEPER_COUNCIL_CLAUDE")
            
            # Call DeepSeek as Adversarial Risk Devil's Advocate
            sys_deepseek = (
                "You are the Chief Risk Officer (Devil's Advocate). "
                "Find flaws or risks in current price action. "
                "Output strictly a JSON with keys: 'risk_score' (1-10), 'warning' (under 25 words), 'trade_allowed' (bool)."
            )
            raw_deepseek = await vyce_deepseek.chat_completion(sys_deepseek, user_claude, max_tokens=120, action="SWEEPER_COUNCIL_DEEPSEEK")
            
            logger.info(f"[{sym}] Claude Cố Vấn: {raw_claude}")
            logger.info(f"[{sym}] DeepSeek Phản Biện: {raw_deepseek}")
            
        logger.info("✅ HOÀN TẤT CHU KỲ QUÉT HỘI ĐỒNG ĐA TÁC TỬ TOÀN DIỆN!")
        
    except Exception as e:
        logger.error(f"Lỗi Sweeper: {e}")
    finally:
        await vyce_claude.close()
        await vyce_deepseek.close()
        await f_ex.close()
        await db.close()

if __name__ == '__main__':
    asyncio.run(run_market_intelligence_sweep())
