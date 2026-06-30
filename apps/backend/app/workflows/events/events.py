from pydantic import BaseModel
from typing import Any, Dict, Optional
from datetime import datetime


class EventType(str):
    pass


class WorkflowEvent(BaseModel):
    event_id: str
    event_type: str
    workflow_id: str
    task_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    payload: Dict[str, Any] = {}

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


# Common Event Types
WORKFLOW_CREATED = "WorkflowCreated"
WORKFLOW_STARTED = "WorkflowStarted"
WORKFLOW_COMPLETED = "WorkflowCompleted"
WORKFLOW_FAILED = "WorkflowFailed"
WORKFLOW_PAUSED = "WorkflowPaused"
WORKFLOW_RESUMED = "WorkflowResumed"
WORKFLOW_CANCELLED = "WorkflowCancelled"

TASK_STARTED = "TaskStarted"
TASK_COMPLETED = "TaskCompleted"
TASK_FAILED = "TaskFailed"
TASK_RETRIED = "TaskRetried"
TASK_SKIPPED = "TaskSkipped"

APPROVAL_REQUESTED = "ApprovalRequested"
APPROVAL_GRANTED = "ApprovalGranted"
APPROVAL_REJECTED = "ApprovalRejected"
