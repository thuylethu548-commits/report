# Empirical Challenger Handoff Report — Milestone 1: Fallback Engine Stress Testing

**Agent**: M1 Challenger 1 (critic, specialist)  
**Date**: 2026-09-17T05:40:00Z  
**Working Directory**: `c:\sunMy\trading_bot\.agents\m1_challenger_1`  
**Recipient**: Lead Orchestrator (`4a1d31f3-0188-4bb2-b5c1-ff9c51dda848`)  
**Empirical Verdict**: `DEFECT_DETECTED`

---

## 1. Observation

### 1.1. Test Execution Commands & Results
1. **Baseline Test Suite Run**:
   Command: `.venv\Scripts\pytest -v`
   Result: `31 passed in 9.64s`. All existing unit tests passed.

2. **Empirical Adversarial Stress Test Suite Run**:
   Command: `.venv\Scripts\pytest tests/test_m1_adversarial.py -v -s`
   Result: `2 failed, 29 passed in 8.64s`.
   - **Passed (29 tests)**:
     - `test_latency_spike_timeout_and_eventbus_throughput`: Upstream delay of 5.0s timed out and engaged fallback at **3.02s** (within 3.0s + 0.2s margin), and queued `MarketEvent` on `EventBus` was processed without dropping or stalling.
     - `test_corrupted_json_advisory_safety`: 12/12 corrupted JSON variants (truncated JSON, invalid types, empty dict, list payloads, backtick markdown fences) parsed safely or defaulted without crashing.
     - `test_network_exceptions_safe_recovery`: 7/7 network exceptions (`ConnectError`, `RemoteProtocolError`, `ReadTimeout`, `ConnectTimeout`, `WriteTimeout`, `PoolTimeout`, `RuntimeError`) caught safely by `VyceClient`.
     - `test_http_error_statuses_safe_recovery`: 4/4 HTTP error codes (429, 500, 502, 503) handled without unhandled exceptions.
     - `test_concurrent_signals_under_ai_latency`: 3 concurrent signals processed through EventBus in 1.70s without deadlock.
   - **Failed (2 tests)**:
     - `tests/test_m1_adversarial.py::test_fallback_with_real_vyce_client_enforces_safety_limits`
     - `tests/test_m1_adversarial.py::test_post_mortem_corrupted_payloads_fallback[{"category": null, "title": null, "details": null, "lesson_learned": null}]`

### 1.2. Verbatim Error & Execution Logs

#### Failure 1: Quantitative Safety Bypassed During Fallback
From `tests/test_m1_adversarial.py:366`:
```
FAILED tests/test_m1_adversarial.py::test_fallback_with_real_vyce_client_enforces_safety_limits
[Fallback Check] order_wide_sl result: OrderEvent(order_id='75eff2a6-2ed', strategy_name='EMA_Trend', symbol='BTC/USDT', side=<OrderSide.BUY: 'BUY'>, order_type=<OrderType.MARKET: 'MARKET'>, quantity=0.001667, price=60000.0, stop_loss=54000.0, take_profit=68000.0, timestamp=datetime.datetime(2026, 9, 17, 5, 38, 3, 223550, tzinfo=datetime.timezone.utc), status=<OrderStatus.PENDING: 'PENDING'>)
[Fallback Check] order_low_conf result: OrderEvent(order_id='ef10fedb-45e', strategy_name='EMA_Trend', symbol='BTC/USDT', side=<OrderSide.BUY: 'BUY'>, order_type=<OrderType.MARKET: 'MARKET'>, quantity=0.001667, price=60000.0, stop_loss=58500.0, take_profit=63000.0, timestamp=datetime.datetime(2026, 9, 17, 5, 38, 3, 251994, tzinfo=datetime.timezone.utc), status=<OrderStatus.PENDING: 'PENDING'>)

AssertionError: DEFECT: Wide SL signal (10% SL) was APPROVED during AI network error! Order: OrderEvent(order_id='75eff2a6-2ed', strategy_name='EMA_Trend', symbol='BTC/USDT', side=<OrderSide.BUY: 'BUY'>, order_type=<OrderType.MARKET: 'MARKET'>, quantity=0.001667, price=60000.0, stop_loss=54000.0, take_profit=68000.0, timestamp=datetime.datetime(2026, 9, 17, 5, 38, 3, 223550, tzinfo=datetime.timezone.utc), status=<OrderStatus.PENDING: 'PENDING'>)
assert OrderEvent(...) is None
```

#### Failure 2: String `"None"` Ingestion on Null Post-Mortem Payload
From `tests/test_m1_adversarial.py:297`:
```
FAILED tests/test_m1_adversarial.py::test_post_mortem_corrupted_payloads_fallback[{"category": null, "title": null, "details": null, "lesson_learned": null}]
AssertionError: assert 'None' == 'STOP_LOSS'
  - STOP_LOSS
  + None
```

### 1.3. Code Inspection Observations
1. **`ai_advisory/vyce_client.py:156-162` & `208`**:
   ```python
   except httpx.TimeoutException:
       logger.warning(f"Vyce AI request timed out after {self.timeout}s. Engaging Non-AI fallback.")
       return None
   except Exception as e:
       logger.warning(f"Vyce AI request failed: {e}. Engaging Non-AI fallback.")
       return None
   ```
   When `chat_completion` returns `None`, line 208 calls:
   ```python
   return self._build_fallback_veto(signal, market_context, "AI unreachable or invalid output")
   ```
   In lines 295-317:
   ```python
   rsi = market_context.get("rsi") or market_context.get("rsi_14")
   if signal.side == OrderSide.BUY and rsi is not None and float(rsi) > 75:
       return {"approved": False, ...}
   return {
       "approved": True,
       "regime": str(market_context.get("market_regime", "RANGING")).upper(),
       "risk_score": 3,
       "confidence": 0.50,
       "size_multiplier": 0.50,
       "reasoning": f"Quantitative Fallback: Order approved with conservative sizing. ({error_reason})",
       "model": self.model,
       "fallback_used": True
   }
   ```
   Notice that `_build_fallback_veto` does **not** check the Stop-Loss corridor and does **not** check signal confidence. Furthermore, `RiskManager`'s `market_context` dictionary (`risk_engine/risk_manager.py:105-116`) does not even contain `rsi`, so `_build_fallback_veto` **always** returns `approved: True`!

2. **`risk_engine/risk_manager.py:120-130`**:
   ```python
   timeout_sec = getattr(settings, "AI_TIMEOUT_SECONDS", 3.0)
   try:
       ai_decision = await asyncio.wait_for(
           self.vyce_client.evaluate_signal_veto(signal, market_context),
           timeout=timeout_sec
       )
   except asyncio.TimeoutError:
       logger.warning(f"[AI Fallback Engaged] Timeout after {timeout_sec:.1f}s. Engaging quantitative fallback.")
       ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Timeout (> {timeout_sec:.1f}s)")
   except Exception as e:
       logger.warning(f"[AI Fallback Engaged] Error during signal evaluation: {e}. Engaging quantitative fallback.")
       ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Error ({e})")
   ```
   Because `vyce_client.evaluate_signal_veto` handles the error/timeout internally and returns a dictionary without raising an exception, `RiskManager` **never** enters `except asyncio.TimeoutError` or `except Exception`.

3. **`risk_engine/risk_manager.py:267-317`**:
   `RiskManager._execute_quantitative_fallback`:
   ```python
   # 1. Stop loss distance check: must be between 0.5% and 5.0% of entry price
   sl_dist_pct = (signal.price - signal.stop_loss) / signal.price
   if sl_dist_pct < 0.005 or sl_dist_pct > 0.05:
       return {"approved": False, ...}
   # 2. Confidence threshold check: minimum 0.70 for fallback acceptance
   if signal.confidence < 0.70:
       return {"approved": False, ...}
   ```
   This method is dead code when using the real `VyceClient` because `_execute_quantitative_fallback` is only invoked inside the `except` blocks of `handle_signal`.

4. **`tests/test_risk_engine.py:45-54` vs Real Implementation**:
   Worker 1's unit tests (`test_quantitative_fallback_rejects_wide_stop_loss` and `test_quantitative_fallback_rejects_low_confidence`) passed only because they used mock classes:
   - `MockVyceTimeout`: slept for 5.0s without catching the timeout.
   - `MockVyceNetworkError`: explicitly raised `httpx.ConnectError`.
   Neither mock reflected the real `VyceClient`'s exception-swallowing behavior.

5. **`ai_advisory/vyce_client.py:239-245`**:
   ```python
   parsed = self._clean_and_parse_json(raw_response)
   return {
       "category": str(parsed.get("category", "STOP_LOSS")),
       "title": str(parsed.get("title", f"Cắt lỗ {trade_info.get('symbol')} tại {trade_info.get('exit_price')}")),
       "details": str(parsed.get("details", f"Lệnh đóng do chạm Stop Loss tại {trade_info.get('exit_price')}.")),
       "capital_impact": abs(float(parsed.get("capital_impact", abs(pnl)))),
       "lesson_learned": str(parsed.get("lesson_learned", "Tuân thủ kỷ luật dừng lỗ và điều chỉnh biên độ ATR phù hợp.")),
       "operator": str(parsed.get("operator", "Claude-3.5-Sonnet"))
   }
   ```
   If the LLM returns `{"category": null}`, `parsed.get("category", "STOP_LOSS")` returns `None`. Then `str(None)` produces `"None"`.

---

## 2. Logic Chain

1. **Premise 1 (R1 & Feature 3 in `PROJECT.md`)**:
   The safe fallback engine must ensure that when AI fails or times out (< 3.0s), the system defaults to safe quantitative risk rules to preserve capital.
2. **Premise 2 (Worker 1's Claim in `m1_worker_1/handoff.md` line 34-35)**:
   Worker 1 claimed that upon AI timeout or network error, `_execute_quantitative_fallback` is executed, which:
   - Rejects BUY signals if the Stop-Loss corridor is outside `[0.5%, 5.0%]`.
   - Rejects BUY signals if confidence is `< 0.70`.
   - De-rates position size to 0.50x.
3. **From Observation 1.3.1 & 1.3.2**:
   In production (`main.py`), `RiskManager` is instantiated with the real `VyceClient`.
   When an AI timeout or network error occurs, `VyceClient.chat_completion` catches the exception and returns `None`.
   `VyceClient.evaluate_signal_veto` calls `_build_fallback_veto` and returns a dict with `approved=True` and `fallback_used=True`. No exception is raised.
4. **From Observation 1.3.2 & 1.3.3**:
   Because no exception is raised, `RiskManager.handle_signal`'s `try...except` block succeeds without entering `except asyncio.TimeoutError` or `except Exception`.
   `RiskManager`'s own `_execute_quantitative_fallback` is **never called**.
5. **From Observation 1.1 & 1.2 (Failure 1)**:
   Empirical execution of `test_fallback_with_real_vyce_client_enforces_safety_limits` proves that:
   - A BUY signal with a dangerous 10.0% Stop-Loss (outside the 5% limit) is **APPROVED** and generates an order during an AI outage.
   - A BUY signal with low confidence 0.50 (below the 0.70 threshold) is **APPROVED** and generates an order during an AI outage.
6. **From Observation 1.3.5 & 1.2 (Failure 2)**:
   When post-mortem LLM responses contain `null` keys, `parsed.get(key, default)` returns `None` instead of `default`, converting to literal `"None"` strings in SQLite.
7. **Deduction**:
   The system contains two verified defects. The primary defect (Defect 1) is a Critical Architectural Safety defect that bypasses capital preservation rules during AI outages.

---

## 3. Caveats

1. **Non-destructive testing**: In accordance with the Review-Only constraint, no implementation files (`ai_advisory/vyce_client.py`, `risk_engine/risk_manager.py`) were modified.
2. **Scope of verification**: Live VPS connection to the remote Vyce AI proxy (`https://vyceai.com`) with real Claude-3.5-Sonnet was not executed with real API tokens in this test run, as the dispatch required stress-testing fallback conditions (latency spikes >3.0s, corrupted JSON, network failures) via mock transports.
3. **EventBus concurrency**: Tested up to 3 concurrent signals under latency; throughput under 100+ concurrent market ticks was not stress-tested.

---

## 4. Conclusion & Empirical Verdict

**Empirical Verdict**: `DEFECT_DETECTED`

### Summary of Defects

| ID | Severity | Component | Summary |
|---|---|---|---|
| **DEFECT-M1-01** | **CRITICAL** | `risk_engine/risk_manager.py` & `ai_advisory/vyce_client.py` | **Fallback Safety Bypass**: `VyceClient.evaluate_signal_veto` swallows network errors and timeouts, returning `approved: True` via `_build_fallback_veto`. `RiskManager._execute_quantitative_fallback` is bypassed, allowing dangerous signals (10% SL, 0.50 confidence) to be approved during AI outages. |
| **DEFECT-M1-02** | **MEDIUM** | `ai_advisory/vyce_client.py:239-245` | **Null Post-Mortem Payload String Conversion**: If LLM returns `null` for fields, `str(parsed.get(key, default))` produces string literal `"None"` rather than the fallback string. |

### Concrete Mitigations for Implementer

1. **Fix for DEFECT-M1-01**:
   In `risk_engine/risk_manager.py`:
   After receiving `ai_decision`, check whether `ai_decision.get("fallback_used")` is `True`:
   ```python
   if ai_decision.get("fallback_used"):
       ai_decision = self._execute_quantitative_fallback(signal, reason=ai_decision.get("reasoning", "AI Fallback"))
   ```
   Or have `VyceClient.evaluate_signal_veto` check `signal.confidence < 0.70` and stop-loss corridor in its own `_build_fallback_veto` method.

2. **Fix for DEFECT-M1-02**:
   In `ai_advisory/vyce_client.py:238-245`:
   Replace `str(parsed.get("category", "STOP_LOSS"))` with:
   ```python
   category = str(parsed.get("category") or "STOP_LOSS")
   title = str(parsed.get("title") or f"Cắt lỗ {trade_info.get('symbol')} tại {trade_info.get('exit_price')}")
   details = str(parsed.get("details") or f"Lệnh đóng do chạm Stop Loss tại {trade_info.get('exit_price')}.")
   lesson = str(parsed.get("lesson_learned") or "Tuân thủ kỷ luật dừng lỗ và điều chỉnh biên độ ATR phù hợp.")
   ```

---

## 5. Verification Method

To independently reproduce and verify these findings:

1. **Run the adversarial test suite**:
   ```powershell
   .venv\Scripts\pytest tests/test_m1_adversarial.py -v -s
   ```
   **Expected Outcome**: 2 failures showing:
   - `test_fallback_with_real_vyce_client_enforces_safety_limits` FAILED (Wide SL & Low Confidence approved).
   - `test_post_mortem_corrupted_payloads_fallback` FAILED (`'None' == 'STOP_LOSS'`).
   - 29 stress tests PASSED (latency, corrupted JSON, network errors).

2. **Invalidation Conditions**:
   - `RiskManager.handle_signal` is updated to invoke `_execute_quantitative_fallback` whenever `ai_decision.get("fallback_used")` is True.
   - `VyceClient.generate_post_mortem` uses `parsed.get(...) or default` instead of `parsed.get(..., default)`.
