"""
ALPHA MINER DAEMON SERVICE
Chạy ngầm 24/7 qua PM2: Tự động khai thác nến BTC, ETH, SOL
và xoay tua 4 siêu model (gpt-5.6-sol, claude-opus-5, claude-sonnet-5, gpt-5.6-terra)
để tạo tập dữ liệu CoT độc quyền và tiêu hao credit AI có ích.
"""
import sys
import asyncio
from pathlib import Path

BOT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOT_ROOT))

from scripts.ai_synthetic_trainer import daemon_loop

if __name__ == "__main__":
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    models = [
        "gpt-5.6-sol",      # Flagship Logic & Reasoning
        "claude-opus-5",    # Deepest Forensic & Devil's Advocate
        "claude-sonnet-5",  # Institutional Quant Arbiter
        "gpt-5.6-terra"     # Macro & Liquidity Flow Analysis
    ]
    asyncio.run(daemon_loop(
        symbols=symbols,
        models=models,
        interval_seconds=60,
        samples_per_cycle=2
    ))
