import logging
from typing import Dict, Any, Optional
import pandas as pd
from config.settings import settings

logger = logging.getLogger("SpotDCAStrategy")


class SpotDCAStrategy:
    """
    Smart DCA & Trend Swing Strategy for Spot Trading:
    - 500U Bitcoin Dedicated Pyramid DCA:
      * Tier 1 (30% = 150 USDT): Anchor buy at market price ($85.5k - $86.5k).
      * Tier 2 (40% = 200 USDT): Dip accumulation at support level ($82.8k - $83.8k).
      * Tier 3 (30% = 150 USDT): Deep flash crash reserve ($80.0k - $81.5k).
      * Take-Profit Ladder: Step 1 (33% @ $90k), Step 2 (33% @ $93k), Step 3 (34% @ $95k+).
    - General DCA for other Spot coins (ETH/SOL) with RSI oversold (< 35) & step TP.
    """
    def __init__(
        self,
        total_capital_usdt: float = 500.0,
        tranche_usdt: float = 15.0,
        max_tranches: int = 4
    ):
        self.total_capital_usdt = total_capital_usdt
        self.tranche_usdt = tranche_usdt
        self.max_tranches = max_tranches
        
        # State tracking for BTC Pyramid DCA
        self.btc_tier1_filled = False
        self.btc_tier1_price = 0.0
        self.btc_tier2_filled = False
        self.btc_tier2_price = 0.0
        self.btc_tier3_filled = False
        self.btc_tier3_price = 0.0
        self.btc_tp1_filled = False
        self.btc_tp2_filled = False
        self.btc_tp3_filled = False

    def evaluate_signal(
        self,
        symbol: str,
        df: pd.DataFrame,
        current_holding: Dict[str, float],
        ai_regime: Optional[str] = None
    ) -> Dict[str, Any]:
        if df is None or len(df) < 20:
            return {"action": "HOLD", "reason": "Insufficient candles"}

        close = float(df["close"].iloc[-1])
        hold_qty = float(current_holding.get("amount", 0.0))
        avg_price = float(current_holding.get("avg_price", 0.0))

        # --- 1. SPECIAL 500U BTC PYRAMID DCA STRATEGY ---
        if symbol == "BTC/USDT" and getattr(settings, "SPOT_BTC_PYRAMID_DCA", True):
            total_budget = self.total_capital_usdt or getattr(settings, "SPOT_STARTING_BALANCE_USDT", 500.0)
            t1_amt = total_budget * getattr(settings, "SPOT_BTC_TIER1_RATIO", 0.30)
            t2_amt = total_budget * getattr(settings, "SPOT_BTC_TIER2_RATIO", 0.40)
            t3_amt = total_budget * getattr(settings, "SPOT_BTC_TIER3_RATIO", 0.30)
            
            tp1_target = getattr(settings, "SPOT_BTC_TP1_PRICE", 90000.0)
            tp2_target = getattr(settings, "SPOT_BTC_TP2_PRICE", 93000.0)
            tp3_target = getattr(settings, "SPOT_BTC_TP3_PRICE", 95000.0)

            # 1.1 Take-Profit Ladder
            if hold_qty > 0 and avg_price > 0:
                if close >= tp3_target and not self.btc_tp3_filled:
                    self.btc_tp3_filled = True
                    return {
                        "action": "SELL",
                        "percent": 100.0,
                        "price": close,
                        "reason": f"BTC_TP3_LADDER: Reached ${close:,.1f} >= ${tp3_target:,.1f} (Take all remaining)"
                    }
                elif close >= tp2_target and not self.btc_tp2_filled:
                    self.btc_tp2_filled = True
                    return {
                        "action": "SELL",
                        "percent": 33.0,
                        "price": close,
                        "reason": f"BTC_TP2_LADDER: Reached ${close:,.1f} >= ${tp2_target:,.1f} (Lock 33%)"
                    }
                elif close >= tp1_target and not self.btc_tp1_filled:
                    self.btc_tp1_filled = True
                    return {
                        "action": "SELL",
                        "percent": 33.0,
                        "price": close,
                        "reason": f"BTC_TP1_LADDER: Reached ${close:,.1f} >= ${tp1_target:,.1f} (Lock 33%)"
                    }

            # 1.2 Pyramid DCA Accumulation Ladder
            if hold_qty <= 0 or not self.btc_tier1_filled:
                # Tier 1: Anchor Entry (30% = 150 USDT)
                self.btc_tier1_filled = True
                self.btc_tier1_price = close
                return {
                    "action": "BUY",
                    "usdt_amount": t1_amt,
                    "price": close,
                    "reason": f"BTC_TIER_1_ANCHOR (30% = ${t1_amt:.0f} USDT @ ${close:,.1f})"
                }

            anchor_price = self.btc_tier1_price or avg_price
            
            # Tier 2: Dip support accumulation (40% = 200 USDT) when price pulls back >= 3.5% or <= $83,800
            t2_trigger_price = max(anchor_price * 0.965, 83800.0)
            if not self.btc_tier2_filled and close <= t2_trigger_price:
                self.btc_tier2_filled = True
                self.btc_tier2_price = close
                return {
                    "action": "BUY",
                    "usdt_amount": t2_amt,
                    "price": close,
                    "reason": f"BTC_TIER_2_SUPPORT_DIP (40% = ${t2_amt:.0f} USDT @ ${close:,.1f} <= ${t2_trigger_price:,.1f})"
                }

            # Tier 3: Flash crash reserve (30% = 150 USDT) when price pulls back >= 6.5% or <= $81,500
            t3_trigger_price = max(anchor_price * 0.935, 81500.0)
            if not self.btc_tier3_filled and close <= t3_trigger_price:
                self.btc_tier3_filled = True
                self.btc_tier3_price = close
                return {
                    "action": "BUY",
                    "usdt_amount": t3_amt,
                    "price": close,
                    "reason": f"BTC_TIER_3_FLASH_CRASH_DISCOUNT (30% = ${t3_amt:.0f} USDT @ ${close:,.1f} <= ${t3_trigger_price:,.1f})"
                }

            return {
                "action": "HOLD",
                "reason": f"BTC Pyramid In Position (Hold: {hold_qty:.6f}, Avg: ${avg_price:,.1f}, Current: ${close:,.1f})"
            }

        # --- 2. GENERAL SPOT DCA LOGIC (For ETH/SOL) ---
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, 1e-9)
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        if hold_qty > 0 and avg_price > 0:
            gain_pct = (close - avg_price) / avg_price
            if gain_pct >= 0.10:
                return {"action": "SELL", "percent": 50.0, "reason": f"TP2 (+{gain_pct*100:.1f}%) reached", "price": close}
            elif gain_pct >= 0.05:
                return {"action": "SELL", "percent": 30.0, "reason": f"TP1 (+{gain_pct*100:.1f}%) reached", "price": close}

        is_oversold = rsi < 35.0
        is_bull_ai = ai_regime in ("bull_trend", "BULL_TREND")

        if is_oversold or is_bull_ai:
            reason = "RSI_OVERSOLD" if is_oversold else "AI_BULL_TREND"
            return {
                "action": "BUY",
                "usdt_amount": self.tranche_usdt,
                "price": close,
                "reason": f"{reason} (RSI={rsi:.1f}, AI={ai_regime})"
            }

        return {"action": "HOLD", "reason": f"Waiting for entry (RSI={rsi:.1f})"}
