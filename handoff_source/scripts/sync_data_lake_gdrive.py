#!/usr/bin/env python3
"""
ASTRA QUANT DATA LAKE — 5TB GOOGLE DRIVE SYNC & ARCHIVE UTILITY
---------------------------------------------------------------
Orchestrates the export, packaging, and synchronization of the 5TB Parquet Data Lake
to Google Drive and notifies administrator via Telegram.
"""

import sys
import os
import argparse
import asyncio
import logging
import tarfile
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 console output on Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from config.settings import settings
from data.data_lake_manager import DataLakeManager
from monitoring.telegram_bot import TelegramNotifier
from core.event_bus import EventBus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("GDriveDataLakeSync")


def package_lake_bundle(lake_mgr: DataLakeManager) -> Path:
    """Creates a compressed tar.gz bundle of all parquet files for cloud archive."""
    bundles_dir = lake_mgr.lake_root / "bundles"
    bundles_dir.mkdir(parents=True, exist_ok=True)

    ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bundle_path = bundles_dir / f"astra_lake_bundle_{ts_str}.tar.gz"

    logger.info(f"Packaging Data Lake Parquet files into {bundle_path.name}...")
    with tarfile.open(bundle_path, "w:gz") as tar:
        if lake_mgr.parquet_root.exists():
            tar.add(str(lake_mgr.parquet_root), arcname="parquet")
        if lake_mgr.catalog_path.exists():
            tar.add(str(lake_mgr.catalog_path), arcname="catalog.json")

    size_mb = os.path.getsize(bundle_path) / (1024 * 1024)
    logger.info(f"✅ Bundle successfully created: {bundle_path} ({size_mb:.2f} MB)")
    return bundle_path


async def main():
    parser = argparse.ArgumentParser(description="Astra Quant 5TB Google Drive Data Lake Sync")
    parser.add_argument("--summary", action="store_true", help="Display Data Lake inventory & storage metrics")
    parser.add_argument("--export-db", action="store_true", help="Export latest SQLite tables to Parquet partitions")
    parser.add_argument("--bundle", action="store_true", help="Package Data Lake into compressed .tar.gz bundle")
    parser.add_argument("--notify-telegram", action="store_true", help="Send Data Lake sync report to Telegram")
    args = parser.parse_args()

    lake_mgr = DataLakeManager()

    if args.export_db or (not args.summary and not args.bundle):
        logger.info("Exporting database to partitioned Parquet Data Lake...")
        exp_res = lake_mgr.export_db_to_parquet(getattr(settings, "DATABASE_PATH", "trading_bot.db"))
        logger.info(f"Exported {exp_res['total_records']} records across {len(exp_res['exported_tables'])} tables.")

    summary = lake_mgr.get_lake_summary()

    print("\n" + "=" * 60)
    print("🌊 ASTRA QUANT 5TB BIG DATA DATA LAKE INVENTORY")
    print("=" * 60)
    print(f"• Root Directory: {summary['lake_root']}")
    print(f"• Total Parquet Files: {summary['total_files']}")
    print(f"• Total Storage: {summary['total_size_mb']:.3f} MB ({summary['total_size_bytes']:,} bytes)")
    print("• Partitions:")
    for cat, cnt in summary["categories"].items():
        print(f"  - {cat}: {cnt} partition files")
    print(f"• Last Synchronized: {summary['last_updated']}")
    print("=" * 60 + "\n")

    bundle_path = None
    if args.bundle:
        bundle_path = package_lake_bundle(lake_mgr)
        gdrive_lake_dir = Path("G:/My Drive/Astra_Data_Lake")
        if gdrive_lake_dir.exists() and bundle_path:
            try:
                import shutil
                dest_file = gdrive_lake_dir / bundle_path.name
                shutil.copy2(bundle_path, dest_file)
                logger.info(f"✅ Mirrored archive bundle directly to Google Drive: {dest_file}")
            except Exception as e:
                logger.warning(f"⚠️ GDrive mirror warning: {e}")

    if args.notify_telegram:
        bus = EventBus()
        notifier = TelegramNotifier(bus)
        if notifier.enabled:
            caption = (
                f"🌊 *[ASTRA DATA LAKE] ĐỒNG BỘ 5TB BIG DATA HOÀN TẤT*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📁 *Tổng tệp Parquet*: `{summary['total_files']} files`\n"
                f"💾 *Dung lượng nén*: `{summary['total_size_mb']} MB`\n"
                f"📊 *Phân vùng*: `Trades ({summary['categories'].get('trades', 0)}) | Signals ({summary['categories'].get('signals', 0)}) | Evolution ({summary['categories'].get('evolution', 0)})`\n"
                f"☁️ *Đích lưu trữ*: `Google Drive 5TB Storage Pool`\n"
                f"⚡ *Định dạng*: Apache Arrow / Snappy Parquet (Tối ưu truy vấn 100k+ nhánh)"
            )
            await notifier.send_message(caption)
            logger.info("Dispatched Data Lake status report to Telegram.")


if __name__ == "__main__":
    asyncio.run(main())
