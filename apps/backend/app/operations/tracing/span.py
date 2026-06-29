from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import time
import datetime


class Span(BaseModel):
    trace_id: str
    span_id: str = ""
    parent_span_id: Optional[str] = None
    operation: str = ""
    start_time: float = 0.0
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: str = "OK"
    attributes: Dict[str, Any] = {}

    def __init__(self, **data):
        super().__init__(**data)
        if not self.span_id:
            self.span_id = str(uuid.uuid4())[:8]
        if not self.start_time:
            self.start_time = time.time()

    def finish(self, status: str = "OK"):
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation": self.operation,
            "start_time": (
                datetime.datetime.fromtimestamp(self.start_time).isoformat()
                if self.start_time
                else None
            ),
            "end_time": (
                datetime.datetime.fromtimestamp(self.end_time).isoformat()
                if self.end_time
                else None
            ),
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "attributes": self.attributes,
        }
