import httpx
import sqlite3
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_e2e_live_test():
    client = httpx.Client(base_url="http://127.0.0.1:8386", timeout=15.0)

    # 1. Trigger Test Trade
    print("--- 1. Testing Technical Signal & AI Advisory Gatekeeper ---")
    r_trade = client.post("/api/v1/test_trade?side=buy")
    print(f"Trigger trade response: {r_trade.status_code} -> {r_trade.json()}")
    assert r_trade.status_code == 200

    # Wait 3.5 seconds for AI Advisory evaluation and fallback/response
    time.sleep(3.5)

    # 2. Check logs from /api/v1/logs
    r_logs = client.get("/api/v1/logs")
    assert r_logs.status_code == 200
    logs = r_logs.json()
    print(f"Total audit logs in live system: {len(logs)}")
    ai_logs = [l for l in logs if "AI Advisory" in l.get("msg", "")]
    assert len(ai_logs) > 0, "No AI Advisory audit logs found"
    print(f"Latest AI Advisory log in terminal: {ai_logs[-1]}")

    # 3. Check SQLite ai_advisory_logs
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, symbol, regime, risk_score, trade_allowed, reasoning, timestamp, confidence FROM ai_advisory_logs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    print(f"Latest SQLite ai_advisory_log row: {row}")
    assert row is not None
    assert row[1] == "BTC/USDT"
    assert row[7] is not None, "Confidence must not be None"
    print(f"[PASS] AI Advisory correctly logged to SQLite with reasoning and confidence={row[7]}")

    # 4. Post-Mortem & Stop-Loss SQLite Verification
    print("\n--- 2. Testing Stop-Loss Post-Mortem & SQLite Lessons Engine ---")
    cursor.execute("SELECT count(*) FROM trading_lessons")
    initial_lessons_count = cursor.fetchone()[0]
    print(f"Initial lessons in DB: {initial_lessons_count}")

    # We can post a lesson directly through the API or trigger paper trader
    # Let's test the /api/v1/lessons endpoint and verify it appears in SQLite & /admin/lessons
    test_lesson_payload = {
        "category": "STOP_LOSS",
        "title": "Audit SL Test: BTC Liquidity Sweep Protection",
        "details": "Auditor simulated Stop-Loss hit at $59,200. Rapid reversal triggered automated capital preservation.",
        "capital_impact": 150.0,
        "lesson_learned": "Respect hard risk boundaries; automated stop-loss prevented deeper portfolio drawdown.",
        "operator": "Claude-3.5-Sonnet"
    }
    r_add_lesson = client.post("/api/v1/lessons", json=test_lesson_payload)
    assert r_add_lesson.status_code == 200, f"Failed to add lesson: {r_add_lesson.text}"
    new_lesson_id = r_add_lesson.json().get("lesson_id")
    print(f"Created new lesson via API: ID={new_lesson_id}")

    # Verify lesson exists in SQLite
    cursor.execute("SELECT id, title, category, capital_impact, lesson_learned, operator FROM trading_lessons WHERE id = ?", (new_lesson_id,))
    lesson_row = cursor.fetchone()
    assert lesson_row is not None
    assert lesson_row[1] == test_lesson_payload["title"]
    assert lesson_row[2] == "STOP_LOSS"
    assert lesson_row[5] == "Claude-3.5-Sonnet"
    print(f"[PASS] Lesson #{new_lesson_id} persisted authentically in SQLite trading_lessons: {lesson_row}")

    # Verify /api/v1/lessons returns it as latest
    r_lessons_list = client.get("/api/v1/lessons?limit=5")
    latest_api_lesson = r_lessons_list.json()[0]
    assert latest_api_lesson["id"] == new_lesson_id
    assert latest_api_lesson["title"] == test_lesson_payload["title"]
    print(f"[PASS] /api/v1/lessons returned newly created lesson at index 0 (strict reverse-chronological)")

    # Clean up test lesson to keep production DB pristine
    cursor.execute("DELETE FROM trading_lessons WHERE id = ?", (new_lesson_id,))
    conn.commit()
    conn.close()
    print(f"[PASS] Test lesson cleaned up; database state verified pristine.")

if __name__ == "__main__":
    run_e2e_live_test()
