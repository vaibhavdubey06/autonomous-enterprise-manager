from pydantic import BaseModel
from typing import Dict, List, Optional
import uuid
import datetime

class ApprovalRequest(BaseModel):
    request_id: str
    workflow_id: str
    task_id: Optional[str] = None
    reason: str
    required_role: str = "Administrator"
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, EXPIRED
    created_at: datetime.datetime
    resolved_at: Optional[datetime.datetime] = None
    resolved_by: Optional[str] = None

class ApprovalRuntime:
    def __init__(self):
        self.requests: Dict[str, ApprovalRequest] = {}

    def request_approval(self, workflow_id: str, reason: str, task_id: Optional[str] = None, role: str = "Administrator") -> ApprovalRequest:
        req = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            task_id=task_id,
            reason=reason,
            required_role=role,
            created_at=datetime.datetime.utcnow()
        )
        self.requests[req.request_id] = req
        return req

    def get_pending_requests(self) -> List[ApprovalRequest]:
        return [r for r in self.requests.values() if r.status == "PENDING"]

    def resolve_request(self, request_id: str, approved: bool, resolved_by: str) -> Optional[ApprovalRequest]:
        req = self.requests.get(request_id)
        if not req or req.status != "PENDING":
            return None
            
        req.status = "APPROVED" if approved else "REJECTED"
        req.resolved_by = resolved_by
        req.resolved_at = datetime.datetime.utcnow()
        return req
