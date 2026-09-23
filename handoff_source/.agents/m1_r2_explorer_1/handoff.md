# Handoff Report — Milestone 1 Round 2 Investigation: VyceClient Architecture & Safety Fixes

**Agent**: M1 R2 Explorer 1 (explorer, specialist)  
**Date**: 2026-09-17T05:45:00Z  
**Working Directory**: `c:\sunMy\trading_bot\.agents\m1_r2_explorer_1`  
**Recipient**: Lead Orchestrator (`4a1d31f3-0188-4bb2-b5c1-ff9c51dda848`)  

---

## 1. Observation

### 1.1. Empirical Test Suite Execution & Current Failures
Executing `.venv\Scripts\pytest -v` produced 2 failing tests out of 98:
```
================================== FAILURES ===================================
_ test_post_mortem_corrupted_payloads_fallback[{"category": null, "title": null, "details": null, "lesson_learned": null}] _

tests\test_m1_adversarial.py:297: in test_post_mortem_corrupted_payloads_fallback
    assert lesson["category"] == "STOP_LOSS"
E   AssertionError: assert 'None' == 'STOP_LOSS'
E     - STOP_LOSS
E     + None

_________ test_fallback_with_real_vyce_client_enforces_safety_limits __________

tests\test_m1_adversarial.py:366: in test_fallback_with_real_vyce_client_enforces_safety_limits
    assert order_wide_sl is None, f"DEFECT: Wide SL signal (10% SL) was APPROVED during AI network error! Order: {order_wide_sl}"
E   AssertionError: DEFECT: Wide SL signal (10% SL) was APPROVED during AI network error! Order: OrderEvent(order_id='40f59e6e-2f2', strategy_name='EMA_Trend', symbol='BTC/USDT', side=<OrderSide.BUY: 'BUY'>, order_type=<OrderType.MARKET: 'MARKET'>, quantity=0.001667, price=60000.0, stop_loss=54000.0, take_profit=68000.0, timestamp=datetime.datetime(2026, 9, 17, 5, 40, 30, 112778, tzinfo=datetime.timezone.utc), status=<OrderStatus.PENDING: 'PENDING'>)
E   assert OrderEvent(...) is None

=========================== short test summary info ===========================
FAILED tests/test_m1_adversarial.py::test_post_mortem_corrupted_payloads_fallback[{"category": null, "title": null, "details": null, "lesson_learned": null}]
FAILED tests/test_m1_adversarial.py::test_fallback_with_real_vyce_client_enforces_safety_limits
======================== 2 failed, 96 passed in 22.33s ========================
```

### 1.2. Root Cause Code Observations

#### 1.2.1. Fallback Safety Bypass in `ai_advisory/vyce_client.py` & `risk_engine/risk_manager.py`
In `ai_advisory/vyce_client.py:156-161`:
```python
except httpx.TimeoutException:
    logger.warning(f"Vyce AI request timed out after {self.timeout}s. Engaging Non-AI fallback.")
    return None
except Exception as e:
    logger.warning(f"Vyce AI request failed: {e}. Engaging Non-AI fallback.")
    return None
```
When `chat_completion` catches network failures/timeouts and returns `None`, line 208 calls:
```python
# Non-blocking quantitative fallback
return self._build_fallback_veto(signal, market_context, "AI unreachable or invalid output")
```
In lines 288–317 (`_build_fallback_veto`):
```python
def _build_fallback_veto(
    self,
    signal: SignalEvent,
    market_context: Dict[str, Any],
    error_reason: str
) -> Dict[str, Any]:
    rsi = market_context.get("rsi") or market_context.get("rsi_14")
    if signal.side == OrderSide.BUY and rsi is not None and float(rsi) > 75:
        return {"approved": False, "regime": "EXTREME_VOLATILITY", ...}
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
`_build_fallback_veto` checks neither the Stop-Loss corridor (`[0.5%, 5.0%]`) nor signal confidence (`>= 0.70`). It returns `approved: True` for any BUY signal where RSI is not > 75.

In `risk_engine/risk_manager.py:120-130`:
```python
timeout_sec = getattr(settings, "AI_TIMEOUT_SECONDS", 3.0)
try:
    ai_decision = await asyncio.wait_for(
        self.vyce_client.evaluate_signal_veto(signal, market_context),
        timeout=timeout_sec
    )
except asyncio.TimeoutError:
    ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Timeout (> {timeout_sec:.1f}s)")
except Exception as e:
    ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Error ({e})")
```
Because `evaluate_signal_veto` handles errors internally and returns a dict with `approved: True` without raising an exception, `RiskManager` never enters `except asyncio.TimeoutError` or `except Exception`. `RiskManager._execute_quantitative_fallback()` is bypassed.

#### 1.2.2. Null Field Ingestion Bug in `ai_advisory/vyce_client.py:237-246`
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
When `raw_response` is `'{"category": null, "title": null, "details": null, "lesson_learned": null}'`:
1. `parsed` is a dictionary where each key has value `None`.
2. In Python, `dict.get(key, default)` returns `None` (not `default`) because the key exists.
3. `str(None)` converts to string literal `"None"`.
4. The test at `tests/test_m1_adversarial.py:295-302` asserts:
   ```python
   lesson = await client.generate_post_mortem(trade_info)
   assert lesson["category"] == "STOP_LOSS"
   assert "BTC/USDT" in lesson["title"]
   assert lesson["capital_impact"] == 15.0
   assert "Bảo toàn vốn" in lesson["lesson_learned"] or "kỷ luật" in lesson["lesson_learned"]
   assert lesson["operator"] == "Deterministic-Fallback"
   ```
   Because `title` and `lesson_learned` are null, this is an empty/corrupted response from the LLM. It must fail validation and trigger the deterministic fallback (`operator: "Deterministic-Fallback"`).

#### 1.2.3. Existing Interface Contracts and Test Expectations
In `PROJECT.md` (lines 40-58):
```python
async def evaluate_signal_veto(
    self,
    signal: SignalEvent,
    market_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Returns:
    {
        "approved": bool,
        ...
        "fallback_used": bool
    }
    """
```
Existing tests in `tests/test_ai_advisory.py:248-298` and `tests/test_m1_adversarial.py:214-254` verify:
1. `test_vyce_client_evaluate_signal_veto_timeout_fallback`: expects `res["fallback_used"] is True` without raising.
2. `test_vyce_client_evaluate_signal_veto_invalid_json_fallback`: expects `res["fallback_used"] is True` without raising.
3. `test_network_exceptions_safe_recovery`: tests 7 network exceptions and asserts `decision["fallback_used"] is True` without raising.
4. `test_http_error_statuses_safe_recovery`: tests 4 HTTP error status codes and asserts `decision["fallback_used"] is True` without raising.

---

## 2. Logic Chain

1. **Premise 1 (Capital Preservation & Safe Fallback Mandate)**:
   Per `ORIGINAL_REQUEST.md` §R1 and `PROJECT.md` Feature 3, whenever AI proxy communication fails or exceeds `< 3.0s`, execution must not stall and must fall back safely to deterministic quantitative rules. Under quantitative fallback, BUY signals outside the Stop-Loss corridor `[0.5%, 5.0%]` or with strategy confidence `< 0.70` must be vetoed (`approved: False`).

2. **Premise 2 (Interface Contract & Existing Test Invariants)**:
   Multiple unit and stress test suites (`test_ai_advisory.py`, `test_m1_adversarial.py`, `test_m1_adversarial_stress.py`) explicitly require `VyceClient.evaluate_signal_veto` to catch internal transport errors and return a structured dictionary with `fallback_used: True`.
   If `VyceClient.evaluate_signal_veto` were modified to re-raise network/timeout exceptions, **at least 12 existing tests would break**, violating the interface contract specified in `PROJECT.md`.

3. **Architectural Resolution — Defense-in-Depth Structured Fallback**:
   To reconcile Premise 1 and Premise 2 without introducing regressions:
   - **Layer 1 (`VyceClient._build_fallback_veto`)**: Equip `_build_fallback_veto` with complete quantitative safety logic:
     - Unconditionally approve SELL orders (risk reduction).
     - For BUY orders, validate RSI <= 75, Stop-Loss corridor `[0.5%, 5.0%]`, and confidence `>= 0.70`.
     - Veto (`approved: False`) any BUY order failing these criteria.
     - Approve valid BUY orders with conservative 0.50x sizing.
   - **Layer 2 (`RiskManager.handle_signal`)**: In `RiskManager`, add an explicit check for `ai_decision.get("fallback_used")`:
     - If `fallback_used` is True and `approved` is True, route through `self._execute_quantitative_fallback(signal, reason=...)` to guarantee that RiskManager independently enforces its safety rules.
     - This guarantees capital protection even if `VyceClient` is mocked or replaced.

4. **Post-Mortem Null Value Logic**:
   - `{"category": null, "title": null, "details": null, "lesson_learned": null}` represents a corrupted/empty response from the LLM.
   - In `generate_post_mortem`, parsing must validate that `title`, `details`, and `lesson_learned` are non-empty strings.
   - If any required field is missing, None, or empty, a `ValueError` must be raised within the `try` block, catching into `except Exception as e:` and returning the deterministic fallback record with `"operator": "Deterministic-Fallback"`.
   - If `category` is null but other fields are valid, default to `"STOP_LOSS"`.
   - If `capital_impact` is null, default to `abs(pnl)`.

5. **RiskManager SQLite Exception Safety**:
   - Calls to `await self.db.save_ai_advisory(...)` and `await self.db.save_signal(...)` must be wrapped in `try...except Exception as e: logger.error(...)` so that transient database locks do not crash the order routing pipeline.

---

## 3. Caveats

1. **Read-Only Constraint**: In accordance with the Explorer protocol, no production source files were directly modified in this turn. All code edits are provided as exact drop-in specifications for the Worker.
2. **Upstream Network Dependence**: Verification of live proxy queries requires network access to `vyceai.com` and valid credentials (`VYCE_API_KEY` or `ANTHROPIC_API_KEY`), which were already proven operational by M1 Auditor (`m1_auditor_1`). Fallback tests use mocked transports (`httpx.MockTransport`, `FailTransport`).
3. **No Caveats on Root Cause**: Both defects have been isolated to exact line numbers and verified via reproducible pytest failures.

---

## 4. Conclusion & Actionable Fix Recommendations

### Summary of Required Code Changes

| Target File | Lines | Component | Change Rationale |
|---|---|---|---|
| `ai_advisory/vyce_client.py` | 235–258 | `generate_post_mortem` | Add required-field validation for `title`, `details`, `lesson_learned`. Null/empty fields raise `ValueError` and trigger deterministic fallback (`operator: "Deterministic-Fallback"`). Handle null `category` and null `capital_impact` safely. |
| `ai_advisory/vyce_client.py` | 288–317 | `_build_fallback_veto` | Add Stop-Loss corridor check `[0.5%, 5.0%]` and confidence check `>= 0.70` to quantitative fallback, rejecting unsafe BUY signals with `approved: False`. |
| `risk_engine/risk_manager.py` | 131–138 | `handle_signal` | Add defense-in-depth re-validation: if `ai_decision.get("fallback_used") and ai_decision.get("approved")`, validate through `self._execute_quantitative_fallback`. |
| `risk_engine/risk_manager.py` | 152–162, 228–240, 320–334 | SQLite persistence | Wrap `save_ai_advisory` and `save_signal` calls in `try...except Exception as e: logger.error(...)`. |

---

### Exact Fix Specifications for the Worker

#### Fix 1: `ai_advisory/vyce_client.py` — `generate_post_mortem` (Lines 235–258)

**Target Content**:
```python
        if raw_response:
            try:
                parsed = self._clean_and_parse_json(raw_response)
                return {
                    "category": str(parsed.get("category", "STOP_LOSS")),
                    "title": str(parsed.get("title", f"Cắt lỗ {trade_info.get('symbol')} tại {trade_info.get('exit_price')}")),
                    "details": str(parsed.get("details", f"Lệnh đóng do chạm Stop Loss tại {trade_info.get('exit_price')}.")),
                    "capital_impact": abs(float(parsed.get("capital_impact", abs(pnl)))),
                    "lesson_learned": str(parsed.get("lesson_learned", "Tuân thủ kỷ luật dừng lỗ và điều chỉnh biên độ ATR phù hợp.")),
                    "operator": str(parsed.get("operator", "Claude-3.5-Sonnet"))
                }
            except Exception as e:
                logger.warning(f"Failed to parse post-mortem response: {e}")

        # Deterministic fallback post-mortem
        return {
            "category": "STOP_LOSS",
            "title": f"Dừng lỗ tự động {trade_info.get('symbol', 'BTC/USDT')} bảo toàn vốn",
            "details": f"Vị thế {trade_info.get('symbol')} đóng tại {trade_info.get('exit_price', 0.0):.2f} do chạm ngưỡng Stop Loss {trade_info.get('pnl_percent', 0.0):.2f}%.",
            "capital_impact": abs(pnl),
            "lesson_learned": "Bảo toàn vốn là ưu tiên số 1; kích hoạt fallback an toàn ghi nhận kỷ luật cắt lỗ tự động.",
            "operator": "Deterministic-Fallback"
        }
```

**Replacement Content**:
```python
        if raw_response:
            try:
                parsed = self._clean_and_parse_json(raw_response)
                if not isinstance(parsed, dict):
                    raise ValueError("Post-mortem response must be a JSON dictionary")

                title = parsed.get("title")
                details = parsed.get("details")
                lesson = parsed.get("lesson_learned")
                category = parsed.get("category")
                cap_impact = parsed.get("capital_impact")

                # Validate essential fields - if missing, None, or empty, reject and trigger deterministic fallback
                if not title or not isinstance(title, str) or not title.strip():
                    raise ValueError("Post-mortem response missing or empty 'title'")
                if not details or not isinstance(details, str) or not details.strip():
                    raise ValueError("Post-mortem response missing or empty 'details'")
                if not lesson or not isinstance(lesson, str) or not lesson.strip():
                    raise ValueError("Post-mortem response missing or empty 'lesson_learned'")

                impact_val = abs(float(cap_impact if cap_impact is not None else abs(pnl)))
                category_str = str(category).strip() if category else "STOP_LOSS"
                operator_str = str(parsed.get("operator") or "Claude-3.5-Sonnet").strip()

                return {
                    "category": category_str,
                    "title": str(title).strip(),
                    "details": str(details).strip(),
                    "capital_impact": impact_val,
                    "lesson_learned": str(lesson).strip(),
                    "operator": operator_str
                }
            except Exception as e:
                logger.warning(f"Failed to parse post-mortem response: {e}")

        # Deterministic fallback post-mortem
        return {
            "category": "STOP_LOSS",
            "title": f"Dừng lỗ tự động {trade_info.get('symbol', 'BTC/USDT')} bảo toàn vốn",
            "details": f"Vị thế {trade_info.get('symbol')} đóng tại {trade_info.get('exit_price', 0.0):.2f} do chạm ngưỡng Stop Loss {trade_info.get('pnl_percent', 0.0):.2f}%.",
            "capital_impact": abs(pnl),
            "lesson_learned": "Bảo toàn vốn là ưu tiên số 1; kích hoạt fallback an toàn ghi nhận kỷ luật cắt lỗ tự động.",
            "operator": "Deterministic-Fallback"
        }
```

---

#### Fix 2: `ai_advisory/vyce_client.py` — `_build_fallback_veto` (Lines 288–317)

**Target Content**:
```python
    def _build_fallback_veto(
        self,
        signal: SignalEvent,
        market_context: Dict[str, Any],
        error_reason: str
    ) -> Dict[str, Any]:
        """Deterministic quantitative fallback rule when AI service is unavailable."""
        rsi = market_context.get("rsi") or market_context.get("rsi_14")
        if signal.side == OrderSide.BUY and rsi is not None and float(rsi) > 75:
            return {
                "approved": False,
                "regime": "EXTREME_VOLATILITY",
                "risk_score": 4,
                "confidence": 0.50,
                "size_multiplier": 0.20,
                "reasoning": f"Quantitative Fallback Veto: RSI ({float(rsi):.1f}) is overbought. ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

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

**Replacement Content**:
```python
    def _build_fallback_veto(
        self,
        signal: SignalEvent,
        market_context: Dict[str, Any],
        error_reason: str
    ) -> Dict[str, Any]:
        """
        Deterministic quantitative fallback rule when AI service is unavailable.
        - SELL/Exit: Always approve unconditionally to facilitate risk reduction.
        - BUY: Validate RSI overbought limit, Stop-Loss safe corridor [0.5%, 5.0%],
          and signal confidence >= 0.70 before approving with 50% sizing de-rating.
        """
        if signal.side == OrderSide.SELL:
            return {
                "approved": True,
                "regime": "RANGING",
                "risk_score": 2,
                "confidence": signal.confidence,
                "size_multiplier": 1.0,
                "reasoning": f"Quantitative Fallback: Exit signal approved unconditionally. ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

        # BUY Signal Validation:
        # 1. RSI Overbought check
        rsi = market_context.get("rsi") or market_context.get("rsi_14")
        if rsi is not None and float(rsi) > 75:
            return {
                "approved": False,
                "regime": "EXTREME_VOLATILITY",
                "risk_score": 4,
                "confidence": signal.confidence,
                "size_multiplier": 0.20,
                "reasoning": f"Quantitative Fallback Veto: RSI ({float(rsi):.1f}) is overbought. ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

        # 2. Stop Loss Distance Corridor Check [0.5%, 5.0%]
        if signal.stop_loss <= 0 or signal.stop_loss >= signal.price:
            return {
                "approved": False,
                "regime": "RANGING",
                "risk_score": 4,
                "confidence": signal.confidence,
                "size_multiplier": 0.0,
                "reasoning": f"Quantitative Fallback Veto: Invalid Stop Loss ({signal.stop_loss} vs Price {signal.price}). ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

        sl_dist_pct = (signal.price - signal.stop_loss) / signal.price
        if sl_dist_pct < 0.005 or sl_dist_pct > 0.05:
            return {
                "approved": False,
                "regime": "RANGING",
                "risk_score": 4,
                "confidence": signal.confidence,
                "size_multiplier": 0.0,
                "reasoning": f"Quantitative Fallback Veto: Stop Loss distance {sl_dist_pct*100:.2f}% outside safe corridor [0.5%, 5.0%]. ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

        # 3. Confidence Threshold Check: minimum 0.70 for fallback acceptance
        if signal.confidence < 0.70:
            return {
                "approved": False,
                "regime": "RANGING",
                "risk_score": 3,
                "confidence": signal.confidence,
                "size_multiplier": 0.0,
                "reasoning": f"Quantitative Fallback Veto: Signal confidence ({signal.confidence:.2f}) below safe threshold 0.70. ({error_reason})",
                "model": self.model,
                "fallback_used": True
            }

        # 4. Approved with conservative 50% sizing de-rating
        return {
            "approved": True,
            "regime": str(market_context.get("market_regime", "RANGING")).upper(),
            "risk_score": 3,
            "confidence": signal.confidence,
            "size_multiplier": 0.50,
            "reasoning": f"Quantitative Fallback: Order approved with conservative sizing (SL corridor valid, Conf={signal.confidence:.2f}, Size=0.50x). ({error_reason})",
            "model": self.model,
            "fallback_used": True
        }
```

---

#### Fix 3: `risk_engine/risk_manager.py` — Defense-in-Depth & DB Error Handling

**Target Content 3A (Lines 130–133)**:
```python
            except Exception as e:
                logger.warning(f"[AI Fallback Engaged] Error during signal evaluation: {e}. Engaging quantitative fallback.")
                ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Error ({e})")

            # Parse AI decision
            approved = bool(ai_decision.get("approved", True))
```

**Replacement Content 3A**:
```python
            except Exception as e:
                logger.warning(f"[AI Fallback Engaged] Error during signal evaluation: {e}. Engaging quantitative fallback.")
                ai_decision = self._execute_quantitative_fallback(signal, reason=f"AI Error ({e})")

            # Defense-in-depth: If AI client engaged fallback, re-verify via RiskManager's quantitative safety engine
            if ai_decision.get("fallback_used") and ai_decision.get("approved", True):
                ai_decision = self._execute_quantitative_fallback(
                    signal,
                    reason=ai_decision.get("reasoning", "AI Fallback Engaged")
                )

            # Parse AI decision
            approved = bool(ai_decision.get("approved", True))
```

**Target Content 3B (Lines 151–162)**:
```python
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
```

**Replacement Content 3B**:
```python
            # Persist to SQLite ai_advisory_logs table
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
                    logger.error(f"Failed to persist AI advisory to database: {e}")
```

**Target Content 3C (Lines 228–240)**:
```python
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
```

**Replacement Content 3C**:
```python
        # Record approved signal in SQLite signals table
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
                logger.error(f"Failed to persist approved signal to database: {e}")
```

**Target Content 3D (Lines 319–334)**:
```python
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

**Replacement Content 3D**:
```python
    async def _record_rejection(self, signal: SignalEvent, reason: str) -> None:
        """Persist rejected signal and reason into SQLite signals table."""
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
                logger.error(f"Failed to persist rejected signal to database: {e}")
```

---

## 5. Verification Method

### 5.1. Run Complete Automated Test Suite
After applying the fixes, run:
```powershell
.venv\Scripts\pytest -v
```
**Expected Outcome**: **98 passed in ~20s (100% pass rate)**.
- `tests/test_m1_adversarial.py::test_fallback_with_real_vyce_client_enforces_safety_limits` turns **GREEN (PASS)**.
- `tests/test_m1_adversarial.py::test_post_mortem_corrupted_payloads_fallback` turns **GREEN (PASS)**.
- All 36 tests in `tests/test_m1_adversarial_stress.py` remain **GREEN (PASS)**.
- All 31 unit tests in `tests/test_ai_advisory.py` and `tests/test_risk_engine.py` remain **GREEN (PASS)**.

### 5.2. Direct Python Verification of Safety Corridor Rejection with Real VyceClient
Run:
```python
import asyncio
from datetime import datetime, timezone
import httpx
from core.constants import OrderSide
from core.events import SignalEvent
from core.event_bus import EventBus
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
from risk_engine.risk_manager import RiskManager
from ai_advisory.vyce_client import VyceClient

async def verify():
    class FailTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            raise httpx.ConnectError("Offline")

    bus = EventBus()
    db = Database("trading_bot.db")
    cb = CircuitBreaker()
    client = VyceClient(http_client=httpx.AsyncClient(transport=FailTransport()))
    rm = RiskManager(bus, db, cb, vyce_client=client)

    # 10% SL BUY signal must be REJECTED during outage
    sig = SignalEvent("EMA_Trend", "BTC/USDT", OrderSide.BUY, 60000.0, datetime.now(timezone.utc), 54000.0, 68000.0, 0.85)
    order = await rm.handle_signal(sig)
    assert order is None, f"Expected None, got {order}"
    print("Safety corridor rejection under network outage: VERIFIED PASS")

asyncio.run(verify())
```

### 5.3. Direct Python Verification of Post-Mortem Null Field Sanitization
Run:
```python
import asyncio
import httpx
from ai_advisory.vyce_client import VyceClient

async def verify_pm():
    class MockTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(200, json={"choices": [{"message": {"content": '{"category": null, "title": null, "details": null, "lesson_learned": null}'}}]})

    client = VyceClient(http_client=httpx.AsyncClient(transport=MockTransport()))
    trade_info = {"symbol": "BTC/USDT", "pnl_usdt": -15.0, "exit_price": 58500.0, "pnl_percent": -2.5}
    res = await client.generate_post_mortem(trade_info)
    assert res["category"] == "STOP_LOSS", f"Expected STOP_LOSS, got {res['category']}"
    assert res["operator"] == "Deterministic-Fallback", f"Expected Deterministic-Fallback, got {res['operator']}"
    assert "BTC/USDT" in res["title"]
    assert res["capital_impact"] == 15.0
    print("Post-mortem null sanitization: VERIFIED PASS")

asyncio.run(verify_pm())
```

### 5.4. Invalidation Conditions
- If any test in `test_ai_advisory.py` fails due to unhandled exceptions when calling `evaluate_signal_veto`.
- If a BUY signal with Stop-Loss outside `[0.5%, 5.0%]` is approved during an AI timeout or network error.
- If a post-mortem record with `"None"` literal strings appears in SQLite `trading_lessons`.
