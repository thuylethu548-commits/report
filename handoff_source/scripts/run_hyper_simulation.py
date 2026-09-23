#!/usr/bin/env python3
"""
ASTRA QUANT — HYPER-ACCELERATED VIRTUAL SIMULATION RUNNER & MARKET ORACLE
-------------------------------------------------------------------------
Executes time-warped Monte Carlo simulations (up to 100,000+ branches at 10,000x speed)
and synthesizes long-horizon 5 - 20 year institutional macroeconomic prophecies.
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
from core.hyper_simulation_world import TimeWarpEngine, MarketOracleEngine
from monitoring.telegram_bot import TelegramNotifier
from core.event_bus import EventBus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("HyperSimulationRunner")


async def main():
    parser = argparse.ArgumentParser(description="Run Hyper-Accelerated Virtual Simulation & Market Oracle")
    parser.add_argument("--scenarios", type=int, default=10000, help="Number of Monte Carlo scenarios (e.g. 10000, 100000)")
    parser.add_argument("--speed", type=int, default=5000, help="Time warp multiplier (e.g. 1000, 5000, 10000)")
    parser.add_argument("--oracle", action="store_true", help="Execute 5-20 Year Deep Thinking Market Oracle")
    parser.add_argument("--asset", default="BTC", help="Focus asset for Market Oracle")
    parser.add_argument("--notify-telegram", action="store_true", help="Send simulation results and prophecy to Telegram")
    args = parser.parse_args()

    engine = TimeWarpEngine()

    print("\n" + "=" * 65)
    print("⏳ ASTRA QUANT — KHỞI CHẠY THẾ GIỚI ẢO SIÊU GIA TỐC (TIME WARP)")
    print("=" * 65)
    print(f"• Số nhánh kịch bản: {args.scenarios:,} cases")
    print(f"• Tốc độ gia tốc thời gian: {args.speed:,}x (1 giây thực = {args.speed} giây ảo)")
    print(f"• 12 Tác tử tham chiến: Astra, Rik, Hash, Prof, Palermo, Tory, Volt, Meme...")
    print("=" * 65 + "\n")

    # Run Monte Carlo Time Warp
    sim_summary = engine.run_simulation(total_scenarios=args.scenarios, time_warp_factor=args.speed)

    print("\n" + "-" * 65)
    print("📊 BẢNG XẾP HẠNG TIẾN HOÁ TÁC TỬ (AGENT EVOLUTION LEADERBOARD)")
    print("-" * 65)
    print(f"{'Tác tử':<10} {'Vai trò':<24} {'Level':<8} {'EXP':<8} {'Win Rate':<10} {'Lợi nhuận ($)':<12}")
    print("-" * 65)
    for a in sim_summary["agent_leaderboard"]:
        print(f"{a['name']:<10} {a['role'][:22]:<24} Lvl {a['level']:<4} {a['exp']:<8} {a['win_rate']:<10} ${a['profit_usd']:<12,}")
    print("-" * 65)
    print(f"• Tổng kịch bản: {sim_summary['total_scenarios']:,} | Thời gian giả lập: {sim_summary['simulated_market_days']} ngày")
    print(f"• Lệnh duyệt: {sim_summary['total_approved']:,} | Lệnh VETO: {sim_summary['total_vetoed']:,} ({sim_summary['veto_rate']})")
    print(f"• Net PnL ảo sinh ra: ${sim_summary['net_simulated_pnl_usd']:,.2f}")
    print(f"• Lưu trữ Data Lake: {sim_summary['parquet_file']}")
    print("-" * 65 + "\n")

    oracle_res = None
    if args.oracle:
        print("\n" + "=" * 65)
        print(f"🔮 VIỆN TIÊN TRI THỊ TRƯỜNG — TẦM NHÌN VĨ MÔ 5 - 10 - 15 - 20 NĂM ({args.asset})")
        print("=" * 65)
        oracle = MarketOracleEngine()
        oracle_res = await oracle.generate_deep_thinking_prophecy(focus_asset=args.asset, use_live_ai=True)

        scenarios = oracle_res.get("probabilistic_scenarios", {})
        print(f"• Xác suất kịch bản: Base Case {scenarios.get('base_case_prob', 0)*100:.0f}% | Supercycle {scenarios.get('supercycle_prob', 0)*100:.0f}% | Stagnation {scenarios.get('secular_stagnation_prob', 0)*100:.0f}%")
        print(f"\n[5 NĂM]: {oracle_res.get('horizon_5y', {}).get('projected_price_range')}")
        print(f"  Động lực: {', '.join(oracle_res.get('horizon_5y', {}).get('core_catalysts', []))}")

        print(f"\n[10 NĂM]: {oracle_res.get('horizon_10y', {}).get('projected_price_range')}")
        print(f"  Chuyển dịch: {oracle_res.get('horizon_10y', {}).get('structural_shift')}")

        print(f"\n[15 NĂM]: {oracle_res.get('horizon_15y', {}).get('projected_price_range')}")
        print(f"  Chuyển dịch: {oracle_res.get('horizon_15y', {}).get('structural_shift')}")

        print(f"\n[20 NĂM]: {oracle_res.get('horizon_20y', {}).get('projected_price_range')}")
        print(f"  Tầm nhìn tối hậu: {oracle_res.get('horizon_20y', {}).get('vision')}")
        print(f"  Triết lý cốt lõi: {oracle_res.get('horizon_20y', {}).get('philosophical_takeaway')}")

        print("\n" + "-" * 65)
        print("📝 TỔNG KẾT CHIẾN LƯỢC:")
        print(oracle_res.get("oracle_summary"))
        print("=" * 65 + "\n")

    if args.notify_telegram:
        bus = EventBus()
        notifier = TelegramNotifier(bus)
        if notifier.enabled:
            top_agents = sorted(sim_summary["agent_leaderboard"], key=lambda x: x["level"], reverse=True)[:3]
            top_str = "\n".join([f"• *{a['name']}* ({a['role'][:16]}): `Lvl {a['level']} (EXP {a['exp']})` - Win: `{a['win_rate']}`" for a in top_agents])

            msg = (
                f"⏳ *[THẾ GIỚI ẢO SIÊU GIA TỐC] BÁO CÁO TIẾN HOÁ TÁC TỬ*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🚀 *Gia tốc*: `{sim_summary['time_warp_factor']}` | *Thời gian ảo*: `{sim_summary['simulated_market_days']} ngày`\n"
                f"📊 *Kịch bản kiểm thử*: `{sim_summary['total_scenarios']:,} nhánh Monte Carlo`\n"
                f"🎯 *Tỷ lệ Veto*: `{sim_summary['veto_rate']}` ({sim_summary['total_vetoed']:,} bẫy bị chặn đứng)\n"
                f"💰 *Lợi nhuận ảo sinh ra*: `+${sim_summary['net_simulated_pnl_usd']:,.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 *Top Tác Tử Tiến Hoá Nhanh Nhất*:\n{top_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💾 *Data Lake Parquet*: `{os.path.basename(sim_summary['parquet_file'])}`\n"
            )
            if oracle_res:
                msg += (
                    f"\n🔮 *TIÊN TRI VĨ MÔ 5 - 20 NĂM ({args.asset})*:\n"
                    f"• 5Y: `{oracle_res.get('horizon_5y', {}).get('projected_price_range')}`\n"
                    f"• 10Y: `{oracle_res.get('horizon_10y', {}).get('projected_price_range')}`\n"
                    f"• 20Y: `{oracle_res.get('horizon_20y', {}).get('projected_price_range')}`\n"
                    f"_{oracle_res.get('oracle_summary')[:180]}..._\n"
                )
            await notifier.send_message(msg)
            logger.info("Dispatched Virtual World Simulation report to Telegram.")


if __name__ == "__main__":
    asyncio.run(main())
