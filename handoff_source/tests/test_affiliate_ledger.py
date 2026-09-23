from datetime import datetime, timezone

import pytest

from data.storage import Database


@pytest.mark.asyncio
async def test_affiliate_ledger_is_separate_and_unverified_by_default(tmp_path):
    db = Database(str(tmp_path / "affiliate.db"))
    await db.connect()
    try:
        event_id = await db.record_affiliate_event(
            platform="okx",
            event_type="REFERRAL_REWARD",
            event_time=datetime.now(timezone.utc),
            referral_code="79650738",
            reward_amount=2.5,
            currency="USDT",
        )
        assert event_id > 0
        summary = await db.get_affiliate_summary()
        assert summary["status"] == "UNVERIFIED"
        assert summary["okx"]["events"] == 1
        assert summary["okx"]["verified_rewards"] == 0.0

        await db.record_affiliate_event(
            platform="okx",
            event_type="REFERRAL_REWARD",
            event_time=datetime.now(timezone.utc),
            referral_code="79650738",
            reward_amount=2.5,
            currency="USDT",
            status="VERIFIED",
            external_ref="okx-event-1",
        )
        summary = await db.get_affiliate_summary()
        assert summary["status"] == "RECENT_RECORD"
        assert summary["verified_total"] == 2.5
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_affiliate_ledger_rejects_unknown_platform(tmp_path):
    db = Database(str(tmp_path / "affiliate-invalid.db"))
    await db.connect()
    try:
        with pytest.raises(ValueError):
            await db.record_affiliate_event(
                platform="unknown",
                event_type="REWARD",
                event_time=datetime.now(timezone.utc),
            )
    finally:
        await db.close()
