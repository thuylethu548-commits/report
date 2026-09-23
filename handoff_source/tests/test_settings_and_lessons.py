import pytest
import os
import aiosqlite
from data.storage import Database
from config.settings import settings


@pytest.mark.asyncio
async def test_settings_and_lessons_lifecycle(tmp_path):
    db_file = str(tmp_path / "test_lifecycle.db")
    db = Database(db_file)
    await db.connect()

    # 1. Test Seed Defaults
    all_settings = await db.get_all_settings()
    assert len(all_settings) >= 8
    keys = [s["key"] for s in all_settings]
    assert "TRADING_MODE" in keys
    assert "DAILY_MAX_DRAWDOWN_PERCENT" in keys

    # 2. Test Get/Set Setting
    await db.set_setting("DAILY_MAX_DRAWDOWN_PERCENT", 0.025, "float", "Test DD")
    val = await db.get_setting("DAILY_MAX_DRAWDOWN_PERCENT")
    assert val == 0.025

    await db.set_setting("ENABLE_AI_ADVISORY", False, "bool", "Test AI")
    val_bool = await db.get_setting("ENABLE_AI_ADVISORY")
    assert val_bool is False

    # 3. Test Seeded Lessons ("Bài học xương máu")
    lessons = await db.get_lessons()
    assert len(lessons) >= 3
    crash_lesson = next((l for l in lessons if l["category"] == "MARKET_CRASH"), None)
    assert crash_lesson is not None
    assert "Circuit Breaker" in crash_lesson["title"]

    # 4. Test Add New Custom Lesson
    lesson_id = await db.add_lesson(
        category="MANUAL_NOTE",
        title="Test Survival Lesson",
        details="Tested during extreme market volatility",
        capital_impact=1000.0,
        lesson_learned="Always use hard risk limits",
        operator="TestOperator"
    )
    assert lesson_id > 0
    updated_lessons = await db.get_lessons()
    assert len(updated_lessons) == len(lessons) + 1

    await db.close()
