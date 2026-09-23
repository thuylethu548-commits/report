import logging
from typing import Optional
import numpy as np
import pandas as pd
from core.events import MarketEvent, SignalEvent
from core.event_bus import EventBus
from core.constants import OrderSide, round_price
from .base_strategy import BaseStrategy

logger = logging.getLogger("EMATrendStrategy")


class EMATrendStrategy(BaseStrategy):
    def __init__(self, symbol: str, event_bus: EventBus, fast_period: int = 9, slow_period: int = 21, atr_period: int = 14):
        super().__init__(name="EMA_Trend", symbol=symbol, event_bus=event_bus, max_candles=100)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.atr_period = atr_period
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
        if len(df) < self.slow_period + 2:
            return None

        # Calculate EMAs
        df["ema_fast"] = df["close"].ewm(span=self.fast_period, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=self.slow_period, adjust=False).mean()

        # Calculate True Range & ATR
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(self.atr_period).mean().iloc[-1]
        if np.isnan(atr) or atr <= 0:
            atr = event.close * 0.015

        # Calculate RSI for pullback momentum validation
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        curr_rsi = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0

        prev_fast = df["ema_fast"].iloc[-2]
        prev_slow = df["ema_slow"].iloc[-2]
        curr_fast = df["ema_fast"].iloc[-1]
        curr_slow = df["ema_slow"].iloc[-1]

        curr_close = df["close"].iloc[-1]
        curr_open = df["open"].iloc[-1]
        prev_low = df["low"].iloc[-2]
        curr_low = df["low"].iloc[-1]
        prev_high = df["high"].iloc[-2]
        curr_high = df["high"].iloc[-1]

        price = event.close
        signal = None

        # 1. Golden Cross -> Close SHORT (if any) & Open LONG
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            # If currently in SHORT, exit first
            if self.position_side == OrderSide.SELL:
                exit_signal = SignalEvent(
                    strategy_name=self.name,
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    price=price,
                    timestamp=event.timestamp,
                    stop_loss=0.0,
                    take_profit=0.0,
                    confidence=0.85
                )
                await self.event_bus.publish(exit_signal)
                logger.info(f"[{self.name}] Closed SHORT position at {price} due to Golden Cross")

            # Open LONG entry
            sl = round_price(price - (1.5 * atr), price)
            tp = round_price(price + (3.0 * atr), price)
            signal = SignalEvent(
                strategy_name=self.name,
                symbol=self.symbol,
                side=OrderSide.BUY,
                price=price,
                timestamp=event.timestamp,
                stop_loss=sl,
                take_profit=tp,
                confidence=0.85
            )
            self.position_side = OrderSide.BUY
            self.last_signal_candle = self.candle_count
            logger.info(f"[{self.name}] BUY (LONG Golden Cross) at {price}, SL: {sl}, TP: {tp}")

        # 2. Death Cross -> Close LONG (if any) & Open SHORT
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            # If currently in LONG, exit first
            if self.position_side == OrderSide.BUY:
                exit_signal = SignalEvent(
                    strategy_name=self.name,
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    price=price,
                    timestamp=event.timestamp,
                    stop_loss=0.0,
                    take_profit=0.0,
                    confidence=0.80
                )
                await self.event_bus.publish(exit_signal)
                logger.info(f"[{self.name}] Closed LONG position at {price} due to Death Cross")

            # Open SHORT entry
            sl = round_price(price + (1.5 * atr), price)
            tp = round_price(price - (3.0 * atr), price)
            signal = SignalEvent(
                strategy_name=self.name,
                symbol=self.symbol,
                side=OrderSide.SELL,
                price=price,
                timestamp=event.timestamp,
                stop_loss=sl,
                take_profit=tp,
                confidence=0.85
            )
            self.position_side = OrderSide.SELL
            self.last_signal_candle = self.candle_count
            logger.info(f"[{self.name}] SELL (SHORT Death Cross) at {price}, SL: {sl}, TP: {tp}")

        # 3. Bull Trend Pullback Continuation (Bắt nhịp hồi quy bám sóng Tăng)
        elif (curr_fast > curr_slow and 
              self.candle_count - self.last_signal_candle >= 3 and 
              self.position_side != OrderSide.BUY):
            # Price dipped near or touched EMA fast on previous or current candle, and confirmed bounce green
            min_dip = min(prev_low, curr_low)
            if min_dip <= curr_fast * 1.006 and curr_close > curr_open and curr_close >= curr_fast * 0.998 and 38.0 <= curr_rsi <= 65.0:
                sl = round_price(price - (1.5 * atr), price)
                tp = round_price(price + (3.0 * atr), price)
                signal = SignalEvent(
                    strategy_name=self.name,
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    price=price,
                    timestamp=event.timestamp,
                    stop_loss=sl,
                    take_profit=tp,
                    confidence=0.80
                )
                self.position_side = OrderSide.BUY
                self.last_signal_candle = self.candle_count
                logger.info(f"[{self.name}] BUY (LONG Trend Pullback) at {price}, RSI: {curr_rsi:.1f}, SL: {sl}, TP: {tp}")

        # 4. Bear Trend Pullback Continuation (Bắt nhịp hồi quy bám sóng Giảm)
        elif (curr_fast < curr_slow and 
              self.candle_count - self.last_signal_candle >= 3 and 
              self.position_side != OrderSide.SELL):
            # Price pulled up near or touched EMA fast on previous or current candle, and confirmed rejection red
            max_pull = max(prev_high, curr_high)
            if max_pull >= curr_fast * 0.994 and curr_close < curr_open and curr_close <= curr_fast * 1.002 and 35.0 <= curr_rsi <= 62.0:
                sl = round_price(price + (1.5 * atr), price)
                tp = round_price(price - (3.0 * atr), price)
                signal = SignalEvent(
                    strategy_name=self.name,
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    price=price,
                    timestamp=event.timestamp,
                    stop_loss=sl,
                    take_profit=tp,
                    confidence=0.80
                )
                self.position_side = OrderSide.SELL
                self.last_signal_candle = self.candle_count
                logger.info(f"[{self.name}] SELL (SHORT Trend Pullback) at {price}, RSI: {curr_rsi:.1f}, SL: {sl}, TP: {tp}")

        if signal:
            await self.event_bus.publish(signal)
            return signal
        return None
