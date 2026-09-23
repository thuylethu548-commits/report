#!/usr/bin/env python3
"""
ASTRA QUANT DESK — AUTOMATED DATABASE BACKUP TO TELEGRAM
---------------------------------------------------------
Creates an atomic online snapshot of trading_bot.db, compresses to .db.gz,
and uploads the backup directly to the administrator's Telegram channel.
"""

import sys
import os
import argparse
import asyncio
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from core.event_bus import EventBus
from monitoring.telegram_bot import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DBBackupToTelegram")


async def main():
    parser = argparse.ArgumentParser(description="Backup SQLite DB to Telegram as .db.gz")
    parser.add_argument("--db", default="trading_bot.db", help="Path to SQLite database")
    parser.add_argument("--note", default="Lưu trữ snapshot dữ liệu định kỳ", help="Custom note for caption")
    parser.add_argument("--local-only", action="store_true", help="Only save locally, do not upload to Telegram")
    args = parser.parse_args()

    db_path = str(PROJECT_ROOT / args.db) if not os.path.isabs(args.db) else args.db
    if not os.path.exists(db_path):
        logger.error(f"Database not found at: {db_path}")
        sys.exit(1)

    logger.info(f"Initiating atomic online backup for {db_path}...")
    bus = EventBus()
    notifier = TelegramNotifier(bus)

    if args.local_only:
        notifier.enabled = False

    backup_file = await notifier.backup_database_to_telegram(db_path=db_path, note=args.note)
    if backup_file and os.path.exists(backup_file):
        size_kb = os.path.getsize(backup_file) / 1024
        logger.info(f"✅ Backup successful! File created: {backup_file} ({size_kb:.2f} KB)")
        if notifier.enabled:
            logger.info("🚀 Dispatched archive to Telegram channel successfully.")
        else:
            logger.info("📁 Saved archive locally (Telegram upload skipped).")
    else:
        logger.error("❌ Backup failed.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
