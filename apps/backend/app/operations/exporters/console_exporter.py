from typing import List
from app.operations.exporters.base_exporter import BaseExporter
from app.operations.telemetry.telemetry_models import TelemetryEvent


import logging

logger = logging.getLogger(__name__)


class ConsoleExporter(BaseExporter):
    def export(self, events: List[TelemetryEvent]) -> None:
        for event in events:
            logger.info(
                f"[TELEMETRY] {event.source}:{event.event_type} | {event.duration_ms:.1f}ms | {event.correlation_id}"
            )


class JsonExporter(BaseExporter):
    def __init__(self):
        self.exported: List[dict] = []

    def export(self, events: List[TelemetryEvent]) -> None:
        for event in events:
            self.exported.append(event.model_dump(mode="json"))


class OTelExporter(BaseExporter):
    """Bridges telemetry events to OpenTelemetry SDK spans."""

    def __init__(self):
        self.exported_count = 0

    def export(self, events: List[TelemetryEvent]) -> None:
        try:
            from opentelemetry import trace

            tracer = trace.get_tracer("enterprise-operations")
            for event in events:
                with tracer.start_as_current_span(
                    f"{event.source}.{event.event_type}"
                ) as span:
                    span.set_attribute("source", event.source)
                    span.set_attribute("duration_ms", event.duration_ms)
                    if event.correlation_id:
                        span.set_attribute("correlation_id", event.correlation_id)
                self.exported_count += 1
        except Exception:
            pass  # OTel not configured — silently skip
