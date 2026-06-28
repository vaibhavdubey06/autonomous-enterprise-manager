from typing import List, Optional
from sqlalchemy.orm import Session
from app.workflows.models.workflow import Workflow, WorkflowStatus
from app.workflows.schemas.workflow import WorkflowCreate, WorkflowSchema
from app.workflows.builder.workflow_builder import WorkflowBuilder
from app.workflows.engine.workflow_engine import WorkflowEngine
from app.workflows.repositories.workflow_repository import WorkflowRepository

class WorkflowService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = WorkflowRepository(db)
        self.engine = WorkflowEngine(db)

    def create_workflow_from_builder(self, builder: WorkflowBuilder) -> WorkflowSchema:
        workflow_schema = builder.build()
        
        # Persist
        workflow_data = workflow_schema.model_dump(exclude={"tasks"})
        workflow = self.repository.create_workflow(workflow_data)
        
        for task_schema in workflow_schema.tasks:
            task_data = task_schema.model_dump()
            self.repository.create_task(task_data)
            
        return workflow_schema

    async def execute_workflow(self, workflow_id: str) -> None:
        await self.engine.start_workflow(workflow_id)
        
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self.repository.get_workflow(workflow_id)
        
    def list_workflows(self, skip: int = 0, limit: int = 100) -> List[Workflow]:
        return self.repository.list_workflows(skip=skip, limit=limit)
        
    def pause_workflow(self, workflow_id: str) -> None:
        self.engine.pause_workflow(workflow_id)
        
    def cancel_workflow(self, workflow_id: str) -> None:
        self.engine.cancel_workflow(workflow_id)
