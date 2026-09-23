import asyncio
import sys
sys.path.insert(0, '.')
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from data.storage import Database
from config.settings import settings
import ccxt.async_support as ccxt

async def run_audit():
    db = Database('trading_bot.db')
    await db.connect()

    print("======================================================================")
    print("           ASTRA QUANT DESK — BÁO CÁO AUDIT TOÀN DIỆN HỆ THỐNG        ")
    print("======================================================================")
    
    async with db._conn.cursor() as cur:
        # 1. Total Metrics
        await cur.execute('SELECT COUNT(*) FROM trades')
        total_trades = (await cur.fetchone())[0]
        
        await cur.execute('SELECT COUNT(*) FROM signals')
        total_signals = (await cur.fetchone())[0]
        
        await cur.execute('SELECT COUNT(*) FROM ai_advisory_logs')
        total_vetoes = (await cur.fetchone())[0]
        
        await cur.execute('SELECT COUNT(*) FROM trading_lessons')
        total_lessons = (await cur.fetchone())[0]
        
        await cur.execute('SELECT COUNT(*) FROM ai_token_usage')
        total_tokens = (await cur.fetchone())[0]

        await cur.execute('SELECT COUNT(*) FROM candles')
        total_candles = (await cur.fetchone())[0]
        
        print(f"\n[1] THỐNG KÊ KHO DỮ LIỆU SQLITE (DATABASE TELEMETRY):")
        print(f"    - Tổng số lệnh đã ghi nhận (Trades): {total_trades}")
        print(f"    - Tổng tín hiệu chiến lược sinh ra (Signals): {total_signals}")
        print(f"    - Nhật ký Cố Vấn AI thẩm định (Advisory/Veto Logs): {total_vetoes}")
        print(f"    - Bài học xương máu tích lũy (Lessons Learned): {total_lessons}")
        print(f"    - Số bản ghi giám sát Token AI: {total_tokens}")
        print(f"    - Số nến lịch sử đa khung đang lưu (Candles): {total_candles:,}")

        # 2. Latest Signals
        print(f"\n[2] TÍN HIỆU CHIẾN LƯỢC KỸ THUẬT GẦN NHẤT (SIGNALS):")
        await cur.execute('SELECT id, timestamp, symbol, strategy_name, side, price, approved, rejection_reason FROM signals ORDER BY timestamp DESC LIMIT 6')
        signals = await cur.fetchall()
        if signals:
            for s in signals:
                status_str = "[ĐÃ DUYỆT]" if s[6] else f"[TỪ CHỐI: {s[7] or 'N/A'}]"
                print(f"    * [{s[1]}] {s[2]:<10} | Phe: {s[4]:<4} @ ${s[5]:,.2f} | Chiến lược: {s[3]:<18} | {status_str}")
        else:
            print("    * Chưa có tín hiệu thô nào được kích hoạt gần đây.")

        # 3. AI Gatekeeper Decisions
        print(f"\n[3] QUYẾT ĐỊNH CỐ VẤN TỐI CAO AI (AI GATEKEEPER & VETO ENGINE):")
        await cur.execute('SELECT id, timestamp, symbol, regime, risk_score, trade_allowed, size_multiplier, reasoning, confidence FROM ai_advisory_logs ORDER BY timestamp DESC LIMIT 5')
        vetoes = await cur.fetchall()
        if vetoes:
            for v in vetoes:
                tag = "[CHẤP THUẬN/APPROVED]" if v[5] == 1 else "[PHỦ QUYẾT/VETO]"
                print(f"    * [{v[1]}] {v[2]:<10} -> {tag} | Regime: {v[3]} | Risk Score: {v[4]}/100 | Confidence: {v[8]*100:.0f}% | Size: {v[6]}x")
                print(f"      Nhận định vĩ mô: {v[7]}")
        else:
            print("    * Chưa có log phân tích AI nào gần đây.")

        # 4. Trades Ledger
        print(f"\n[4] SỔ LỆNH GIAO DỊCH THỰC CHIẾN (TRADES LEDGER - CẢ SPOT & FUTURES):")
        await cur.execute('SELECT order_id, entry_time, symbol, side, strategy_name, entry_price, exit_price, quantity, pnl_usdt, status, is_paper FROM trades ORDER BY entry_time DESC LIMIT 8')
        trades = await cur.fetchall()
        if trades:
            for t in trades:
                pnl_val = float(t[8] or 0.0)
                pnl_str = f"+{pnl_val:.4f} USDT" if pnl_val >= 0 else f"{pnl_val:.4f} USDT"
                mode_str = "PAPER" if t[10] else "LIVE REAL"
                exit_p = f"${t[6]:,.2f}" if t[6] else "ĐANG MỞ"
                print(f"    * [{t[1]}] {t[2]:<12} {t[3]:<4} | Qty: {t[7]} @ ${t[5]:,.2f} -> {exit_p} | PnL: {pnl_str:<12} | {t[9]} ({mode_str})")
        else:
            print("    * Chưa có lệnh nào trong lịch sử.")

        # 5. Trading Lessons
        print(f"\n[5] BÀI HỌC XƯƠNG MÁU & QUẢN TRỊ RỦI RO (AUTO POST-MORTEM LESSONS):")
        await cur.execute('SELECT id, timestamp, category, title, capital_impact, lesson_learned FROM trading_lessons ORDER BY timestamp DESC LIMIT 3')
        lessons = await cur.fetchall()
        if lessons:
            for l in lessons:
                impact = f"-{l[4]:.2f} USDT" if l[4] else "Bảo vệ an toàn"
                print(f"    * [{l[1]}] Danh mục: {l[2]} | Tiêu đề: {l[3]} (Tác động vốn: {impact})")
                print(f"      Bài học cốt lõi: {l[5]}")
        else:
            print("    * Không có bài học hoặc sự cố nào.")

    await db.close()

    # 6. Live Binance Account & Positions Audit
    print(f"\n[6] TRẠNG THÁI SÀN BINANCE THỰC TẾ (FUTURES & SPOT):")
    exchange = ccxt.binance({
        "apiKey": settings.BINANCE_API_KEY,
        "secret": settings.BINANCE_API_SECRET,
        "enableRateLimit": True,
        "options": {"defaultType": "future"}
    })
    try:
        positions = await exchange.fetch_positions(["BTC/USDT:USDT"])
        active_pos = [p for p in positions if float(p.get("contracts", 0) or 0) > 0]
        print(f"    - [FUTURES] Vị thế đang mở: {len(active_pos)}")
        for p in active_pos:
            entry = float(p.get("entryPrice", 0))
            mark = float(p.get("markPrice", 0))
            pnl = float(p.get("unrealizedPnl", 0))
            roi = ((mark - entry) / entry * 100 * float(p.get("leverage", 1))) if entry > 0 and p.get("side") == "long" else 0.0
            print(f"      * Cặp: {p['symbol']} | Chiều: {p['side'].upper()} | Khối lượng: {p['contracts']} BTC (Đòn bẩy: {p.get('leverage')}x)")
            print(f"      * Entry Price: ${entry:,.2f} | Mark Price: ${mark:,.2f}")
            print(f"      * Unrealized PnL: {pnl:+.4f} USDT (ROI: {roi:+.2f}%)")
            liq_p = p.get('liquidationPrice')
            liq_str = f"${float(liq_p):,.2f}" if liq_p is not None else "Không áp dụng (An toàn cao / Isolated Margin thấp)"
            print(f"      * Giá thanh lý (Liq Price): {liq_str}")

        balance = await exchange.fetch_balance()
        usdt_free = float(balance.get("USDT", {}).get("free") or 0)
        usdt_total = float(balance.get("USDT", {}).get("total") or 0)
        print(f"    - [FUTURES] Số dư ký quỹ: Tổng {usdt_total:.4f} USDT | Khả dụng vào lệnh: {usdt_free:.4f} USDT")
    except Exception as e:
        print(f"    - Lỗi truy vấn Binance Futures: {e}")
    finally:
        await exchange.close()

    # Spot check
    spot_exchange = ccxt.binance({
        "apiKey": settings.BINANCE_API_KEY,
        "secret": settings.BINANCE_API_SECRET,
        "enableRateLimit": True,
        "options": {"defaultType": "spot"}
    })
    try:
        spot_bal = await spot_exchange.fetch_balance()
        spot_usdt = float(spot_bal.get("USDT", {}).get("free") or 0)
        spot_btc = float(spot_bal.get("BTC", {}).get("total") or 0)
        spot_bnb = float(spot_bal.get("BNB", {}).get("total") or 0)
        print(f"    - [SPOT] Tài sản ví Spot: {spot_usdt:.4f} USDT | {spot_btc:.6f} BTC | {spot_bnb:.4f} BNB")
    except Exception as e:
        print(f"    - Lỗi truy vấn Binance Spot: {e}")
    finally:
        await spot_exchange.close()

    print("\n======================================================================")
    print("                     KẾT THÚC BÁO CÁO AUDIT                           ")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(run_audit())
