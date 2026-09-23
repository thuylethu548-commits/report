import sqlite3
import urllib.request
import json
from datetime import datetime, timezone

def audit_database():
    conn = sqlite3.connect('trading_bot.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    print("=== 1. AUDIT DATABASE TRADES (TODAY: 2026-09-22) ===")
    c.execute("SELECT order_id, symbol, side, entry_price, exit_price, pnl_usdt, status, entry_time, exit_time FROM trades WHERE entry_time LIKE '2026-09-22%' OR exit_time LIKE '2026-09-22%'")
    trades_today = [dict(r) for r in c.fetchall()]
    print(f"Total trades recorded today: {len(trades_today)}")
    today_pnl = sum(t.get('pnl_usdt') or 0.0 for t in trades_today if t.get('status') == 'CLOSED')
    print(f"Realized PnL today: ${today_pnl:.4f} USDT")
    for t in trades_today:
        print("  -", t)

    print("\n=== 2. AUDIT RECENT SIGNALS (TODAY: 2026-09-22) ===")
    c.execute("SELECT id, strategy_name, symbol, side, price, stop_loss, take_profit, confidence, approved, rejection_reason, timestamp FROM signals WHERE timestamp LIKE '2026-09-22%' ORDER BY id DESC LIMIT 15")
    signals_today = [dict(r) for r in c.fetchall()]
    print(f"Total signals generated today: {len(signals_today)}")
    for s in signals_today:
        print("  -", s)

    print("\n=== 3. AUDIT ALL-TIME METRICS ===")
    c.execute("SELECT COUNT(*), SUM(pnl_usdt) FROM trades WHERE status='CLOSED'")
    total_closed, total_pnl = c.fetchone()
    print(f"All-time closed trades: {total_closed}, All-time PnL: ${total_pnl or 0.0:.4f} USDT")

def audit_running_system():
    print("\n=== 4. AUDIT RUNNING BOT STATUS & CIRCUIT BREAKER ===")
    try:
        res = urllib.request.urlopen('http://localhost:8386/api/v1/status', timeout=5)
        data = json.loads(res.read().decode('utf-8'))
        print(f"Trading Mode: {data.get('trading_mode')}")
        print(f"Balance USDT: ${data.get('balance_usdt')}")
        print(f"Equity USDT: ${data.get('equity_usdt')}")
        print(f"Circuit Breaker Tripped: {data.get('circuit_breaker_tripped')}")
        print(f"Trip Reason: {data.get('trip_reason')}")
        print(f"Open Positions count: {len(data.get('open_positions', []))}")
        for p in data.get('open_positions', []):
            print("  Pos:", p)
        print(f"Active Symbols: {data.get('symbols')}")
        print(f"Auto Trade Enabled: {data.get('auto_trade_enabled')}")
        print(f"AI Advisory Enabled: {data.get('ai_advisory_enabled')}")
        print(f"Multi-Timeframe Enabled: {data.get('multi_timeframe_enabled')}")
    except Exception as e:
        print(f"Could not connect to /api/v1/status: {e}")

if __name__ == "__main__":
    audit_database()
    audit_running_system()
