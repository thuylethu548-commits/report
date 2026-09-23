import pytest
from httpx import AsyncClient, ASGITransport
from data.storage import Database
from web.app import create_web_app
from risk_engine.circuit_breaker import CircuitBreaker
from web.routes.admin_routes import get_expected_admin_token


@pytest.mark.asyncio
async def test_antigravity_canvas_page_and_apis():
    db = Database("trading_bot.db")
    await db.connect()
    cb = CircuitBreaker()
    app = create_web_app(db=db, circuit_breaker=cb)

    token = get_expected_admin_token()
    headers = {"Cookie": f"admin_session_token={token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Admin Canvas Page
        resp = await client.get("/admin/antigravity-canvas", headers=headers)
        assert resp.status_code == 200
        html = resp.text
        assert "panel-sidebar" in html
        assert "panel-chat" in html
        assert "panel-auxiliary" in html
        assert "editor-textarea" in html
        assert "antigravity_canvas.js" in html

        # 2. Workspace Tree API
        resp_tree = await client.get("/api/v1/canvas/workspace-tree", headers=headers)
        assert resp_tree.status_code == 200
        tree_data = resp_tree.json()
        assert "tree" in tree_data
        assert len(tree_data["tree"]) > 0

        # 3. Models Quota API
        resp_quota = await client.get("/api/v1/canvas/models-quota", headers=headers)
        assert resp_quota.status_code == 200
        quota_data = resp_quota.json()
        assert quota_data["success"] is True
        assert any("Grok" in m["name"] for m in quota_data["models"])

        # 4. File Content API
        resp_file = await client.get("/api/v1/canvas/file-content?path=config/settings.py", headers=headers)
        assert resp_file.status_code == 200
        file_data = resp_file.json()
        assert file_data["language"] == "python"
        assert "Astra" in file_data["content"] or "settings" in file_data["content"].lower()

        # 5. Canvas Agent Chat API
        resp_chat = await client.post(
            "/api/v1/canvas/chat",
            json={"prompt": "Audit hệ thống", "model": "deepseek-v4-flash"},
            headers=headers
        )
        assert resp_chat.status_code == 200
        chat_data = resp_chat.json()
        assert "thoughts" in chat_data
        assert "actions" in chat_data
        assert "content" in chat_data

    await db.close()
