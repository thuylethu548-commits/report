import asyncio
import logging
from collections import defaultdict
from typing import Callable, Coroutine, Dict, List, Type, Any

logger = logging.getLogger("EventBus")


class EventBus:
    def __init__(self):
        self._subscribers: Dict[Type[Any], List[Callable[[Any], Coroutine[Any, Any, None]]]] = defaultdict(list)
        self._queue: asyncio.Queue = asyncio.Queue()
        self._signal_queue: asyncio.Queue = asyncio.Queue(maxsize=128)
        self._signal_worker_task = None
        self._running: bool = False
        self._worker_task: asyncio.Task | None = None

    def subscribe(self, event_type: Type[Any], handler: Callable[[Any], Coroutine[Any, Any, None]]) -> None:
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler {handler.__name__} to {event_type.__name__}")

    async def publish(self, event: Any) -> None:
        from core.events import SignalEvent
        if isinstance(event, SignalEvent):
            try:
                self._signal_queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Signal queue full: stale opportunity dropped; safety queue remains available")
            return
        await self._queue.put(event)

    async def _worker(self, queue=None) -> None:
        queue = self._queue if queue is None else queue
        while self._running:
            try:
                event = await queue.get()
                event_type = type(event)
                handlers = self._subscribers.get(event_type, [])
                for handler in handlers:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Error executing handler {handler.__name__} for {event_type.__name__}: {e}", exc_info=True)
                queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in EventBus worker: {e}", exc_info=True)

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
            self._signal_worker_task = asyncio.create_task(self._worker(self._signal_queue))
            logger.info("EventBus started.")

    async def join(self) -> None:
        """Drain signal work and the execution events it emits."""
        while True:
            await self._signal_queue.join()
            await self._queue.join()
            if self._signal_queue.empty() and self._queue.empty():
                return

    async def stop(self) -> None:
        self._running = False
        if self._signal_worker_task:
            self._signal_worker_task.cancel()
            await asyncio.gather(self._signal_worker_task, return_exceptions=True)
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("EventBus stopped.")
