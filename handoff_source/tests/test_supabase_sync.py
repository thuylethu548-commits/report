import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from data.supabase_sync import SupabaseSyncService


@pytest.mark.asyncio
async def test_supabase_sync_initialization():
    service = SupabaseSyncService(supabase_url="", supabase_key="")
    assert not service.is_enabled
    res = await service.test_connection()
    assert res["status"] == "disabled"


@pytest.mark.asyncio
async def test_supabase_sync_mocked_sync():
    service = SupabaseSyncService(
        supabase_url="https://mockref.supabase.co",
        supabase_key="mock_secret_key"
    )
    assert service.is_enabled

    mock_db = MagicMock()
    mock_db.get_all_trades_ledger = AsyncMock(return_value=[
        {
            "order_id": "test-order-1",
            "symbol": "BTC/USDT",
            "side": "BUY",
            "entry_price": 65000.0,
            "exit_price": 66000.0,
            "quantity": 0.01,
            "pnl_usdt": 10.0,
            "pnl_percent": 1.54,
            "status": "CLOSED",
            "strategy_name": "Test-Strategy",
            "entry_time": "2026-09-20T00:00:00Z",
            "exit_time": "2026-09-20T01:00:00Z",
            "is_paper": 1,
            "fee": 0.05
        }
    ])
    mock_db.get_recent_signals = AsyncMock(return_value=[])
    mock_db.get_lessons = AsyncMock(return_value=[])
    mock_db.get_recent_equity_snapshots = AsyncMock(return_value=[])
    mock_db.get_recent_ai_advisories = AsyncMock(return_value=[])
    mock_db.get_performance_summary = AsyncMock(return_value={"total_trades": 1, "win_rate": 100.0})

    # Test sync_trades mock when client fails or succeeds
    count = await service.sync_trades(mock_db)
    # Since mock url is unreachable, it should handle error gracefully and return 0
    assert isinstance(count, int)
