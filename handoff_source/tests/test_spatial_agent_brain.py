import pytest
import asyncio
from core.spatial_agent_brain import SpatialAgentBrain, get_spatial_brain
from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker


@pytest.mark.asyncio
async def test_spatial_brain_initialization_and_metadata():
    db = Database(db_path=":memory:")
    await db.connect()
    cb = CircuitBreaker()
    brain = SpatialAgentBrain(db=db, circuit_breaker=cb)

    assert len(brain.agents) == 10
    assert "Astra" in brain.agents
    assert "Palermo" in brain.agents
    assert "Rik" in brain.agents
    assert "Prof" in brain.agents

    assert brain.agents["Palermo"].dept_key == "spot_dca"
    assert brain.agents["Rik"].dept_key == "risk_council"
    assert brain.agents["Astra"].dept_key == "lead_pm"

    await db.close()


@pytest.mark.asyncio
async def test_spatial_debate_generation():
    db = Database(db_path=":memory:")
    await db.connect()
    cb = CircuitBreaker()
    brain = SpatialAgentBrain(db=db, circuit_breaker=cb)

    ctx = await brain.get_live_market_context()
    assert "btc_price" in ctx
    assert "drawdown_pct" in ctx

    debate = await brain._generate_contextual_debate(ctx)
    assert debate is not None
    assert "topic" in debate
    assert len(debate["steps"]) == 4
    assert debate["steps"][0]["speaker_name"] in ["Palermo", "Tory", "Hash"]

    await db.close()


@pytest.mark.asyncio
async def test_spatial_intercom_dialogue():
    db = Database(db_path=":memory:")
    await db.connect()
    cb = CircuitBreaker()
    brain = SpatialAgentBrain(db=db, circuit_breaker=cb)

    # Test asking Rik
    reply_rik = await brain.interact_with_agent("Rik", "Tại sao chú lại VETO lệnh?")
    assert reply_rik["agent_name"] == "Rik"
    assert "VETO" in reply_rik["reply"] or "Rủi Ro" in reply_rik["reply"]

    # Test asking Palermo
    reply_palermo = await brain.interact_with_agent("Palermo", "Kèo nào ngon nhất?")
    assert reply_palermo["agent_name"] == "Palermo"
    assert any(k in reply_palermo["reply"] for k in ["Palermo", "Xu Hướng", "Boss", "EMA", "kèo", "tín hiệu"])

    # Test asking Astra
    reply_astra = await brain.interact_with_agent("Astra", "Tổng kết tình hình?")
    assert reply_astra["agent_name"] == "Astra"
    assert "Astra" in reply_astra["reply"]

    # Test Boss Supreme Override execution
    reply_override = await brain.interact_with_agent("Palermo", "Tao bảo vào lệnh test 10U ngay!")
    assert reply_override["executed_order"] is not None
    assert reply_override["executed_order"]["status"] == "OPEN"
    assert "BOSS-OVR-" in reply_override["executed_order"]["order_id"]
    assert "BOSS-OVR-" in reply_override["reply"]

    # Test 5D Quantum Tensor query
    reply_quantum = await brain.interact_with_agent("Prof", "Chỉ số 5D Quantum Tensor hiện tại thế nào?")
    assert "QUANTUM 5D CONFLUENCE TENSOR" in reply_quantum["reply"]
    assert "Coherence" in reply_quantum["reply"]

    await db.close()

