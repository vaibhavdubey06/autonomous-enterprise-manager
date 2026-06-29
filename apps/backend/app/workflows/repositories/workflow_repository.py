from sqlalchemy.orm import Session
from typing import List, Optional
from app.workflows.models.workflow import Workflow, WorkflowStatus
from app.workflows.models.task import Task, TaskStatus


class WorkflowRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_workflow(self, workflow_data: dict) -> Workflow:
        workflow = Workflow(**workflow_data)
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return (
            self.db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        )

    def list_workflows(self, skip: int = 0, limit: int = 100) -> List[Workflow]:
        return (
            self.db.query(Workflow)
            .order_by(Workflow.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_workflow_status(
        self, workflow_id: str, status: WorkflowStatus
    ) -> Optional[Workflow]:
        workflow = self.get_workflow(workflow_id)
        if workflow:
            workflow.status = status
            self.db.commit()
            self.db.refresh(workflow)
        return workflow

    def create_task(self, task_data: dict) -> Task:
        task = Task(**task_data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.db.query(Task).filter(Task.task_id == task_id).first()

    def update_task_status(
        self, task_id: str, status: TaskStatus, error: str = None
    ) -> Optional[Task]:
        task = self.get_task(task_id)
        if task:
            task.status = status
            if error is not None:
                task.error = error
            self.db.commit()
            self.db.refresh(task)
        return task

    def update_task(self, task_id: str, update_data: dict) -> Optional[Task]:
        task = self.get_task(task_id)
        if task:
            for key, value in update_data.items():
                setattr(task, key, value)
            self.db.commit()
            self.db.refresh(task)
        return task
