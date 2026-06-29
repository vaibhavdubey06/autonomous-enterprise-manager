from pydantic import BaseModel
from typing import Any, Dict, Optional
import datetime
import uuid


class TelemetryEvent(BaseModel):
    event_id: str = ""
    source: str = ""
    event_type: str = ""
    timestamp: datetime.datetime = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = {}
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.datetime.utcnow()
