import logging
from typing import List, Callable, Optional
from app.operations.telemetry.telemetry_models import TelemetryEvent
from app.operations.telemetry.telemetry_context import TelemetryContext

logger = logging.getLogger(__name__)


class TelemetryPipeline:
    """
    Processes telemetry events through a configurable pipeline:
    Enrichment → Correlation → Sampling → Filtering → Aggregation → Persistence → Export.
    Each stage is a callable that receives and returns a TelemetryEvent (or None to drop).
    """

    def __init__(self):
        self._enrichers: List[Callable] = []
        self._filters: List[Callable] = []
        self._exporters: List[Callable] = []
        self._events: List[TelemetryEvent] = []

    def add_enricher(self, fn: Callable[[TelemetryEvent], TelemetryEvent]):
        self._enrichers.append(fn)

    def add_filter(self, fn: Callable[[TelemetryEvent], bool]):
        self._filters.append(fn)

    def add_exporter(self, fn: Callable[[TelemetryEvent], None]):
        self._exporters.append(fn)

    def _enrich(self, event: TelemetryEvent) -> TelemetryEvent:
        """Attach current TelemetryContext to the event."""
        ctx = TelemetryContext.get_snapshot()
        if not event.trace_id:
            event.trace_id = ctx.get("trace_id")
        if not event.correlation_id:
            event.correlation_id = ctx.get("correlation_id")
        for enricher in self._enrichers:
            event = enricher(event)
        return event

    def _should_keep(self, event: TelemetryEvent) -> bool:
        for f in self._filters:
            if not f(event):
                return False
        return True

    def process(self, event: TelemetryEvent) -> Optional[TelemetryEvent]:
        event = self._enrich(event)
        if not self._should_keep(event):
            return None
        self._events.append(event)
        for exporter in self._exporters:
            try:
                exporter(event)
            except Exception as e:
                logger.error(f"Exporter failed: {e}")
        return event

    def get_events(
        self, source: Optional[str] = None, event_type: Optional[str] = None
    ) -> List[TelemetryEvent]:
        results = self._events
        if source:
            results = [e for e in results if e.source == source]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        return results
