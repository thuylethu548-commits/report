import abc
import logging
from typing import Optional, List
import pandas as pd
from core.events import MarketEvent, SignalEvent
from core.event_bus import EventBus
from core.constants import OrderSide

logger = logging.getLogger("Strategy")


class BaseStrategy(abc.ABC):
    def __init__(self, name: str, symbol: str, event_bus: EventBus, max_candles: int = 200):
        self.name = name
        self.symbol = symbol
        self.event_bus = event_bus
        self.max_candles = max_candles
        self._candles: List[dict] = []

    def add_candle(self, event: MarketEvent) -> None:
        self._candles.append({
            "timestamp": event.timestamp,
            "open": event.open,
            "high": event.high,
            "low": event.low,
            "close": event.close,
            "volume": event.volume
        })
        if len(self._candles) > self.max_candles:
            self._candles.pop(0)

    @property
    def dataframe(self) -> pd.DataFrame:
        if not self._candles:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = pd.DataFrame(self._candles)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        return df

    @abc.abstractmethod
    async def on_market_event(self, event: MarketEvent) -> Optional[SignalEvent]:
        """Process incoming market event and return SignalEvent if entry/exit triggered."""
        pass
