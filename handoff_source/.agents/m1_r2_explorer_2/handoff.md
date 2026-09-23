# Handoff Report — Milestone 1 Round 2: RiskManager Fallback Enforcement & SQLite Error Handling

**Agent**: M1 R2 Explorer 2 (RiskManager Fallback Unification & SQLite Specialist)  
**Date**: 2026-09-17T05:44:30Z  
**Working Directory**: `c:\sunMy\trading_bot\.agents\m1_r2_explorer_2`  
**Recipient**: Lead Orchestrator (`4a1d31f3-0188-4bb2-b5c1-ff9c51dda848`) & M1 Worker  
**Status**: COMPLETE (Actionable Fix Recommendations Ready)

---

## 1. Observation

### 1.1. Empirical Test Failure Output
Executing `.venv\Scripts\pytest -v` produced the following reproducible failure:

```
================================== FAILURES ===================================
_________ test_fallback_with_real_vyce_client_enforces_safety_limits __________

tests\test_m1_adversarial.py:366: in test_fallback_with_real_vyce_client_enforces_safety_limits
    assert order_wide_sl is None, f"DEFECT: Wide SL signal (10% SL) was APPROVED during AI network error! Order: {order_wide_sl}"
E   AssertionError: DEFECT: Wide SL signal (10% SL) was APPROVED during AI network error! Order: OrderEvent(order_id='bd95b9a1-b3e', strategy_name='EMA_Trend', symbol='BTC/USDT', side=<OrderSide.BUY: 'BUY'>, order_type=<OrderType.MARKET: 'MARKET'>, quantity=0.001667, price=60000.0, stop_loss=54000.0, take_profit=68000.0, timestamp=datetime.datetime(2026, 9, 17, 5, 40, 23, 504360, tzinfo=datetime.timezone.utc), status=<OrderStatus.PENDING: 'PENDING'>)

[Fallback Check] order_wide_sl result: OrderEvent(...)
[Fallback Check] order_low_conf result: OrderEvent(...)
```

### 1.2. Root Cause in Code Tracing
1. **`ai_advisory/vyce_client.py` (lines 156–161 & 208)**:
   ```python
   except httpx.TimeoutException:
       logger.warning(f"Vyce AI request timed out after {self.timeout}s. Engaging Non-AI fallback.")
       return None
   except Exception as e:
       logger.warning(f"Vyce AI request failed: {e}. Engaging Non-AI fallback.")
       return None
   ...
   return self._build_fallback_veto(signal, market_context, "AI unreachable or invalid output")
   ```
   `chat_completion` catches all `httpx.RequestError` and timeout exceptions, returning `None`. `evaluate_signal_veto` calls `_build_fallback_veto()` which returns:
   ```python
   {
       "approved": True,
       "regime": "RANGING",
       "risk_score": 3,
       "confidence": 0.50,
       "size_multiplier": 0.50,
       "reasoning": "Quantitative Fallback: Order approved with conservative sizing. (AI unreachable or invalid output)",
       "model": self.model,
       "fallback_used": True
   }
   ```
   Crucially, `_build_fallback_veto` **does not validate** the Stop-Loss corridor `[0.5%, 5.0%]` or signal confidence `>= 0.70`.

2. **`risk_engine/risk_manager.py` (lines 119–137)**:
   ```python
   try:
       ai_decision = await asyncio.wait_for(
           self.vyce_client.evaluate_signal_veto(signal, market_context),
           timeout=timeout_sec
       )
   except asyncio.TimeoutError:
       ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Timeout (> {timeout_sec:.1f}s)")
   except Exception as e:
       ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Error ({e})")

   approved = bool(ai_decision.get("approved", True))
   ```
   Because `evaluate_signal_veto` returns a normal dictionary instead of raising an exception, `wait_for` succeeds. `RiskManager` consumes `ai_decision` directly. It **never checks** `ai_decision.get("fallback_used")`.
   Consequently, `RiskManager._execute_quantitative_fallback(signal, ...)` (lines 249–318) is bypassed, and the unsafe trade (10% Stop-Loss, 0.50 confidence) is approved!

3. **Unhandled SQLite Exceptions in `risk_engine/risk_manager.py`**:
   - **Line 153**: `await self.db.save_ai_advisory(...)` is called with no `try...except`.
   - **Line 229**: `await self.db.save_signal(..., approved=True, ...)` is called with no `try...except`.
   - **Line 322**: In `_record_rejection`, `await self.db.save_signal(..., approved=False, ...)` is called with no `try...except`.
   If SQLite encounters a concurrency lock (`sqlite3.OperationalError: database is locked`) or I/O error:
   - An approved trade crashes and is never published to `EventBus` (`await self.event_bus.publish(order_event)` is never reached).
   - An advisory logging failure aborts the risk pipeline, dropping valid signals.

---

## 2. Logic Chain

1. **Premise 1 (R1 & Feature 3 Mandate)**:
   Under `ORIGINAL_REQUEST.md` §R1 and `PROJECT.md` Feature 3, whenever AI advisory is unavailable (timeout, connection error, DNS failure, 5xx), the quantitative fallback must strictly protect capital:
   - BUY signals with Stop-Loss outside `[0.5%, 5.0%]` must be rejected.
   - BUY signals with confidence `< 0.70` must be rejected.
   - Only compliant BUY signals may proceed, de-rated to `0.50x` sizing.
   - SELL signals must be approved unconditionally to facilitate capital exit.

2. **From Observation 1.1 & 1.2**:
   `RiskManager._execute_quantitative_fallback` correctly implements these exact four rules. However, when using a real `VyceClient` under network failure, `VyceClient` absorbs the error internally and returns a fallback dictionary with `"fallback_used": True` and `"approved": True`.

3. **From Observation 1.2**:
   Because `RiskManager.handle_signal` only invoked `_execute_quantitative_fallback` inside its `except` blocks, `_execute_quantitative_fallback` was never executed when `VyceClient` returned its internal fallback dictionary.

4. **From Observation 1.3**:
   Furthermore, without `try...except` guarding SQLite writes, any transient database lock completely crashes `handle_signal`, either failing to place approved orders or raising an unhandled task exception to the EventBus worker.

5. **Inference (Defense-in-Depth Solution)**:
   `RiskManager` is the supreme guardian of desk capital. It must never assume that an upstream client's fallback is safe.
   By checking:
   ```python
   if not isinstance(ai_decision, dict):
       ai_decision = self._execute_quantitative_fallback(signal, reason="Invalid AI Decision Payload")
   elif ai_decision.get("fallback_used") is True and ai_decision.get("model") != "quantitative-fallback":
       if not ai_decision.get("approved", True):
           logger.warning(f"[AI Fallback Engaged] AI provider fallback vetoed signal: {ai_decision.get('reasoning')}")
       else:
           fb_reason = ai_decision.get("reasoning") or "AI provider fallback engaged"
           ai_decision = self._execute_quantitative_fallback(signal, reason=fb_reason)
   ```
   `RiskManager` intercepts any fallback approval and subjects it to its strict quantitative corridor and confidence checks. If already vetoed by the provider (e.g. RSI overbought), the veto is preserved.
   Wrapping all three database write calls in `try...except Exception as e:` ensures transient database lockouts degrade gracefully without dropping live orders.

---

## 3. Exact Fix Specifications for Worker

### Fix 1: Fallback Enforcement in `risk_engine/risk_manager.py`
**File**: `c:\sunMy\trading_bot\risk_engine\risk_manager.py`  
**Target Lines**: ~128–135  

#### Code Replacement:
```python
<<<<
            except Exception as e:
                logger.warning(f"[AI Fallback Engaged] Error during signal evaluation: {e}. Engaging quantitative fallback.")
                ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Error ({e})")

            # Parse AI decision
            approved = bool(ai_decision.get("approved", True))
            regime_raw = str(ai_decision.get("regime", "ranging")).lower()
====
            except Exception as e:
                logger.warning(f"[AI Fallback Engaged] Error during signal evaluation: {e}. Engaging quantitative fallback.")
                ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Error ({e})")

            # Enforce RiskManager quantitative fallback rules if AI provider engaged fallback or returned invalid payload
            if not isinstance(ai_decision, dict):
                logger.warning(f"[AI Fallback Engaged] Invalid non-dict AI decision payload ({type(ai_decision)}). Engaging quantitative fallback.")
                ai_decision = self._execute_quantitative_fallback(signal, reason="Invalid AI Decision Payload")
            elif ai_decision.get("fallback_used") is True and ai_decision.get("model") != "quantitative-fallback":
                if not ai_decision.get("approved", True):
                    # Upstream fallback already vetoed (e.g. extreme volatility or RSI overbought); respect the veto
                    logger.warning(f"[AI Fallback Engaged] AI provider fallback vetoed signal: {ai_decision.get('reasoning')}")
                else:
                    # Upstream fallback tentatively approved; enforce RiskManager quantitative corridor & confidence gates
                    fb_reason = ai_decision.get("reasoning") or "AI provider fallback engaged"
                    logger.warning(f"[AI Fallback Engaged] Fallback flagged by AI provider; enforcing RiskManager quantitative rules: {fb_reason}")
                    ai_decision = self._execute_quantitative_fallback(signal, reason=fb_reason)

            # Parse AI decision
            approved = bool(ai_decision.get("approved", True))
            regime_raw = str(ai_decision.get("regime", "ranging")).lower()
>>>>
```

---

### Fix 2: SQLite Lock Protection for `save_ai_advisory`
**File**: `c:\sunMy\trading_bot\risk_engine\risk_manager.py`  
**Target Lines**: ~151–162  

#### Code Replacement:
```python
<<<<
            # Persist to SQLite ai_advisory_logs table
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
====
            # Persist to SQLite ai_advisory_logs table with transient lock guard
            if self.db:
                try:
                    await self.db.save_ai_advisory(
                        symbol=signal.symbol,
                        regime=advisory_event.regime.value,
                        risk_score=advisory_event.risk_score,
                        trade_allowed=advisory_event.trade_allowed,
                        size_multiplier=advisory_event.size_multiplier,
                        reasoning=advisory_event.reasoning,
                        dt=advisory_event.timestamp
                    )
                except Exception as e:
                    logger.warning(f"Failed to persist AI advisory log to SQLite (lock/concurrency): {e}")
>>>>
```

---

### Fix 3: SQLite Lock Protection for Approved `save_signal`
**File**: `c:\sunMy\trading_bot\risk_engine\risk_manager.py`  
**Target Lines**: ~227–241  

#### Code Replacement:
```python
<<<<
        # Record approved signal in SQLite signals table
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
                approved=True,
                rejection_reason=""
            )
====
        # Record approved signal in SQLite signals table with transient lock guard
        if self.db:
            try:
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
            except Exception as e:
                logger.warning(f"Failed to persist approved signal to SQLite (lock/concurrency): {e}")
>>>>
```

---

### Fix 4: SQLite Lock Protection in `_record_rejection`
**File**: `c:\sunMy\trading_bot\risk_engine\risk_manager.py`  
**Target Lines**: ~319–334  

#### Code Replacement:
```python
<<<<
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
====
    async def _record_rejection(self, signal: SignalEvent, reason: str) -> None:
        """Persist rejected signal and reason into SQLite signals table with transient lock guard."""
        if self.db:
            try:
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
            except Exception as e:
                logger.warning(f"Failed to persist rejected signal to SQLite (lock/concurrency): {e}")
>>>>
```

---

### Fix 5: Unit Tests to Append to `tests/test_risk_engine.py`
Add the following two tests to `tests/test_risk_engine.py`:

```python
@pytest.mark.asyncio
async def test_risk_manager_with_real_vyce_client_outage_rejects_unsafe_signals(setup_env):
    """
    Verifies that when a real VyceClient encounters a network outage, RiskManager enforces
    its quantitative corridor checks and rejects wide Stop-Loss and low-confidence BUY signals.
    """
    db, event_bus, cb, _ = setup_env

    class FailTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            raise httpx.ConnectError("Offline")

    mock_client = httpx.AsyncClient(transport=FailTransport())
    vyce_client = VyceClient(http_client=mock_client)
    rm = RiskManager(event_bus, db, cb, vyce_client=vyce_client)

    try:
        # Signal 1: Wide Stop-Loss (10% SL)
        wide_sl_signal = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=60000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=54000.0,
            take_profit=68000.0,
            confidence=0.85
        )
        order1 = await rm.handle_signal(wide_sl_signal)
        assert order1 is None, "Expected rejection for 10% Stop-Loss signal"

        # Signal 2: Low Confidence (0.50)
        low_conf_signal = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=60000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=58500.0,
            take_profit=63000.0,
            confidence=0.50
        )
        order2 = await rm.handle_signal(low_conf_signal)
        assert order2 is None, "Expected rejection for confidence < 0.70"

        # Signal 3: Safe Signal (2.5% SL, 0.85 conf)
        safe_signal = SignalEvent(
            strategy_name="EMA_Trend",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            price=60000.0,
            timestamp=datetime.now(timezone.utc),
            stop_loss=58500.0,
            take_profit=63000.0,
            confidence=0.85
        )
        order3 = await rm.handle_signal(safe_signal)
        assert order3 is not None, "Expected approval for safe signal in quantitative fallback"
        assert order3.quantity == 0.000167  # 50% de-rated sizing
    finally:
        await vyce_client.close()
        await mock_client.aclose()


@pytest.mark.asyncio
async def test_risk_manager_handles_sqlite_locks_gracefully(setup_env):
    """
    Verifies that transient SQLite locks during advisory or signal logging do not
    crash RiskManager.handle_signal or drop approved orders.
    """
    _, event_bus, cb, _ = setup_env

    class LockedDb:
        async def get_recent_candles(self, *args, **kwargs):
            return []
        async def save_ai_advisory(self, *args, **kwargs):
            raise RuntimeError("sqlite3.OperationalError: database is locked")
        async def save_signal(self, *args, **kwargs):
            raise RuntimeError("sqlite3.OperationalError: database is locked")

    class MockAiApproval:
        async def evaluate_signal_veto(self, signal, market_context):
            return {
                "approved": True,
                "regime": "BULL_TREND",
                "risk_score": 2,
                "confidence": 0.85,
                "size_multiplier": 0.8,
                "reasoning": "Trend solid",
                "fallback_used": False
            }

    rm = RiskManager(event_bus, LockedDb(), cb, vyce_client=MockAiApproval())

    sig = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=60000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=58500.0,
        take_profit=63000.0,
        confidence=0.85
    )

    # Must complete successfully and return OrderEvent without raising unhandled exception
    order = await rm.handle_signal(sig)
    assert order is not None
    assert order.symbol == "BTC/USDT"
```

---

## 4. Caveats

1. **Read-Only Protocol Adherence**: M1 R2 Explorer 2 did not modify production code in `risk_engine/` or `tests/`. All proposed changes were validated in memory via programmatic monkeypatching and dry runs.
2. **Post-Mortem Parsing Scope**: The failure in `test_post_mortem_corrupted_payloads_fallback[{"category": null...}]` is located in `ai_advisory/vyce_client.py:238-245` (`parsed.get("category") or "STOP_LOSS"`). This is addressed by Explorer 1 and is independent of the RiskManager fallback logic.

---

## 5. Conclusion

- **Defect Isolated**: The critical failure in `test_fallback_with_real_vyce_client_enforces_safety_limits` occurred because `RiskManager.handle_signal` did not inspect `ai_decision.get("fallback_used") is True`, thereby bypassing its internal Stop-Loss corridor `[0.5%, 5.0%]` and confidence threshold `>= 0.70` checks.
- **SQLite Robustness**: Wrapping the three database write points in `RiskManager` ensures resilience against high-concurrency database locks.
- **Empirical Validation**: When patched, `test_fallback_with_real_vyce_client_enforces_safety_limits` passed 100%, rejecting wide Stop-Loss and low confidence trades while successfully sizing compliant trades at 50%.

---

## 6. Verification Method

### 6.1. Execute Full Adversarial Test
After Worker applies Fixes 1–4:
```powershell
.venv\Scripts\pytest -v tests/test_m1_adversarial.py -k "test_fallback_with_real_vyce_client_enforces_safety_limits"
```
**Expected Result**:
```
tests/test_m1_adversarial.py::test_fallback_with_real_vyce_client_enforces_safety_limits PASSED [100%]
```

### 6.2. Run Entire Test Suite
```powershell
.venv\Scripts\pytest -v
```
**Expected Result**: 100% pass across all tests.
