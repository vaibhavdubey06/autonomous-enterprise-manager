from abc import ABC, abstractmethod
from typing import Callable, Any
from app.workflows.events.events import WorkflowEvent


class BaseEventBus(ABC):
    @abstractmethod
    def publish(self, event: WorkflowEvent) -> None:
        """Publish an event to the bus."""
        pass

    @abstractmethod
    def subscribe(
        self, event_type: str, handler: Callable[[WorkflowEvent], Any]
    ) -> None:
        """Subscribe to a specific event type."""
        pass
