import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
from web.app import create_web_app


@pytest_asyncio.fixture
async def app_client(tmp_path):
    db_path = str(tmp_path / "test_quantum_routes.db")
    db = Database(db_path)
    await db.connect()
    cb = CircuitBreaker()
    app = create_web_app(db=db, circuit_breaker=cb)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await db.close()


@pytest.mark.asyncio
async def test_get_quantum_5d_tensor_endpoint(app_client):
    response = await app_client.get("/api/v1/quantum/5d_tensor?symbol=BTC/USDT")
    assert response.status_code == 200
    data = response.json()

    assert "tensor_score" in data
    assert "dimensions" in data
    assert "verdict" in data
    assert data["symbol"] == "BTC/USDT"
    assert "d1_price_action" in data["dimensions"]
    assert "d5_risk_funding" in data["dimensions"]


@pytest.mark.asyncio
async def test_post_quantum_5d_evaluate_endpoint(app_client):
    payload = {
        "symbol": "BTC/USDT",
        "is_boss_override": True
    }
    response = await app_client.post("/api/v1/quantum/5d_tensor/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["is_boss_override"] is True
    assert data["verdict"] == "BOSS_SUPREME_APPROVED"
    assert data["action"] == "FORCE_EXECUTE_10U"
    assert "Chủ Tịch" in data["speech_brief"]
