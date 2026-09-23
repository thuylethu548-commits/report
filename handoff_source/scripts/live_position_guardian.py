import asyncio
import sys
import logging
from datetime import datetime, timezone

sys.path.insert(0, r'c:\sunMy\trading_bot')

import ccxt.async_support as ccxt
from config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [LiveGuardian] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("LiveGuardian")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

async def run_guardian():
    logger.info("LIVE POSITION GUARDIAN DA KHOI CHAY (BAO VE LOI NHUAN THOI GIAN THUC)")
    logger.info("Muc tieu: Chot loi $2,508.0 | Trailing Stop an toan | Bao dong xa hang khan cap")

    f_ex = ccxt.binance({
        'apiKey': settings.BINANCE_API_KEY,
        'secret': settings.BINANCE_API_SECRET,
        'options': {'defaultType': 'future'}
    })

    peak_profit = 0.0

    try:
        while True:
            try:
                # 1. Check if ETH position is still open
                risks = await f_ex.fapiPrivateV2GetPositionRisk({'symbol': 'ETHUSDT'})
                eth_pos = [r for r in risks if float(r.get('positionAmt', 0)) != 0]

                if not eth_pos:
                    logger.info("VI THE ETH DA DUOC CHOT LOI THANH CONG! Hoan tat nhiem vu.")
                    break

                pos = eth_pos[0]
                amt = float(pos.get('positionAmt'))
                entry = float(pos.get('entryPrice'))
                mark = float(pos.get('markPrice'))
                pnl = float(pos.get('unRealizedProfit'))

                if pnl > peak_profit:
                    peak_profit = pnl

                # 2. Log status
                logger.info(f"ETH: ${mark:.2f} (Entry: ${entry:.2f}) | PnL: {pnl:+.4f} USDT (Peak: {peak_profit:+.4f} USDT)")

                # 3. Emergency Risk Guardian Check:
                # If position was in profit (>= +0.15 USDT) and drops back to near zero (<= +0.03 USDT)
                if peak_profit >= 0.15 and pnl <= 0.03:
                    logger.warning("CANH BAO BAO TOAN LAI: Thi truong co dau hieu quay dau! Chot loi khan cap ('Co con hon khong').")
                    try:
                        await f_ex.fapiPrivateDeleteAllOpenOrders({'symbol': 'ETHUSDT'})
                    except Exception:
                        pass
                    await f_ex.create_market_sell_order('ETH/USDT', abs(amt), params={'reduceOnly': True})
                    logger.info("DA CHOT LAI KHAN CAP THANH CONG BAO VE TIEN VE VI!")
                    break

                # 4. Check 15m technical health
                ohlcv = await f_ex.fetch_ohlcv('ETH/USDT', timeframe='15m', limit=15)
                closes = [c[4] for c in ohlcv]
                if len(closes) >= 14:
                    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
                    gains = [d if d > 0 else 0 for d in deltas]
                    losses = [-d if d < 0 else 0 for d in deltas]
                    avg_gain = sum(gains[-14:]) / 14
                    avg_loss = sum(losses[-14:]) / 14
                    rsi_15m = 100 - (100 / (1 + (avg_gain / avg_loss))) if avg_loss != 0 else 100

                    # Sudden flash dump (RSI collapses < 35 rapidly and PnL still positive)
                    if rsi_15m < 35.0 and pnl > 0:
                        logger.warning(f"BAO DONG NGUY HIEM: RSI 15M gay sau ({rsi_15m:.1f})! Chot loi khan cap ngay!")
                        try:
                            await f_ex.fapiPrivateDeleteAllOpenOrders({'symbol': 'ETHUSDT'})
                        except Exception:
                            pass
                        await f_ex.create_market_sell_order('ETH/USDT', abs(amt), params={'reduceOnly': True})
                        logger.info("DA CHOT LAI KHAN CAP!")
                        break

            except Exception as e:
                logger.error(f"Loi vong lap Guardian: {e}")

            await asyncio.sleep(6)

    finally:
        await f_ex.close()

if __name__ == '__main__':
    asyncio.run(run_guardian())
