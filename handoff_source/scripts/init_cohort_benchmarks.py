#!/usr/bin/env python3
"""
ASTRA QUANT DESK — A/B COHORT BENCHMARK INITIALIZER
Sets up the comparison between Batch 1 (First 10 Trades Baseline) and
Batch 2 (Next 10 Trades under Grok 4.7 & GPT-6 Astra VaR Council).
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "trading_bot.db"

def init_cohorts():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS trade_cohort_benchmarks (
        cohort_id TEXT PRIMARY KEY,
        cohort_name TEXT NOT NULL,
        total_trades INTEGER DEFAULT 0,
        win_trades INTEGER DEFAULT 0,
        loss_trades INTEGER DEFAULT 0,
        win_rate REAL DEFAULT 0.0,
        realized_pnl_usdt REAL DEFAULT 0.0,
        max_drawdown_pct REAL DEFAULT 0.0,
        ai_veto_count INTEGER DEFAULT 0,
        description TEXT,
        status TEXT DEFAULT 'ACTIVE_IN_PROGRESS',
        updated_at TEXT NOT NULL
    )
    """)

    now_iso = datetime.now(timezone.utc).isoformat()

    # Seed BATCH_1_BASELINE
    cur.execute("""
    INSERT OR REPLACE INTO trade_cohort_benchmarks (
        cohort_id, cohort_name, total_trades, win_trades, loss_trades,
        win_rate, realized_pnl_usdt, max_drawdown_pct, ai_veto_count,
        description, status, updated_at
    ) VALUES (
        'BATCH_1_BASELINE',
        '10 Lenh Dau Tien (Baseline Giai Doan 1)',
        10, 7, 3,
        0.70, 3.84, 0.08, 14,
        'Mo hinh Sonnet/Consensus truyen thong. Ty le thang 70%, PnL +$3.84 USDT.',
        'COMPLETED',
        ?
    )
    """, (now_iso,))

    # Seed BATCH_2_GROK_GPT6
    cur.execute("""
    INSERT OR REPLACE INTO trade_cohort_benchmarks (
        cohort_id, cohort_name, total_trades, win_trades, loss_trades,
        win_rate, realized_pnl_usdt, max_drawdown_pct, ai_veto_count,
        description, status, updated_at
    ) VALUES (
        'BATCH_2_GROK_GPT6',
        '10 Lenh Tiep Theo (Hoi Dong VaR: Grok 4.7 & GPT-6 Astra)',
        0, 0, 0,
        0.0, 0.0, 0.0, 0,
        'Ky nguyen moi: Bull (gpt-oss-120b) vs Bear (Grok 4.7) vs Dong Trong Tai (GPT-6 Astra & Grok 4.7).',
        'ACTIVE_IN_PROGRESS',
        ?
    )
    """, (now_iso,))

    conn.commit()
    conn.close()
    print("Successfully initialized trade_cohort_benchmarks table and cohorts.")

if __name__ == "__main__":
    init_cohorts()
