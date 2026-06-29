from app.workflows.events.base_event_bus import BaseEventBus
from app.workflows.events.events import (
    WorkflowEvent,
    APPROVAL_REQUESTED,
    APPROVAL_GRANTED,
    APPROVAL_REJECTED,
)


class ApprovalManager:
    def __init__(self, event_bus: BaseEventBus):
        self.event_bus = event_bus

    def request_approval(self, workflow_id: str) -> None:
        self.event_bus.publish(
            WorkflowEvent(
                event_id=f"evt_{workflow_id}_approval_req",
                event_type=APPROVAL_REQUESTED,
                workflow_id=workflow_id,
                payload={"message": "Workflow execution paused, waiting for approval."},
            )
        )

    def grant_approval(self, workflow_id: str, approver: str) -> None:
        self.event_bus.publish(
            WorkflowEvent(
                event_id=f"evt_{workflow_id}_approval_granted",
                event_type=APPROVAL_GRANTED,
                workflow_id=workflow_id,
                payload={"approver": approver},
            )
        )

    def reject_approval(self, workflow_id: str, approver: str, reason: str) -> None:
        self.event_bus.publish(
            WorkflowEvent(
                event_id=f"evt_{workflow_id}_approval_rejected",
                event_type=APPROVAL_REJECTED,
                workflow_id=workflow_id,
                payload={"approver": approver, "reason": reason},
            )
        )
