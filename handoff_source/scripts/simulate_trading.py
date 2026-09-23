import asyncio
import sys
import os
from datetime import datetime, timezone
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.binance_client import BinanceClient
from config.settings import settings


class TradeSimulator:
    def __init__(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        initial_balance: float = 100.0,
        position_pct: float = 0.20,
        leverage: float = 5.0,
        sl_pct: float = 0.015,       # 1.5% Stop Loss
        tp_pct: float = 0.030,       # 3.0% Take Profit
        be_trigger_pct: float = 0.015, # Break-even trigger at 1.5% profit
        trail_callback_pct: float = 0.010, # Trailing distance 1.0%
        candle_limit: int = 1000
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.position_pct = position_pct
        self.leverage = leverage
        self.sl_pct = sl_pct
        self.tp_pct = tp_pct
        self.be_trigger_pct = be_trigger_pct
        self.trail_callback_pct = trail_callback_pct
        self.candle_limit = candle_limit

        self.trades = []
        self.equity_curve = [initial_balance]
        self.peak_balance = initial_balance
        self.max_drawdown = 0.0

    async def fetch_data(self) -> pd.DataFrame:
        client = BinanceClient()
        print(f"[1/4] Dang tai {self.candle_limit} nen {self.timeframe} cua {self.symbol} tu Binance Live...")
        ohlcv = await client.fetch_ohlcv(symbol=self.symbol, timeframe=self.timeframe, limit=self.candle_limit)
        await client.close()

        if not ohlcv:
            raise ValueError(f"Khong the lay du lieu nen tu Binance cho {self.symbol}")

        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f"[2/4] Dang tinh toan cac chi bao ky thuat (EMA 9/21, RSI 14, ATR)...")
        # EMA 9 & 21
        df["ema_fast"] = df["close"].ewm(span=9, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=21, adjust=False).mean()

        # ATR 14
        hl = df["high"] - df["low"]
        hc = (df["high"] - df["close"].shift()).abs()
        lc = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        df["atr"] = tr.rolling(14).mean()

        # RSI 14
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df["rsi"] = 100 - (100 / (1 + rs))

        return df

    def run_simulation(self, df: pd.DataFrame):
        print(f"[3/4] Dang gia lap mo phong giao dich 2 chieu (Long/Short) kem Trailing Stop...")
        position = None

        for i in range(25, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i - 1]
            curr_price = float(row["close"])
            curr_high = float(row["high"])
            curr_low = float(row["low"])
            curr_time = row["datetime"]

            # 1. Update Existing Position (Check TP, SL, Trailing Stop)
            if position is not None:
                side = position["side"]
                entry_p = position["entry_price"]
                sl = position["sl"]
                tp = position["tp"]
                cost = position["cost"]
                qty = position["qty"]

                exit_price = None
                exit_reason = None

                if side == "LONG":
                    # Update peak price
                    if curr_high > position["peak_price"]:
                        position["peak_price"] = curr_high

                    # Check Break-Even Lock: if profit >= be_trigger_pct
                    if not position["be_active"] and (position["peak_price"] - entry_p) / entry_p >= self.be_trigger_pct:
                        position["be_active"] = True
                        position["sl"] = max(position["sl"], entry_p * 1.001)

                    # Dynamic Trailing Stop update
                    if position["be_active"]:
                        new_trail_sl = position["peak_price"] * (1.0 - self.trail_callback_pct)
                        if new_trail_sl > position["sl"]:
                            position["sl"] = new_trail_sl

                    # Check Stop Loss / Trailing Hit
                    if curr_low <= position["sl"]:
                        exit_price = position["sl"]
                        exit_reason = "TRAILING_STOP" if position["be_active"] else "STOP_LOSS"
                    # Check Take Profit
                    elif curr_high >= tp:
                        exit_price = tp
                        exit_reason = "TAKE_PROFIT"

                elif side == "SHORT":
                    # Update peak price (for short, lowest is peak)
                    if curr_low < position["peak_price"]:
                        position["peak_price"] = curr_low

                    # Check Break-Even Lock: if price dropped >= be_trigger_pct
                    if not position["be_active"] and (entry_p - position["peak_price"]) / entry_p >= self.be_trigger_pct:
                        position["be_active"] = True
                        position["sl"] = min(position["sl"], entry_p * 0.999)

                    # Dynamic Trailing Stop for Short
                    if position["be_active"]:
                        new_trail_sl = position["peak_price"] * (1.0 + self.trail_callback_pct)
                        if new_trail_sl < position["sl"]:
                            position["sl"] = new_trail_sl

                    # Check Stop Loss / Trailing Hit for Short
                    if curr_high >= position["sl"]:
                        exit_price = position["sl"]
                        exit_reason = "TRAILING_STOP" if position["be_active"] else "STOP_LOSS"
                    elif curr_low <= tp:
                        exit_price = tp
                        exit_reason = "TAKE_PROFIT"

                # If Position Closed
                if exit_price is not None:
                    if side == "LONG":
                        pnl_pct = (exit_price - entry_p) / entry_p
                    else:
                        pnl_pct = (entry_p - exit_price) / entry_p

                    # PnL with leverage
                    pnl_usdt = cost * pnl_pct * self.leverage
                    # Fee 0.05% on notional
                    fee = (cost * self.leverage) * 0.0005 * 2
                    net_pnl = pnl_usdt - fee

                    self.balance += net_pnl
                    if self.balance > self.peak_balance:
                        self.peak_balance = self.balance
                    dd = (self.peak_balance - self.balance) / self.peak_balance * 100.0
                    if dd > self.max_drawdown:
                        self.max_drawdown = dd

                    self.equity_curve.append(self.balance)
                    self.trades.append({
                        "id": len(self.trades) + 1,
                        "side": side,
                        "entry_time": position["entry_time"],
                        "exit_time": curr_time,
                        "entry_price": entry_p,
                        "exit_price": exit_price,
                        "pnl_pct": pnl_pct * self.leverage * 100.0,
                        "pnl_usdt": net_pnl,
                        "balance_after": self.balance,
                        "reason": exit_reason
                    })
                    position = None

            # 2. Check Entry Signals if Not In Position
            if position is None:
                fast_prev = prev_row["ema_fast"]
                slow_prev = prev_row["ema_slow"]
                fast_curr = row["ema_fast"]
                slow_curr = row["ema_slow"]
                rsi = row["rsi"]

                # Golden Cross + Healthy RSI -> LONG
                if fast_prev <= slow_prev and fast_curr > slow_curr and rsi < 70:
                    cost = self.balance * self.position_pct
                    sl = curr_price * (1.0 - self.sl_pct)
                    tp = curr_price * (1.0 + self.tp_pct)
                    position = {
                        "side": "LONG",
                        "entry_price": curr_price,
                        "qty": (cost * self.leverage) / curr_price,
                        "cost": cost,
                        "sl": sl,
                        "tp": tp,
                        "peak_price": curr_price,
                        "be_active": False,
                        "entry_time": curr_time
                    }

                # Death Cross + RSI not oversold -> SHORT
                elif fast_prev >= slow_prev and fast_curr < slow_curr and rsi > 30:
                    cost = self.balance * self.position_pct
                    sl = curr_price * (1.0 + self.sl_pct)
                    tp = curr_price * (1.0 - self.tp_pct)
                    position = {
                        "side": "SHORT",
                        "entry_price": curr_price,
                        "qty": (cost * self.leverage) / curr_price,
                        "cost": cost,
                        "sl": sl,
                        "tp": tp,
                        "peak_price": curr_price,
                        "be_active": False,
                        "entry_time": curr_time
                    }

    def print_report(self):
        print("\n" + "=" * 70)
        print(f"      KET QUA GIA LAP TRADE (BACKTEST SIMULATION) - {self.symbol}")
        print("=" * 70)
        print(f"Khung thoi gian:     {self.timeframe} (1000 nen gan nhat tu Binance Live)")
        print(f"Von ban dau:         ${self.initial_balance:.2f} USDT | Don bay: {self.leverage:.0f}x")
        print(f"Quan tri von:        {self.position_pct*100:.0f}% moi lenh | SL: {self.sl_pct*100:.1f}% | TP: {self.tp_pct*100:.1f}%")
        print(f"Trailing Stop:       Khoa hoa von tai +{self.be_trigger_pct*100:.1f}% | Trailing +{self.trail_callback_pct*100:.1f}%")
        print("-" * 70)

        total_trades = len(self.trades)
        if total_trades == 0:
            print("Khong co lenh nao duoc sinh ra trong giai doan nay.")
            return

        wins = [t for t in self.trades if t["pnl_usdt"] > 0]
        losses = [t for t in self.trades if t["pnl_usdt"] <= 0]
        win_rate = (len(wins) / total_trades) * 100.0

        gross_profit = sum(t["pnl_usdt"] for t in wins)
        gross_loss = abs(sum(t["pnl_usdt"] for t in losses)) if losses else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 999.0
        net_profit = self.balance - self.initial_balance
        roi_pct = (net_profit / self.initial_balance) * 100.0

        tp_count = sum(1 for t in self.trades if t["reason"] == "TAKE_PROFIT")
        trail_count = sum(1 for t in self.trades if t["reason"] == "TRAILING_STOP")
        sl_count = sum(1 for t in self.trades if t["reason"] == "STOP_LOSS")

        print(f"TONG SO LENH:        {total_trades} lenh ({len(wins)} Thang / {len(losses)} Thua)")
        print(f"TY LE THANG (WIN%):  {win_rate:.1f}%")
        print(f"SO DU CUOI CUNG:     ${self.balance:.2f} USDT")
        print(f"LOI NHUAN RONG:      ${net_profit:+.2f} USDT ({roi_pct:+.2f}% ROI)")
        print(f"PROFIT FACTOR:       {profit_factor:.2f}")
        print(f"MAX DRAWDOWN:        {self.max_drawdown:.2f}%")
        print(f"PHAN BO DONG LENH:   Take Profit: {tp_count} | Trailing Stop (Chot loi dong): {trail_count} | Stop Loss: {sl_count}")
        print("=" * 70)

        # Print top trades
        print("\n--- 10 LENH GAN NHAT TRONG MO PHONG ---")
        header = f"{'#':<3} {'SIDE':<6} {'ENTRY':<9} {'EXIT':<9} {'PNL (%)':<10} {'PNL ($)':<10} {'REASON':<15}"
        print(header)
        print("-" * len(header))
        for t in self.trades[-10:]:
            side_badge = "LONG" if t["side"] == "LONG" else "SHORT"
            pnl_str = f"{t['pnl_pct']:+.2f}%"
            usd_str = f"${t['pnl_usdt']:+.2f}"
            print(f"{t['id']:<3} {side_badge:<6} {t['entry_price']:<9.1f} {t['exit_price']:<9.1f} {pnl_str:<10} {usd_str:<10} {t['reason']:<15}")
        print("=" * 70)


async def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')

    sim = TradeSimulator(
        symbol="BTC/USDT",
        timeframe="15m",
        initial_balance=100.0,
        position_pct=0.20,
        leverage=5.0,
        candle_limit=1000
    )
    df = await sim.fetch_data()
    df = sim.compute_indicators(df)
    sim.run_simulation(df)
    sim.print_report()


if __name__ == "__main__":
    asyncio.run(main())
