import argparse
import asyncio
import logging
import signal
import sys
from typing import List, Dict, Any
import uvicorn
from config.settings import settings
from core.event_bus import EventBus
from core.events import MarketEvent
from data.storage import Database
from data.binance_client import BinanceClient
from data.websocket_feed import BinanceWebSocketFeed
from strategies.ema_trend import EMATrendStrategy
from strategies.rsi_bollinger import RSIBollingerStrategy
from strategies.multi_timeframe import MultiTimeframeFilter
from ai_advisory.vyce_client import VyceClient
from ai_advisory.regime_classifier import MarketRegimeClassifier
from risk_engine.circuit_breaker import CircuitBreaker
from risk_engine.risk_manager import RiskManager
from execution.oms import OrderManagementSystem
from execution.paper_trader import PaperTrader
from execution.binance_executor import BinanceExecutor
from monitoring.telegram_bot import TelegramNotifier
from core.fleet_manager import AutonomousFleetCoordinator
from web.app import create_web_app


# Ensure Windows console supports Vietnamese UTF-8 without errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Main")


async def main():
    parser = argparse.ArgumentParser(description="Crypto Quantitative Trading Lab")
    parser.add_argument("--mode", choices=["paper", "testnet", "live"], default=settings.TRADING_MODE, help="Trading mode")
    parser.add_argument("--symbol", default=settings.SYMBOL, help="Trading pair symbol (e.g. BTC/USDT)")
    parser.add_argument("--port", type=int, default=settings.DASHBOARD_PORT, help="Dashboard port")
    args = parser.parse_args()

    settings.TRADING_MODE = args.mode
    settings.SYMBOL = args.symbol
    settings.DASHBOARD_PORT = args.port

    logger.info("=" * 60)
    logger.info(f"STARTING CRYPTO TRADING LAB - MODE: {settings.TRADING_MODE.upper()}")
    logger.info(f"Target Symbol: {settings.SYMBOL} | Timeframe: {settings.TIMEFRAME}")
    logger.info("=" * 60)

    # 1. Database
    db = Database(settings.DATABASE_PATH)
    await db.connect()

    # Sync dynamic settings from SQLite if present
    db_settings = await db.get_all_settings()
    for s in db_settings:
        k, v = s["key"], s["value"]
        if k == "SYMBOL": settings.SYMBOL = v
        elif k == "TIMEFRAME": settings.TIMEFRAME = v
        elif k == "AUTO_TRADE_ENABLED":
            settings.AUTO_TRADE_ENABLED = v.lower() in ("true", "1")
        elif k == "FUTURES_LEVERAGE": settings.FUTURES_LEVERAGE = int(v)
        elif k == "LIVE_MAX_USDT_PER_ORDER": settings.LIVE_MAX_USDT_PER_ORDER = float(v)
        elif k == "COOLDOWN_MINUTES": settings.COOLDOWN_MINUTES = int(v)
        elif k == "DAILY_MAX_DRAWDOWN_PERCENT":
            settings.DAILY_MAX_DRAWDOWN_PERCENT = float(v)
        elif k == "TARGET_DAILY_PROFIT_USD": settings.TARGET_DAILY_PROFIT_USD = float(v)
        elif k == "MAX_DAILY_LOSS_USD": settings.MAX_DAILY_LOSS_USD = float(v)
        elif k == "MAX_POSITION_PERCENT": settings.MAX_POSITION_PERCENT = float(v)
        elif k == "MAX_OPEN_POSITIONS": settings.MAX_OPEN_POSITIONS = int(v)
        elif k == "ENABLE_AI_ADVISORY":
            settings.ENABLE_AI_ADVISORY = v.lower() in ("true", "1")
        elif k == "VYCE_MODEL":
            settings.VYCE_MODEL = str(v)
        elif k == "AI_TIMEOUT_SECONDS":
            settings.AI_TIMEOUT_SECONDS = float(v)
        elif k == "ENABLE_MULTI_TIMEFRAME":
            settings.ENABLE_MULTI_TIMEFRAME = v.lower() in ("true", "1")
        elif k == "AI_COUNCIL_MODE":
            settings.AI_COUNCIL_MODE = str(v).lower()

    # Environment selection is fixed before constructing any client/worker.
    settings.BINANCE_USE_TESTNET = settings.TRADING_MODE != "live"
    if settings.TRADING_MODE == "live" and not settings.LIVE_SAFETY_RELEASE_APPROVED:
        raise RuntimeError("Live release requires testnet acceptance and LIVE_SAFETY_RELEASE_APPROVED=true")

    # 2. Event Bus
    event_bus = EventBus()
    event_bus.start()

    # 3. Vyce AI Client (Shared Keep-Alive Connection Pool with Grok 4.7 & GPT-6 Astra)
    vyce_client = VyceClient(db=db, council_mode=settings.AI_COUNCIL_MODE)

    # 4. Risk Engine
    circuit_breaker = CircuitBreaker(
        max_daily_drawdown_percent=settings.DAILY_MAX_DRAWDOWN_PERCENT,
        target_daily_profit_usd=getattr(settings, "TARGET_DAILY_PROFIT_USD", 10.0),
        max_daily_loss_usd=getattr(settings, "MAX_DAILY_LOSS_USD", 3.5),
        house_money_mode_enabled=getattr(settings, "HOUSE_MONEY_MODE_ENABLED", True)
    )
    circuit_breaker.reset_daily_metrics(settings.STARTING_BALANCE_USDT)
    mtf_filter = MultiTimeframeFilter(ema_period=settings.MTF_EMA_PERIOD)
    risk_manager = RiskManager(event_bus, db, circuit_breaker, vyce_client=vyce_client, mtf_filter=mtf_filter)

    # 5. OMS & Execution
    audit_logs: List[Dict[str, Any]] = []
    oms = OrderManagementSystem(event_bus)
    paper_trader = PaperTrader(
        event_bus, db, circuit_breaker,
        vyce_client=vyce_client, audit_logs=audit_logs,
        enabled=(settings.TRADING_MODE == "paper")
    )
    binance_client = BinanceClient()
    if settings.TRADING_MODE == "live":
        try:
            live_bal = await binance_client.fetch_balance()
            total_margin = float(live_bal.get("info", {}).get("totalMarginBalance", 0.0) or 0.0)
            usdt_total = float(live_bal.get("USDT", {}).get("total", 0.0) or live_bal.get("USDT", {}).get("free", 0.0))
            active_bal = total_margin if total_margin > 0 else usdt_total
            if active_bal > 0:
                circuit_breaker.reset_daily_metrics(active_bal, force=True)
                logger.info(f"[Live Balance Synced] Circuit Breaker reset with Binance Futures margin balance (Multi-Assets): ${active_bal:.2f}")
        except Exception as e:
            logger.warning(f"Could not sync live balance from Binance: {e}")

    binance_executor = BinanceExecutor(event_bus, binance_client, db, vyce_client=vyce_client, audit_logs=audit_logs)
    if settings.TRADING_MODE in ("live", "testnet"):
        await binance_executor.sync_open_positions()
    else:
        await paper_trader.sync_open_positions_from_db()

    # Synchronize RiskManager with database state to ensure Anti-Duplicate protection
    await risk_manager.sync_open_positions_from_db()

    # 6. AI Advisory (Vyce AI)
    ai_classifier = MarketRegimeClassifier(event_bus, db, client=vyce_client)

    # 6. Strategies (Multi-Pair Orchestration)
    symbols = getattr(settings, "SYMBOLS", [settings.SYMBOL])
    strategies_ema: Dict[str, EMATrendStrategy] = {
        s: EMATrendStrategy(symbol=s, event_bus=event_bus) for s in symbols
    }
    strategies_rsi: Dict[str, RSIBollingerStrategy] = {
        s: RSIBollingerStrategy(symbol=s, event_bus=event_bus) for s in symbols
    }

    # 6.1 Spot Engine (Hybrid 20U Desk: DCA & Trend Swing)
    spot_executor = None
    spot_strategy = None
    if getattr(settings, "ENABLE_SPOT_ENGINE", True):
        from execution.spot_executor import SpotExecutor
        from strategies.spot_dca_strategy import SpotDCAStrategy
        spot_executor = SpotExecutor(event_bus, db, binance_client)
        spot_capital = getattr(settings, "SPOT_STARTING_BALANCE_USDT", 500.0)
        spot_strategy = SpotDCAStrategy(total_capital_usdt=spot_capital)
        logger.info(f"[Spot Engine Active] {spot_capital:.0f}U Dedicated Spot BTC Pyramid DCA & Trend Swing ready.")

    # Forward market events to corresponding symbol strategies & Spot DCA Engine
    async def on_market_event(event: MarketEvent):
        if event.symbol in strategies_ema:
            await strategies_ema[event.symbol].on_market_event(event)
        if event.symbol in strategies_rsi:
            await strategies_rsi[event.symbol].on_market_event(event)

        # Evaluate Spot DCA
        if spot_executor and spot_strategy and event.symbol in getattr(settings, "SPOT_SYMBOLS", ["BTC/USDT", "ETH/USDT", "SOL/USDT"]):
            spot_executor.update_price(event.symbol, event.close)
            strat = strategies_ema.get(event.symbol)
            if strat and hasattr(strat, "get_dataframe"):
                df_sym = strat.get_dataframe()
                if df_sym is not None and len(df_sym) >= 20:
                    holding = spot_executor.holdings.get(event.symbol, {})
                    ai_reg = getattr(ai_classifier, "current_advisory", None)
                    reg_name = ai_reg.regime.value if ai_reg and hasattr(ai_reg, "regime") else None
                    sig = spot_strategy.evaluate_signal(event.symbol, df_sym, holding, reg_name)
                    if sig.get("action") == "BUY":
                        await spot_executor.execute_spot_buy(event.symbol, sig["usdt_amount"], sig["price"], sig.get("reason", "DCA"))
                    elif sig.get("action") == "SELL":
                        await spot_executor.execute_spot_sell(event.symbol, sig["percent"], sig["price"], sig.get("reason", "TP"))

    event_bus.subscribe(MarketEvent, on_market_event)

    # 7. Notifications & Monitoring
    telegram = TelegramNotifier(event_bus)
    asyncio.create_task(telegram.start_periodic_patrol(db, binance_client=binance_client, interval_seconds=2700))
    asyncio.create_task(telegram.start_interactive_listener(db, binance_client=binance_client, vyce_client=vyce_client))

    # 8. Web Application (Client Portal & Admin Control Desk) & 10-Agent Autonomous Fleet
    fleet_coordinator = AutonomousFleetCoordinator(
        db=db,
        circuit_breaker=circuit_breaker,
        event_bus=event_bus,
        binance_client=binance_client,
        vyce_client=vyce_client
    )
    fleet_coordinator.start_autonomous_tracking_loop()
    web_app = create_web_app(
        db, circuit_breaker, event_bus, paper_trader, binance_client,
        audit_logs=audit_logs, binance_executor=binance_executor, fleet_coordinator=fleet_coordinator
    )
    server_config = uvicorn.Config(
        app=web_app,
        host=settings.DASHBOARD_HOST,
        port=settings.DASHBOARD_PORT,
        log_level="warning"
    )
    server = uvicorn.Server(server_config)
    dashboard_task = asyncio.create_task(server.serve())
    logger.info(f"Web Platform online at http://{settings.DASHBOARD_HOST}:{settings.DASHBOARD_PORT}")
    logger.info(f"Client Portal: http://{settings.DASHBOARD_HOST}:{settings.DASHBOARD_PORT}/")
    logger.info(f"Admin Control Panel: http://{settings.DASHBOARD_HOST}:{settings.DASHBOARD_PORT}/admin")

    # 9. Market Data Feed (Combined Streams for all active pairs)
    ws_feed = BinanceWebSocketFeed(event_bus, db, symbols=symbols)
    ws_feed.start()

    # Pre-populate historical candles for indicator warm-up across all active symbols
    for sym in symbols:
        logger.info(f"Warming up strategies with historical candles for {sym}...")
        historical_candles = await binance_client.fetch_ohlcv(sym, timeframe=settings.TIMEFRAME, limit=60)
        for c in historical_candles:
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(c[0] / 1000, tz=timezone.utc)
            me = MarketEvent(
                symbol=sym,
                timestamp=dt,
                open=float(c[1]),
                high=float(c[2]),
                low=float(c[3]),
                close=float(c[4]),
                volume=float(c[5]),
                is_candle_closed=True
            )
            if sym in strategies_ema:
                strategies_ema[sym].add_candle(me)
            if sym in strategies_rsi:
                strategies_rsi[sym].add_candle(me)
        logger.info(f"Warmup complete for {sym} ({len(historical_candles)} candles loaded).")

        # Warm up Multi-Timeframe Confluence Engine (1h & 4h candles)
        await mtf_filter.warmup(binance_client, sym)

    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Shutdown signal received. Cleaning up...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass  # Windows event loop limitation for add_signal_handler

    try:
        while not stop_event.is_set():
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        logger.info("Shutting down Trading Lab services...")
        await fleet_coordinator.stop_autonomous_tracking_loop()
        await ws_feed.stop()
        await event_bus.stop()
        await paper_trader.close()
        await binance_executor.close()
        await binance_client.close()
        await vyce_client.close()
        await db.close()
        server.should_exit = True
        await dashboard_task
        logger.info("All services stopped safely.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process terminated by user.")
