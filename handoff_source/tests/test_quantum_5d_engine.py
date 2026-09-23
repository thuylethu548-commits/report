import pytest
from core.quantum_5d_engine import Quantum5DTensorEngine, get_quantum_5d_engine


@pytest.mark.asyncio
async def test_quantum_5d_engine_evaluation_and_dimensions():
    engine = Quantum5DTensorEngine()

    res = await engine.evaluate_confluence(symbol="BTC/USDT", is_boss_override=False)

    assert "tensor_score" in res
    assert "coherence_pct" in res
    assert "verdict" in res
    assert "dimensions" in res

    dims = res["dimensions"]
    assert "d1_price_action" in dims
    assert "d2_orderbook" in dims
    assert "d3_volatility_gauss" in dims
    assert "d4_nlp_sentiment" in dims
    assert "d5_risk_funding" in dims

    # Verify score bounds
    assert 0 <= res["tensor_score"] <= 100
    assert 0 <= res["coherence_pct"] <= 100

    # Verify dimensional scores
    for dim_key, dim_data in dims.items():
        assert 0 <= dim_data["score"] <= 100
        assert "details" in dim_data


@pytest.mark.asyncio
async def test_quantum_5d_boss_supreme_override():
    engine = Quantum5DTensorEngine()

    # Even if regular conditions were vetoed, Boss override MUST force approve
    res = await engine.evaluate_confluence(symbol="BTC/USDT", is_boss_override=True)

    assert res["is_boss_override"] is True
    assert res["verdict"] == "BOSS_SUPREME_APPROVED"
    assert res["action"] == "FORCE_EXECUTE_10U"
    assert "CHỦ TỊCH" in res["approval_status"].upper()
    assert "Chủ Tịch" in res["speech_brief"]


@pytest.mark.asyncio
async def test_quantum_5d_singleton():
    inst1 = get_quantum_5d_engine()
    inst2 = get_quantum_5d_engine()
    assert inst1 is inst2
