import datetime
import json
import logging
from typing import List, Dict, Any, Optional
from app.operations.telemetry.telemetry_context import TelemetryContext

logger = logging.getLogger(__name__)


class StructuredLogger:
    """Emits structured JSON log entries with automatic TelemetryContext attachment."""

    def __init__(self):
        self._logs: List[Dict[str, Any]] = []

    def log(self, component: str, message: str, severity: str = "INFO", **metadata):
        ctx = TelemetryContext.get_snapshot()
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "component": component,
            "severity": severity,
            "message": message,
            "trace_id": ctx.get("trace_id"),
            "workflow_id": ctx.get("workflow_id"),
            "agent": ctx.get("executive_agent"),
            "correlation_id": ctx.get("correlation_id"),
            "metadata": metadata,
        }
        self._logs.append(entry)
        logger.log(
            getattr(logging, severity, logging.INFO), json.dumps(entry, default=str)
        )

    def info(self, component: str, message: str, **metadata):
        self.log(component, message, "INFO", **metadata)

    def warning(self, component: str, message: str, **metadata):
        self.log(component, message, "WARNING", **metadata)

    def error(self, component: str, message: str, **metadata):
        self.log(component, message, "ERROR", **metadata)

    def get_logs(
        self,
        component: Optional[str] = None,
        severity: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = self._logs
        if component:
            results = [l for l in results if l["component"] == component]
        if severity:
            results = [l for l in results if l["severity"] == severity]
        if trace_id:
            results = [l for l in results if l["trace_id"] == trace_id]
        return results


class LogRepository:
    """In-memory log store. Wraps StructuredLogger for query access."""

    def __init__(self, structured_logger: StructuredLogger):
        self.logger = structured_logger

    def search(self, **kwargs) -> List[Dict[str, Any]]:
        return self.logger.get_logs(**kwargs)
