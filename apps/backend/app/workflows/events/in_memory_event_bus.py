import asyncio
import logging
from collections import defaultdict
from typing import Callable, Any, List
from app.workflows.events.base_event_bus import BaseEventBus
from app.workflows.events.events import WorkflowEvent

logger = logging.getLogger(__name__)

class InMemoryEventBus(BaseEventBus):
    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[WorkflowEvent], Any]) -> None:
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to event type: {event_type}")

    def publish(self, event: WorkflowEvent) -> None:
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                # Dispatch event async if possible, otherwise sync
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event.event_type}: {e}", exc_info=True)
