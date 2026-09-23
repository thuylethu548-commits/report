import httpx
import sys

def verify_all():
    client = httpx.Client(base_url="http://127.0.0.1:8386", timeout=10.0)

    # 1. Admin cockpit
    r_admin = client.get("/admin")
    assert r_admin.status_code == 200, f"Expected 200, got {r_admin.status_code}"
    assert "ASTRA CONTROL DESK" in r_admin.text, "Cockpit title missing"
    print("[PASS] GET /admin: 200 OK")

    # 2. Admin lessons HTML
    r_lessons_html = client.get("/admin/lessons")
    assert r_lessons_html.status_code == 200, f"Expected 200, got {r_lessons_html.status_code}"
    assert "lessons-container" in r_lessons_html.text, "lessons-container missing"
    print("[PASS] GET /admin/lessons: 200 OK")

    # 3. Admin settings HTML
    r_settings_html = client.get("/admin/settings")
    assert r_settings_html.status_code == 200, f"Expected 200, got {r_settings_html.status_code}"
    assert "ENABLE_AI_ADVISORY" in r_settings_html.text, "ENABLE_AI_ADVISORY missing"
    print("[PASS] GET /admin/settings: 200 OK")

    # 4. Status API
    r_status = client.get("/api/v1/status")
    assert r_status.status_code == 200, f"Expected 200, got {r_status.status_code}"
    data_status = r_status.json()
    assert "latest_ai_advisory" in data_status, "latest_ai_advisory missing"
    assert "confidence" in data_status["latest_ai_advisory"], "confidence missing from latest_ai_advisory"
    assert "ai_model" in data_status, "ai_model missing"
    adv = data_status["latest_ai_advisory"]
    print(f"[PASS] GET /api/v1/status: 200 OK | model={data_status['ai_model']} | confidence={adv['confidence']} | regime={adv['regime']}")

    # 5. Lessons API
    r_lessons = client.get("/api/v1/lessons")
    assert r_lessons.status_code == 200, f"Expected 200, got {r_lessons.status_code}"
    lessons = r_lessons.json()
    assert len(lessons) >= 1, "Expected at least 1 lesson"
    timestamps = [x["timestamp"] for x in lessons]
    assert timestamps == sorted(timestamps, reverse=True), "Lessons not sorted descending by timestamp"
    print(f"[PASS] GET /api/v1/lessons: 200 OK | count={len(lessons)} | sorted descending confirmed")

    # 6. Settings Hot-Reload API
    # Test updating settings
    r_update = client.post("/api/v1/settings", json={
        "ENABLE_AI_ADVISORY": "true",
        "AI_TIMEOUT_SECONDS": 2.8,
        "MAX_ORDER_SIZE_USDT": 75.0
    })
    assert r_update.status_code == 200, f"Expected 200, got {r_update.status_code}: {r_update.text}"
    print("[PASS] POST /api/v1/settings (valid): 200 OK")

    # Verify settings took effect in status
    r_status_after = client.get("/api/v1/status").json()
    assert r_status_after["ai_advisory_enabled"] is True, "AI advisory not enabled"
    assert r_status_after["ai_timeout_seconds"] == 2.8, f"Timeout mismatch: {r_status_after['ai_timeout_seconds']}"
    print("[PASS] Hot-Reload Verification: AI_TIMEOUT_SECONDS updated to 2.8s without server restart")

    # Test safety bounds enforcement (e.g. DD > 5%)
    r_bad_dd = client.post("/api/v1/settings", json={"DAILY_MAX_DRAWDOWN_PERCENT": 0.08})
    assert r_bad_dd.status_code == 400, f"Expected 400 for bad DD, got {r_bad_dd.status_code}"
    print("[PASS] POST /api/v1/settings (bound check DD > 0.05): correctly rejected with 400")

    # Test safety bounds enforcement (e.g. AI timeout > 10.0s)
    r_bad_timeout = client.post("/api/v1/settings", json={"AI_TIMEOUT_SECONDS": 15.0})
    assert r_bad_timeout.status_code == 400, f"Expected 400 for bad timeout, got {r_bad_timeout.status_code}"
    print("[PASS] POST /api/v1/settings (bound check timeout > 10s): correctly rejected with 400")

if __name__ == "__main__":
    verify_all()
