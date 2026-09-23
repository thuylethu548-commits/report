import asyncio
import time
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import settings
from ai_advisory.vyce_client import VyceClient

async def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("Astra Quant Desk - Multi-Model AI Council Connectivity Checker")
    print("=" * 60)
    print(f"Base URL:       {settings.VYCE_BASE_URL}")
    print(f"Primary Model:  {settings.VYCE_MODEL} (Supreme Gatekeeper)")
    print(f"Fast Model:     {settings.VYCE_FAST_MODEL} (Technical Scout)")
    print(f"Council Mode:   {settings.AI_COUNCIL_MODE}")
    key_masked = (settings.VYCE_API_KEY[:6] + "..." + settings.VYCE_API_KEY[-4:]) if len(settings.VYCE_API_KEY) > 10 else "***"
    print(f"API Key:        {key_masked}")
    print("-" * 60)

    client = VyceClient()
    client.timeout = 7.0
    client.fast_timeout = 5.0

    prompt = (
        "Respond with a strict JSON object: "
        "{\"status\": \"ONLINE\", \"market_regime\": \"BULLISH\", \"risk_score\": 2, \"confidence\": 0.95}"
    )
    sys_prompt = "You are Astra Quant Desk supreme market advisor."

    # Test 1: Primary (Claude)
    print(f"1. Testing Primary Model [{client.model}]...")
    t0 = time.perf_counter()
    r1 = await client.chat_completion(sys_prompt, prompt, model=client.model)
    e1 = (time.perf_counter() - t0) * 1000.0
    if r1:
        print(f"   [SUCCESS] Received response in {e1:.1f}ms: {r1.strip()[:60]}...")
    else:
        print(f"   [WARNING] Primary model timed out or failed.")

    # Test 2: Fast Scout (DeepSeek)
    print(f"2. Testing Fast Model [{client.fast_model}]...")
    t0 = time.perf_counter()
    r2 = await client.chat_completion(sys_prompt, prompt, model=client.fast_model)
    e2 = (time.perf_counter() - t0) * 1000.0
    if r2:
        print(f"   [SUCCESS] Received response in {e2:.1f}ms: {r2.strip()[:60]}...")
    else:
        print(f"   [WARNING] Fast model timed out or failed.")

    # Test 3: Council Veto Consensus Call
    print(f"3. Testing Live Council Consensus...")
    from core.events import SignalEvent
    from core.constants import OrderSide
    from datetime import datetime, timezone

    sig = SignalEvent(
        strategy_name="EMA_Trend",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        price=65000.0,
        timestamp=datetime.now(timezone.utc),
        stop_loss=64000.0,
        take_profit=67000.0,
        confidence=0.85
    )
    t0 = time.perf_counter()
    council_res = await client.evaluate_signal_veto(sig, {"rsi": 54.0, "market_regime": "BULL_TREND"})
    e3 = (time.perf_counter() - t0) * 1000.0

    print(f"   [COUNCIL DECISION in {e3:.1f}ms]:")
    print(f"   - Approved:       {council_res.get('approved')}")
    print(f"   - Model Operator: {council_res.get('model')}")
    print(f"   - Risk Score:     {council_res.get('risk_score')}/5")
    print(f"   - Confidence:     {council_res.get('confidence')}")
    print(f"   - Sizing Mult:    {council_res.get('size_multiplier')}x")
    print(f"   - Reasoning:      {council_res.get('reasoning')}")
    print("=" * 60)
    print("Multi-Model Council Live Verification COMPLETE.")
    return 0


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
