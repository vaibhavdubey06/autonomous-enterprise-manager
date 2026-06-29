from app.workflows.models.workflow import WorkflowStatus


class WorkflowStateMachine:
    VALID_TRANSITIONS = {
        WorkflowStatus.DRAFT: [WorkflowStatus.PLANNED, WorkflowStatus.CANCELLED],
        WorkflowStatus.PLANNED: [WorkflowStatus.READY, WorkflowStatus.CANCELLED],
        WorkflowStatus.READY: [WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED],
        WorkflowStatus.RUNNING: [
            WorkflowStatus.WAITING_FOR_APPROVAL,
            WorkflowStatus.PAUSED,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        ],
        WorkflowStatus.WAITING_FOR_APPROVAL: [
            WorkflowStatus.RUNNING,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        ],
        WorkflowStatus.PAUSED: [WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED],
        WorkflowStatus.RETRYING: [
            WorkflowStatus.RUNNING,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        ],
        WorkflowStatus.COMPLETED: [],
        WorkflowStatus.CANCELLED: [],
        WorkflowStatus.FAILED: [WorkflowStatus.RETRYING, WorkflowStatus.CANCELLED],
    }

    @classmethod
    def can_transition(
        cls, current_status: WorkflowStatus, new_status: WorkflowStatus
    ) -> bool:
        allowed = cls.VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed
