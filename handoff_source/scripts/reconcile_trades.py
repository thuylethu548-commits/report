import sqlite3
from datetime import datetime, timezone

def reconcile():
    conn = sqlite3.connect('trading_bot.db')
    c = conn.cursor()
    
    # 1. Update SOL trade
    c.execute("""
        UPDATE trades 
        SET status = 'CLOSED',
            exit_price = 119.15,
            exit_time = '2026-09-23T05:03:08.062000+00:00',
            pnl_usdt = 0.1512,
            pnl_percent = 1.61
        WHERE order_id = 'adopt-SOLUSDT-1790091046'
    """)
    print("Updated SOL trade:", c.rowcount)
    
    # 2. Update 1000PEPE trade
    c.execute("""
        UPDATE trades 
        SET status = 'CLOSED',
            exit_price = 0.0050073,
            exit_time = '2026-09-23T05:03:49.061000+00:00',
            pnl_usdt = 0.3398,
            pnl_percent = 2.73
        WHERE order_id = 'adopt-1000PEPEUSDT-1790128844'
    """)
    print("Updated 1000PEPE trade:", c.rowcount)
    
    conn.commit()
    
    # Check remaining open trades
    rows = list(c.execute("SELECT order_id, symbol, status FROM trades WHERE status = 'OPEN'"))
    print("Remaining OPEN trades in DB:", rows)
    
    conn.close()

if __name__ == '__main__':
    reconcile()
