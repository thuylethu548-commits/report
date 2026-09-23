"""
AI SYNTHETIC TRAINING DATASET GENERATOR & ADVANCED QUANT MINER
------------------------------------------------------------------
Động cơ khai thác nến lịch sử đa cặp tiền (BTC, ETH, SOL, DOGE)
và đa model AI (gpt-5.6-sol, claude-opus-5, claude-sonnet-5, gpt-5.6-terra)
để tạo ra Tập Dữ Liệu Huấn Luyện Độc Quyền (Proprietary Alpha Dataset).
"""

import os
import sys
import re
import json
import time
import random
import asyncio
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

BOT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOT_ROOT))

import pandas as pd
import numpy as np

from config.settings import settings
from data.binance_client import BinanceClient
from ai_advisory.vyce_client import VyceClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("AlphaMiner")

DATASET_FILE = BOT_ROOT / "data" / "dataset_alpha_training.jsonl"

AVAILABLE_MODELS = [
    "gpt-5.6-sol",      # Flagship Logic & Reasoning
    "claude-opus-5",    # Deepest Forensic & Devil's Advocate
    "claude-sonnet-5",  # Institutional Quant Arbiter
    "gpt-5.6-terra"     # Macro & Liquidity Flow Analysis
]

COT_SYSTEM_PROMPT = """You are the Supreme Chief Quantitative Research Scientist and Legend Trader at an elite proprietary crypto fund.
Your task is to perform an institutional-grade forensic analysis on historical multi-timeframe cryptocurrency market setups.
For each given market snapshot (OHLCV candles + Quantitative Indicators), you MUST generate a comprehensive, step-by-step Chain of Thought (CoT) reasoning before delivering your final quantitative trading verdict.

You MUST respond strictly in valid JSON matching this schema:
{
  "market_structure": {
    "trend_regime": "BULL_TREND | BEAR_TREND | RANGING | HIGH_VOLATILITY_EXPANSION",
    "key_support": 0.0,
    "key_resistance": 0.0,
    "liquidity_pools": "Description of resting stops"
  },
  "trap_and_manipulation_diagnosis": {
    "is_trap": false,
    "trap_type": "BULL_TRAP | BEAR_TRAP | LIQUIDITY_SWEEP | NONE",
    "institutional_orderflow": "ACCUMULATION | DISTRIBUTION | ABSORPTION | CHOP"
  },
  "chain_of_thought_reasoning": "Step-by-step institutional reasoning (80-150 words) detailing why retail traders lose here, what smart money is doing, and the edge.",
  "trade_decision": {
    "action": "BUY | SELL | PASS",
    "confidence_pct": 85,
    "optimal_entry": 0.0,
    "stop_loss": 0.0,
    "take_profit_1": 0.0,
    "take_profit_2": 0.0,
    "risk_reward_ratio": 2.5
  }
}
STRICT RULE: Output pure JSON only. No markdown fences, no backticks, no introductory or concluding text.
"""


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    return None


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    df["ema_20"] = close.ewm(span=20, adjust=False).mean()
    df["ema_50"] = close.ewm(span=50, adjust=False).mean()
    df["ema_200"] = close.ewm(span=200, adjust=False).mean()

    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df["rsi_14"] = 100 - (100 / (1 + rs))

    bb_mid = close.rolling(window=20).mean()
    bb_std = close.rolling(window=20).std()
    df["bb_upper"] = bb_mid + (bb_std * 2)
    df["bb_lower"] = bb_mid - (bb_std * 2)

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(window=14).mean()

    vol_ma20 = volume.rolling(window=20).mean()
    df["vol_ratio"] = volume / (vol_ma20 + 1e-9)

    return df


class SyntheticDatasetGenerator:
    def __init__(self, models: Optional[List[str]] = None):
        self.models = models or AVAILABLE_MODELS
        self.vyce_client = VyceClient()
        self.binance_client = BinanceClient()
        self.output_file = DATASET_FILE
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

    async def close(self):
        try:
            await self.binance_client.close()
        except Exception:
            pass
        try:
            await self.vyce_client.close()
        except Exception:
            pass

    async def fetch_historical_candles(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        logger.info(f"Fetching {limit} historical candles for {symbol} ({timeframe})...")
        try:
            ohlcv = await self.binance_client.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
            if not ohlcv or len(ohlcv) < 50:
                logger.warning(f"Insufficient candles fetched for {symbol}.")
                return pd.DataFrame()

            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            return pd.DataFrame()

    def extract_interesting_clusters(self, df: pd.DataFrame, max_samples: int = 50) -> List[Dict[str, Any]]:
        df = compute_indicators(df)
        clusters = []

        for idx in range(50, len(df) - 5):
            row = df.iloc[idx]
            prev_row = df.iloc[idx - 1]

            is_rsi_extreme = row["rsi_14"] >= 68 or row["rsi_14"] <= 32
            is_volume_spike = row["vol_ratio"] >= 1.8
            is_bb_touch = row["close"] >= row["bb_upper"] or row["close"] <= row["bb_lower"]
            is_ema_cross = (prev_row["ema_20"] <= prev_row["ema_50"] and row["ema_20"] > row["ema_50"]) or \
                           (prev_row["ema_20"] >= prev_row["ema_50"] and row["ema_20"] < row["ema_50"])

            if is_rsi_extreme or is_volume_spike or is_bb_touch or is_ema_cross:
                window = df.iloc[idx - 9: idx + 1]
                candles_summary = []
                for _, w in window.iterrows():
                    candles_summary.append({
                        "time": w["datetime"].strftime("%Y-%m-%d %H:%M"),
                        "o": round(float(w["open"]), 2),
                        "h": round(float(w["high"]), 2),
                        "l": round(float(w["low"]), 2),
                        "c": round(float(w["close"]), 2),
                        "vol": round(float(w["volume"]), 2)
                    })

                future_window = df.iloc[idx + 1: idx + 6]
                max_future_high = float(future_window["high"].max())
                min_future_low = float(future_window["low"].min())
                entry_close = float(row["close"])
                max_gain_pct = round(((max_future_high - entry_close) / entry_close) * 100, 2)
                max_drawdown_pct = round(((entry_close - min_future_low) / entry_close) * 100, 2)

                cluster_data = {
                    "timestamp": int(row["timestamp"]),
                    "datetime": row["datetime"].strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "current_price": entry_close,
                    "indicators": {
                        "rsi_14": round(float(row["rsi_14"]), 2),
                        "ema_20": round(float(row["ema_20"]), 2),
                        "ema_50": round(float(row["ema_50"]), 2),
                        "ema_200": round(float(row["ema_200"]), 2),
                        "bb_upper": round(float(row["bb_upper"]), 2),
                        "bb_lower": round(float(row["bb_lower"]), 2),
                        "atr_14": round(float(row["atr_14"]), 2),
                        "volume_ratio": round(float(row["vol_ratio"]), 2)
                    },
                    "recent_candles": candles_summary,
                    "ground_truth_future": {
                        "max_gain_next_5_bars_pct": max_gain_pct,
                        "max_drawdown_next_5_bars_pct": max_drawdown_pct,
                        "actual_direction": "UP" if max_gain_pct > max_drawdown_pct else "DOWN"
                    }
                }
                clusters.append(cluster_data)
                if len(clusters) >= max_samples:
                    break

        logger.info(f"Extracted {len(clusters)} high-value market clusters.")
        return clusters

    async def generate_cot_for_cluster(self, symbol: str, timeframe: str, cluster: Dict[str, Any], model_name: str) -> Optional[Dict[str, Any]]:
        user_content = f"""MARKET FORENSIC AUDIT REQUEST
Symbol: {symbol}
Timeframe: {timeframe}
Snapshot Time: {cluster['datetime']}
Current Close Price: ${cluster['current_price']}

TECHNICAL INDICATORS:
- RSI-14: {cluster['indicators']['rsi_14']}
- EMA-20: {cluster['indicators']['ema_20']} | EMA-50: {cluster['indicators']['ema_50']} | EMA-200: {cluster['indicators']['ema_200']}
- Bollinger Bands: Lower = {cluster['indicators']['bb_lower']} | Upper = {cluster['indicators']['bb_upper']}
- ATR-14: {cluster['indicators']['atr_14']}
- Volume Spike Ratio: {cluster['indicators']['volume_ratio']}x 20-period average

LAST 10 CANDLES SEQUENCE (Oldest to Newest):
{json.dumps(cluster['recent_candles'], indent=2)}

Perform institutional analysis:
1. Examine Market Structure & SMC liquidity levels.
2. Diagnose if this is a Bull/Bear Trap or genuine Smart Money momentum.
3. Formulate Chain-of-Thought reasoning.
4. Output institutional trade decision (BUY, SELL, or PASS) with precise Entry, SL, TP1, TP2, R:R.
"""

        try:
            response_text = await self.vyce_client.chat_completion(
                system_prompt=COT_SYSTEM_PROMPT,
                user_content=user_content,
                max_tokens=1500,
                temperature=0.2,
                timeout=90.0,
                model=model_name,
                action="SYNTHETIC_DATASET_GENERATION"
            )

            if not response_text:
                logger.warning(f"Empty response from AI Model ({model_name}).")
                return None

            parsed_json = extract_json_object(response_text)
            if not parsed_json:
                logger.warning(f"Could not parse JSON from model {model_name}.")
                return None

            training_sample = {
                "messages": [
                    {"role": "system", "content": COT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": json.dumps(parsed_json, ensure_ascii=False, indent=2)}
                ],
                "metadata": {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": cluster["timestamp"],
                    "datetime": cluster["datetime"],
                    "model": model_name,
                    "action": parsed_json.get("trade_decision", {}).get("action", "PASS"),
                    "confidence": parsed_json.get("trade_decision", {}).get("confidence_pct", 50),
                    "trap_type": parsed_json.get("trap_and_manipulation_diagnosis", {}).get("trap_type", "NONE"),
                    "ground_truth_future": cluster["ground_truth_future"]
                }
            }
            return training_sample

        except Exception as e:
            logger.error(f"Error generating CoT with {model_name} for {cluster['datetime']}: {e}")
            return None

    def save_sample_to_jsonl(self, sample: Dict[str, Any]) -> None:
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    def get_dataset_stats(self) -> Dict[str, Any]:
        if not self.output_file.exists():
            return {
                "total_samples": 0,
                "file_size_bytes": 0,
                "file_size_human": "0 KB",
                "estimated_tokens_consumed": 0,
                "breakdown_by_action": {},
                "models_used": [],
                "file_path": str(self.output_file)
            }

        total_samples = 0
        actions = {}
        models = set()
        file_size = self.output_file.stat().st_size

        with open(self.output_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    total_samples += 1
                    meta = data.get("metadata", {})
                    act = meta.get("action", "UNKNOWN")
                    actions[act] = actions.get(act, 0) + 1
                    mod = meta.get("model")
                    if mod:
                        models.add(mod)
                except Exception:
                    pass

        size_kb = round(file_size / 1024, 2)
        size_human = f"{size_kb} KB" if size_kb < 1024 else f"{round(size_kb / 1024, 2)} MB"

        return {
            "total_samples": total_samples,
            "file_size_bytes": file_size,
            "file_size_human": size_human,
            "estimated_tokens_consumed": total_samples * 1500,
            "breakdown_by_action": actions,
            "models_used": list(models),
            "file_path": str(self.output_file)
        }

    async def run_batch(self, symbols: List[str], timeframe: str = "15m", samples_per_symbol: int = 5):
        logger.info(f"=== BẮT ĐẦU ĐỢT KHAI THÁC DỮ LIỆU ALPHA (MULTI-MODEL) ===")
        logger.info(f"Cặp theo dõi: {symbols} | Khung: {timeframe} | Mục tiêu/Cặp: {samples_per_symbol}")
        logger.info(f"Danh sách Models xoay tua: {self.models}")

        total_saved = 0
        for symbol in symbols:
            df = await self.fetch_historical_candles(symbol=symbol, timeframe=timeframe, limit=max(samples_per_symbol * 15, 300))
            if df.empty:
                continue

            clusters = self.extract_interesting_clusters(df, max_samples=samples_per_symbol)
            for i, cluster in enumerate(clusters, 1):
                # Xoay tua model theo vòng tròn
                target_model = self.models[(total_saved + i) % len(self.models)]
                logger.info(f"[{symbol} {i}/{len(clusters)}] Phân tích {cluster['datetime']} (${cluster['current_price']}) qua model [{target_model}]...")
                
                sample = await self.generate_cot_for_cluster(symbol, timeframe, cluster, model_name=target_model)
                if sample:
                    self.save_sample_to_jsonl(sample)
                    total_saved += 1
                    meta = sample["metadata"]
                    logger.info(f"-> [THÀNH CÔNG] Model: {meta['model']} | Quyết định: {meta['action']} | Độ tin cậy: {meta['confidence']}%")
                
                await asyncio.sleep(2.0)

        stats = self.get_dataset_stats()
        logger.info(f"=== HOÀN TẤT ĐỢT | Đã lưu: +{total_saved} mẫu mới | Tổng kho: {stats['total_samples']} mẫu ({stats['file_size_human']}) ===")
        logger.info(f"Models trong kho: {stats['models_used']}")
        return total_saved


async def daemon_loop(symbols: List[str], models: List[str], interval_seconds: int = 120, samples_per_cycle: int = 2):
    """Vòng lặp chạy ngầm tự động 24/7 trên VPS."""
    logger.info(f"=== KHỞI ĐỘNG TIẾN TRÌNH MINER CHẠY NGẦM 24/7 ===")
    generator = SyntheticDatasetGenerator(models=models)
    
    try:
        while True:
            try:
                await generator.run_batch(symbols=symbols, timeframe="15m", samples_per_symbol=samples_per_cycle)
            except Exception as e:
                logger.error(f"Lỗi trong chu kỳ miner: {e}")
            
            logger.info(f"Nghỉ {interval_seconds}s trước chu kỳ tiếp theo...")
            await asyncio.sleep(interval_seconds)
    finally:
        await generator.close()


async def main():
    parser = argparse.ArgumentParser(description="AI Synthetic Training Dataset Generator & Alpha Miner")
    parser.add_argument("--symbols", type=str, default="BTC/USDT,ETH/USDT,SOL/USDT", help="Danh sách cặp cách nhau bởi dấu phẩy")
    parser.add_argument("--models", type=str, default="gpt-5.6-sol,claude-opus-5,claude-sonnet-5,gpt-5.6-terra", help="Danh sách model AI xoay tua")
    parser.add_argument("--timeframe", type=str, default="15m", help="Khung thời gian nến (15m, 1h, 4h)")
    parser.add_argument("--samples", type=int, default=5, help="Số mẫu CoT mỗi cặp")
    parser.add_argument("--stats", action="store_true", help="Chỉ hiển thị thống kê kho dữ liệu hiện tại")
    parser.add_argument("--daemon", action="store_true", help="Chạy ngầm liên tục 24/7")
    parser.add_argument("--interval", type=int, default=120, help="Khoảng nghỉ giữa các chu kỳ daemon (giây)")

    args = parser.parse_args()

    symbols_list = [s.strip() for s in args.symbols.split(",") if s.strip()]
    models_list = [m.strip() for m in args.models.split(",") if m.strip()]

    generator = SyntheticDatasetGenerator(models=models_list)

    if args.stats:
        stats = generator.get_dataset_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        await generator.close()
        return

    if args.daemon:
        await daemon_loop(symbols=symbols_list, models=models_list, interval_seconds=args.interval, samples_per_cycle=args.samples)
    else:
        try:
            await generator.run_batch(symbols=symbols_list, timeframe=args.timeframe, samples_per_symbol=args.samples)
        finally:
            await generator.close()


if __name__ == "__main__":
    asyncio.run(main())
