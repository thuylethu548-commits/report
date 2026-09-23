import sys
sys.path.insert(0, ".")
import asyncio
from config.settings import settings
import ccxt.async_support as ccxt

async def check():
    exchange = ccxt.binance({
        "apiKey": settings.BINANCE_API_KEY,
        "secret": settings.BINANCE_API_SECRET,
        "enableRateLimit": True,
        "options": {"defaultType": "future"}
    })
    try:
        positions = await exchange.fetch_positions(["BTC/USDT:USDT"])
        active = [p for p in positions if float(p.get("contracts", 0) or 0) > 0]
        print(f"Active positions: {len(active)}")
        for p in active:
            print(f"Position: {p['symbol']} {p['side']} {p['contracts']} @ {p['entryPrice']}, Mark: {p['markPrice']}, PnL: {p['unrealizedPnl']}")
        balance = await exchange.fetch_balance()
        print(f"USDT Free: {balance.get('USDT', {}).get('free')}, Total: {balance.get('USDT', {}).get('total')}")
    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(check())
