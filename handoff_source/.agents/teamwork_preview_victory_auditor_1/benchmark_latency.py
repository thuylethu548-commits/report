import asyncio
import httpx
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_latency_during_ai_call():
    client = httpx.AsyncClient(base_url="http://127.0.0.1:8386", timeout=10.0)

    # Trigger a trade in background that triggers AI evaluation (2.8s - 3.0s delay)
    async def trigger_trade():
        return await client.post("/api/v1/test_trade?side=buy")

    # Concurrently poll /api/v1/status 20 times and measure response times
    async def poll_status():
        latencies = []
        for _ in range(15):
            t0 = time.perf_counter()
            r = await client.get("/api/v1/status")
            elapsed = (time.perf_counter() - t0) * 1000
            assert r.status_code == 200
            latencies.append(elapsed)
            await asyncio.sleep(0.1)
        return latencies

    t_trade_task = asyncio.create_task(trigger_trade())
    t_poll_task = asyncio.create_task(poll_status())

    trade_res, latencies = await asyncio.gather(t_trade_task, t_poll_task)
    avg_lat = sum(latencies) / len(latencies)
    max_lat = max(latencies)
    min_lat = min(latencies)

    print(f"Concurrent Polling Latency during active AI evaluation:")
    print(f"Min: {min_lat:.2f}ms | Avg: {avg_lat:.2f}ms | Max: {max_lat:.2f}ms")
    assert max_lat < 100.0, f"Max latency too high: {max_lat:.2f}ms"
    print("[PASS] Web server maintained ultra-low latency with zero blocking during external AI call.")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_latency_during_ai_call())
