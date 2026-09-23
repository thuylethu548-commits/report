import asyncio
from data.binance_client import BinanceClient

async def test():
    client = BinanceClient(market_type="futures", use_testnet=False)
    try:
        for sym in ["SOL/USDT:USDT", "1000PEPE/USDT:USDT"]:
            trades = await client.exchange.fetch_my_trades(sym, limit=15)
            print(f"=== Trades for {sym} (count: {len(trades)}) ===")
            for t in trades:
                print(t.get("datetime"), t.get("side"), "px:", t.get("price"), "amt:", t.get("amount"), "pnl:", t.get("info", {}).get("realizedPnl"))
    finally:
        await client.close()

if __name__ == '__main__':
    asyncio.run(test())
