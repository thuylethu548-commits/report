import logging
from typing import Optional
import numpy as np
import pandas as pd
from core.events import MarketEvent, SignalEvent
from core.event_bus import EventBus
from core.constants import OrderSide, round_price
from .base_strategy import BaseStrategy

logger = logging.getLogger("RSIBollingerStrategy")


class RSIBollingerStrategy(BaseStrategy):
    def __init__(self, symbol: str, event_bus: EventBus, bb_period: int = 20, bb_std: float = 2.0, rsi_period: int = 14):
        super().__init__(name="RSI_Bollinger", symbol=symbol, event_bus=event_bus, max_candles=100)
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.position_side: Optional[OrderSide] = None
        self.candle_count: int = 0
        self.last_signal_candle: int = -999

    @property
    def in_position(self) -> bool:
        return self.position_side is not None

    @in_position.setter
    def in_position(self, val: bool):
        if not val:
            self.position_side = None

    async def on_market_event(self, event: MarketEvent) -> Optional[SignalEvent]:
        if not event.is_candle_closed:
            return None

        self.candle_count += 1
        self.add_candle(event)
        df = self.dataframe
        if len(df) < max(self.bb_period, self.rsi_period) + 2:
            return None

        # Bollinger Bands
        sma = df["close"].rolling(self.bb_period).mean()
        std = df["close"].rolling(self.bb_period).std()
        df["bb_mid"] = sma
        df["bb_upper"] = sma + (self.bb_std * std)
        df["bb_lower"] = sma - (self.bb_std * std)

        # RSI calculation
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0).rolling(self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(self.rsi_period).mean()
        rs = gain / (loss + 1e-9)
        df["rsi"] = 100 - (100 / (1 + rs))

        curr_close = df["close"].iloc[-1]
        curr_rsi = float(df["rsi"].iloc[-1])
        bb_lower = df["bb_lower"].iloc[-1]
        bb_upper = df["bb_upper"].iloc[-1]
        bb_mid = df["bb_mid"].iloc[-1]

        signal = None

        # 1. Oversold + Lower Band touch OR Extreme Oversold (RSI <= 30) -> Close SHORT & Open LONG
        is_oversold_band = (curr_rsi <= 35.0 and curr_close <= bb_lower * 1.002)
        is_extreme_oversold = (curr_rsi <= 30.0)

        if (is_oversold_band or is_extreme_oversold) and (self.candle_count - self.last_signal_candle >= 3 or self.position_side != OrderSide.BUY):
            # If in SHORT, exit first
            if self.position_side == OrderSide.SELL:
                exit_signal = SignalEvent(
                    strategy_name=self.name,
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    price=curr_close,
                    timestamp=event.timestamp,
                    stop_loss=0.0,
                    take_profit=0.0,
                    confidence=0.75
                )
                await self.event_bus.publish(exit_signal)
                logger.info(f"[{self.name}] Closed SHORT at {curr_close} due to Oversold/Extreme RSI bounce")

            # Open LONG entry
            sl = round_price(curr_close * 0.985, curr_close)
            tp = round_price(bb_mid, curr_close)
            conf = 0.80 if is_extreme_oversold else 0.75
            signal = SignalEvent(
                strategy_name=self.name,
                symbol=self.symbol,
                side=OrderSide.BUY,
                price=curr_close,
                timestamp=event.timestamp,
                stop_loss=sl,
                take_profit=tp,
                confidence=conf
            )
            self.position_side = OrderSide.BUY
            self.last_signal_candle = self.candle_count
            logger.info(f"[{self.name}] BUY (LONG Mean Reversion) at {curr_close}, RSI: {curr_rsi:.1f}, SL: {sl}, TP: {tp}")

        # 2. Overbought + Upper Band touch OR Extreme Overbought (RSI >= 70) -> Close LONG & Open SHORT
        elif (curr_rsi >= 68.0 and curr_close >= bb_upper * 0.998 or curr_rsi >= 70.0) and (self.candle_count - self.last_signal_candle >= 3 or self.position_side != OrderSide.SELL):
            # If in LONG, exit first
            if self.position_side == OrderSide.BUY:
                exit_signal = SignalEvent(
                    strategy_name=self.name,
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    price=curr_close,
                    timestamp=event.timestamp,
                    stop_loss=0.0,
                    take_profit=0.0,
                    confidence=0.75
                )
                await self.event_bus.publish(exit_signal)
                logger.info(f"[{self.name}] Closed LONG at {curr_close} due to Overbought/Extreme RSI rejection")

            # Open SHORT entry
            sl = round_price(curr_close * 1.015, curr_close)
            tp = round_price(bb_mid, curr_close)
            conf = 0.80 if curr_rsi >= 70.0 else 0.75
            signal = SignalEvent(
                strategy_name=self.name,
                symbol=self.symbol,
                side=OrderSide.SELL,
                price=curr_close,
                timestamp=event.timestamp,
                stop_loss=sl,
                take_profit=tp,
                confidence=conf
            )
            self.position_side = OrderSide.SELL
            self.last_signal_candle = self.candle_count
            logger.info(f"[{self.name}] SELL (SHORT Mean Reversion) at {curr_close}, RSI: {curr_rsi:.1f}, SL: {sl}, TP: {tp}")

        if signal:
            await self.event_bus.publish(signal)
            return signal
        return None
