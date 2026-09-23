import asyncio
import logging
from typing import List, Dict, Any, Optional
import ccxt.async_support as ccxt
from config.settings import settings

logger = logging.getLogger("BinanceClient")


class BinanceClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
        market_type: Optional[str] = None,
        use_testnet: Optional[bool] = None
    ):
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.secret = secret or settings.BINANCE_API_SECRET
        self.market_type = market_type or getattr(settings, "MARKET_TYPE", "spot")
        self.use_testnet = use_testnet if use_testnet is not None else settings.BINANCE_USE_TESTNET

        default_type = "future" if self.market_type == "futures" else "spot"

        exchange_config = {
            "apiKey": self.api_key,
            "secret": self.secret,
            "enableRateLimit": True,
            "options": {
                "defaultType": default_type,
            },
        }
        self.exchange = ccxt.binance(exchange_config)
        if self.use_testnet:
            self.exchange.set_sandbox_mode(True)
            logger.info(f"Binance client initialized in TESTNET mode ({default_type}).")
        else:
            logger.info(f"Binance client initialized in LIVE mode ({default_type}).")

    async def close(self) -> None:
        await self.exchange.close()
        logger.info("Binance client connection closed.")

    def market_symbol(self, symbol: str) -> str:
        if self.market_type == "futures" and ":" not in symbol and "/" in symbol:
            return symbol + ":" + symbol.split("/")[1]
        return symbol

    async def fetch_positions(self, symbols=None):
        normalized = [self.market_symbol(s) for s in symbols] if symbols else None
        return await self.exchange.fetch_positions(normalized)

    async def fetch_position_mode(self):
        return await self.exchange.fetch_position_mode()

    async def fetch_protective_order(self, order_id, symbol):
        return await self.exchange.fetch_order(order_id, self.market_symbol(symbol), {"stop": True})

    async def cancel_protective_order(self, order_id, symbol):
        return await self.exchange.cancel_order(order_id, self.market_symbol(symbol), {"stop": True})

    async def fetch_order_fee(self, result, symbol):
        """Resolve actual commissions; an absent commission is not a zero fee."""
        trades = await self.exchange.fetch_my_trades(
            self.market_symbol(symbol), params={"orderId": result["id"]})
        fills = [t for t in trades if str(t.get("order")) == str(result["id"])]
        quantity = sum(float(t.get("amount") or 0) for t in fills)
        if not fills or abs(quantity - float(result["filled"])) > max(1e-10, quantity * 1e-8):
            raise RuntimeError("Incomplete fill commissions; accounting reconciliation required")
        quote = symbol.split(":")[0].split("/")[-1]
        fees = [(t.get("fee") or {}) for t in fills]
        if any(f.get("cost") is None or f.get("currency") != quote for f in fees):
            raise RuntimeError("Commission conversion required")
        return sum(float(f["cost"]) for f in fees)

    async def load_markets(self) -> Dict[str, Any]:
        return await self.exchange.load_markets()

    async def fetch_ohlcv(self, symbol: str = "BTC/USDT", timeframe: str = "15m", limit: int = 100) -> List[List[Any]]:
        """
        Returns list of [timestamp, open, high, low, close, volume]
        """
        try:
            return await self.exchange.fetch_ohlcv(self.market_symbol(symbol), timeframe=timeframe, limit=limit)
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return []

    async def fetch_ticker(self, symbol: str = "BTC/USDT") -> Dict[str, Any]:
        try:
            return await self.exchange.fetch_ticker(self.market_symbol(symbol))
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}

    async def fetch_order_book(self, symbol: str = "BTC/USDT", limit: int = 20) -> Dict[str, Any]:
        try:
            # Binance Futures requires limit in [5, 10, 20, 50, 100, 500, 1000]
            valid_limits = [5, 10, 20, 50, 100, 500, 1000]
            api_limit = 20
            for vl in valid_limits:
                if vl >= limit:
                    api_limit = vl
                    break
            return await self.exchange.fetch_order_book(self.market_symbol(symbol), limit=api_limit)
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return {"bids": [], "asks": []}

    async def fetch_trades(self, symbol: str = "BTC/USDT", limit: int = 30) -> List[Dict[str, Any]]:
        try:
            return await self.exchange.fetch_trades(self.market_symbol(symbol), limit=limit)
        except Exception as e:
            logger.error(f"Error fetching trades for {symbol}: {e}")
            return []

    async def fetch_balance(self) -> Dict[str, Any]:
        try:
            return await self.exchange.fetch_balance()
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {}

    async def set_leverage(self, symbol: str, leverage: int = 3) -> Dict[str, Any]:
        """Sets leverage for a futures symbol if supported by exchange."""
        try:
            if hasattr(self.exchange, "set_leverage"):
                clean_sym = symbol.replace("/", "")
                return await self.exchange.set_leverage(leverage, clean_sym)
            return {"status": "unsupported", "leverage": leverage}
        except Exception as e:
            logger.warning(f"Error setting leverage {leverage}x for {symbol}: {e}")
            return {"status": "error", "error": str(e)}

    async def check_connection(self) -> Dict[str, Any]:
        """Validates API credentials and queries account connectivity & USDT balance."""
        try:
            balance = await self.fetch_balance()
            if balance:
                usdt_free = float(balance.get("USDT", {}).get("free", 0.0) or balance.get("free", {}).get("USDT", 0.0) or 0.0)
                usdt_total = float(balance.get("USDT", {}).get("total", 0.0) or balance.get("total", {}).get("USDT", 0.0) or 0.0)
                return {
                    "connected": True,
                    "market_type": self.market_type,
                    "testnet": self.use_testnet,
                    "usdt_free": usdt_free,
                    "usdt_total": usdt_total,
                    "message": f"Kết nối Binance thành công ({self.market_type.upper()}). Số dư khả dụng: ${usdt_free:,.2f} USDT"
                }
            return {
                "connected": False,
                "error": "Không lấy được dữ liệu số dư từ Binance"
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }

    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        params = params or {}
        try:
            return await self.exchange.create_order(
                symbol=self.market_symbol(symbol),
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params
            )
        except Exception as e:
            logger.error(f"Error creating {side} order for {symbol} ({amount}): {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        try:
            return await self.exchange.cancel_order(order_id, self.market_symbol(symbol))
        except Exception as e:
            logger.error(f"Error canceling order {order_id} for {symbol}: {e}")
            raise

    def __getattr__(self, name: str):
        return getattr(self.exchange, name)
