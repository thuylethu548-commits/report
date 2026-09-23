import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone
from core.event_bus import EventBus
from core.events import FillEvent, SignalEvent, TrailingStopEvent, AIAdvisoryEvent
from core.constants import OrderSide, MarketRegime
from config.settings import settings
from monitoring.telegram_bot import TelegramNotifier


@pytest.mark.asyncio
async def test_telegram_notifier_dispatch():
    event_bus = EventBus()
    event_bus.start()

    orig_enable = settings.ENABLE_TELEGRAM
    orig_token = settings.TELEGRAM_BOT_TOKEN
    orig_chat = settings.TELEGRAM_CHAT_ID

    settings.ENABLE_TELEGRAM = True
    settings.TELEGRAM_BOT_TOKEN = "test_bot_token"
    settings.TELEGRAM_CHAT_ID = "test_chat_id"

    try:
        notifier = TelegramNotifier(event_bus)

        with patch.object(notifier, "send_message", new_callable=AsyncMock) as mock_send:
            # 1. Test Signal Alert
            sig = SignalEvent(
                strategy_name="EMA_Trend",
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                price=50000.0,
                timestamp=datetime.now(timezone.utc),
                stop_loss=49000.0,
                take_profit=52000.0
            )
            await event_bus.publish(sig)
            await asyncio.sleep(0.05)
            assert mock_send.call_count >= 1
            assert "TÍN HIỆU CHIẾN LƯỢC" in mock_send.call_args_list[0][0][0]

            # 2. Test Trailing Stop Alert (Break Even)
            ts_be = TrailingStopEvent(
                order_id="ord_1",
                symbol="BTC/USDT",
                action="BREAK_EVEN_LOCK",
                old_sl=49000.0,
                new_sl=50100.0,
                current_price=50700.0,
                pnl_pct=1.4,
                reason="Lãi đạt +1.4%",
                timestamp=datetime.now(timezone.utc)
            )
            await event_bus.publish(ts_be)
            await asyncio.sleep(0.05)
            assert any("BREAK-EVEN LOCK" in c[0][0] for c in mock_send.call_args_list)

            # 3. Test AI Advisory Veto Alert
            ai_veto = AIAdvisoryEvent(
                symbol="BTC/USDT",
                timestamp=datetime.now(timezone.utc),
                regime=MarketRegime.BEAR_TREND,
                risk_score=5,
                trade_allowed=False,
                size_multiplier=0.0,
                reasoning="Macro breakdown imminent",
                confidence=0.92
            )
            await event_bus.publish(ai_veto)
            await asyncio.sleep(0.05)
            assert any("AI VETO" in c[0][0] for c in mock_send.call_args_list)
    finally:
        settings.ENABLE_TELEGRAM = orig_enable
        settings.TELEGRAM_BOT_TOKEN = orig_token
        settings.TELEGRAM_CHAT_ID = orig_chat
        await event_bus.stop()
