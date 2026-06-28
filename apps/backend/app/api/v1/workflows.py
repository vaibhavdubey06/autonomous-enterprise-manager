from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.workflows.schemas.workflow import WorkflowCreate, WorkflowSchema
from app.workflows.services.workflow_service import WorkflowService
from app.workflows.builder.workflow_builder import WorkflowBuilder

router = APIRouter()

@router.post("/", response_model=WorkflowSchema)
def create_workflow(workflow_in: WorkflowCreate, db: Session = Depends(get_db)):
    service = WorkflowService(db)
    builder = WorkflowBuilder(workflow_in)
    return service.create_workflow_from_builder(builder)

@router.get("/", response_model=List[WorkflowSchema])
def list_workflows(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = WorkflowService(db)
    workflows = service.list_workflows(skip=skip, limit=limit)
    # Convert SQLAlchemy models to schemas manually or rely on from_attributes
    return workflows

@router.get("/{workflow_id}", response_model=WorkflowSchema)
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    service = WorkflowService(db)
    workflow = service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, db: Session = Depends(get_db)):
    service = WorkflowService(db)
    workflow = service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    await service.execute_workflow(workflow_id)
    return {"status": "Execution started"}

@router.post("/{workflow_id}/pause")
def pause_workflow(workflow_id: str, db: Session = Depends(get_db)):
    service = WorkflowService(db)
    service.pause_workflow(workflow_id)
    return {"status": "Paused"}

@router.post("/{workflow_id}/cancel")
def cancel_workflow(workflow_id: str, db: Session = Depends(get_db)):
    service = WorkflowService(db)
    service.cancel_workflow(workflow_id)
    return {"status": "Cancelled"}
