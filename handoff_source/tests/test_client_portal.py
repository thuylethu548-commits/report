import pytest
import pytest_asyncio
from datetime import datetime, timezone
from data.storage import Database
from core.events import OrderEvent
from core.constants import OrderSide, OrderType
from execution.multi_account_dispatcher import (
    MultiAccountDispatcher,
    hash_password,
    verify_password
)


@pytest_asyncio.fixture
async def portal_db(tmp_path):
    db_path = str(tmp_path / "test_portal.db")
    db = Database(db_path)
    await db.connect()
    yield db
    await db.close()


def test_password_hashing():
    pwd = "SecretPassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


@pytest.mark.asyncio
async def test_user_creation_and_auth(portal_db):
    pwd = "AnhHoSafePassword888"
    hashed = hash_password(pwd)
    user_id = await portal_db.create_user(
        username="anhho_quant",
        hashed_password=hashed,
        full_name="Anh Họ VIP",
        email="anhho@example.com"
    )
    assert user_id > 0

    user = await portal_db.get_user_by_username("anhho_quant")
    assert user is not None
    assert user["full_name"] == "Anh Họ VIP"
    assert verify_password(pwd, user["hashed_password"]) is True


@pytest.mark.asyncio
async def test_non_custodial_api_storage_and_dispatch(portal_db):
    dispatcher = MultiAccountDispatcher(portal_db, is_paper=True)

    # 1. Non-Custodial verification on mock key
    valid, msg = await dispatcher.verify_binance_non_custodial("mock_key_safe", "mock_secret")
    assert valid is True
    assert "Non-Custodial an toàn" in msg

    # 2. Create user & save credentials
    user_id = await portal_db.create_user(
        username="anhho_vip",
        hashed_password=hash_password("test1234"),
        full_name="Anh Họ",
        email="anhho@crypto.vn"
    )
    cred_id = await portal_db.save_user_api_credentials(
        user_id=user_id,
        api_key="mock_anh_ho_key",
        api_secret="***REDACTED***",
        label="Tài Khoản Binance Anh Họ",
        leverage=5,
        max_margin_usdt=50.0,
        profit_share_pct=0.25,
        withdrawals_disabled=True
    )
    assert cred_id > 0

    # 3. Dispatch Master Trade to client
    master_order = OrderEvent(
        order_id="MOCK_MASTER_001",
        strategy_name="Astra_Trend",
        symbol="ETH/USDT",
        order_type=OrderType.MARKET,
        side=OrderSide.BUY,
        price=2500.0,
        quantity=0.01,
        timestamp=datetime.now(timezone.utc),
        stop_loss=2460.0,
        take_profit=2550.0
    )

    dispatched = await dispatcher.dispatch_signal_to_clients(master_order, master_margin_usdt=20.0)
    assert len(dispatched) == 1
    assert dispatched[0]["username"] == "anhho_vip"
    assert dispatched[0]["symbol"] == "ETH/USDT"
    assert dispatched[0]["notional"] == 100.0  # 20.0 margin * 5 leverage = 100.0 notional

    # 4. Check client trades in DB
    trades = await portal_db.get_client_trades(user_id)
    assert len(trades) == 1
    assert trades[0]["status"] == "OPEN"

    # 5. Position closes with +5% profit
    closed = await dispatcher.handle_position_close_for_clients(
        symbol="ETH/USDT",
        side="BUY",
        exit_price=2625.0,
        pnl_pct=5.0
    )
    assert len(closed) == 1
    assert closed[0]["pnl_usdt"] == 5.0  # 5% of 100 notional = $5.0 USDT
    assert closed[0]["profit_share_due"] == 1.25  # 25% of $5.0 = $1.25 USDT commission for user!

    # 6. Check Dashboard & Admin stats
    stats = await portal_db.get_client_dashboard_stats(user_id)
    assert stats["total_trades"] == 1
    assert stats["win_trades"] == 1
    assert stats["win_rate"] == 100.0
    assert stats["total_pnl_usdt"] == 5.0
    assert stats["total_profit_share_due"] == 1.25
    assert stats["net_profit_client"] == 3.75

    admin_summary = await portal_db.get_all_clients_admin_summary()
    assert admin_summary["total_clients"] == 1
    assert admin_summary["active_api_keys"] == 1
    assert admin_summary["total_client_pnl"] == 5.0
    assert admin_summary["total_desk_commission"] == 1.25
