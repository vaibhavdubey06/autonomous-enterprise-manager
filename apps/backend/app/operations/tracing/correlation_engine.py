import uuid
from typing import Optional
from app.operations.telemetry.telemetry_context import TelemetryContext


class CorrelationEngine:
    """
    Assigns and propagates a single correlation_id across the entire execution chain:
    User → Supervisor → Agent → Workflow → Governance → Capability → Response.
    """

    def __init__(self):
        self._correlations = {}

    def start_correlation(self, source: str = "user") -> str:
        cid = str(uuid.uuid4())[:12]
        self._correlations[cid] = {"source": source, "chain": [source]}
        TelemetryContext.new_context(correlation_id=cid)
        return cid

    def extend_correlation(self, correlation_id: str, component: str):
        if correlation_id in self._correlations:
            self._correlations[correlation_id]["chain"].append(component)

    def get_chain(self, correlation_id: str) -> list:
        entry = self._correlations.get(correlation_id)
        return entry["chain"] if entry else []

    def get_current_correlation_id(self) -> Optional[str]:
        return TelemetryContext._correlation_id.get()
