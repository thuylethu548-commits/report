import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from data.storage import Database
from config.settings import settings
from web.routes.admin_routes import get_admin_router, get_expected_admin_token
from web.app import create_web_app
from risk_engine.circuit_breaker import CircuitBreaker


@pytest_asyncio.fixture
async def sec_db(tmp_path):
    db_file = str(tmp_path / "test_sec.db")
    db = Database(db_file)
    await db.connect()
    yield db
    await db.close()


@pytest.fixture
def sec_app(sec_db):
    cb = CircuitBreaker()
    app = create_web_app(db=sec_db, circuit_breaker=cb)
    return app


@pytest.mark.asyncio
async def test_admin_unauthorized_redirect(sec_app):
    transport = ASGITransport(app=sec_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Accessing /admin without credentials must redirect to /admin/login
        res = await client.get("/admin", follow_redirects=False)
        assert res.status_code == 303
        assert "/admin/login" in res.headers["location"]


@pytest.mark.asyncio
async def test_admin_login_invalid_password(sec_app):
    transport = ASGITransport(app=sec_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/admin/login", data={"password": "wrong_password", "next": "/admin"})
        assert res.status_code == 200
        assert "Mật khẩu quản trị viên không chính xác" in res.text


@pytest.mark.asyncio
async def test_admin_login_success_and_access(sec_app):
    transport = ASGITransport(app=sec_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login with valid password
        res = await client.post(
            "/admin/login",
            data={"password": "AstraAdmin@2026", "next": "/admin"},
            follow_redirects=False
        )
        assert res.status_code == 303
        assert res.headers["location"] == "/admin"
        cookie = res.cookies.get("admin_session_token")
        assert cookie is not None
        assert cookie == get_expected_admin_token()

        # Follow with cookie to /admin
        client.cookies.set("admin_session_token", cookie)
        cockpit_res = await client.get("/admin")
        assert cockpit_res.status_code == 200
        assert "ASTRA CONTROL DESK" in cockpit_res.text


@pytest.mark.asyncio
async def test_admin_logout(sec_app):
    transport = ASGITransport(app=sec_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("admin_session_token", get_expected_admin_token())
        res = await client.get("/admin/logout", follow_redirects=False)
        assert res.status_code == 303
        assert "/admin/login" in res.headers["location"]


@pytest.mark.asyncio
async def test_security_headers_present(sec_app):
    transport = ASGITransport(app=sec_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        assert res.headers.get("x-frame-options") == "SAMEORIGIN"
        assert res.headers.get("x-content-type-options") == "nosniff"
        assert res.headers.get("x-xss-protection") == "1; mode=block"
        assert "strict-transport-security" in res.headers
        assert "content-security-policy" in res.headers
