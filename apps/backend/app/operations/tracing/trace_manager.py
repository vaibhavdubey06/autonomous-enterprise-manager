import uuid
from typing import Dict, List, Optional
from contextlib import contextmanager
from app.operations.tracing.span import Span
from app.operations.telemetry.telemetry_context import TelemetryContext


class TraceManager:
    """Creates and manages distributed traces (trees of Spans)."""

    def __init__(self):
        self._traces: Dict[str, List[Span]] = {}

    def start_trace(self, operation: str, **attributes) -> Span:
        trace_id = str(uuid.uuid4())[:12]
        span = Span(trace_id=trace_id, operation=operation, attributes=attributes)
        self._traces[trace_id] = [span]
        TelemetryContext.new_context(trace_id=trace_id, span_id=span.span_id)
        return span

    def start_span(
        self,
        trace_id: str,
        operation: str,
        parent_span_id: Optional[str] = None,
        **attributes,
    ) -> Span:
        span = Span(
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation=operation,
            attributes=attributes,
        )
        if trace_id not in self._traces:
            self._traces[trace_id] = []
        self._traces[trace_id].append(span)
        TelemetryContext.new_context(span_id=span.span_id)
        return span

    def end_span(self, span: Span, status: str = "OK"):
        span.finish(status)

    @contextmanager
    def trace(self, operation: str, **attributes):
        root = self.start_trace(operation, **attributes)
        try:
            yield root
            self.end_span(root, "OK")
        except Exception:
            self.end_span(root, "ERROR")
            raise

    @contextmanager
    def span(
        self,
        trace_id: str,
        operation: str,
        parent_span_id: Optional[str] = None,
        **attributes,
    ):
        s = self.start_span(trace_id, operation, parent_span_id, **attributes)
        try:
            yield s
            self.end_span(s, "OK")
        except Exception:
            self.end_span(s, "ERROR")
            raise

    def get_trace(self, trace_id: str) -> List[Span]:
        return self._traces.get(trace_id, [])

    def get_all_traces(self) -> Dict[str, List[dict]]:
        return {
            tid: [s.to_dict() for s in spans] for tid, spans in self._traces.items()
        }
