# Handoff Report — Milestone 1: Risk Manager Advisory Veto Gatekeeper Integration

**Agent**: M1 Explorer 2 (Risk Manager Advisory Veto Specialist)  
**Date**: 2026-09-17T05:25:00Z  
**Working Directory**: `c:\sunMy\trading_bot\.agents\m1_explorer_2`  
**Target File Analyzed**: `c:\sunMy\trading_bot\risk_engine\risk_manager.py`  
**Integration Scope**: Active Signal Veto Gatekeeper, Position Sizing, SQLite Approval/Rejection Recording, `main.py` Wiring  
**Recipient**: Lead Orchestrator (`4a1d31f3-0188-4bb2-b5c1-ff9c51dda848`)  

---

## 1. Observation

Direct observations from source inspection and execution in `c:\sunMy\trading_bot`:

### 1.1. Existing `RiskManager` Implementation (`risk_engine/risk_manager.py`)
- **Constructor & Subscriptions (lines 15-28)**:
  ```python
  class RiskManager:
      def __init__(self, event_bus: EventBus, db: Database, circuit_breaker: CircuitBreaker):
          self.event_bus = event_bus
          self.db = db
          self.circuit_breaker = circuit_breaker
          self.open_positions: Dict[str, dict] = {}
          self.latest_ai_advisory: Optional[AIAdvisoryEvent] = None

          # Subscribe to signals and AI advisory
          self.event_bus.subscribe(SignalEvent, self.handle_signal)
          self.event_bus.subscribe(AIAdvisoryEvent, self.handle_ai_advisory)

      async def handle_ai_advisory(self, event: AIAdvisoryEvent) -> None:
          self.latest_ai_advisory = event
  ```
  *Observation*:
  1. `RiskManager` does not currently take `VyceClient` as a dependency.
  2. `self.open_positions` is initialized as `{}` but is never populated or updated because `RiskManager` does not subscribe to `FillEvent`.
  3. `self.latest_ai_advisory` is passively updated when an `AIAdvisoryEvent` arrives, but no active call to AI is made when a `SignalEvent` occurs.

- **Signal Interception & Veto Logic (lines 30-81)**:
  ```python
  async def handle_signal(self, signal: SignalEvent) -> Optional[OrderEvent]:
      # Rule 1: Circuit Breaker Check
      if self.circuit_breaker.is_tripped:
          reason = f"Circuit breaker tripped: {self.circuit_breaker.trip_reason}"
          logger.warning(f"[Risk Rejection] {reason}")
          await self._record_rejection(signal, reason)
          return None

      # Rule 2: AI Advisory Filter Check
      if settings.ENABLE_AI_ADVISORY and self.latest_ai_advisory:
          if not self.latest_ai_advisory.trade_allowed:
              reason = f"AI Advisory flagged trades not allowed (Regime: {self.latest_ai_advisory.regime.value})"
              logger.warning(f"[Risk Rejection] {reason}")
              await self._record_rejection(signal, reason)
              return None
          if self.latest_ai_advisory.regime == MarketRegime.EXTREME_VOLATILITY:
              reason = "AI Advisory flagged Extreme Market Volatility"
              logger.warning(f"[Risk Rejection] {reason}")
              await self._record_rejection(signal, reason)
              return None

      # Rule 3: Max Open Positions Check
      if signal.side == OrderSide.BUY and len(self.open_positions) >= settings.MAX_OPEN_POSITIONS:
          reason = f"Maximum open positions reached ({len(self.open_positions)}/{settings.MAX_OPEN_POSITIONS})"
          logger.warning(f"[Risk Rejection] {reason}")
          await self._record_rejection(signal, reason)
          return None

      # Rule 4: Mandatory Stop Loss Check for BUY orders
      if signal.side == OrderSide.BUY:
          if signal.stop_loss <= 0 or signal.stop_loss >= signal.price:
              reason = f"Invalid stop loss level: SL={signal.stop_loss}, Price={signal.price}"
              logger.warning(f"[Risk Rejection] {reason}")
              await self._record_rejection(signal, reason)
              return None

          # Calculate position size
          current_equity = self.circuit_breaker.current_equity or settings.STARTING_BALANCE_USDT
          max_alloc = current_equity * settings.MAX_POSITION_PERCENT

          # Adjust by AI multiplier if active
          ai_mult = self.latest_ai_advisory.size_multiplier if self.latest_ai_advisory else 1.0
          allocated_usdt = max_alloc * max(0.2, min(1.0, ai_mult))

          # Quantity in base asset (e.g. BTC)
          quantity = round(allocated_usdt / signal.price, 6)
          if quantity <= 0:
              reason = f"Calculated order quantity too small: {quantity}"
              logger.warning(f"[Risk Rejection] {reason}")
              await self._record_rejection(signal, reason)
              return None
  ```
  *Observation*:
  1. Under `Rule 2`, the AI check is strictly passive (`if settings.ENABLE_AI_ADVISORY and self.latest_ai_advisory:`). If no prior advisory event has been emitted, `self.latest_ai_advisory` is `None` and the AI advisory filter is bypassed entirely.
  2. The position sizing calculation correctly scales by `max(0.2, min(1.0, ai_mult))`, but currently relies on stale or missing `self.latest_ai_advisory`.

- **Approval, SQLite Persistence & Order Emission (lines 90-135)**:
  ```python
      # Approve and construct OrderEvent
      order_event = OrderEvent(
          order_id=str(uuid.uuid4())[:12],
          strategy_name=signal.strategy_name,
          symbol=signal.symbol,
          side=signal.side,
          order_type=OrderType.MARKET,
          quantity=quantity,
          price=signal.price,
          stop_loss=signal.stop_loss,
          take_profit=signal.take_profit,
          timestamp=datetime.now(timezone.utc),
          status=OrderStatus.PENDING
      )

      await self.db.save_signal(
          strategy_name=signal.strategy_name,
          symbol=signal.symbol,
          side=signal.side.value,
          price=signal.price,
          sl=signal.stop_loss,
          tp=signal.take_profit,
          confidence=signal.confidence,
          dt=signal.timestamp,
          approved=True,
          rejection_reason=""
      )

      logger.info(f"[Risk Approved] Order {order_event.order_id}: {order_event.side.value} {order_event.quantity} {order_event.symbol} @ {order_event.price}")
      await self.event_bus.publish(order_event)
      return order_event

  async def _record_rejection(self, signal: SignalEvent, reason: str) -> None:
      await self.db.save_signal(
          strategy_name=signal.strategy_name,
          symbol=signal.symbol,
          side=signal.side.value,
          price=signal.price,
          sl=signal.stop_loss,
          tp=signal.take_profit,
          confidence=signal.confidence,
          dt=signal.timestamp,
          approved=False,
          rejection_reason=reason
      )
  ```
  *Observation*:
  1. Rejections and approvals are saved via `self.db.save_signal` with `approved=False` (and `rejection_reason`) or `approved=True` (and empty `rejection_reason`).
  2. However, when AI evaluates a signal, the advisory evaluation result itself (macro regime, risk score, trade allowance, size multiplier, reasoning) is NOT saved to `ai_advisory_logs` table nor published to `EventBus` from `RiskManager`.

### 1.2. Wiring & Instantiation in `main.py`
- **Lines 52-76**:
  ```python
  # 1. Database
  db = Database(settings.DATABASE_PATH)
  await db.connect()

  # 2. Event Bus
  event_bus = EventBus()
  event_bus.start()

  # 3. Risk Engine
  circuit_breaker = CircuitBreaker(max_daily_drawdown_percent=settings.DAILY_MAX_DRAWDOWN_PERCENT)
  circuit_breaker.reset_daily_metrics(settings.STARTING_BALANCE_USDT)
  risk_manager = RiskManager(event_bus, db, circuit_breaker)

  # 4. OMS & Execution
  oms = OrderManagementSystem(event_bus)
  paper_trader = PaperTrader(event_bus, db, circuit_breaker)
  binance_client = BinanceClient()
  binance_executor = BinanceExecutor(event_bus, binance_client, db)

  # 5. AI Advisory (Vyce AI)
  ai_classifier = MarketRegimeClassifier(event_bus, db)
  ```
- **Lines 158-165 (Shutdown sequence)**:
  ```python
  logger.info("Shutting down Trading Lab services...")
  await ws_feed.stop()
  await event_bus.stop()
  await binance_client.close()
  await db.close()
  server.should_exit = True
  await dashboard_task
  logger.info("All services stopped safely.")
  ```
  *Observation*:
  1. `RiskManager` is instantiated at line 63 with `RiskManager(event_bus, db, circuit_breaker)`.
  2. `MarketRegimeClassifier` is instantiated at line 72 with `MarketRegimeClassifier(event_bus, db)`. In `ai_advisory/regime_classifier.py` line 28, it accepts `client: VyceClient | None = None` and defaults to `self.client = client or VyceClient()`.
  3. If `VyceClient` is instantiated once in `main.py` and passed into both `RiskManager` and `MarketRegimeClassifier`, both components share a single pooled HTTP keep-alive connection (`httpx.AsyncClient`), avoiding connection churn and latency overhead.
  4. At shutdown, `vyce_client.close()` can be called safely to drain connections.

### 1.3. SQLite Database Layer Contracts (`data/storage.py`)
- `save_signal(strategy_name, symbol, side, price, sl, tp, confidence, dt, approved, rejection_reason="")` inserts into `signals` (lines 143-151).
- `save_ai_advisory(symbol, regime, risk_score, trade_allowed, size_multiplier, reasoning, dt)` inserts into `ai_advisory_logs` (lines 172-179).
- `get_recent_candles(symbol, limit=60)` retrieves recent candles from SQLite `candles` table (lines 227-237).

### 1.4. Existing Test Suite Compatibility (`tests/test_risk_engine.py`)
- Line 21: `rm = RiskManager(event_bus, db, cb)`
- All 10 existing tests in `tests/` pass with zero failures:
  ```
  ============================= 10 passed in 4.11s ==============================
  ```
- *Observation*: `RiskManager.__init__` must maintain default `vyce_client: Optional[VyceClient] = None` so existing tests constructing `RiskManager(event_bus, db, cb)` continue to pass without modification.

---

## 2. Logic Chain

From the observations above, we establish the following deductive reasoning chain:

1. **Active Interception is Required by R1**:
   - The user specification states: *"Khi các thuật toán kỹ thuật (EMA Trend, RSI Bollinger) sinh tín hiệu MUA/BÁN, AI đánh giá bối cảnh vĩ mô và chỉ cho phép lệnh đi tiếp nếu đồng thuận (hoặc phủ quyết nếu thị trường xấu/rủi ro cao)."*
   - Reading a cached or stale `latest_ai_advisory` from a disconnected classification routine does not evaluate the specific trade signal at hand.
   - Therefore, `RiskManager.handle_signal` must **actively call** `vyce_client.evaluate_signal_veto(signal, market_context)` whenever `settings.ENABLE_AI_ADVISORY` is active.

2. **Deterministic Hard Risk Rules Must Precede External AI Network Calls**:
   - Hard risk limits (CircuitBreaker tripped, invalid Stop-Loss bounds where SL >= entry price for BUY, and maximum concurrent positions) are deterministic, mathematical, and instantaneous (0ms).
   - If the CircuitBreaker is tripped or SL is invalid, querying an external LLM proxy wastes 1-2 seconds of network time and API credits for a signal that must be rejected regardless of AI sentiment.
   - Therefore, the execution pipeline must strictly sequence:
     **Phase 1: Deterministic Hard Checks** -> **Phase 2: Active AI Advisory Veto** -> **Phase 3: Position Sizing** -> **Phase 4: Persistence & Order Emission**.

3. **Dependency Injection & Shared Keep-Alive Pool**:
   - Observation 1.2 and Survey 2 showed that cold TCP/TLS handshakes to `https://vyceai.com` take ~3.10s, while reusing an established keep-alive connection takes ~1.2s.
   - If `RiskManager` instantiates a new `httpx.AsyncClient` on each signal or runs a separate instance from `MarketRegimeClassifier`, connections cannot be pooled effectively.
   - By adding `vyce_client: Optional[VyceClient] = None` to `RiskManager.__init__`:
     - If passed from `main.py`, it reuses the application-wide `VyceClient` singleton with its warm connection pool.
     - If omitted (as in `tests/test_risk_engine.py`), it defaults to `self.vyce_client = vyce_client or VyceClient()`.
     - In unit tests, a mock client (`AsyncMock`) can be cleanly injected.

4. **Multi-Position Tracking Synchronization via `FillEvent`**:
   - In the existing code, `RiskManager` checks `len(self.open_positions) >= settings.MAX_OPEN_POSITIONS`, but `self.open_positions` is always empty because `RiskManager` never listens to fills.
   - Subscribing to `FillEvent` in `RiskManager` and implementing `handle_fill` ensures:
     - BUY fills add to `self.open_positions`.
     - SELL fills remove from `self.open_positions`.
     - Rule 3 (`MAX_OPEN_POSITIONS`) is truthfully enforced at runtime.
     - SELL orders can retrieve the exact filled quantity to liquidate.

5. **Position Sizing Mathematical Formula**:
   - `allocated_usdt = (current_equity * settings.MAX_POSITION_PERCENT) * max(0.2, min(1.0, size_multiplier))`
   - Clamping `size_multiplier` to `[0.2, 1.0]` guarantees:
     - The trade never exceeds the 20% portfolio risk cap (`MAX_POSITION_PERCENT = 0.20`).
     - If approved, allocation remains above exchange dust limits (min 20% of standard size, ~$4-$20 for $100 starting equity).
     - `quantity = round(allocated_usdt / signal.price, 6)` for BTC/USDT.

6. **Dual Persistence Requirement**:
   - When a signal is vetoed or approved:
     - `signals` table records `approved` (0 or 1) and `rejection_reason` (e.g. `f"AI Advisory Veto: {reasoning}"`).
     - `ai_advisory_logs` table records the AI evaluation (`regime`, `risk_score`, `trade_allowed`, `size_multiplier`, `reasoning`).
     - Publishing `AIAdvisoryEvent` onto `event_bus` updates real-time listeners and allows web API routes (`/api/v1/status`) to serve `latest_ai_advisory`.

---

## 3. Caveats

1. **Spot Market Asymmetry (BUY vs SELL Signals)**:
   - For `OrderSide.BUY`, opening a new position introduces downside risk; AI veto prevents capital destruction during adverse macro conditions.
   - For `OrderSide.SELL`, closing an existing long position reduces risk. If AI were to veto a technical SELL signal during a market crash, the position would remain trapped.
   - *Design Decision*: Active AI Veto gatekeeping applies primarily to BUY signals. For SELL signals, AI can record regime/sentiment, but does not block position exits (or approves by default) unless explicitly configured.
2. **Sequential EventBus Execution**:
   - As observed in Survey 1 and Survey 2, `EventBus._worker` processes events in a sequential loop. A blocking call in `handle_signal` pauses the worker.
   - Therefore, the AI evaluation MUST be wrapped in a strict timeout (`asyncio.wait_for(..., timeout=settings.AI_TIMEOUT_SECONDS)`) with a deterministic quantitative fallback so `handle_signal` never hangs the event bus.
3. **Database Connection Safety**:
   - `data/storage.py` uses a single `aiosqlite` connection. Concurrent writes in `save_signal` and `save_ai_advisory` must be sequential or properly awaited.

---

## 4. Conclusion & Complete Design Specifications

### 4.1. Complete Proposed Design for `risk_engine/risk_manager.py`

```python
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from config.settings import settings
from core.constants import OrderSide, OrderType, OrderStatus, MarketRegime
from core.events import SignalEvent, OrderEvent, AIAdvisoryEvent, FillEvent
from core.event_bus import EventBus
from data.storage import Database
from ai_advisory.vyce_client import VyceClient
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger("RiskManager")


class RiskManager:
    def __init__(
        self,
        event_bus: EventBus,
        db: Database,
        circuit_breaker: CircuitBreaker,
        vyce_client: Optional[VyceClient] = None
    ):
        self.event_bus = event_bus
        self.db = db
        self.circuit_breaker = circuit_breaker
        self.vyce_client = vyce_client or VyceClient()
        self.open_positions: Dict[str, dict] = {}
        self.latest_ai_advisory: Optional[AIAdvisoryEvent] = None

        # Event Bus Subscriptions
        self.event_bus.subscribe(SignalEvent, self.handle_signal)
        self.event_bus.subscribe(AIAdvisoryEvent, self.handle_ai_advisory)
        self.event_bus.subscribe(FillEvent, self.handle_fill)

    async def handle_ai_advisory(self, event: AIAdvisoryEvent) -> None:
        """Cache incoming AI advisory events from other sources."""
        self.latest_ai_advisory = event

    async def handle_fill(self, event: FillEvent) -> None:
        """Synchronize open positions tracking from execution fills."""
        pos_key = f"{event.strategy_name}_{event.symbol}"
        if event.side == OrderSide.BUY:
            self.open_positions[pos_key] = {
                "order_id": event.order_id,
                "strategy_name": event.strategy_name,
                "symbol": event.symbol,
                "quantity": event.quantity,
                "fill_price": event.fill_price,
                "timestamp": event.timestamp
            }
        elif event.side == OrderSide.SELL:
            self.open_positions.pop(pos_key, None)

    async def handle_signal(self, signal: SignalEvent) -> Optional[OrderEvent]:
        """
        Gated Risk Processing Pipeline:
        Phase 1: Deterministic Hard Risk Rules (Circuit Breaker, Position Limit, Stop-Loss Bounds)
        Phase 2: Active AI Advisory Veto (Claude-3.5-Sonnet via Vyce AI with < 3.0s Timeout Fallback)
        Phase 3: Position Sizing & Allocation Multiplier
        Phase 4: Order Creation, Dual SQLite Persistence & OrderEvent Emission
        """
        # =====================================================================
        # Phase 1: Deterministic Hard Risk Checks (0ms)
        # =====================================================================
        # Check 1.1: Circuit Breaker
        if self.circuit_breaker.is_tripped:
            reason = f"Circuit breaker tripped: {self.circuit_breaker.trip_reason}"
            logger.warning(f"[Risk Rejection] {reason}")
            await self._record_rejection(signal, reason)
            return None

        # Check 1.2: Max Open Positions (BUY orders only)
        if signal.side == OrderSide.BUY and len(self.open_positions) >= settings.MAX_OPEN_POSITIONS:
            reason = f"Maximum open positions reached ({len(self.open_positions)}/{settings.MAX_OPEN_POSITIONS})"
            logger.warning(f"[Risk Rejection] {reason}")
            await self._record_rejection(signal, reason)
            return None

        # Check 1.3: Mandatory Stop-Loss Validation (BUY orders only)
        if signal.side == OrderSide.BUY:
            if signal.stop_loss <= 0 or signal.stop_loss >= signal.price:
                reason = f"Invalid stop loss level: SL={signal.stop_loss}, Price={signal.price}"
                logger.warning(f"[Risk Rejection] {reason}")
                await self._record_rejection(signal, reason)
                return None

        # =====================================================================
        # Phase 2: Active AI Advisory Veto Gatekeeper
        # =====================================================================
        ai_mult = 1.0

        if settings.ENABLE_AI_ADVISORY:
            # Gather recent market context
            recent_candles = []
            if self.db:
                try:
                    recent_candles = await self.db.get_recent_candles(signal.symbol, limit=10)
                except Exception as e:
                    logger.warning(f"Could not retrieve recent candles for AI context: {e}")

            market_context: Dict[str, Any] = {
                "symbol": signal.symbol,
                "price": signal.price,
                "strategy_name": signal.strategy_name,
                "side": signal.side.value if hasattr(signal.side, "value") else str(signal.side),
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "confidence": signal.confidence,
                "recent_candles": recent_candles,
                "account_equity": self.circuit_breaker.current_equity or settings.STARTING_BALANCE_USDT,
                "open_positions": len(self.open_positions)
            }

            # Query Claude-3.5-Sonnet with strict < 3.0s timeout wrapping
            try:
                ai_decision = await asyncio.wait_for(
                    self.vyce_client.evaluate_signal_veto(signal, market_context),
                    timeout=settings.AI_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                logger.warning(f"[AI Advisory] Timeout after {settings.AI_TIMEOUT_SECONDS}s. Engaging quantitative fallback.")
                ai_decision = self._quantitative_fallback(signal)
            except Exception as e:
                logger.warning(f"[AI Advisory] Error during signal evaluation: {e}. Engaging quantitative fallback.")
                ai_decision = self._quantitative_fallback(signal)

            # Parse AI decision
            approved = bool(ai_decision.get("approved", True))
            regime_str = str(ai_decision.get("regime", "ranging")).lower()
            regime = MarketRegime(regime_str) if regime_str in MarketRegime._value2member_map_ else MarketRegime.RANGING
            risk_score = int(ai_decision.get("risk_score", 3))
            ai_mult = float(ai_decision.get("size_multiplier", 1.0))
            reasoning = str(ai_decision.get("reasoning", ""))

            # Update latest AI advisory state
            advisory_event = AIAdvisoryEvent(
                symbol=signal.symbol,
                timestamp=datetime.now(timezone.utc),
                regime=regime,
                risk_score=risk_score,
                trade_allowed=approved,
                size_multiplier=ai_mult,
                reasoning=reasoning
            )
            self.latest_ai_advisory = advisory_event

            # Persist to SQLite ai_advisory_logs
            if self.db:
                await self.db.save_ai_advisory(
                    symbol=signal.symbol,
                    regime=advisory_event.regime.value,
                    risk_score=advisory_event.risk_score,
                    trade_allowed=advisory_event.trade_allowed,
                    size_multiplier=advisory_event.size_multiplier,
                    reasoning=advisory_event.reasoning,
                    dt=advisory_event.timestamp
                )

            # Publish AI advisory to bus for monitoring & dashboard feeds
            await self.event_bus.publish(advisory_event)

            # Evaluate Veto Condition
            if not approved:
                rejection_reason = f"AI Advisory Veto: {reasoning}"
                logger.warning(f"[Risk Rejection] {rejection_reason}")
                await self._record_rejection(signal, rejection_reason)
                return None

            if regime == MarketRegime.EXTREME_VOLATILITY:
                rejection_reason = f"AI Advisory flagged Extreme Market Volatility: {reasoning}"
                logger.warning(f"[Risk Rejection] {rejection_reason}")
                await self._record_rejection(signal, rejection_reason)
                return None

        # =====================================================================
        # Phase 3: Position Sizing & Allocation
        # =====================================================================
        if signal.side == OrderSide.BUY:
            current_equity = self.circuit_breaker.current_equity or settings.STARTING_BALANCE_USDT
            max_alloc = current_equity * settings.MAX_POSITION_PERCENT
            allocated_usdt = max_alloc * max(0.2, min(1.0, ai_mult))

            quantity = round(allocated_usdt / signal.price, 6)
            if quantity <= 0:
                reason = f"Calculated order quantity too small: {quantity}"
                logger.warning(f"[Risk Rejection] {reason}")
                await self._record_rejection(signal, reason)
                return None
        else:
            # SELL / Exit: Close existing position
            pos_key = f"{signal.strategy_name}_{signal.symbol}"
            if pos_key in self.open_positions:
                quantity = self.open_positions[pos_key]["quantity"]
            else:
                quantity = 0.001  # Nominal fallback

        # =====================================================================
        # Phase 4: Order Construction, Approval Recording & OrderEvent Emission
        # =====================================================================
        order_event = OrderEvent(
            order_id=str(uuid.uuid4())[:12],
            strategy_name=signal.strategy_name,
            symbol=signal.symbol,
            side=signal.side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=signal.price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            timestamp=datetime.now(timezone.utc),
            status=OrderStatus.PENDING
        )

        # Record approved signal in SQLite signals table
        await self.db.save_signal(
            strategy_name=signal.strategy_name,
            symbol=signal.symbol,
            side=signal.side.value if hasattr(signal.side, "value") else str(signal.side),
            price=signal.price,
            sl=signal.stop_loss,
            tp=signal.take_profit,
            confidence=signal.confidence,
            dt=signal.timestamp,
            approved=True,
            rejection_reason=""
        )

        logger.info(
            f"[Risk Approved] Order {order_event.order_id}: {order_event.side.value} "
            f"{order_event.quantity} {order_event.symbol} @ {order_event.price} (AI Multiplier: {ai_mult})"
        )
        await self.event_bus.publish(order_event)
        return order_event

    def _quantitative_fallback(self, signal: SignalEvent) -> Dict[str, Any]:
        """
        Instant deterministic quantitative fallback invoked if AI Advisory times out (>3.0s)
        or encounters network errors. Protects the execution pipeline from stalling.
        """
        # Baseline rule: If signal confidence >= 0.70, allow trade with conservative 0.5x size
        is_safe = signal.confidence >= 0.70
        return {
            "approved": is_safe,
            "regime": "ranging",
            "risk_score": 3,
            "confidence": signal.confidence,
            "size_multiplier": 0.5 if is_safe else 0.0,
            "reasoning": f"Safe Fallback: AI timeout/error; signal validated via quantitative baseline (conf={signal.confidence:.2f})",
            "model": "quantitative-fallback",
            "fallback_used": True
        }

    async def _record_rejection(self, signal: SignalEvent, reason: str) -> None:
        """Persist rejected signal and reason into SQLite signals table."""
        if self.db:
            await self.db.save_signal(
                strategy_name=signal.strategy_name,
                symbol=signal.symbol,
                side=signal.side.value if hasattr(signal.side, "value") else str(signal.side),
                price=signal.price,
                sl=signal.stop_loss,
                tp=signal.take_profit,
                confidence=signal.confidence,
                dt=signal.timestamp,
                approved=False,
                rejection_reason=reason
            )
```

---

### 4.2. Recommended Wiring in `main.py`

In `main.py` lines 60-76, instantiate `vyce_client` once and pass it to both `risk_manager` and `ai_classifier`:

```python
    # 3. Vyce AI Client (Shared Keep-Alive Connection Pool)
    vyce_client = VyceClient()

    # 4. Risk Engine
    circuit_breaker = CircuitBreaker(max_daily_drawdown_percent=settings.DAILY_MAX_DRAWDOWN_PERCENT)
    circuit_breaker.reset_daily_metrics(settings.STARTING_BALANCE_USDT)
    risk_manager = RiskManager(event_bus, db, circuit_breaker, vyce_client=vyce_client)

    # 5. OMS & Execution
    oms = OrderManagementSystem(event_bus)
    paper_trader = PaperTrader(event_bus, db, circuit_breaker)
    binance_client = BinanceClient()
    binance_executor = BinanceExecutor(event_bus, binance_client, db)

    # 6. AI Advisory (Vyce AI)
    ai_classifier = MarketRegimeClassifier(event_bus, db, client=vyce_client)
```

In `main.py` lines 158-166 (Shutdown cleanup):
```python
    finally:
        logger.info("Shutting down Trading Lab services...")
        await ws_feed.stop()
        await event_bus.stop()
        await binance_client.close()
        await vyce_client.close()
        await db.close()
        server.should_exit = True
        await dashboard_task
        logger.info("All services stopped safely.")
```

---

## 5. Verification Method

### 5.1. Automated Regression Verification
Run the existing test suite:
```powershell
.venv\Scripts\pytest.exe -v
```
**Expected**: All 10 existing tests in `tests/` pass with 100% pass rate.

### 5.2. New Unit Tests to Add (`tests/test_ai_gatekeeper.py`)
Worker must create unit tests verifying:
1. **AI Veto Flow**:
   - Set `settings.ENABLE_AI_ADVISORY = True`.
   - Mock `vyce_client.evaluate_signal_veto` returning `{"approved": False, "reasoning": "Bearish trend rejection"}`.
   - Dispatch `SignalEvent`.
   - Assert `order is None`.
   - Query `db.get_recent_signals(limit=1)` -> assert `approved == 0` and `"AI Advisory Veto"` in `rejection_reason`.
2. **AI Approval & Position Sizing Flow**:
   - Mock `vyce_client.evaluate_signal_veto` returning `{"approved": True, "size_multiplier": 0.5, "reasoning": "Strong setup"}`.
   - Dispatch `SignalEvent`.
   - Assert `order is not None`.
   - Assert `order.quantity == round((equity * 0.20 * 0.5) / price, 6)`.
   - Query `db.get_recent_signals(limit=1)` -> assert `approved == 1`.
   - Query `db.get_recent_ai_advisories(limit=1)` -> assert record exists.
3. **Safe Fallback on Timeout**:
   - Mock `vyce_client.evaluate_signal_veto` raising `asyncio.TimeoutError()`.
   - Assert order is approved via `_quantitative_fallback` with `size_multiplier == 0.5` without unhandled exceptions.

### 5.3. Invalidation Conditions
This design would be invalidated if:
1. `SignalEvent` schema is changed to remove `stop_loss` or `confidence`.
2. `aiosqlite` is replaced with a synchronous database driver.
3. `EventBus` moves to multi-threaded worker pools where shared in-memory state requires threading locks.
