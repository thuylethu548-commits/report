import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx

from dotenv import load_dotenv
load_dotenv()

try:
    from config.settings import settings
except ImportError:
    settings = None

logger = logging.getLogger("SupabaseSync")


class SupabaseSyncService:
    """
    Supabase Cloud Hybrid Database Synchronization Engine.
    Periodically synchronizes local SQLite trading telemetry, trades, signals, 
    risk metrics, and multi-agent spatial debates to Supabase Cloud PostgreSQL.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        pat: Optional[str] = None,
    ):
        if supabase_url is not None:
            raw_url = supabase_url
        else:
            raw_url = os.getenv("SUPABASE_URL", "") or (getattr(settings, "SUPABASE_URL", "") if settings else "")
        self.supabase_url = raw_url.rstrip("/")

        if supabase_key is not None:
            self.supabase_key = supabase_key
        else:
            self.supabase_key = (
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
                or os.getenv("SUPABASE_ANON_KEY")
                or (getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "") if settings else "")
                or (getattr(settings, "SUPABASE_ANON_KEY", "") if settings else "")
            )
        self.pat = pat or os.getenv("SUPABASE_PAT") or (getattr(settings, "SUPABASE_PAT", "") if settings else "")
        self.is_enabled = bool(self.supabase_url and self.supabase_key)
        
        self.is_online = False
        self.last_sync_time: Optional[str] = None
        self.last_error: Optional[str] = None
        self.sync_stats: Dict[str, int] = {
            "trades": 0,
            "signals": 0,
            "equity_snapshots": 0,
            "ai_advisory_logs": 0,
            "trading_lessons": 0,
            "spatial_debates": 0,
            "system_telemetry": 0,
        }
        
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()

    def _headers(self, merge_conflict: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }
        if merge_conflict:
            headers["Prefer"] = "resolution=merge-duplicates"
        else:
            headers["Prefer"] = "return=minimal"
        return headers

    async def test_connection(self) -> Dict[str, Any]:
        """Verify connection to Supabase REST endpoint."""
        if not self.is_enabled:
            return {"status": "disabled", "message": "SUPABASE_URL or Key not configured"}
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(f"{self.supabase_url}/rest/v1/", headers=self._headers())
                if resp.status_code == 200:
                    self.is_online = True
                    return {
                        "status": "connected",
                        "url": self.supabase_url,
                        "project_ref": self.supabase_url.replace("https://", "").split(".")[0],
                        "code": 200,
                    }
                else:
                    self.is_online = False
                    return {"status": "error", "code": resp.status_code, "detail": resp.text[:200]}
        except Exception as e:
            self.is_online = False
            self.last_error = str(e)
            return {"status": "unreachable", "error": str(e)}

    async def sync_trades(self, db) -> int:
        """Sync closed and open trades from local SQLite to Supabase."""
        if not self.is_enabled:
            return 0
        try:
            # Fetch all trades from local db
            local_trades = await db.get_all_trades_ledger(limit=300)
            if not local_trades:
                return 0

            payload = []
            for t in local_trades:
                order_id = t.get("order_id") or ""
                if not order_id:
                    continue
                payload.append({
                    "trade_id": order_id,
                    "symbol": t.get("symbol", "BTC/USDT"),
                    "side": t.get("side", "BUY"),
                    "entry_price": float(t.get("entry_price") or 0.0),
                    "exit_price": float(t.get("exit_price")) if t.get("exit_price") is not None else None,
                    "amount": float(t.get("quantity") or 0.0),
                    "leverage": 3,
                    "pnl": float(t.get("pnl_usdt")) if t.get("pnl_usdt") is not None else 0.0,
                    "pnl_percent": float(t.get("pnl_percent")) if t.get("pnl_percent") is not None else 0.0,
                    "status": t.get("status", "OPEN"),
                    "strategy": t.get("strategy_name", "Quantitative-Fleet"),
                    "entry_time": t.get("entry_time"),
                    "exit_time": t.get("exit_time"),
                    "notes": f"Paper={t.get('is_paper', 1)}, Fee={t.get('fee', 0.0)}",
                })

            if not payload:
                return 0

            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.supabase_url}/rest/v1/trades?on_conflict=trade_id"
                resp = await client.post(url, headers=self._headers(merge_conflict="trade_id"), json=payload)
                if resp.status_code in (200, 201, 204):
                    self.sync_stats["trades"] = len(payload)
                    return len(payload)
                else:
                    logger.warning(f"Supabase sync_trades HTTP {resp.status_code}: {resp.text[:200]}")
                    return 0
        except Exception as e:
            logger.error(f"Error syncing trades to Supabase: {e}")
            return 0

    async def sync_signals(self, db, limit: int = 100) -> int:
        """Sync signals from local SQLite to Supabase."""
        if not self.is_enabled:
            return 0
        try:
            signals = await db.get_recent_signals(limit=limit)
            if not signals:
                return 0

            payload = []
            for s in signals:
                payload.append({
                    "symbol": s.get("symbol", "BTC/USDT"),
                    "signal_type": s.get("side", "BUY"),
                    "confidence": float(s.get("confidence") or 0.0),
                    "price": float(s.get("price") or 0.0),
                    "strategy": s.get("strategy_name", "Fleet-Confluence"),
                    "ai_reasoning": f"SL={s.get('stop_loss', 0.0)} | TP={s.get('take_profit', 0.0)} | Approved={s.get('approved', 1)} | Reason={s.get('rejection_reason', '')}",
                    "created_at": s.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                })

            if not payload:
                return 0

            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.supabase_url}/rest/v1/signals"
                resp = await client.post(url, headers=self._headers(), json=payload)
                if resp.status_code in (200, 201, 204):
                    self.sync_stats["signals"] = len(payload)
                    return len(payload)
                else:
                    logger.warning(f"Supabase sync_signals HTTP {resp.status_code}: {resp.text[:200]}")
                    return 0
        except Exception as e:
            logger.error(f"Error syncing signals to Supabase: {e}")
            return 0

    async def sync_trading_lessons(self, db) -> int:
        """Sync trading lessons / risk prevention lessons to Supabase."""
        if not self.is_enabled:
            return 0
        try:
            lessons = await db.get_lessons(limit=100)
            if not lessons:
                return 0

            payload = []
            for l in lessons:
                payload.append({
                    "category": l.get("category", "RISK_CONTROL"),
                    "title": l.get("title", "Risk Principle"),
                    "lesson_text": f"{l.get('details', '')}\n\n[BÀI HỌC CỐT LÕI]: {l.get('lesson_learned', '')}",
                    "source": l.get("operator", "Astra-Supervisor"),
                    "created_at": l.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                })

            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.supabase_url}/rest/v1/trading_lessons"
                resp = await client.post(url, headers=self._headers(), json=payload)
                if resp.status_code in (200, 201, 204):
                    self.sync_stats["trading_lessons"] = len(payload)
                    return len(payload)
                return 0
        except Exception as e:
            logger.error(f"Error syncing lessons to Supabase: {e}")
            return 0

    async def sync_equity_snapshots(self, db, limit: int = 50) -> int:
        """Sync equity snapshots to Supabase."""
        if not self.is_enabled:
            return 0
        try:
            snaps = await db.get_recent_equity_snapshots(limit=limit)
            if not snaps:
                return 0

            payload = []
            for s in snaps:
                payload.append({
                    "total_balance": float(s.get("balance_usdt") or 0.0),
                    "available_balance": float(s.get("balance_usdt") or 0.0),
                    "unrealized_pnl": 0.0,
                    "realized_pnl": 0.0,
                    "open_positions": int(s.get("open_positions") or 0),
                    "snapshot_time": s.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                })

            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.supabase_url}/rest/v1/equity_snapshots"
                resp = await client.post(url, headers=self._headers(), json=payload)
                if resp.status_code in (200, 201, 204):
                    self.sync_stats["equity_snapshots"] = len(payload)
                    return len(payload)
                return 0
        except Exception as e:
            logger.error(f"Error syncing equity snapshots to Supabase: {e}")
            return 0

    async def sync_ai_advisory_logs(self, db, limit: int = 50) -> int:
        """Sync AI Advisory logs to Supabase."""
        if not self.is_enabled:
            return 0
        try:
            logs = await db.get_recent_ai_advisories(limit=limit)
            if not logs:
                return 0

            payload = []
            for item in logs:
                allowed = bool(item.get("trade_allowed", 1))
                payload.append({
                    "symbol": item.get("symbol", "BTC/USDT"),
                    "provider": "VyceAI",
                    "model": "deepseek-v4-flash",
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "action": "ALLOW" if allowed else "VETO",
                    "advice": f"Regime: {item.get('regime')} | Risk: {item.get('risk_score')}/10 | Mult: {item.get('size_multiplier')}x | {item.get('reasoning')}",
                    "created_at": item.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                })

            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.supabase_url}/rest/v1/ai_advisory_logs"
                resp = await client.post(url, headers=self._headers(), json=payload)
                if resp.status_code in (200, 201, 204):
                    self.sync_stats["ai_advisory_logs"] = len(payload)
                    return len(payload)
                return 0
        except Exception as e:
            logger.error(f"Error syncing AI logs to Supabase: {e}")
            return 0

    async def sync_spatial_debates(self, spatial_brain) -> int:
        """Sync multi-agent spatial debates from memory to Supabase Cloud."""
        if not self.is_enabled or not spatial_brain:
            return 0
        try:
            debates = getattr(spatial_brain, "debate_history", [])
            if not debates:
                return 0

            payload = []
            for d in debates[-20:]:  # Last 20 debates
                payload.append({
                    "debate_id": d.get("debate_id"),
                    "topic": d.get("topic", "Multi-Agent Consensus"),
                    "verdict": d.get("verdict", "APPROVED"),
                    "consensus_score": float(d.get("consensus_score", 0.85)),
                    "steps": d.get("steps", []),
                    "created_at": d.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                })

            if not payload:
                return 0

            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.supabase_url}/rest/v1/spatial_debates?on_conflict=debate_id"
                resp = await client.post(url, headers=self._headers(merge_conflict="debate_id"), json=payload)
                if resp.status_code in (200, 201, 204):
                    self.sync_stats["spatial_debates"] = len(payload)
                    return len(payload)
                return 0
        except Exception as e:
            logger.error(f"Error syncing spatial debates to Supabase: {e}")
            return 0

    async def sync_system_telemetry(self, db, circuit_breaker=None) -> bool:
        """Upsert current system telemetry snapshot to Supabase."""
        if not self.is_enabled:
            return False
        try:
            perf = await db.get_performance_summary()
            total_trades = perf.get("total_trades", 0)
            win_rate = perf.get("win_rate", 0.0)

            is_tripped = bool(getattr(circuit_breaker, "is_tripped", False)) if circuit_breaker else False
            risk_status = "CIRCUIT_BREAKER_TRIPPED" if is_tripped else "NORMAL"

            payload = [{
                "id": 1,
                "source_vps": "Astra-Quant-Primary-VPS",
                "uptime_seconds": 86400.0,
                "risk_gate_status": risk_status,
                "win_rate": float(win_rate),
                "total_trades": int(total_trades),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }]

            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.supabase_url}/rest/v1/system_telemetry?on_conflict=id"
                resp = await client.post(url, headers=self._headers(merge_conflict="id"), json=payload)
                if resp.status_code in (200, 201, 204):
                    self.sync_stats["system_telemetry"] += 1
                    return True
                return False
        except Exception as e:
            logger.error(f"Error syncing telemetry to Supabase: {e}")
            return False

    async def sync_all(self, db, spatial_brain=None, circuit_breaker=None) -> Dict[str, Any]:
        """Trigger comprehensive synchronization across all entities."""
        async with self._lock:
            start_t = datetime.now(timezone.utc)
            conn_res = await self.test_connection()
            if conn_res.get("status") not in ("connected", 200):
                return {
                    "success": False,
                    "error": conn_res.get("error") or conn_res.get("detail") or "Connection failed",
                    "stats": self.sync_stats,
                }

            t_synced = await self.sync_trades(db)
            s_synced = await self.sync_signals(db)
            l_synced = await self.sync_trading_lessons(db)
            eq_synced = await self.sync_equity_snapshots(db)
            a_synced = await self.sync_ai_advisory_logs(db)
            d_synced = await self.sync_spatial_debates(spatial_brain)
            telem_ok = await self.sync_system_telemetry(db, circuit_breaker)

            self.last_sync_time = datetime.now(timezone.utc).isoformat()
            self.last_error = None
            self.is_online = True

            logger.info(
                f"[Supabase Cloud Sync OK] Trades={t_synced}, Signals={s_synced}, "
                f"Lessons={l_synced}, Equity={eq_synced}, AI_Logs={a_synced}, Debates={d_synced}, Telem={'OK' if telem_ok else 'SKIP'}"
            )

            return {
                "success": True,
                "timestamp": self.last_sync_time,
                "duration_ms": round((datetime.now(timezone.utc) - start_t).total_seconds() * 1000, 2),
                "synced_counts": {
                    "trades": t_synced,
                    "signals": s_synced,
                    "trading_lessons": l_synced,
                    "equity_snapshots": eq_synced,
                    "ai_advisory_logs": a_synced,
                    "spatial_debates": d_synced,
                    "system_telemetry": 1 if telem_ok else 0,
                },
                "total_records": self.sync_stats,
            }

    def start_background_sync(self, db, spatial_brain=None, circuit_breaker=None, interval_seconds: int = 60):
        """Starts asynchronous non-blocking periodic sync task."""
        if not self.is_enabled:
            logger.info("Supabase sync disabled (missing credentials).")
            return

        if self._sync_task and not self._sync_task.done():
            return

        self._running = True

        async def _loop():
            logger.info(f"Supabase Cloud Sync background service started (interval: {interval_seconds}s).")
            # Initial sync on startup
            try:
                await self.sync_all(db, spatial_brain, circuit_breaker)
            except Exception as e:
                logger.warning(f"Initial Supabase sync error: {e}")

            while self._running:
                try:
                    await asyncio.sleep(interval_seconds)
                    if not self._running:
                        break
                    await self.sync_all(db, spatial_brain, circuit_breaker)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Unhandled error in Supabase sync loop: {e}")
                    await asyncio.sleep(10)

        self._sync_task = asyncio.create_task(_loop())

    async def stop(self):
        """Stop background sync task cleanly."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Supabase Cloud Sync service stopped.")


# Global Singleton
_SUPABASE_SYNC_INSTANCE: Optional[SupabaseSyncService] = None


def get_supabase_sync() -> SupabaseSyncService:
    global _SUPABASE_SYNC_INSTANCE
    if _SUPABASE_SYNC_INSTANCE is None:
        _SUPABASE_SYNC_INSTANCE = SupabaseSyncService()
    return _SUPABASE_SYNC_INSTANCE
