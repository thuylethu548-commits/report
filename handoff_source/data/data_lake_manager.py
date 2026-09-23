"""
ASTRA QUANT DATA LAKE MANAGER — 5TB BIG DATA & PARQUET STORAGE
--------------------------------------------------------------
High-performance analytical storage engine utilizing Apache Arrow & Parquet.
Designed for massive-scale time-series, Monte Carlo scenario branches (100k+),
institutional forensic archives, and 5TB Google Drive sync.
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger("DataLakeManager")


class DataLakeManager:
    """Manages local partitioned Parquet data lake and coordinates cloud sync."""

    def __init__(self, lake_root: Optional[Union[str, Path]] = None):
        if lake_root:
            self.lake_root = Path(lake_root)
        else:
            self.lake_root = Path(__file__).resolve().parent / "lake"

        self.parquet_root = self.lake_root / "parquet"
        self.catalog_path = self.lake_root / "catalog.json"

        # Ensure directory structure
        for subdir in ["trades", "signals", "ticks", "simulations", "evolution", "staging"]:
            (self.parquet_root / subdir).mkdir(parents=True, exist_ok=True)

    def write_parquet(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        category: str,
        partition_subpath: str = "",
        compression: str = "snappy"
    ) -> Path:
        """
        Writes tabular records or DataFrame to an optimized Parquet file.
        Returns the saved file path.
        """
        if isinstance(data, list):
            if not data:
                logger.warning(f"write_parquet called with empty data for {category}")
                return Path()
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("Data must be a pandas DataFrame or list of dicts")

        target_dir = self.parquet_root / category
        if partition_subpath:
            target_dir = target_dir / partition_subpath
        target_dir.mkdir(parents=True, exist_ok=True)

        ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{category}_{ts_str}.parquet"
        file_path = target_dir / filename

        # Convert to Arrow Table and write with Snappy or ZSTD compression
        table = pa.Table.from_pandas(df)
        pq.write_table(table, file_path, compression=compression)

        logger.info(f"[DataLake] Wrote {len(df)} rows to Parquet: {file_path.relative_to(self.lake_root)}")
        self._update_catalog()
        return file_path

    def export_db_to_parquet(self, db_path: str = "trading_bot.db") -> Dict[str, Any]:
        """
        Exports all analytical tables from SQLite database into Parquet Data Lake.
        """
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")

        conn = sqlite3.connect(db_path)
        tables_to_export = [
            ("trades", "trades"),
            ("signals", "signals"),
            ("trading_lessons", "evolution"),
            ("ai_advisory_logs", "evolution"),
            ("equity_snapshots", "trades")
        ]

        summary = {"exported_tables": {}, "total_records": 0, "timestamp": datetime.now(timezone.utc).isoformat()}
        now_date = datetime.now(timezone.utc).strftime("date=%Y-%m-%d")

        for table_name, category in tables_to_export:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                if not df.empty:
                    saved_path = self.write_parquet(
                        df,
                        category=category,
                        partition_subpath=f"{table_name}/{now_date}"
                    )
                    summary["exported_tables"][table_name] = {
                        "row_count": len(df),
                        "file": str(saved_path)
                    }
                    summary["total_records"] += len(df)
            except Exception as e:
                logger.warning(f"[DataLake] Skipped table {table_name}: {e}")

        conn.close()
        return summary

    def save_simulation_batch(
        self,
        batch_id: str,
        regime: str,
        records: List[Dict[str, Any]]
    ) -> Path:
        """
        Saves massive batches of simulation runs (e.g. 100k Monte Carlo iterations).
        """
        partition = f"regime={regime}/batch={batch_id}"
        return self.write_parquet(records, category="simulations", partition_subpath=partition)

    def get_lake_summary(self) -> Dict[str, Any]:
        """
        Calculates storage statistics across the entire Data Lake.
        """
        total_size_bytes = 0
        total_files = 0
        categories_stat = {}

        if self.parquet_root.exists():
            for root, dirs, files in os.walk(self.parquet_root):
                for f in files:
                    if f.endswith(".parquet"):
                        p = Path(root) / f
                        size = p.stat().st_size
                        total_size_bytes += size
                        total_files += 1

                        rel = p.relative_to(self.parquet_root)
                        cat = rel.parts[0] if rel.parts else "misc"
                        categories_stat[cat] = categories_stat.get(cat, 0) + 1

        summary = {
            "lake_root": str(self.lake_root),
            "total_files": total_files,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 3),
            "total_size_gb": round(total_size_bytes / (1024 * 1024 * 1024), 5),
            "categories": categories_stat,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        return summary

    def _update_catalog(self) -> None:
        """Saves JSON metadata catalog."""
        try:
            summary = self.get_lake_summary()
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to update catalog: {e}")

    def package_bundle(self) -> Path:
        """Creates a compressed tar.gz bundle of all parquet files for cloud archive."""
        import tarfile
        bundles_dir = self.lake_root / "bundles"
        bundles_dir.mkdir(parents=True, exist_ok=True)
        ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        bundle_path = bundles_dir / f"astra_lake_bundle_{ts_str}.tar.gz"
        with tarfile.open(bundle_path, "w:gz") as tar:
            if self.parquet_root.exists():
                tar.add(str(self.parquet_root), arcname="parquet")
            if self.catalog_path.exists():
                tar.add(str(self.catalog_path), arcname="catalog.json")
        return bundle_path

    def sync_to_gdrive(self) -> Dict[str, Any]:
        """Mirrors latest parquet bundle and files to Google Drive 5TB storage."""
        import shutil
        gdrive_dir = Path("G:/My Drive/Astra_Data_Lake")
        if not gdrive_dir.exists():
            return {"synced": False, "reason": "G:/My Drive/Astra_Data_Lake not mounted"}
        bundle_path = self.package_bundle()
        dest_path = gdrive_dir / bundle_path.name
        shutil.copy2(bundle_path, dest_path)
        logger.info(f"[DataLakeManager] ✅ Mirrored bundle to Google Drive: {dest_path}")
        return {
            "synced": True,
            "bundle": str(dest_path),
            "size_mb": round(bundle_path.stat().st_size / (1024 * 1024), 3)
        }
