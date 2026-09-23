import logging
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from data.binance_client import BinanceClient
from config.settings import settings

logger = logging.getLogger("BacktestEngine")


class BacktestEngine:
    """
    GPTHEIST QUANTUM PROTOCOL - High-Performance Backtesting & Strategy Simulator.
    Simulates quantitative strategies on real historical Binance Futures candles
    with leverage, maker/taker fees, Hard Stop Loss, Take Profit, Break-Even Lock,
    and Dynamic ATR Trailing Stops.
    """

    def __init__(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        strategy: str = "EMA_TREND_MTF",
        initial_balance: float = 10000.0,
        position_pct: float = 0.20,
        leverage: float = 5.0,
        sl_pct: float = 0.015,
        tp_pct: float = 0.030,
        be_trigger_pct: float = 0.015,
        trail_callback_pct: float = 0.010,
        enable_trailing: bool = True,
        enable_break_even: bool = True,
        candle_limit: int = 500,
        binance_client: Optional[BinanceClient] = None
    ):
        self.symbol = symbol or "BTC/USDT"
        self.timeframe = timeframe or "15m"
        self.strategy = strategy or "EMA_CROSS"
        self.initial_balance = float(initial_balance or 10000.0)
        self.balance = self.initial_balance
        self.position_pct = float(position_pct or 0.20)
        self.leverage = float(leverage or 5.0)
        self.sl_pct = float(sl_pct or 0.015)
        self.tp_pct = float(tp_pct or 0.030)
        self.be_trigger_pct = float(be_trigger_pct or 0.015)
        self.trail_callback_pct = float(trail_callback_pct or 0.010)
        self.enable_trailing = bool(enable_trailing)
        self.enable_break_even = bool(enable_break_even)
        self.candle_limit = min(max(int(candle_limit or 500), 50), 1000)
        self.binance_client = binance_client

        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.peak_balance = self.initial_balance
        self.max_drawdown = 0.0
        self.max_drawdown_usdt = 0.0
        self.start_price = 0.0
        self.end_price = 0.0
        self.data_source = "unavailable"
        self.dataset_fingerprint = ""
        self.dataset_start = ""
        self.dataset_end = ""
        self.candles_fetched = 0
        self.open_position_at_end = False

    async def fetch_historical_data(self) -> pd.DataFrame:
        """Fetch historical OHLCV candles from Binance. Never substitute synthetic candles."""
        client = self.binance_client or BinanceClient()
        should_close = (self.binance_client is None)
        ohlcv = None
        try:
            fetch_limit = min(self.candle_limit, 1000)
            ohlcv = await client.fetch_ohlcv(symbol=self.symbol, timeframe=self.timeframe, limit=fetch_limit)
        except Exception as e:
            raise RuntimeError(f"Binance historical candle request failed: {e}") from e
        finally:
            if should_close:
                try:
                    await client.close()
                except Exception:
                    pass

        if not ohlcv or len(ohlcv) < 30:
            raise RuntimeError(
                f"Binance returned only {len(ohlcv) if ohlcv else 0} candles; at least 30 real candles are required"
            )

        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        self.data_source = "binance_live_rest_api"
        self.candles_fetched = int(len(df))
        self.dataset_start = df.iloc[0]["datetime"].isoformat()
        self.dataset_end = df.iloc[-1]["datetime"].isoformat()
        digest_payload = df[["timestamp", "open", "high", "low", "close", "volume"]].to_csv(
            index=False, float_format="%.10g"
        ).encode("utf-8")
        self.dataset_fingerprint = hashlib.sha256(digest_payload).hexdigest()[:20]
        self.start_price = float(df.iloc[0]["close"])
        self.end_price = float(df.iloc[-1]["close"])
        return df

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all quantitative technical indicators needed for strategies."""
        # 1. EMAs (9, 20, 50, 200)
        df["ema_9"] = df["close"].ewm(span=9, adjust=False).mean()
        df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
        df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()

        # 2. ATR 14
        hl = df["high"] - df["low"]
        hc = (df["high"] - df["close"].shift()).abs()
        lc = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        df["atr"] = tr.rolling(14).mean().fillna(0.0)

        # 3. RSI 14
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df["rsi"] = (100 - (100 / (1 + rs))).fillna(50.0)

        # 4. Bollinger Bands (20, 2.0)
        sma20 = df["close"].rolling(window=20).mean()
        std20 = df["close"].rolling(window=20).std()
        df["bb_upper"] = (sma20 + (std20 * 2.0)).fillna(df["close"])
        df["bb_lower"] = (sma20 - (std20 * 2.0)).fillna(df["close"])
        df["bb_mid"] = sma20.fillna(df["close"])

        # 5. Donchian Channel 20 (Breakout)
        df["donchian_high"] = df["high"].rolling(window=20).max().fillna(df["high"])
        df["donchian_low"] = df["low"].rolling(window=20).min().fillna(df["low"])
        df["volume_ma20"] = df["volume"].rolling(window=20).mean().fillna(df["volume"])

        return df

    def check_entry_signal(self, row: pd.Series, prev_row: pd.Series) -> Optional[str]:
        """Evaluate strategy entry rules on the current candle."""
        strat = (self.strategy or "EMA_CROSS").upper().replace("-", "_")
        curr_price = float(row["close"])
        rsi = float(row["rsi"]) if not np.isnan(row["rsi"]) else 50.0

        # Strategy 1: EMA 20/50 Multi-Timeframe Trend & Cross
        if any(k in strat for k in ("EMA", "TREND", "CROSS", "DEFAULT")):
            fast_curr, fast_prev = float(row["ema_20"]), float(prev_row["ema_20"])
            slow_curr, slow_prev = float(row["ema_50"]), float(prev_row["ema_50"])
            # Crossover or Trend Pullback to EMA20
            if (fast_prev <= slow_prev and fast_curr > slow_curr and rsi < 68) or \
               (fast_curr > slow_curr and float(row["low"]) <= fast_curr and curr_price > fast_curr and 42 <= rsi <= 64):
                return "LONG"
            elif (fast_prev >= slow_prev and fast_curr < slow_curr and rsi > 32) or \
                 (fast_curr < slow_curr and float(row["high"]) >= fast_curr and curr_price < fast_curr and 36 <= rsi <= 58):
                return "SHORT"

        # Strategy 2: RSI Divergence & Mean Reversion
        elif any(k in strat for k in ("RSI", "DIVERGENCE", "REVERSION")):
            bb_lower = float(row["bb_lower"])
            bb_upper = float(row["bb_upper"])
            prev_rsi = float(prev_row["rsi"]) if not np.isnan(prev_row["rsi"]) else 50.0
            # Oversold bounce
            if (float(row["low"]) <= bb_lower or prev_rsi < 32) and rsi > prev_rsi and curr_price > float(row["open"]):
                return "LONG"
            # Overbought rejection
            elif (float(row["high"]) >= bb_upper or prev_rsi > 68) and rsi < prev_rsi and curr_price < float(row["open"]):
                return "SHORT"

        # Strategy 3: Bollinger Bands / Donchian Breakout
        elif any(k in strat for k in ("BOLLINGER", "DONCHIAN", "BREAKOUT")):
            d_high_prev = float(prev_row["donchian_high"])
            d_low_prev = float(prev_row["donchian_low"])
            bb_upper = float(row["bb_upper"])
            bb_lower = float(row["bb_lower"])
            vol = float(row["volume"])
            vol_ma = float(row["volume_ma20"]) if not np.isnan(row["volume_ma20"]) else vol

            if (curr_price > d_high_prev or curr_price > bb_upper) and vol >= vol_ma * 1.05 and rsi > 52:
                return "LONG"
            elif (curr_price < d_low_prev or curr_price < bb_lower) and vol >= vol_ma * 1.05 and rsi < 48:
                return "SHORT"

        return None

    def run_simulation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute full backtest simulation over candles DataFrame."""
        self.trades = []
        self.equity_curve = [{
            "index": 0,
            "time": df.iloc[0]["datetime"].strftime("%Y-%m-%d %H:%M"),
            "balance": round(self.initial_balance, 2),
            "drawdown": 0.0,
            "buy_hold": round(self.initial_balance, 2)
        }]
        self.balance = self.initial_balance
        self.peak_balance = self.initial_balance
        self.max_drawdown = 0.0
        self.max_drawdown_usdt = 0.0

        position = None
        first_close = float(df.iloc[0]["close"])

        for i in range(25, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i - 1]
            curr_price = float(row["close"])
            curr_high = float(row["high"])
            curr_low = float(row["low"])
            curr_time = row["datetime"]
            curr_time_str = curr_time.strftime("%Y-%m-%d %H:%M")

            # 1. Update Existing Position (Check TP, SL, Trailing Stop, Break-Even)
            if position is not None:
                side = position["side"]
                entry_p = position["entry_price"]
                sl = position["sl"]
                tp = position["tp"]
                cost = position["cost"]

                exit_price = None
                exit_reason = None

                if side == "LONG":
                    # Stops active at candle open are evaluated before any new
                    # intrabar high. This avoids look-ahead from moving a stop
                    # using a high that may have occurred after the candle low.
                    if curr_low <= position["sl"]:
                        exit_price = position["sl"]
                        if position["be_active"] and abs(exit_price - entry_p) / entry_p < 0.003:
                            exit_reason = "BREAK_EVEN"
                        elif position["be_active"]:
                            exit_reason = "TRAILING_STOP"
                        else:
                            exit_reason = "STOP_LOSS"
                    elif curr_high >= tp:
                        exit_price = tp
                        exit_reason = "TAKE_PROFIT"

                    if exit_price is None:
                        position["peak_price"] = max(position["peak_price"], curr_high)
                        if self.enable_break_even and not position["be_active"] and (position["peak_price"] - entry_p) / entry_p >= self.be_trigger_pct:
                            position["be_active"] = True
                            position["sl"] = max(position["sl"], entry_p * 1.0005)
                        if self.enable_trailing and position["be_active"]:
                            position["sl"] = max(position["sl"], position["peak_price"] * (1.0 - self.trail_callback_pct))

                elif side == "SHORT":
                    if curr_high >= position["sl"]:
                        exit_price = position["sl"]
                        if position["be_active"] and abs(exit_price - entry_p) / entry_p < 0.003:
                            exit_reason = "BREAK_EVEN"
                        elif position["be_active"]:
                            exit_reason = "TRAILING_STOP"
                        else:
                            exit_reason = "STOP_LOSS"
                    elif curr_low <= tp:
                        exit_price = tp
                        exit_reason = "TAKE_PROFIT"

                    if exit_price is None:
                        position["peak_price"] = min(position["peak_price"], curr_low)
                        if self.enable_break_even and not position["be_active"] and (entry_p - position["peak_price"]) / entry_p >= self.be_trigger_pct:
                            position["be_active"] = True
                            position["sl"] = min(position["sl"], entry_p * 0.9995)
                        if self.enable_trailing and position["be_active"]:
                            position["sl"] = min(position["sl"], position["peak_price"] * (1.0 + self.trail_callback_pct))

                # If Position Closed on this candle
                if exit_price is not None:
                    if side == "LONG":
                        pnl_pct = (exit_price - entry_p) / entry_p
                    else:
                        pnl_pct = (entry_p - exit_price) / entry_p

                    # PnL with leverage
                    pnl_usdt = cost * pnl_pct * self.leverage
                    # Binance Taker Fee (0.05% on notional both sides)
                    fee = (cost * self.leverage) * 0.0005 * 2
                    net_pnl = pnl_usdt - fee

                    self.balance += net_pnl
                    if self.balance > self.peak_balance:
                        self.peak_balance = self.balance
                    dd = ((self.peak_balance - self.balance) / self.peak_balance) * 100.0 if self.peak_balance > 0 else 0.0
                    dd_usdt = self.peak_balance - self.balance
                    if dd > self.max_drawdown:
                        self.max_drawdown = dd
                    if dd_usdt > self.max_drawdown_usdt:
                        self.max_drawdown_usdt = dd_usdt

                    # Trade duration
                    entry_dt = position["entry_dt"]
                    diff_mins = int((curr_time - entry_dt).total_seconds() / 60)
                    hrs = diff_mins // 60
                    mins = diff_mins % 60
                    duration_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins}m"

                    self.trades.append({
                        "id": len(self.trades) + 1,
                        "side": side,
                        "entry_time": position["entry_time"],
                        "exit_time": curr_time_str,
                        "duration": duration_str,
                        "duration_mins": diff_mins,
                        "entry_price": round(entry_p, 2),
                        "exit_price": round(exit_price, 2),
                        "pnl_pct": round(pnl_pct * self.leverage * 100.0, 2),
                        "pnl_usdt": round(net_pnl, 2),
                        "fee": round(fee, 2),
                        "reason": exit_reason,
                        "balance_after": round(self.balance, 2)
                    })
                    position = None

            # 2. Check Entry Signals if Not In Position
            if position is None:
                signal = self.check_entry_signal(row, prev_row)
                if signal == "LONG":
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
                        "entry_time": curr_time_str,
                        "entry_dt": curr_time
                    }
                elif signal == "SHORT":
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
                        "entry_time": curr_time_str,
                        "entry_dt": curr_time
                    }

            # Record mark-to-market equity on every candle, not just closed
            # trades. This makes the curve and maximum drawdown meaningful.
            mark_equity = self.balance
            if position is not None:
                entry_p = position["entry_price"]
                move = (curr_price - entry_p) / entry_p if position["side"] == "LONG" else (entry_p - curr_price) / entry_p
                estimated_roundtrip_fee = (position["cost"] * self.leverage) * 0.0005 * 2
                mark_equity += position["cost"] * move * self.leverage - estimated_roundtrip_fee
            self.peak_balance = max(self.peak_balance, mark_equity)
            mark_dd_usdt = max(0.0, self.peak_balance - mark_equity)
            mark_dd = (mark_dd_usdt / self.peak_balance * 100.0) if self.peak_balance else 0.0
            self.max_drawdown = max(self.max_drawdown, mark_dd)
            self.max_drawdown_usdt = max(self.max_drawdown_usdt, mark_dd_usdt)
            self.equity_curve.append({
                "index": i - 24,
                "time": curr_time_str,
                "balance": round(mark_equity, 2),
                "drawdown": round(mark_dd, 2),
                "buy_hold": round(self.initial_balance * (curr_price / first_close), 2)
            })

        self.open_position_at_end = position is not None
        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        """Compute aggregate performance statistics."""
        total_trades = len(self.trades)
        wins = [t for t in self.trades if t["pnl_usdt"] > 0]
        losses = [t for t in self.trades if t["pnl_usdt"] <= 0]
        win_rate = (len(wins) / total_trades * 100.0) if total_trades > 0 else 0.0

        gross_profit = sum(t["pnl_usdt"] for t in wins)
        gross_loss = abs(sum(t["pnl_usdt"] for t in losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None

        net_pnl = self.balance - self.initial_balance
        roi_pct = (net_pnl / self.initial_balance) * 100.0

        tp_hits = sum(1 for t in self.trades if t["reason"] == "TAKE_PROFIT")
        trail_hits = sum(1 for t in self.trades if t["reason"] == "TRAILING_STOP")
        be_hits = sum(1 for t in self.trades if t["reason"] == "BREAK_EVEN")
        sl_hits = sum(1 for t in self.trades if t["reason"] == "STOP_LOSS")

        tp_pct = round(tp_hits / total_trades * 100.0, 1) if total_trades > 0 else 0.0
        sl_pct = round(sl_hits / total_trades * 100.0, 1) if total_trades > 0 else 0.0
        tr_pct = round(trail_hits / total_trades * 100.0, 1) if total_trades > 0 else 0.0
        be_pct = round(be_hits / total_trades * 100.0, 1) if total_trades > 0 else 0.0

        # Sharpe ratio calculation
        if total_trades >= 2:
            pnls = [t["pnl_pct"] for t in self.trades]
            std_pnl = float(np.std(pnls))
            mean_pnl = float(np.mean(pnls))
            sharpe = (mean_pnl / (std_pnl + 1e-9)) * np.sqrt(min(total_trades, 50))
            sharpe = round(max(-3.0, min(4.5, sharpe)), 2)
        else:
            sharpe = 0.0

        # Averages
        avg_win_pct = round(np.mean([t["pnl_pct"] for t in wins]), 2) if wins else 0.0
        avg_loss_pct = round(np.mean([abs(t["pnl_pct"]) for t in losses]), 2) if losses else 0.0
        avg_rr = round(avg_win_pct / (avg_loss_pct + 1e-9), 2) if avg_loss_pct > 0 else 0.0

        durations = [t["duration_mins"] for t in self.trades if "duration_mins" in t]
        avg_dur_mins = int(np.mean(durations)) if durations else 0
        avg_dur_str = f"{avg_dur_mins // 60}h {avg_dur_mins % 60}m" if durations else ""

        total_fees = round(sum(t.get("fee", 0.0) for t in self.trades), 2)

        # Buy & Hold Return
        bh_roi = round(((self.end_price - self.start_price) / self.start_price * 100.0), 2) if self.start_price > 0 else 0.0

        # Monthly return aggregation
        monthly_map: Dict[str, float] = {}
        for t in self.trades:
            m = t["exit_time"][:7] if len(t.get("exit_time", "")) >= 7 else "2026-09"
            monthly_map[m] = monthly_map.get(m, 0.0) + t["pnl_usdt"]

        monthly_returns = []
        for m, pnl in sorted(monthly_map.items()):
            monthly_returns.append({
                "month": m,
                "pnl_usdt": round(pnl, 2),
                "roi_pct": round((pnl / self.initial_balance) * 100.0, 2)
            })

        # Drawdown distribution histogram bins
        dd_bins = [0] * 10
        for pt in self.equity_curve:
            d = pt.get("drawdown", 0.0)
            bin_idx = min(int(d / 3.0), 9)
            dd_bins[bin_idx] += 1

        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "strategy": self.strategy,
            "candle_limit": self.candle_limit,
            "initial_balance": round(self.initial_balance, 2),
            "final_balance": round(self.balance, 2),
            "net_pnl_usdt": round(net_pnl, 2),
            "roi_pct": round(roi_pct, 2),
            "total_trades": total_trades,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
            "metrics_reliable": total_trades >= 20,
            "max_drawdown": round(self.max_drawdown, 2),
            "max_drawdown_usdt": round(self.max_drawdown_usdt, 2),
            "sharpe_ratio": sharpe,
            "avg_win_pct": avg_win_pct,
            "avg_loss_pct": avg_loss_pct,
            "avg_rr": avg_rr,
            "avg_duration": avg_dur_str,
            "total_fees": total_fees,
            "buy_and_hold_roi_pct": bh_roi,
            "provenance": {
                "source": self.data_source,
                "synthetic_used": False,
                "candles_requested": self.candle_limit,
                "candles_fetched": self.candles_fetched,
                "dataset_start": self.dataset_start,
                "dataset_end": self.dataset_end,
                "dataset_fingerprint": self.dataset_fingerprint,
                "engine_version": "astra-backtest-2.0",
                "open_position_at_end": self.open_position_at_end,
                "assumptions": [
                    "Market orders use candle OHLC with stop-first handling when TP and SL overlap",
                    "Taker fee is fixed at 0.05% per side",
                    "Funding, latency and additional slippage are not modeled",
                    "Any open position at dataset end is excluded from realized PnL",
                    "Stops updated from a candle high/low become active on the next candle",
                    "Metrics based on fewer than 20 closed trades are flagged as low-sample"
                ]
            },
            "distribution": {
                "take_profit": tp_hits,
                "stop_loss": sl_hits,
                "trailing_stop": trail_hits,
                "break_even": be_hits,
                "tp_pct": tp_pct,
                "sl_pct": sl_pct,
                "tr_pct": tr_pct,
                "be_pct": be_pct
            },
            "monthly_returns": monthly_returns,
            "dd_bins": dd_bins,
            "equity_curve": self.equity_curve,
            "trades": list(reversed(self.trades))  # Most recent trades first
        }
