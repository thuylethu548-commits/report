import sqlite3
from datetime import datetime, timezone

def run():
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()

    # 1. Add columns to users if missing
    columns = [
        ('registration_ip', "TEXT DEFAULT '113.161.72.18'"),
        ('last_login_ip', "TEXT DEFAULT '113.161.72.18'"),
        ('last_active_at', 'TEXT'),
        ('device_info', "TEXT DEFAULT 'Chrome 128 / Windows 11'"),
        ('risk_flag', "TEXT DEFAULT 'NORMAL'"),
        ('notes', 'TEXT')
    ]
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except Exception:
            pass

    # 2. Update existing users with rich forensic data
    now_str = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        UPDATE users 
        SET registration_ip = '113.161.72.18',
            last_login_ip = '113.161.72.18',
            last_active_at = ?,
            device_info = 'Chrome 128 / Windows 11 (Viettel HCMC)',
            risk_flag = 'NORMAL',
            notes = 'Tài khoản chính chủ Sếp — Master Account'
        WHERE username = 'mtienduc'
    """, (now_str,))

    cursor.execute("""
        UPDATE users 
        SET registration_ip = '14.232.108.92',
            last_login_ip = '14.232.108.92',
            last_active_at = ?,
            device_info = 'Safari 18 / iOS 18 (FPT Telecom Hà Nội)',
            risk_flag = 'NORMAL',
            notes = 'Anh họ Nam — Sao chép toàn phần 100%'
        WHERE username = 'nam123456'
    """, (now_str,))

    cursor.execute("""
        UPDATE users 
        SET registration_ip = '115.78.231.14',
            last_login_ip = '42.118.89.55',
            last_active_at = ?,
            device_info = 'Chrome Mobile 127 / Android 14 (VNPT Đà Nẵng)',
            risk_flag = 'WATCHLIST',
            notes = 'Khách VIP Huy — Vừa đổi IP từ 4G sang Wifi, cần theo dõi'
        WHERE username = 'huy123456'
    """, (now_str,))

    # 3. Seed user_api_credentials for the 3 clients
    cursor.execute("DELETE FROM user_api_credentials")
    cursor.execute("""
        INSERT INTO user_api_credentials (user_id, api_key, api_secret, is_active, label, leverage, max_margin_usdt, profit_share_pct, withdrawals_disabled, created_at)
        VALUES 
        (1, 'vmK89s1Lq72pXo4992Mzk019qLzP1', 's92MkqP0192LskqpWmzk1029Lkqp192', 1, 'Binance VIP Desk (Sếp Đức)', 10, 5000.0, 0.25, 1, ?),
        (2, 'bN72pLz0192MskPwq0192LkqP102', 'w0192MskPq72pLz0192LkqpWmzk102', 1, 'Binance Futures (Anh Họ Nam)', 5, 2500.0, 0.25, 1, ?),
        (3, 'okx_live_920192LskqpWmzk1029', 'okx_sec_0192MskPq72pLz0192Lkqp1', 1, 'OKX Arbitrage (Khách VIP Huy)', 3, 1200.0, 0.25, 1, ?)
    """, (now_str, now_str, now_str))

    # 4. Seed realistic client_trades
    cursor.execute("DELETE FROM client_trades")
    cursor.execute("""
        INSERT INTO client_trades (user_id, order_id, symbol, side, entry_price, exit_price, quantity, notional_value, pnl_usdt, profit_share_due, status, created_at, closed_at)
        VALUES
        (1, 'ord_c1_01', 'BTC/USDT', 'BUY', 81200.0, 82450.0, 0.25, 20300.0, 312.50, 78.12, 'CLOSED', ?, ?),
        (1, 'ord_c1_02', 'ETH/USDT', 'BUY', 2850.0, 2960.0, 2.8, 7980.0, 308.00, 77.00, 'CLOSED', ?, ?),
        (2, 'ord_c2_01', 'BTC/USDT', 'BUY', 81200.0, 82450.0, 0.12, 9744.0, 150.00, 37.50, 'CLOSED', ?, ?),
        (2, 'ord_c2_02', 'SOL/USDT', 'BUY', 165.0, 178.5, 12.0, 1980.0, 162.00, 40.50, 'CLOSED', ?, ?),
        (3, 'ord_c3_01', 'BTC/USDT', 'BUY', 81200.0, 82450.0, 0.06, 4872.0, 75.00, 18.75, 'CLOSED', ?, ?),
        (3, 'ord_c3_02', 'DOGE/USDT', 'BUY', 0.125, 0.138, 5400.0, 675.0, 70.20, 17.55, 'CLOSED', ?, ?)
    """, (now_str, now_str, now_str, now_str, now_str, now_str, now_str, now_str, now_str, now_str, now_str, now_str))

    # 5. Also sync ai_token_usage with the models from ai-orchestration (GPT-6-Astra, gpt-6-luna, gpt-6-sol, Gemini-3.8-Flash)
    cursor.execute("SELECT count(*) FROM ai_token_usage WHERE model = 'cx/gpt-6-astra'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO ai_token_usage (timestamp, model, action, prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd)
            VALUES 
            (?, 'cx/gpt-6-astra', 'Lead PM Reasoning & Arbiter', 18450, 4200, 22650, 0.0453),
            (?, 'cx/gpt-6-luna', 'GuRouter Tier 4 Test', 14200, 3100, 17300, 0.0173),
            (?, 'gemini-3.8-flash', 'Google 1M Context Reasoning', 21500, 5200, 26700, 0.0267)
        """, (now_str, now_str, now_str))

    conn.commit()
    conn.close()
    print("SUCCESS: Seeded client forensic audit and synced AI token usage!")

if __name__ == '__main__':
    run()
