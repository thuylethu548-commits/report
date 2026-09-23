import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional
import websockets
from config.settings import settings
from core.events import MarketEvent
from core.event_bus import EventBus
from data.storage import Database

logger = logging.getLogger("WebSocketFeed")


class BinanceWebSocketFeed:
    def __init__(self, event_bus: EventBus, db: Database, symbols: Optional[List[str]] = None):
        self.event_bus = event_bus
        self.db = db
        self.symbols = symbols or getattr(settings, "SYMBOLS", [settings.SYMBOL])
        self.symbol = settings.SYMBOL
        self.timeframe = settings.TIMEFRAME
        self._running = False
        self._task: asyncio.Task | None = None

        # Symbol mapping from RAW (e.g. BTCUSDT) to formatted (e.g. BTC/USDT)
        self.symbol_map = {s.split(":")[0].replace("/", "").upper(): s.split(":")[0] for s in self.symbols}

        def _to_stream_name(sym: str) -> str:
            raw = sym.replace("/", "").lower()
            raw = raw.split(":")[0]
            return f"{raw}@kline_{self.timeframe}"

        # Determine WebSocket URL:
        # If multiple symbols: use Binance Combined Streams (/stream?streams=...)
        # If single symbol: use single stream (/ws/...)
        if settings.MARKET_TYPE == "futures":
            base_url = "wss://stream.binancefuture.com"
        else:
            base_url = "wss://stream.testnet.binance.vision" if settings.BINANCE_USE_TESTNET else "wss://stream.binance.com:9443"
        if len(self.symbols) > 1:
            stream_names = [_to_stream_name(s) for s in self.symbols]
            self.ws_url = f"{base_url}/stream?streams={'/'.join(stream_names)}"
        else:
            self.ws_url = f"{base_url}/ws/{_to_stream_name(self.symbols[0])}"

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._listen_loop())
            logger.info(f"WebSocketFeed started for {self.symbols} ({self.timeframe}) at {self.ws_url}")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocketFeed stopped.")

    async def _listen_loop(self) -> None:
        while self._running:
            try:
                async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=20) as ws:
                    logger.info(f"Connected to Binance WebSocket stream: {self.ws_url}")
                    while self._running:
                        message = await ws.recv()
                        data = json.loads(message)
                        payload = data.get("data", data)
                        if "k" in payload:
                            kline = payload["k"]
                            raw_symbol = payload.get("s") or kline.get("s") or ""
                            event_symbol = self.symbol_map.get(raw_symbol.upper())
                            if event_symbol is None:
                                continue

                            is_candle_closed = kline["x"]
                            candle_time = datetime.fromtimestamp(kline["t"] / 1000, tz=timezone.utc)
                            open_p = float(kline["o"])
                            high_p = float(kline["h"])
                            low_p = float(kline["l"])
                            close_p = float(kline["c"])
                            volume = float(kline["v"])

                            market_event = MarketEvent(
                                symbol=event_symbol,
                                timestamp=candle_time,
                                open=open_p,
                                high=high_p,
                                low=low_p,
                                close=close_p,
                                volume=volume,
                                is_candle_closed=is_candle_closed
                            )

                            if is_candle_closed:
                                await self.db.save_candle(
                                    symbol=event_symbol,
                                    dt=candle_time,
                                    o=open_p,
                                    h=high_p,
                                    l=low_p,
                                    c=close_p,
                                    v=volume
                                )

                            await self.event_bus.publish(market_event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"WebSocket connection error: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
