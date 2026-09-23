"""
ASTRA DIGITAL RESEARCH LAB — KNOWLEDGE STORE & DUCKDB ANALYTICS
---------------------------------------------------------------
Integrates DuckDB columnar querying over Parquet Data Lake,
manages SQLite experiment records, and maintains persistent Research Memory
(including Failed Hypotheses to prevent repeat errors).
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import duckdb
import pandas as pd

from config.settings import settings

logger = logging.getLogger("ResearchKnowledgeStore")


class ResearchKnowledgeStore:
    """Analytical data store powered by DuckDB and SQLite research ledger."""

    def __init__(self, db_path: str = "trading_bot.db", lake_root: Optional[Path] = None):
        self.db_path = db_path
        if lake_root:
            self.lake_root = Path(lake_root)
        else:
            self.lake_root = Path(__file__).resolve().parent.parent.parent / "data" / "lake"

        self.parquet_dir = self.lake_root / "parquet"
        self._init_sqlite_schema()

    def _init_sqlite_schema(self) -> None:
        """Initializes the research_experiments table in SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT UNIQUE NOT NULL,
                hypothesis_id TEXT NOT NULL,
                title TEXT NOT NULL,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                parameters_json TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                stress_results_json TEXT NOT NULL,
                status TEXT NOT NULL,
                reviewer_notes TEXT,
                score REAL DEFAULT 0.0,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,  -- 'GOLD_STANDARD' | 'FAILED_HYPOTHESIS' | 'REGIME_NOTE'
                title TEXT NOT NULL,
                insight TEXT NOT NULL,
                evidence_json TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def query_lake_duckdb(self, query: str) -> List[Dict[str, Any]]:
        """Executes analytical SQL query on local Parquet files via DuckDB."""
        conn = duckdb.connect(database=":memory:")
        try:
            # Register Parquet paths as views if available
            sim_path = str(self.parquet_dir / "simulations" / "**" / "*.parquet").replace("\\", "/")
            trades_path = str(self.parquet_dir / "trades" / "**" / "*.parquet").replace("\\", "/")

            if any((self.parquet_dir / "simulations").glob("**/*.parquet")):
                conn.execute(f"CREATE OR REPLACE VIEW simulations AS SELECT * FROM read_parquet('{sim_path}')")
            if any((self.parquet_dir / "trades").glob("**/*.parquet")):
                conn.execute(f"CREATE OR REPLACE VIEW trades_lake AS SELECT * FROM read_parquet('{trades_path}')")

            df = conn.execute(query).df()
            return df.to_dict(orient="records")
        except Exception as e:
            logger.warning(f"[DuckDB Query Error]: {e}")
            return []
        finally:
            conn.close()

    def save_experiment(
        self,
        experiment_id: str,
        hypothesis_id: str,
        title: str,
        symbol: str,
        strategy: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, Any],
        stress_results: Dict[str, Any],
        status: str,
        reviewer_notes: str,
        score: float
    ) -> None:
        """Persists completed experiment record into SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO research_experiments (
                experiment_id, hypothesis_id, title, symbol, strategy,
                parameters_json, metrics_json, stress_results_json,
                status, reviewer_notes, score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            experiment_id, hypothesis_id, title, symbol, strategy,
            json.dumps(parameters), json.dumps(metrics), json.dumps(stress_results),
            status, reviewer_notes, score, datetime.now(timezone.utc).isoformat()
        ))

        # Update Research Memory if approved or rejected with high certainty
        if status == "APPROVED":
            cursor.execute("""
                INSERT INTO research_memory (category, title, insight, evidence_json, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "GOLD_STANDARD",
                f"Approved: {title}",
                f"Strategy {strategy} on {symbol} demonstrated Sharpe {metrics.get('sharpe_ratio', 0):.2f} with robust tail-risk survival.",
                json.dumps({"metrics": metrics, "params": parameters}),
                datetime.now(timezone.utc).isoformat()
            ))
        elif status == "REJECTED":
            cursor.execute("""
                INSERT INTO research_memory (category, title, insight, evidence_json, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "FAILED_HYPOTHESIS",
                f"Rejected: {title}",
                f"Hypothesis failed audit: {reviewer_notes[:180]}",
                json.dumps({"params": parameters, "metrics": metrics}),
                datetime.now(timezone.utc).isoformat()
            ))

        conn.commit()
        conn.close()
        logger.info(f"[KnowledgeStore] Saved experiment {experiment_id} ({status})")

    def get_experiments(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches recent experiments from SQLite."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM research_experiments ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        result = [dict(r) for r in rows]
        conn.close()
        return result

    def get_research_memory(self, category: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        """Retrieves lessons and gold standards from research memory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM research_memory WHERE category = ? ORDER BY id DESC LIMIT ?", (category, limit))
        else:
            cursor.execute("SELECT * FROM research_memory ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        result = [dict(r) for r in rows]
        conn.close()
        return result
