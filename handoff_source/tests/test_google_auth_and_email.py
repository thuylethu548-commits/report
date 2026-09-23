import asyncio
import os
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from data.storage import Database
from config.settings import settings
from monitoring.email_service import EmailService, email_service
from web.routes.client_routes import get_client_router
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates


@pytest_asyncio.fixture
async def test_db(tmp_path):
    db_file = str(tmp_path / "test_auth_email.db")
    db = Database(db_file)
    await db.connect()
    yield db
    await db.close()


@pytest.fixture
def test_app(test_db):
    app = FastAPI()
    templates = Jinja2Templates(directory="web/templates")
    router = get_client_router(templates, db=test_db)
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_email_service_config():
    service = EmailService(
        host="smtp.gmail.com",
        port=587,
        user="test@gmail.com",
        password="***REDACTED***"
    )
    assert service.host == "smtp.gmail.com"
    assert service.port == 587
    assert service.user == "test@gmail.com"
    assert service.enabled is True


@pytest.mark.asyncio
async def test_email_service_send_mock():
    service = EmailService(
        host="smtp.gmail.com",
        port=587,
        user="test@gmail.com",
        password="***REDACTED***"
    )
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp_instance
        
        success = await service.send_welcome_email(
            to_email="client@example.com",
            full_name="Nguyễn Văn Test",
            username="test_client"
        )
        assert success is True
        assert mock_smtp_instance.starttls.called
        assert mock_smtp_instance.login.called
        assert mock_smtp_instance.send_message.called


@pytest.mark.asyncio
async def test_google_auth_missing_token(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # JSON post without credential
        res = await client.post("/portal/auth/google", json={})
        assert res.status_code == 400
        assert "Thiếu mã" in res.json()["error"]


@pytest.mark.asyncio
async def test_google_auth_invalid_token(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_res = MagicMock()
            mock_res.status_code = 400
            mock_res.text = "Invalid Value"
            mock_get.return_value = mock_res

            res = await client.post("/portal/auth/google", json={"credential": "invalid_jwt_token"})
            assert res.status_code == 400
            assert "Xác thực Google không hợp lệ" in res.json()["error"]


@pytest.mark.asyncio
async def test_google_auth_new_user_success(test_app, test_db):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        mock_google_info = {
            "iss": "https://accounts.google.com",
            "sub": "google_uid_998877",
            "email": "trader.vip@gmail.com",
            "name": "Hoan Vi VIP",
            "picture": "https://lh3.googleusercontent.com/a/avatar.jpg"
        }

        with patch("httpx.AsyncClient.get") as mock_get, \
             patch.object(email_service, "send_welcome_email") as mock_welcome:
            mock_res = MagicMock()
            mock_res.status_code = 200
            mock_res.json.return_value = mock_google_info
            mock_get.return_value = mock_res
            mock_welcome.return_value = True

            res = await client.post(
                "/portal/auth/google",
                json={"credential": "valid_mock_jwt_token"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["redirect"] == "/portal/dashboard"

            # Verify cookie set
            cookie = res.cookies.get("client_session_user")
            assert cookie is not None

            # Verify user created in SQLite
            user = await test_db.get_user_by_email("trader.vip@gmail.com")
            assert user is not None
            assert user["google_id"] == "google_uid_998877"
            assert user["picture"] == "https://lh3.googleusercontent.com/a/avatar.jpg"
            assert user["full_name"] == "Hoan Vi VIP"


@pytest.mark.asyncio
async def test_google_auth_existing_user_login(test_app, test_db):
    # Pre-create user with same email
    await test_db.create_user(
        username="hoanvi_vip",
        hashed_password="***REDACTED***",
        full_name="Hoan Vi",
        email="hoanvi.existing@gmail.com",
        role="client"
    )

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        mock_google_info = {
            "sub": "google_uid_112233",
            "email": "hoanvi.existing@gmail.com",
            "name": "Hoan Vi",
            "picture": "https://lh3.googleusercontent.com/new_pic.jpg"
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_res = MagicMock()
            mock_res.status_code = 200
            mock_res.json.return_value = mock_google_info
            mock_get.return_value = mock_res

            res = await client.post(
                "/portal/auth/google",
                data={"credential": "valid_token_existing"}
            )
            # Standard form post redirects to /portal/dashboard
            assert res.status_code == 303
            assert res.headers["location"] == "/portal/dashboard"
            assert res.cookies.get("client_session_user") == "hoanvi_vip"

            # Check google_id & picture updated
            updated_user = await test_db.get_user_by_username("hoanvi_vip")
            assert updated_user["google_id"] == "google_uid_112233"
            assert updated_user["picture"] == "https://lh3.googleusercontent.com/new_pic.jpg"
