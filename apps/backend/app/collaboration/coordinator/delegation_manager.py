from typing import Dict, List, Optional
from pydantic import BaseModel
import uuid
import datetime
import enum

class TaskStatus(str, enum.Enum):
    PENDING = "Pending"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    ESCALATED = "Escalated"

class DelegatedTask(BaseModel):
    task_id: str
    description: str
    assignee: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: str
    completed_at: Optional[str] = None

class DelegationManager:
    def __init__(self):
        self.tasks: Dict[str, DelegatedTask] = {}

    def delegate_task(self, description: str, assignee: Optional[str] = None) -> DelegatedTask:
        tid = str(uuid.uuid4())
        task = DelegatedTask(
            task_id=tid,
            description=description,
            assignee=assignee,
            status=TaskStatus.ASSIGNED if assignee else TaskStatus.PENDING,
            created_at=datetime.datetime.utcnow().isoformat()
        )
        self.tasks[tid] = task
        return task

    def reassign_task(self, task_id: str, new_assignee: str) -> DelegatedTask:
        if task_id not in self.tasks:
            raise ValueError("Task not found")
        task = self.tasks[task_id]
        task.assignee = new_assignee
        task.status = TaskStatus.ASSIGNED
        return task

    def escalate_task(self, task_id: str) -> DelegatedTask:
        if task_id not in self.tasks:
            raise ValueError("Task not found")
        task = self.tasks[task_id]
        task.status = TaskStatus.ESCALATED
        return task

    def complete_task(self, task_id: str) -> DelegatedTask:
        if task_id not in self.tasks:
            raise ValueError("Task not found")
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.datetime.utcnow().isoformat()
        return task
