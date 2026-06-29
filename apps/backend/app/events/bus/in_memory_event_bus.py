"""In-memory event bus implementation for local development and testing."""

import logging
from typing import Callable, Dict, List, Optional

from app.events.base.interfaces import DomainEvent, EventBus

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    """Thread-safe in-memory event bus with history support."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[DomainEvent], None]]] = {}
        self._history: List[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self._history.append(event)
        handlers = self._subscribers.get(event.event_type, [])
        wildcard_handlers = self._subscribers.get("*", [])
        for handler in handlers + wildcard_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Event handler failed for {event.event_type}: {e}",
                    exc_info=True,
                )

    def subscribe(
        self, event_type: str, handler: Callable[[DomainEvent], None]
    ) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(
        self, event_type: str, handler: Callable[[DomainEvent], None]
    ) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h is not handler
            ]

    def get_history(
        self, event_type: Optional[str] = None, limit: int = 100
    ) -> List[DomainEvent]:
        if event_type:
            filtered = [e for e in self._history if e.event_type == event_type]
        else:
            filtered = self._history
        return filtered[-limit:]
