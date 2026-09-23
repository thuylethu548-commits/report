import asyncio
import sys
import os
import logging
import json
from datetime import datetime, timezone
import httpx
import ccxt.async_support as ccxt

# Add project root
sys.path.insert(0, r'c:\sunMy\trading_bot')

from config.settings import settings
from data.storage import Database
from ai_advisory.vyce_client import VyceClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [SpotSniper] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("SpotSniper")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ═══════════════════════════════════════════════════════════
# STRATEGY CONFIG - 3 LAYER SYSTEM
# ═══════════════════════════════════════════════════════════
API_BASE = "http://127.0.0.1:8386/api/v1"

# Layer 1: HOLD (60% capital) - Buy & Hold waiting for Q4 wave
LAYER1_HOLD_PERCENT = 0.60
LAYER1_TP_PERCENT = 5.0          # Take profit at +5% to +8% (swing)
LAYER1_SYMBOLS = ["BTC/USDT", "SOL/USDT", "ETH/USDT"]
LAYER1_ALLOCATION = {
    "BTC/USDT": 0.42,   # 42% of hold layer -> ~200 USDT of 480
    "SOL/USDT": 0.38,   # 38% of hold layer -> ~180 USDT of 480
    "ETH/USDT": 0.20,   # 20% of hold layer -> ~100 USDT of 480
}

# Layer 2: SCALPING (25% capital) - Quick rotation +1.2% per cycle
LAYER2_SCALP_PERCENT = 0.25
LAYER2_TP_PERCENT = 1.2          # Agile take profit: +1.2% per cycle
LAYER2_SL_PERCENT = 1.5          # Stop loss: -1.5%
LAYER2_MAX_PER_ORDER = 100.0     # Max 100 USDT per scalp order
LAYER2_MIN_PER_ORDER = 30.0      # Min 30 USDT per scalp order
LAYER2_SYMBOLS = ["SOL/USDT", "BTC/USDT", "BNB/USDT"]

# Layer 3: BREAKOUT (15% capital) - Catch big waves
LAYER3_BREAKOUT_PERCENT = 0.15
LAYER3_TP_PERCENT = 8.0          # Target +5% to +15% on breakout
LAYER3_BREAKOUT_THRESHOLD = 2.5  # 24h change >= +2.5% signals breakout
LAYER3_VOLUME_SPIKE = 1.8        # Volume must be 1.8x above average
LAYER3_SYMBOLS = ["SOL/USDT", "BTC/USDT"]

# General
TARGET_PROFIT_USDT = 1.0
PRIMARY_SYMBOL = "SOL/USDT"
FALLBACK_SYMBOLS = ["BTC/USDT", "ETH/USDT"]


class AISpotSniper:
    """
    AI Spot Sniper v2.0 - 3-Layer Investment Strategy Engine
    =========================================================
    Layer 1 (HOLD 60%):   Buy & Hold BTC + SOL + ETH, TP at +5-8%
    Layer 2 (SCALP 25%):  Quick rotation, TP at +1.2%, SL at -1.5%
    Layer 3 (BREAK 15%):  Catch breakout waves, TP at +5-15%
    """
    def __init__(self):
        self.db = Database('trading_bot.db')
        self.vyce_claude = VyceClient(model='claude-sonnet-4-6', timeout=20.0)
        self.vyce_deepseek = VyceClient(model='deepseek-v4.1', timeout=20.0)
        self.binance = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_API_SECRET,
            'enableRateLimit': True
        })
        self.http_client = httpx.AsyncClient(timeout=10.0)

        # Position tracking
        self.active_targets = {}       # {symbol: target_price} for hold positions
        self.scalp_targets = {}        # {symbol: {"entry": price, "tp": price, "sl": price}}
        self.breakout_targets = {}     # {symbol: {"entry": price, "tp": price}}

        # Layer capital tracking
        self.scalp_capital_deployed = 0.0
        self.breakout_capital_deployed = 0.0

        # Performance stats
        self.session_trades = 0
        self.session_pnl = 0.0
        self.scalp_wins = 0
        self.scalp_losses = 0

        logger.info("=" * 60)
        logger.info("  AI SPOT SNIPER v2.0 - 3-LAYER STRATEGY")
        logger.info(f"  Layer 1 (HOLD):     {LAYER1_HOLD_PERCENT*100:.0f}% | TP: +{LAYER1_TP_PERCENT}%")
        logger.info(f"  Layer 2 (SCALP):    {LAYER2_SCALP_PERCENT*100:.0f}% | TP: +{LAYER2_TP_PERCENT}%")
        logger.info(f"  Layer 3 (BREAKOUT): {LAYER3_BREAKOUT_PERCENT*100:.0f}% | TP: +{LAYER3_TP_PERCENT}%")
        logger.info("=" * 60)

    # --- API HELPERS ---
    async def get_portfolio(self):
        try:
            res = await self.http_client.get(f"{API_BASE}/spot/portfolio")
            if res.status_code == 200:
                return res.json().get("data", {})
        except Exception as e:
            logger.error(f"Error fetching spot portfolio: {e}")
        return None

    async def execute_buy(self, symbol: str, amount_usdt: float, reason: str):
        try:
            res = await self.http_client.post(
                f"{API_BASE}/spot/buy",
                json={"symbol": symbol, "usdt_amount": amount_usdt, "reason": reason}
            )
            data = res.json()
            logger.info(f"Spot Buy Response: {data.get('status')} | Order: {data.get('order')}")
            self.session_trades += 1
            return data
        except Exception as e:
            logger.error(f"Failed to execute spot buy: {e}")
            return None

    async def execute_sell(self, symbol: str, percent: float, reason: str):
        try:
            res = await self.http_client.post(
                f"{API_BASE}/spot/sell",
                json={"symbol": symbol, "percent": percent, "reason": reason}
            )
            data = res.json()
            logger.info(f"Spot Sell Response: {data.get('status')} | Order: {data.get('order')}")
            self.session_trades += 1
            return data
        except Exception as e:
            logger.error(f"Failed to execute spot sell: {e}")
            return None

    async def fetch_market_data(self, symbol: str):
        """Fetch OHLCV + ticker data from Binance."""
        try:
            ohlcv = await self.binance.fetch_ohlcv(symbol, '1h', limit=30)
            ticker = await self.binance.fetch_ticker(symbol)
            return ohlcv, ticker
        except Exception as e:
            logger.error(f"Failed to fetch market data for {symbol}: {e}")
            return None, None

    def compute_indicators(self, ohlcv, ticker):
        """Compute RSI, SMA, Volume Ratio from OHLCV data."""
        closes = [c[4] for c in ohlcv]
        volumes = [c[5] for c in ohlcv]
        cur_price = closes[-1]
        change_24h = ticker.get("percentage", 0.0)

        # RSI 14
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        rsi = 50.0
        if len(gains) >= 14:
            ag = sum(gains[-14:]) / 14
            al = sum(losses[-14:]) / 14
            rsi = 100 - (100 / (1 + (ag / al))) if al != 0 else 100

        # SMA20 and Volume Ratio
        sma20 = sum(closes[-20:]) / min(20, len(closes))
        avg_vol = sum(volumes[-20:]) / min(20, len(volumes))
        vol_ratio = volumes[-1] / (avg_vol + 1e-9)

        return {
            "price": cur_price,
            "change_24h": change_24h,
            "rsi": rsi,
            "sma20": sma20,
            "vol_ratio": vol_ratio,
            "closes": closes,
            "volumes": volumes,
        }

    # --- AI CONSENSUS ENGINE ---
    async def evaluate_market_consensus(self, symbol: str, layer: str = "SCALP"):
        """Get AI dual-model consensus on whether to buy."""
        try:
            ohlcv, ticker = await self.fetch_market_data(symbol)
            if not ohlcv or not ticker:
                return None

            ind = self.compute_indicators(ohlcv, ticker)
            cur_price = ind["price"]

            # Set TP target based on layer
            if layer == "HOLD":
                tp_target = f"+{LAYER1_TP_PERCENT}% to +8%"
            elif layer == "BREAKOUT":
                tp_target = f"+{LAYER3_TP_PERCENT}% to +15%"
            else:
                tp_target = f"+{LAYER2_TP_PERCENT}% to +2.0%"

            logger.info(f"[{symbol}|{layer}] Price: ${cur_price:.2f} | 24h: {ind['change_24h']:+.2f}% | RSI: {ind['rsi']:.1f} | SMA20: ${ind['sma20']:.2f} | Vol: {ind['vol_ratio']:.2f}x")

            # 1. Claude - Quantitative Momentum Strategist
            sys_claude = (
                f"You are the Lead Quantitative Strategist at Astra Quant Desk. "
                f"Evaluate if we should execute a Spot Buy ({layer} layer) on this asset to capture a {tp_target} swing. "
                f"Output strictly valid JSON with keys: 'signal' ('BUY'/'HOLD'), 'confidence' (0.0-1.0), "
                f"'target_price' (float), 'stop_loss' (float), 'rationale' (under 30 words)."
            )
            user_msg = (
                f"Asset: {symbol}, Current Price: ${cur_price:.2f}, 24h Change: {ind['change_24h']:+.2f}%, "
                f"RSI(14): {ind['rsi']:.1f}, SMA(20): ${ind['sma20']:.2f}, Volume Ratio: {ind['vol_ratio']:.2f}x. "
                f"Strategy: {layer} layer, target {tp_target}. Is this a good entry?"
            )
            claude_raw = await self.vyce_claude.chat_completion(sys_claude, user_msg, max_tokens=120)

            # 2. DeepSeek - Adversarial Risk Officer
            sys_deepseek = (
                "You are the Chief Risk Officer (Devil's Advocate). "
                "Scrutinize current price action for traps, overhead resistance, or exhaustion. "
                "Output strictly valid JSON with keys: 'trade_allowed' (bool), 'risk_score' (1-10), 'warning' (under 25 words)."
            )
            deepseek_raw = await self.vyce_deepseek.chat_completion(sys_deepseek, user_msg, max_tokens=100)

            # Parse JSON safely
            claude_data = json.loads(claude_raw.strip().replace("```json", "").replace("```", "")) if claude_raw else {}
            deepseek_data = json.loads(deepseek_raw.strip().replace("```json", "").replace("```", "")) if deepseek_raw else {}

            logger.info(f"[{symbol}|{layer}] Claude: {claude_data.get('signal')} (conf={claude_data.get('confidence')}) | {claude_data.get('rationale')}")
            logger.info(f"[{symbol}|{layer}] DeepSeek: allowed={deepseek_data.get('trade_allowed')} (risk={deepseek_data.get('risk_score')}/10) | {deepseek_data.get('warning')}")

            # Consensus: Slightly relaxed for scalping
            min_confidence = 0.65 if layer == "SCALP" else 0.70
            max_risk = 7 if layer == "SCALP" else 6

            is_approved = (
                claude_data.get("signal") == "BUY" and
                float(claude_data.get("confidence", 0.0)) >= min_confidence and
                deepseek_data.get("trade_allowed") is True and
                int(deepseek_data.get("risk_score", 10)) <= max_risk
            )

            target_tp = float(claude_data.get("target_price", cur_price * 1.02))

            return {
                "symbol": symbol,
                "current_price": cur_price,
                "approved": is_approved,
                "target_price": target_tp,
                "indicators": ind,
                "claude": claude_data,
                "deepseek": deepseek_data,
                "layer": layer,
            }

        except Exception as e:
            logger.error(f"Error in evaluate_market_consensus for {symbol}: {e}")
            return None

    # --- LAYER 1: HOLD MANAGEMENT ---
    async def manage_hold_layer(self, portfolio, holdings):
        """Manage Layer 1 - Hold positions. Monitor for swing TP."""
        logger.info("-- [LAYER 1: HOLD] Monitoring swing positions --")

        for h in holdings:
            sym = h["symbol"]
            amt = float(h["amount"])
            cost = float(h["avg_price"])
            cur_price = float(h["current_price"])
            roi_pct = float(h["roi_percent"])
            unreal_pnl = float(h["unrealized_pnl"])

            if amt <= 0:
                continue

            target_p = self.active_targets.get(sym, cost * (1 + LAYER1_TP_PERCENT / 100))

            logger.info(f"  [HOLD] {sym}: {amt:.6f} @ ${cost:.2f} | Now: ${cur_price:.2f} | ROI: {roi_pct:+.2f}% | PnL: ${unreal_pnl:+.2f}")

            # Swing Take Profit: +5% or higher
            if roi_pct >= LAYER1_TP_PERCENT or cur_price >= target_p:
                logger.info(f"  TARGET HOLD TP TRIGGERED for {sym}! ROI: {roi_pct:+.2f}% >= {LAYER1_TP_PERCENT}%")
                # Sell 50% of holdings (keep some for further upside)
                await self.execute_sell(sym, 50.0, f"L1_HOLD_TP_+{roi_pct:.1f}%")
                self.session_pnl += unreal_pnl * 0.5
                if sym in self.active_targets:
                    del self.active_targets[sym]

    # --- LAYER 2: SCALPING ENGINE ---
    async def manage_scalp_layer(self, portfolio, holdings):
        """Manage Layer 2 - Quick scalping rotation +1.2% per cycle."""
        logger.info("-- [LAYER 2: SCALP] Quick rotation engine --")

        usdt_bal = float(portfolio.get("usdt_balance", 0.0))

        # First check existing scalp positions for TP/SL
        for sym, target in list(self.scalp_targets.items()):
            holding = next((h for h in holdings if h["symbol"] == sym and float(h["amount"]) > 0), None)
            if not holding:
                if sym in self.scalp_targets:
                    del self.scalp_targets[sym]
                continue

            cur_price = float(holding["current_price"])
            roi_pct = float(holding["roi_percent"])

            # SCALP Take Profit: +1.2%
            if roi_pct >= LAYER2_TP_PERCENT:
                logger.info(f"  SCALP TP HIT! {sym} ROI: {roi_pct:+.2f}% >= +{LAYER2_TP_PERCENT}%")
                await self.execute_sell(sym, 100.0, f"L2_SCALP_TP_+{roi_pct:.1f}%")
                self.scalp_wins += 1
                self.session_pnl += float(holding["unrealized_pnl"])
                del self.scalp_targets[sym]
                logger.info(f"  Scalp Win #{self.scalp_wins}: +{roi_pct:.2f}% | Capital freed for next rotation")
                continue

            # SCALP Stop Loss: -1.5%
            if roi_pct <= -LAYER2_SL_PERCENT:
                logger.info(f"  SCALP SL HIT! {sym} ROI: {roi_pct:.2f}% <= -{LAYER2_SL_PERCENT}%")
                await self.execute_sell(sym, 100.0, f"L2_SCALP_SL_{roi_pct:.1f}%")
                self.scalp_losses += 1
                self.session_pnl += float(holding["unrealized_pnl"])
                del self.scalp_targets[sym]
                continue

        # Enter new scalp if we have free capital
        scalp_budget = usdt_bal * 0.5
        if scalp_budget >= LAYER2_MIN_PER_ORDER:
            buy_amount = min(LAYER2_MAX_PER_ORDER, scalp_budget)

            for sym in LAYER2_SYMBOLS:
                if sym in self.scalp_targets:
                    continue

                already_held = any(h["symbol"] == sym and float(h["amount"]) > 0.01 for h in holdings)
                if already_held:
                    continue

                decision = await self.evaluate_market_consensus(sym, layer="SCALP")
                if decision and decision.get("approved"):
                    logger.info(f"  SCALP ENTRY APPROVED: {sym} | Budget: {buy_amount:.2f} USDT")
                    buy_res = await self.execute_buy(sym, buy_amount, f"L2_SCALP_ENTRY_{sym}")
                    if buy_res and buy_res.get("status") == "SUCCESS":
                        entry_price = decision["current_price"]
                        self.scalp_targets[sym] = {
                            "entry": entry_price,
                            "tp": entry_price * (1 + LAYER2_TP_PERCENT / 100),
                            "sl": entry_price * (1 - LAYER2_SL_PERCENT / 100),
                        }
                        logger.info(f"  Scalp registered: {sym} @ ${entry_price:.2f} | TP: ${self.scalp_targets[sym]['tp']:.2f} | SL: ${self.scalp_targets[sym]['sl']:.2f}")
                    break
                else:
                    logger.info(f"  [{sym}] AI Council: No scalp setup. Waiting...")
        else:
            logger.info(f"  Scalp budget insufficient ({scalp_budget:.2f} < {LAYER2_MIN_PER_ORDER}). Capital fully deployed.")

    # --- LAYER 3: BREAKOUT DETECTOR ---
    async def manage_breakout_layer(self, portfolio, holdings):
        """Manage Layer 3 - Detect and ride breakout waves."""
        logger.info("-- [LAYER 3: BREAKOUT] Scanning for momentum spikes --")

        usdt_bal = float(portfolio.get("usdt_balance", 0.0))

        # Monitor existing breakout positions
        for sym, target in list(self.breakout_targets.items()):
            holding = next((h for h in holdings if h["symbol"] == sym and float(h["amount"]) > 0), None)
            if not holding:
                if sym in self.breakout_targets:
                    del self.breakout_targets[sym]
                continue

            roi_pct = float(holding["roi_percent"])

            if roi_pct >= LAYER3_TP_PERCENT:
                logger.info(f"  BREAKOUT TP HIT! {sym} ROI: {roi_pct:+.2f}% >= +{LAYER3_TP_PERCENT}%")
                await self.execute_sell(sym, 100.0, f"L3_BREAKOUT_TP_+{roi_pct:.1f}%")
                self.session_pnl += float(holding["unrealized_pnl"])
                del self.breakout_targets[sym]
                continue

            if roi_pct <= -3.0:
                logger.info(f"  BREAKOUT FAILED for {sym}! ROI: {roi_pct:.2f}%. Exiting.")
                await self.execute_sell(sym, 100.0, f"L3_BREAKOUT_FAIL_{roi_pct:.1f}%")
                self.session_pnl += float(holding["unrealized_pnl"])
                del self.breakout_targets[sym]

        # Scan for new breakout candidates
        if usdt_bal >= 50.0 and len(self.breakout_targets) == 0:
            for sym in LAYER3_SYMBOLS:
                try:
                    ohlcv, ticker = await self.fetch_market_data(sym)
                    if not ohlcv or not ticker:
                        continue

                    ind = self.compute_indicators(ohlcv, ticker)
                    change_24h = ind["change_24h"]
                    vol_ratio = ind["vol_ratio"]

                    if change_24h >= LAYER3_BREAKOUT_THRESHOLD and vol_ratio >= LAYER3_VOLUME_SPIKE:
                        logger.info(f"  BREAKOUT DETECTED: {sym} | 24h: {change_24h:+.2f}% | Vol: {vol_ratio:.2f}x")

                        decision = await self.evaluate_market_consensus(sym, layer="BREAKOUT")
                        if decision and decision.get("approved"):
                            buy_amount = min(120.0, usdt_bal * 0.3)
                            logger.info(f"  BREAKOUT ENTRY APPROVED: {sym} | Budget: {buy_amount:.2f} USDT")
                            buy_res = await self.execute_buy(sym, buy_amount, f"L3_BREAKOUT_{sym}_+{change_24h:.1f}%_vol{vol_ratio:.1f}x")
                            if buy_res and buy_res.get("status") == "SUCCESS":
                                entry_price = ind["price"]
                                self.breakout_targets[sym] = {
                                    "entry": entry_price,
                                    "tp": entry_price * (1 + LAYER3_TP_PERCENT / 100),
                                }
                                logger.info(f"  Breakout registered: {sym} @ ${entry_price:.2f} | TP: ${self.breakout_targets[sym]['tp']:.2f}")
                            break
                    else:
                        logger.info(f"  [{sym}] No breakout signal (24h: {change_24h:+.2f}%, Vol: {vol_ratio:.2f}x)")
                except Exception as e:
                    logger.error(f"  Breakout scan error for {sym}: {e}")

    # --- MAIN CYCLE ---
    async def run_sniper_cycle(self):
        now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"  AI SPOT SNIPER v2.0 - CYCLE START ({now})")
        logger.info("=" * 60)

        portfolio = await self.get_portfolio()
        if not portfolio:
            logger.warning("Could not reach Spot Portfolio API. Skipping cycle.")
            return

        usdt_bal = float(portfolio.get("usdt_balance", 0.0))
        holdings = portfolio.get("holdings", [])
        realized_pnl = float(portfolio.get("realized_pnl", 0.0))
        total_value = float(portfolio.get("total_portfolio_value", 0.0))

        logger.info(f"  Portfolio: ${total_value:.2f} | Free USDT: ${usdt_bal:.2f} | Realized PnL: ${realized_pnl:+.2f}")
        logger.info(f"  Session: Trades={self.session_trades} | PnL=${self.session_pnl:+.2f} | Scalps: W{self.scalp_wins}/L{self.scalp_losses}")
        logger.info("")

        # Run all 3 layers
        await self.manage_hold_layer(portfolio, holdings)
        await self.manage_scalp_layer(portfolio, holdings)
        await self.manage_breakout_layer(portfolio, holdings)

        # Summary
        logger.info("")
        logger.info(f"  Active Targets: Hold={len(self.active_targets)} | Scalp={len(self.scalp_targets)} | Breakout={len(self.breakout_targets)}")
        logger.info("=" * 60)
        logger.info(f"  CYCLE COMPLETE ({now})")
        logger.info("=" * 60)

    async def start_loop(self, interval_seconds: int = 300):
        logger.info(f"AI Spot Sniper v2.0 Daemon started. Polling: {interval_seconds}s ({interval_seconds//60} min).")
        while True:
            try:
                await self.run_sniper_cycle()
            except Exception as e:
                logger.error(f"Unexpected error in sniper loop: {e}")
            await asyncio.sleep(interval_seconds)

    async def close(self):
        await self.binance.close()
        await self.vyce_claude.close()
        await self.vyce_deepseek.close()
        await self.http_client.aclose()


async def main():
    sniper = AISpotSniper()
    try:
        if "--once" in sys.argv:
            await sniper.run_sniper_cycle()
        else:
            await sniper.start_loop(interval_seconds=300)
    finally:
        await sniper.close()


if __name__ == '__main__':
    asyncio.run(main())
