from app.workflows.models.task import TaskStatus

class TaskStateMachine:
    VALID_TRANSITIONS = {
        TaskStatus.PENDING: [TaskStatus.QUEUED, TaskStatus.SKIPPED, TaskStatus.CANCELLED],
        TaskStatus.QUEUED: [TaskStatus.RUNNING, TaskStatus.CANCELLED],
        TaskStatus.RUNNING: [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED],
        TaskStatus.RETRYING: [TaskStatus.QUEUED, TaskStatus.CANCELLED],
        TaskStatus.COMPLETED: [],
        TaskStatus.FAILED: [TaskStatus.RETRYING, TaskStatus.CANCELLED],
        TaskStatus.SKIPPED: [],
        TaskStatus.CANCELLED: []
    }

    @classmethod
    def can_transition(cls, current_status: TaskStatus, new_status: TaskStatus) -> bool:
        allowed = cls.VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed
