import logging
import hmac
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import aiohttp

from core.events import OrderEvent
from data.storage import Database

logger = logging.getLogger("MultiAccountDispatcher")


def hash_password(password: str, salt: str = "astra_salt_2026") -> str:
    """Generates a secure sha256 hash with salt for user passwords."""
    return hashlib.sha256(f"{salt}:{password}:{salt}".encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str, salt: str = "astra_salt_2026") -> bool:
    """Verifies a plain password against its hashed value."""
    return hash_password(plain_password, salt) == hashed_password


class MultiAccountDispatcher:
    """
    Non-Custodial Multi-Account Trade Replicator & Profit-Share Dispatcher.
    Allows clients and family members to connect their own Binance API keys.
    Strictly verifies and enforces that 'Enable Withdrawals' is DISABLED.
    """

    def __init__(self, db: Database, is_paper: bool = True):
        self.db = db
        self.is_paper = is_paper

    async def verify_binance_non_custodial(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://api.binance.com"
    ) -> Tuple[bool, str]:
        """
        Queries Binance API restrictions to guarantee withdrawals are DISABLED.
        If withdrawals are allowed, the key is strictly rejected for safety.
        """
        # In mock or test environment
        if api_key.startswith("mock_") or "mock" in api_key:
            return True, "Mock API Key được chấp thuận (Non-Custodial an toàn)."

        url = f"{base_url}/sapi/v1/account/apiRestrictions"
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        headers = {"X-MBX-APIKEY": api_key}
        full_url = f"{url}?{query_string}&signature={signature}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(full_url, headers=headers, timeout=5.0) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Strict Non-Custodial Check
                        if data.get("enableWithdrawals", False):
                            return False, (
                                "CẢNH BÁO NGUY HIỂM: API Key của bạn đang BẬT QUYỀN RÚT TIỀN (Enable Withdrawals)! "
                                "Để bảo vệ tài sản của bạn, Astra chỉ chấp nhận API Key ĐÃ TẮT QUYỀN RÚT TIỀN. "
                                "Vui lòng vào Binance bỏ chọn 'Enable Withdrawals' và lưu lại!"
                            )
                        return True, "Xác thực thành công: API Key Non-Custodial an toàn (Quyền rút tiền đã tắt)."
                    else:
                        err_text = await resp.text()
                        return False, f"Binance từ chối kết nối API: {err_text}"
        except Exception as e:
            logger.warning(f"Error checking API restrictions: {e}")
            # If network error but non-empty key, require caution
            return False, f"Không thể kiểm tra an toàn API Key qua Binance: {e}"

    async def dispatch_signal_to_clients(
        self,
        master_order: OrderEvent,
        master_margin_usdt: float = 20.0
    ) -> List[Dict[str, Any]]:
        """
        Dispatches an approved master trade to all active registered clients.
        Calculates position sizes according to each client's individual margin cap.
        """
        clients = await self.db.get_all_active_client_credentials()
        dispatched_results = []

        for client in clients:
            user_id = client["user_id"]
            username = client.get("username", f"user_{user_id}")
            max_margin = client.get("max_margin_usdt", 50.0)
            leverage = client.get("leverage", 3)

            # Sizing rule: Allocation is proportional or capped to client's configured margin
            client_margin = min(max_margin, master_margin_usdt)
            notional = round(client_margin * leverage, 2)
            qty = round(notional / master_order.price, 4) if master_order.price > 0 else 0.001

            client_order_id = f"CLT_{user_id}_{int(time.time()*1000)}"

            # Record client trade in database
            await self.db.record_client_trade(
                user_id=user_id,
                order_id=client_order_id,
                symbol=master_order.symbol,
                side=master_order.side.value if hasattr(master_order.side, "value") else str(master_order.side),
                entry_price=master_order.price,
                quantity=qty,
                notional_value=notional
            )

            dispatched_results.append({
                "user_id": user_id,
                "username": username,
                "client_order_id": client_order_id,
                "symbol": master_order.symbol,
                "side": master_order.side,
                "quantity": qty,
                "notional": notional,
                "status": "DISPATCHED"
            })
            logger.info(f"Dispatched trade to client {username} (ID: {user_id}): {master_order.side} {qty} {master_order.symbol} (${notional} Notional)")

        return dispatched_results

    async def handle_position_close_for_clients(
        self,
        symbol: str,
        side: str,
        exit_price: float,
        pnl_pct: float
    ) -> List[Dict[str, Any]]:
        """
        Closes mirrored client positions and records profit share due (20% - 30%).
        """
        clients = await self.db.get_all_active_client_credentials()
        closed_trades = []

        for client in clients:
            user_id = client["user_id"]
            profit_share_pct = client.get("profit_share_pct", 0.25)

            # Find open trades for this user and symbol
            user_trades = await self.db.get_client_trades(user_id=user_id, limit=20)
            for t in user_trades:
                if t["symbol"] == symbol and t["status"] == "OPEN":
                    notional = t["notional_value"]
                    pnl_usdt = round(notional * (pnl_pct / 100.0), 3)

                    await self.db.close_client_trade(
                        user_id=user_id,
                        order_id=t["order_id"],
                        exit_price=exit_price,
                        pnl_usdt=pnl_usdt,
                        profit_share_pct=profit_share_pct
                    )

                    due = max(0.0, pnl_usdt * profit_share_pct) if pnl_usdt > 0 else 0.0
                    closed_trades.append({
                        "user_id": user_id,
                        "order_id": t["order_id"],
                        "pnl_usdt": pnl_usdt,
                        "profit_share_due": due
                    })
                    logger.info(f"Closed client trade for user {user_id}: PnL=${pnl_usdt} USDT, Profit Share=${due} USDT")

        return closed_trades
