import logging
from typing import Optional
from app.operations.telemetry.telemetry_pipeline import TelemetryPipeline
from app.operations.telemetry.telemetry_models import TelemetryEvent

logger = logging.getLogger(__name__)


class TelemetryManager:
    """Central telemetry sink. All subsystems emit events here."""

    def __init__(self, pipeline: Optional[TelemetryPipeline] = None):
        self.pipeline = pipeline or TelemetryPipeline()

    def emit(
        self, source: str, event_type: str, duration_ms: float = 0.0, **metadata
    ) -> Optional[TelemetryEvent]:
        event = TelemetryEvent(
            source=source,
            event_type=event_type,
            duration_ms=duration_ms,
            metadata=metadata,
        )
        processed = self.pipeline.process(event)
        if processed:
            logger.debug(f"[Telemetry] {source}:{event_type} ({duration_ms:.1f}ms)")
        return processed

    def get_events(self, **kwargs):
        return self.pipeline.get_events(**kwargs)
