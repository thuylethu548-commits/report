import sqlite3

conn = sqlite3.connect('trading_bot.db')
c = conn.cursor()
rows = list(c.execute("SELECT order_id, symbol, side, entry_price, exit_price, pnl_usdt, status, entry_time, exit_time FROM trades WHERE status = 'OPEN'"))
for r in rows:
    print(r)
conn.close()
