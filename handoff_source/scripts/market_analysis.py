import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import pandas as pd
import numpy as np
from data.binance_client import BinanceClient
from ai_advisory.vyce_client import VyceClient

async def full_market_analysis():
    client = BinanceClient()
    try:
        # Fetch candles for SOL/USDT
        candles_15m = await client.fetch_ohlcv("SOL/USDT", timeframe="15m", limit=60)
        candles_1h = await client.fetch_ohlcv("SOL/USDT", timeframe="1h", limit=60)
        candles_4h = await client.fetch_ohlcv("SOL/USDT", timeframe="4h", limit=60)
        ticker_sol = await client.fetch_ticker("SOL/USDT")
        ticker_btc = await client.fetch_ticker("BTC/USDT")
        
        # 15m DataFrame
        df15 = pd.DataFrame(candles_15m, columns=["ts", "open", "high", "low", "close", "vol"])
        df15["ema9"] = df15["close"].ewm(span=9, adjust=False).mean()
        df15["ema21"] = df15["close"].ewm(span=21, adjust=False).mean()
        df15["ema50"] = df15["close"].ewm(span=50, adjust=False).mean()
        
        # RSI
        delta = df15["close"].diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        df15["rsi"] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        sma20 = df15["close"].rolling(20).mean()
        std20 = df15["close"].rolling(20).std()
        bb_upper = sma20 + 2 * std20
        bb_lower = sma20 - 2 * std20
        
        # 1h & 4h EMA50
        df1h = pd.DataFrame(candles_1h, columns=["ts", "open", "high", "low", "close", "vol"])
        ema50_1h = df1h["close"].ewm(span=50, adjust=False).mean().iloc[-1]
        
        df4h = pd.DataFrame(candles_4h, columns=["ts", "open", "high", "low", "close", "vol"])
        ema50_4h = df4h["close"].ewm(span=50, adjust=False).mean().iloc[-1]
        
        curr_price = float(ticker_sol["last"])
        btc_price = float(ticker_btc["last"])
        sol_rsi = float(df15["rsi"].iloc[-1])
        sol_ema9 = float(df15["ema9"].iloc[-1])
        sol_ema21 = float(df15["ema21"].iloc[-1])
        sol_ema50 = float(df15["ema50"].iloc[-1])
        bbu = float(bb_upper.iloc[-1])
        bbl = float(bb_lower.iloc[-1])
        bbm = float(sma20.iloc[-1])
        
        print("=== LIVE MARKET TELEMETRY ===")
        print(f"SOL/USDT Price: ${curr_price:.2f}")
        print(f"BTC/USDT Price: ${btc_price:.2f}")
        print(f"SOL 15m RSI: {sol_rsi:.2f}")
        print(f"SOL 15m EMA(9): ${sol_ema9:.2f} | EMA(21): ${sol_ema21:.2f} | EMA(50): ${sol_ema50:.2f}")
        print(f"SOL Bollinger Bands: Lower=${bbl:.2f} | Mid=${bbm:.2f} | Upper=${bbu:.2f}")
        print(f"SOL 1h EMA50: ${ema50_1h:.2f} -> Price is {'ABOVE' if curr_price >= ema50_1h else 'BELOW'} 1h EMA50")
        print(f"SOL 4h EMA50: ${ema50_4h:.2f} -> Price is {'ABOVE' if curr_price >= ema50_4h else 'BELOW'} 4h EMA50")
        
        # Query Claude via VyceClient
        vyce = VyceClient()
        from core.events import SignalEvent
        from core.constants import OrderSide
        from datetime import datetime, timezone
        sig = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="SOL/USDT",
            side=OrderSide.BUY,
            price=curr_price,
            stop_loss=round(curr_price * 0.985, 2),
            take_profit=round(curr_price * 1.030, 2),
            confidence=0.88,
            timestamp=datetime.now(timezone.utc)
        )
        context = {
            "symbol": "SOL/USDT",
            "timeframe": "15m",
            "current_price": curr_price,
            "rsi_14": sol_rsi,
            "ema_20": sol_ema21,
            "ema_50": sol_ema50,
            "bollinger_upper": bbu,
            "bollinger_lower": bbl,
            "recent_candles": [{"open": c[1], "high": c[2], "low": c[3], "close": c[4], "volume": c[5]} for c in candles_15m[-10:]]
        }
        print("\n=== CLAUDE-3.5-SONNET AI ADVISORY VERDICT ===")
        adv = await vyce.evaluate_signal_veto(sig, context)
        print(f"Regime: {adv.get('regime')}")
        print(f"Risk Score: {adv.get('risk_score')}/5")
        print(f"Approved: {adv.get('approved')}")
        print(f"Reasoning: {adv.get('reasoning')}")
        print(f"Confidence: {adv.get('confidence')}")
        print(f"Model: {adv.get('model')}")
        await vyce.close()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(full_market_analysis())
