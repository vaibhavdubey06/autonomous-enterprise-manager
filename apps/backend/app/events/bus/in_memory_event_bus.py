"""In-memory event bus implementation for local development and testing."""

import logging
import threading
import queue
from typing import Callable, Dict, List, Optional
from app.events.base.interfaces import DomainEvent, EventBus

logger = logging.getLogger(__name__)

class PriorityEventWrapper:
    """Wrapper to make DomainEvents comparable by priority for the PriorityQueue."""
    def __init__(self, event: DomainEvent):
        self.event = event
        
        # Lower number = higher priority. Enum: CRITICAL, HIGH, NORMAL, LOW
        priority_map = {
            "critical": 0,
            "high": 1,
            "normal": 2,
            "low": 3
        }
        self.priority = priority_map.get(event.priority.value, 2)
        
    def __lt__(self, other):
        # If priorities are equal, older timestamp wins
        if self.priority == other.priority:
            return self.event.timestamp < other.event.timestamp
        return self.priority < other.priority

class InMemoryEventBus(EventBus):
    """Thread-safe in-memory event bus with priority background queue support."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[DomainEvent], None]]] = {}
        self._history: List[DomainEvent] = []
        self._queue = queue.PriorityQueue()
        self._stop_event = threading.Event()
        
        # Start background worker
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                # Wait for an event with timeout to allow checking stop_event
                wrapper = self._queue.get(timeout=1.0)
                event = wrapper.event
                self._dispatch(event)
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in EventBus background worker: {e}", exc_info=True)

    def _dispatch(self, event: DomainEvent):
        handlers = self._subscribers.get(event.event_type, [])
        wildcard_handlers = self._subscribers.get("*", [])
        for handler in handlers + wildcard_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler failed for {event.event_type}: {e}", exc_info=True)

    def publish(self, event: DomainEvent) -> None:
        self._history.append(event)
        self._queue.put(PriorityEventWrapper(event))

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h is not handler
            ]

    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[DomainEvent]:
        if event_type:
            filtered = [e for e in self._history if e.event_type == event_type]
        else:
            filtered = self._history
        return filtered[-limit:]
        
    def stop(self):
        """Stop the background worker."""
        self._stop_event.set()
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

