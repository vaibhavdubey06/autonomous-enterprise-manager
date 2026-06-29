from abc import ABC, abstractmethod
from typing import List
from app.operations.telemetry.telemetry_models import TelemetryEvent


class BaseExporter(ABC):
    @abstractmethod
    def export(self, events: List[TelemetryEvent]) -> None:
        pass
