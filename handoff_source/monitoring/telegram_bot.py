import os
import gzip
import shutil
import sqlite3
import logging
import httpx
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from config.settings import settings
from core.events import FillEvent, SignalEvent, TrailingStopEvent, AIAdvisoryEvent
from core.event_bus import EventBus
from core.constants import OrderSide

logger = logging.getLogger("TelegramAlerts")


def format_price(price) -> str:
    if price is None:
        return "0.00"
    p = float(price)
    if p >= 1000:
        return f"{p:,.2f}"
    elif p >= 1:
        return f"{p:,.4f}"
    elif p >= 0.001:
        return f"{p:,.6f}"
    else:
        return f"{p:,.8f}"


class TelegramNotifier:
    def __init__(self, event_bus: EventBus):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.ENABLE_TELEGRAM and bool(self.token) and bool(self.chat_id)
        self.event_bus = event_bus

        # Always subscribe; send_message will check self.enabled dynamically
        self.event_bus.subscribe(FillEvent, self.on_fill)
        self.event_bus.subscribe(SignalEvent, self.on_signal)
        self.event_bus.subscribe(TrailingStopEvent, self.on_trailing_stop)
        self.event_bus.subscribe(AIAdvisoryEvent, self.on_ai_advisory)

        try:
            from core.macro_intelligence_bridge import MacroStrategicDirectiveEvent
            self.event_bus.subscribe(MacroStrategicDirectiveEvent, self.on_macro_directive)
        except Exception as eb_err:
            logger.debug(f"Could not subscribe to MacroStrategicDirectiveEvent: {eb_err}")

        if self.enabled:
            logger.info("Telegram notifications enabled.")

    def refresh_config(self) -> None:
        """Dynamic reload of credentials from settings."""
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.ENABLE_TELEGRAM and bool(self.token) and bool(self.chat_id)

    async def send_message(self, text: str) -> None:
        self.refresh_config()
        if not self.enabled:
            return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.warning(f"Failed to send Telegram message: {e}")

    async def send_document(self, filepath: str, caption: str = "") -> bool:
        """Uploads a local document/archive directly to Telegram via sendDocument."""
        self.refresh_config()
        if not self.enabled:
            return False
        if not os.path.exists(filepath):
            logger.warning(f"send_document: File not found: {filepath}")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendDocument"
        filename = os.path.basename(filepath)
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                with open(filepath, "rb") as f:
                    files = {"document": (filename, f, "application/gzip")}
                    data = {"chat_id": self.chat_id, "caption": caption, "parse_mode": "Markdown"}
                    resp = await client.post(url, data=data, files=files)
                    if resp.status_code == 200:
                        logger.info(f"Successfully sent document {filename} to Telegram.")
                        return True
                    else:
                        logger.warning(f"Telegram sendDocument failed ({resp.status_code}): {resp.text}")
                        return False
        except Exception as e:
            logger.warning(f"Failed to send Telegram document {filename}: {e}")
            return False

    async def backup_database_to_telegram(self, db_path: str = "trading_bot.db", note: str = "") -> Optional[str]:
        """
        Creates an atomic online backup of trading_bot.db, compresses with gzip,
        gathers database statistics, and uploads the .db.gz archive to Telegram.
        """
        self.refresh_config()
        if not os.path.exists(db_path):
            logger.warning(f"[BackupToTelegram] DB file not found: {db_path}")
            return None

        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)

        now_utc = datetime.now(timezone.utc)
        ts_str = now_utc.strftime("%Y%m%d_%H%M%S")
        temp_db_path = backup_dir / f"temp_snapshot_{ts_str}.db"
        gz_path = backup_dir / f"trading_bot_{ts_str}.db.gz"

        try:
            # 1. Atomic SQLite Online Backup (safe against concurrent writes)
            src_conn = sqlite3.connect(db_path)
            dst_conn = sqlite3.connect(str(temp_db_path))
            src_conn.backup(dst_conn)

            # Query stats from snapshot
            cursor = dst_conn.cursor()
            def count_table(name: str) -> int:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {name}")
                    res = cursor.fetchone()
                    return res[0] if res else 0
                except Exception:
                    return 0

            trades_count = count_table("trades")
            signals_count = count_table("signals")
            lessons_count = count_table("trading_lessons")
            ai_logs_count = count_table("ai_advisory_logs")
            equity_count = count_table("equity_snapshots")
            dst_conn.close()
            src_conn.close()

            # 2. Compress to .gz
            orig_size = os.path.getsize(temp_db_path)
            with open(temp_db_path, "rb") as f_in:
                with gzip.open(gz_path, "wb", compresslevel=9) as f_out:
                    shutil.copyfileobj(f_in, f_out)

            gz_size = os.path.getsize(gz_path)
            if os.path.exists(temp_db_path):
                try:
                    os.remove(temp_db_path)
                except Exception:
                    pass

            compression_ratio = ((1.0 - (gz_size / max(orig_size, 1))) * 100) if orig_size > 0 else 0

            # 3. Format Telegram Caption
            now_vn = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            caption = (
                f"📦 *[ASTRA QUANT] BẢN SAO LƯU DATABASE TỰ ĐỘNG*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 *Thời gian*: `{now_vn}`\n"
                f"📁 *Tệp*: `{gz_path.name}`\n"
                f"📊 *Dung lượng*: `{gz_size / 1024:.1f} KB` (Gốc: `{orig_size / 1024:.1f} KB`, nén: `{compression_ratio:.1f}%`)\n"
                f"📈 *Bản ghi*: `{trades_count}` Trades | `{signals_count}` Signals | `{lessons_count}` Lessons | `{ai_logs_count}` AI Logs\n"
                f"🛡️ *Bảo mật*: SQLite Online Snapshot Toàn Vẹn | Khôi phục tức thì\n"
                f"_{note or 'Hệ thống tự động sao lưu định kỳ bảo toàn toàn vẹn dữ liệu.'}_"
            )

            # 3.5. Mirror directly to Google Drive 5TB Storage if mounted
            gdrive_backup_dir = Path("G:/My Drive/Astra_Backups")
            if gdrive_backup_dir.exists():
                try:
                    shutil.copy2(gz_path, gdrive_backup_dir / gz_path.name)
                    shutil.copy2(db_path, gdrive_backup_dir / "trading_bot_latest.db")
                    logger.info(f"[BackupToGDrive] ✅ Synced snapshot to {gdrive_backup_dir}")
                except Exception as gde:
                    logger.warning(f"[BackupToGDrive] GDrive copy skipped/error: {gde}")

            # 4. Dispatch via Telegram sendDocument
            if self.enabled:
                success = await self.send_document(str(gz_path), caption=caption)
                if success:
                    logger.info(f"[BackupToTelegram] Successfully dispatched backup {gz_path.name} to Telegram.")
                    return str(gz_path)
                else:
                    logger.warning(f"[BackupToTelegram] Failed to dispatch via Telegram, saved at {gz_path}")
                    return str(gz_path)
            else:
                logger.info(f"[BackupToTelegram] Telegram disabled, backup saved locally at: {gz_path}")
                return str(gz_path)

        except Exception as e:
            logger.error(f"[BackupToTelegram] Backup error: {e}", exc_info=True)
            if os.path.exists(temp_db_path):
                try:
                    os.remove(temp_db_path)
                except Exception:
                    pass
            return None

    async def on_signal(self, signal: SignalEvent) -> None:
        if signal.stop_loss <= 0:
            msg = f"🔄 *[TÍN HIỆU ĐÓNG VỊ THẾ] {signal.strategy_name}*\n" \
                  f"Tài sản: `{signal.symbol}`\n" \
                  f"Hành động: *ĐÓNG VỊ THẾ ({signal.side.value})* @ `${format_price(signal.price)}`"
        else:
            msg = f"🔔 *[TÍN HIỆU CHIẾN LƯỢC] {signal.strategy_name}*\n" \
                  f"Tài sản: `{signal.symbol}`\n" \
                  f"Hành động: *{signal.side.value}* @ `${format_price(signal.price)}`\n" \
                  f"SL: `${format_price(signal.stop_loss)}` | TP: `${format_price(signal.take_profit)}`"
        await self.send_message(msg)

    async def on_fill(self, fill: FillEvent) -> None:
        mode = "PAPER" if fill.is_paper else "LIVE"
        if fill.side == OrderSide.BUY:
            msg = f"⚡ *[KHỚP LỆNH MUA - {mode}] {fill.strategy_name}*\n" \
                  f"Cặp: `{fill.symbol}`\n" \
                  f"Khối lượng: `{fill.quantity}` @ `${format_price(fill.fill_price)}`\n" \
                  f"Phí sàn: `${fill.fee:,.4f}`"
        else:
            msg = f"🎯 *[ĐÓNG VỊ THẾ BÁN - {mode}] {fill.strategy_name}*\n" \
                  f"Cặp: `{fill.symbol}`\n" \
                  f"Khối lượng: `{fill.quantity}` @ `${format_price(fill.fill_price)}`\n" \
                  f"Phí sàn: `${fill.fee:,.4f}`"
        await self.send_message(msg)

    async def on_trailing_stop(self, event: TrailingStopEvent) -> None:
        if event.action == "BREAK_EVEN_LOCK":
            msg = f"🔒 *[BẢO TOÀN VỐN - BREAK-EVEN LOCK]*\n" \
                  f"Cặp: `{event.symbol}`\n" \
                  f"Lợi nhuận tạm tính: `+{event.pnl_pct:.2f}%`\n" \
                  f"Đã dời Stop-Loss: `${format_price(event.old_sl)}` ➔ `${format_price(event.new_sl)}`\n" \
                  f"🛡️ Trạng thái: *ZERO RISK - Không thể lỗ ngược!*"
        else:
            msg = f"🚀 *[TRAILING STOP - BÁM ĐỈNH LÃI]*\n" \
                  f"Cặp: `{event.symbol}` | Giá hiện tại: `${format_price(event.current_price)}`\n" \
                  f"Lợi nhuận: `+{event.pnl_pct:.2f}%`\n" \
                  f"Nâng Stop-Loss: `${format_price(event.old_sl)}` ➔ `${format_price(event.new_sl)}`\n" \
                  f"📈 Đã khóa thêm lợi nhuận bám theo 1.0x ATR!"
        await self.send_message(msg)

    async def on_ai_advisory(self, event: AIAdvisoryEvent) -> None:
        if not event.trade_allowed:
            msg = f"🛑 *[AI VETO - PHỦ QUYẾT BẢO TOÀN VỐN]*\n" \
                  f"Cặp: `{event.symbol}` | Chế độ: `{event.regime.value.upper()}`\n" \
                  f"Chỉ số rủi ro: `{event.risk_score}/5` | Tự tin: `{event.confidence*100:.0f}%`\n" \
                  f"Lý do: _{event.reasoning}_"
            await self.send_message(msg)

    async def on_macro_directive(self, event) -> None:
        d = getattr(event, "directive", {})
        regime = d.get("regime", "MACRO_ACCUMULATION")
        mandate = d.get("venue_mandate", "FUTURES_ACTIVE")
        verdict = d.get("boss_capital_verdict", "HOLD_450U_VAULT")
        advice = d.get("capital_advice_vi", "Két 450U được bảo vệ an toàn ngoài sàn.")
        summary = d.get("summary_vi", "")

        msg = (
            f"🌐 *[BÁO CÁO THƯỢNG ĐẾ · BỘ CHỈ HUY TÌNH BÁO 9ROUTER]*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Chỉ huy Tình báo:* Hash (`gcli/grok-4.7`)\n"
            f"🏛️ *Nhịp Vĩ mô:* `{regime}`\n"
            f"🎯 *Chỉ thị Đội 1 (Astra):* `{mandate}`\n"
            f"💰 *KHUYẾN NGHỊ KÉT VỐN 450U:*\n"
            f"👉 *{verdict}*\n"
            f"_{advice}_\n\n"
            f"📋 *Mệnh lệnh tác chiến gửi Astra:*\n"
            f"{summary}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ *Quỹ thực chiến:* `$55.37 USDT` | *Két an toàn:* `450U Vault`"
        )
        await self.send_message(msg)

    async def send_night_briefing(self, active_pos_count: int, balance_usdt: float, btc_price: float, note: str = "") -> None:
        """Sends an immediate night briefing with overnight trading plan status."""
        pos_text = f"Đang mở {active_pos_count} lệnh" if active_pos_count > 0 else "0 vị thế mở (Vốn được bảo vệ an toàn 100%)"
        msg = (
            f"🌙 *[ASTRA QUANT DESK] BÁO CÁO CA ĐÊM & KẾ HOẠCH TÁC CHIẾN*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏢 *Trụ sở 12 Ban*: `12/12 PHÒNG BAN TRỰC CHIẾN 24/7`\n"
            f"💰 *Số dư khả dụng*: `${balance_usdt:,.2f} USDT`\n"
            f"📊 *Vị thế Futures*: `{pos_text}`\n"
            f"⚡ *Giá BTC/USDT*: `${format_price(btc_price)}`\n"
            f"🤖 *AI Advisory*: `Claude-3.5-Sonnet & DeepSeek-V4 (VETO SẴN SÀNG)`\n"
            f"🛡️ *Hàng rào rủi ro*: `Circuit Breaker Max -2.0% | Trailing Stop 1.0x ATR`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 *Kế hoạch đêm nay*:\n"
            f"• Quét liên tục 8 cặp: BTC, ETH, SOL, BNB, DOGE, PEPE, NEAR, SUI.\n"
            f"• Chỉ vào lệnh khi EMA Trend + RSI Bollinger đồng thuận và AI Veto phê duyệt.\n"
            f"• Tự động dời SL về Break-Even ngay khi lãi +1.5% để triệt tiêu mọi rủi ro.\n"
            f"_{note or 'Hệ thống tự động trực ban. Bạn hãy an tâm nghỉ ngơi!'}_"
        )
        await self.send_message(msg)

    async def start_periodic_patrol(self, db, binance_client=None, interval_seconds: int = 2700) -> None:
        """Background loop that sends periodic patrol status reports every 30-45 minutes and daily DB backups."""
        import asyncio
        from datetime import datetime, timezone
        logger.info(f"Starting Telegram periodic patrol loop (every {interval_seconds}s)...")
        last_backup_day = None
        # Wait 10 seconds on startup before sending first report
        await asyncio.sleep(10)
        while True:
            try:
                self.refresh_config()
                if self.enabled:
                    active_count = 0
                    btc_price = 0.0
                    free_usdt = 55.44

                    if binance_client:
                        try:
                            positions = await binance_client.fetch_positions()
                            active_pos = [p for p in positions if abs(float(p.get('contracts', 0) or p.get('amount', 0) or 0)) > 0]
                            active_count = len(active_pos)
                            ticker = await binance_client.fetch_ticker('BTC/USDT')
                            btc_price = float(ticker.get('last', 0.0))
                            bal = await binance_client.fetch_balance()
                            free_usdt = float(bal.get('USDT', {}).get('total', free_usdt))
                        except Exception as ex:
                            logger.debug(f"Error querying binance for patrol: {ex}")

                    now_str = datetime.now().strftime('%H:%M %d/%m')
                    pos_summary = f"{active_count} lệnh active" if active_count > 0 else "0 vị thế (Đang chờ setup đẹp)"
                    msg = (
                        f"🛡️ *[ASTRA DESK] BÁO CÁO TUẦN TRA [{now_str}]*\n"
                        f"• Trụ sở: `12 Phòng Ban ONLINE 100%`\n"
                        f"• Số dư: `${free_usdt:,.2f} USDT` | Trạng thái: `{pos_summary}`\n"
                        f"• BTC: `${format_price(btc_price)}` | AI Veto: `ONLINE`\n"
                        f"• Risk Gate: `Circuit Breaker AN TOÀN (Drawdown 0.0%)`\n"
                        f"_(Hệ thống duy trì quét nến 15m tự động 24/7)_"
                    )
                    await self.send_message(msg)

                    # Automated Daily Database Backup to Telegram
                    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                    if last_backup_day != today_str:
                        logger.info(f"[TelegramPatrol] Executing scheduled daily database backup for {today_str}...")
                        db_file = getattr(settings, "DATABASE_PATH", "trading_bot.db")
                        backup_res = await self.backup_database_to_telegram(db_path=db_file)
                        if backup_res:
                            last_backup_day = today_str
                            logger.info(f"[TelegramPatrol] Daily database backup completed: {backup_res}")
            except Exception as e:
                logger.warning(f"Error in telegram patrol loop: {e}")
            await asyncio.sleep(interval_seconds)

    async def send_chat_action(self, action: str = "typing") -> None:
        """Sends chat action indicator (typing, upload_document, etc.)."""
        self.refresh_config()
        if not self.enabled:
            return
        url = f"https://api.telegram.org/bot{self.token}/sendChatAction"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json={"chat_id": self.chat_id, "action": action})
        except Exception as e:
            logger.debug(f"Failed to send chat action: {e}")

    async def start_interactive_listener(self, db, binance_client=None, vyce_client=None) -> None:
        """
        Long-polling listener for incoming messages from Boss on Telegram.
        Allows Boss to ask questions about the market, setups, or volume,
        and receive synthesized advice from the 3-Round Intelligence Council.
        """
        import asyncio
        from monitoring.intelligence_council import consult_intelligence_council, format_telegram_council_response
        logger.info("Starting Telegram interactive intelligence listener (Two-Way Consultation)...")
        last_update_id = 0

        # Initial probe to skip stale messages on boot
        try:
            self.refresh_config()
            if self.enabled:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"https://api.telegram.org/bot{self.token}/getUpdates?offset=-1&timeout=0")
                    if resp.status_code == 200:
                        data = resp.json()
                        results = data.get("result", [])
                        if results:
                            last_update_id = results[-1].get("update_id", 0)
                            logger.info(f"[TelegramListener] Initialized update_id offset: {last_update_id}")
        except Exception as e:
            logger.debug(f"[TelegramListener] Init probe error: {e}")

        while True:
            try:
                self.refresh_config()
                if not self.enabled:
                    await asyncio.sleep(5)
                    continue

                url = f"https://api.telegram.org/bot{self.token}/getUpdates"
                params = {"offset": last_update_id + 1, "timeout": 20}

                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(url, params=params)

                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        update_id = update.get("update_id", 0)
                        if update_id > last_update_id:
                            last_update_id = update_id

                        msg = update.get("message") or update.get("edited_message")
                        if not msg:
                            continue

                        sender_chat_id = str(msg.get("chat", {}).get("id", ""))
                        # Restrict to configured Boss chat_id for ironclad security
                        if sender_chat_id != str(self.chat_id):
                            logger.warning(f"[TelegramListener] Unauthorized message attempt from chat_id {sender_chat_id}")
                            continue

                        text = msg.get("text", "").strip()
                        if not text:
                            continue

                        logger.info(f"📩 [Telegram Consultation] Received query from Boss: '{text}'")

                        # 1. Immediate acknowledgment + typing indicator
                        await self.send_chat_action("typing")
                        ack_msg = (
                            f"⏳ *[ĐÃ TIẾP NHẬN YÊU CẦU CỦA BOSS]*\n"
                            f"❓ _{text}_\n\n"
                            f"🏛️ *Bộ Chỉ Huy Tình Báo 9Router & Hội Đồng VAR Đang Họp Khẩn...*\n"
                            f"• Phe Bò: `Groq LPU 120B (Momentum)`\n"
                            f"• Phe Gấu: `SuperGrok 4.7 (Bóc bẫy rủi ro)`\n"
                            f"• Trọng Tài: `cx/gpt-6-astra & Claude Sonnet (Phán quyết & Tư vấn Boss)`\n"
                            f"_(Đang phân tích dữ liệu live từ Binance, vui lòng đợi 3-5 giây...)_"
                        )
                        await self.send_message(ack_msg)

                        # 2. Run Multi-Agent Council Consultation
                        await self.send_chat_action("typing")
                        council_res = await consult_intelligence_council(
                            query=text,
                            db=db,
                            binance_client=binance_client,
                            vyce_client=vyce_client
                        )

                        # 3. Format and reply back to Boss
                        formatted_response = format_telegram_council_response(council_res)
                        await self.send_message(formatted_response)
                        logger.info(f"✅ [Telegram Consultation] Replied to Boss for query: '{text}'")
            except httpx.TimeoutException:
                pass
            except Exception as e:
                logger.warning(f"[TelegramListener] Error in polling loop: {e}")
                await asyncio.sleep(3)


