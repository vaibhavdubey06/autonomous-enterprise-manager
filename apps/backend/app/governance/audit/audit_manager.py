import datetime
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class AuditRecord(BaseModel):
    audit_id: str
    workflow_id: str
    timestamp: datetime.datetime
    event_type: str
    details: Dict[str, Any]
    previous_audit_id: Optional[str] = None


class AuditManager:
    def __init__(self):
        self.records: List[AuditRecord] = []
        self._last_audit_id = None

    def log_event(
        self, workflow_id: str, event_type: str, details: Dict[str, Any]
    ) -> AuditRecord:
        record = AuditRecord(
            audit_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            timestamp=datetime.datetime.utcnow(),
            event_type=event_type,
            details=details,
            previous_audit_id=self._last_audit_id,
        )
        self.records.append(record)
        self._last_audit_id = record.audit_id
        return record

    def get_audit_chain(self, workflow_id: str) -> List[AuditRecord]:
        return [r for r in self.records if r.workflow_id == workflow_id]
