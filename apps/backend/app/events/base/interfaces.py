"""Enterprise Event Platform - Base interfaces."""

import uuid
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class DomainEvent:
    """Base class for all domain events in the platform."""

    def __init__(
        self,
        event_type: str,
        payload: Dict[str, Any],
        source: str,
        correlation_id: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        version: int = 1,
    ):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.payload = payload
        self.source = source
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.priority = priority
        self.version = version
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "priority": self.priority.value,
            "version": self.version,
            "timestamp": self.timestamp,
        }


class EventBus(ABC):
    """Abstract interface for the enterprise event bus."""

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all subscribers."""
        ...

    @abstractmethod
    def subscribe(
        self, event_type: str, handler: Callable[[DomainEvent], None]
    ) -> None:
        """Subscribe a handler to a specific event type."""
        ...

    @abstractmethod
    def unsubscribe(
        self, event_type: str, handler: Callable[[DomainEvent], None]
    ) -> None:
        """Unsubscribe a handler from a specific event type."""
        ...

    @abstractmethod
    def get_history(
        self, event_type: Optional[str] = None, limit: int = 100
    ) -> List[DomainEvent]:
        """Retrieve event history for replay or auditing."""
        ...


class EventRepository(ABC):
    """Abstract persistence layer for events."""

    @abstractmethod
    def save(self, event: DomainEvent) -> None: ...

    @abstractmethod
    def find_by_type(
        self, event_type: str, limit: int = 100
    ) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def find_by_correlation_id(self, correlation_id: str) -> List[Dict[str, Any]]: ...
