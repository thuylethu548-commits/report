#!/usr/bin/env python3
"""
ASTRA DIGITAL RESEARCH LAB — EXPERIMENT RUNNER CLI
--------------------------------------------------
Runs automated quantitative research cycles, executes DuckDB analytics
over Parquet data lakes, and reports hypothesis discoveries.
"""

import sys
import os
import argparse
import asyncio
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 console output on Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from config.settings import settings
from core.research_lab.continuous_loop import ContinuousImprovementLoop
from core.research_lab.knowledge_store import ResearchKnowledgeStore
from monitoring.telegram_bot import TelegramNotifier
from core.event_bus import EventBus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ResearchLabRunner")


async def main():
    parser = argparse.ArgumentParser(description="Astra Digital Research Lab Runner")
    parser.add_argument("--symbol", default="BTC/USDT", help="Target market symbol")
    parser.add_argument("--cycles", type=int, default=1, help="Number of research experiment cycles")
    parser.add_argument("--query-lake", type=str, default="", help="Run DuckDB analytical SQL on Parquet data lake")
    parser.add_argument("--show-memory", action="store_true", help="Display research memory & failed hypotheses")
    parser.add_argument("--notify-telegram", action="store_true", help="Send research audit summary to Telegram")
    args = parser.parse_args()

    store = ResearchKnowledgeStore()

    # Mode 1: DuckDB Analytics Query
    if args.query_lake:
        print("\n" + "=" * 65)
        print("🦆 DUCKDB ANALYTICAL ENGINE — PARQUET DATA LAKE QUERY")
        print("=" * 65)
        print(f"SQL: {args.query_lake}\n")
        results = store.query_lake_duckdb(args.query_lake)
        for i, row in enumerate(results[:20]):
            print(f"[{i+1:02d}] {row}")
        print(f"\nTotal rows returned: {len(results)}")
        print("=" * 65 + "\n")
        return

    # Mode 2: Show Research Memory
    if args.show_memory:
        print("\n" + "=" * 65)
        print("🧠 BỘ NHỚ TRI THỨC NGHIÊN CỨU (RESEARCH MEMORY)")
        print("=" * 65)
        memories = store.get_research_memory(limit=20)
        for m in memories:
            cat_emoji = "🏆" if m["category"] == "GOLD_STANDARD" else "⚠️"
            print(f"{cat_emoji} [{m['category']}] {m['title']}")
            print(f"   {m['insight']}")
            print(f"   Thời gian: {m['created_at']}\n")
        print("=" * 65 + "\n")
        return

    # Mode 3: Run Research Experiment Cycle
    loop = ContinuousImprovementLoop(knowledge_store=store)

    print("\n" + "=" * 65)
    print("🔬 ASTRA DIGITAL RESEARCH LAB — KHỞI CHẠY THỰC NGHIỆM ĐỊNH LƯỢNG")
    print("=" * 65)
    print(f"• Thị trường mục tiêu: {args.symbol}")
    print(f"• Số chu kỳ nghiên cứu: {args.cycles}")
    print(f"• Tác tử tham gia: Market Research, Quant Dev, Risk Skeptic, Reviewer")
    print("=" * 65 + "\n")

    results = []
    for c in range(args.cycles):
        print(f"▶ Bắt đầu Chu kỳ {c+1}/{args.cycles}...")
        res = await loop.run_experiment_cycle(symbol=args.symbol)
        results.append(res)

        verdict_emoji = "✅" if res.audit_verdict == "APPROVED" else ("⚠️" if res.audit_verdict == "NEEDS_CALIBRATION" else "❌")
        print("\n" + "-" * 65)
        print(f"{verdict_emoji} KẾT QUẢ THỰC NGHIỆM [{res.experiment_id}] — {res.audit_verdict}")
        print("-" * 65)
        print(f"• Giả thuyết: {res.hypothesis.title}")
        print(f"• Chiến lược: {res.hypothesis.proposed_strategy}")
        print(f"• Tham số: {res.hypothesis.parameters}")
        print(f"• Sharpe Ratio: {res.sharpe_ratio} | Calmar: {res.calmar_ratio} | Win Rate: {res.win_rate}%")
        print(f"• Max Drawdown: {res.max_drawdown_pct}% | Profit Factor: {res.profit_factor}")
        print(f"• Stress Tests (Flash Crash, Vol Spike, Funding): {'ĐẠT (PASSED)' if res.passed_stress_tests else 'THẤT BẠI'}")
        print(f"• Đánh giá Reviewer: {res.reviewer_notes}")
        print("-" * 65 + "\n")

    if args.notify_telegram and results:
        bus = EventBus()
        notifier = TelegramNotifier(bus)
        if notifier.enabled:
            latest = results[-1]
            verdict_icon = "🟢" if latest.audit_verdict == "APPROVED" else "🟡"
            caption = (
                f"🔬 *[DIGITAL RESEARCH LAB] BÁO CÁO THỰC NGHIỆM CHIẾN LƯỢC*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 *Tài sản*: `{latest.hypothesis.target_symbol}` | *Mã*: `{latest.experiment_id}`\n"
                f"💡 *Giả thuyết*: `{latest.hypothesis.title}`\n"
                f"📈 *Kết quả định lượng*:\n"
                f"• Sharpe Ratio: `{latest.sharpe_ratio}` | Win Rate: `{latest.win_rate}%`\n"
                f"• Max Drawdown: `{latest.max_drawdown_pct}%` | Calmar: `{latest.calmar_ratio}`\n"
                f"🛡️ *Stress Tests*: `{'VƯỢT QUA 4/4 KỊCH BẢN' if latest.passed_stress_tests else 'CẦN HIỆU CHỈNH'}`\n"
                f"⚖️ *Phán quyết Lead Reviewer*: {verdict_icon} *{latest.audit_verdict}*\n"
                f"_{latest.reviewer_notes[:180]}..._\n"
            )
            await notifier.send_message(caption)
            logger.info("Dispatched research experiment summary to Telegram.")


if __name__ == "__main__":
    asyncio.run(main())
