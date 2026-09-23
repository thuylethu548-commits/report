import logging
from typing import Dict, Optional
from core.events import OrderEvent, FillEvent
from core.event_bus import EventBus
from core.constants import OrderStatus

logger = logging.getLogger("OMS")


class OrderManagementSystem:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.orders: Dict[str, OrderEvent] = {}

        self.event_bus.subscribe(OrderEvent, self.on_order)
        self.event_bus.subscribe(FillEvent, self.on_fill)

    async def on_order(self, order: OrderEvent) -> None:
        self.orders[order.order_id] = order
        logger.debug(f"[OMS] Tracking Order {order.order_id} ({order.status.value})")

    async def on_fill(self, fill: FillEvent) -> None:
        if fill.order_id in self.orders:
            self.orders[fill.order_id].status = OrderStatus.FILLED
            logger.debug(f"[OMS] Order {fill.order_id} marked as FILLED")
