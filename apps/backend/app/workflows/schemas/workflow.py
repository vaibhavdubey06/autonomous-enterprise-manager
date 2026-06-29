from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.workflows.models.workflow import WorkflowStatus
from app.workflows.models.task import TaskStatus, TaskType


class TaskSchema(BaseModel):
    task_id: str
    workflow_id: str
    task_type: TaskType = TaskType.CAPABILITY
    name: Optional[str] = None
    description: Optional[str] = None
    assigned_agent: Optional[str] = None
    required_capability: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    timeout: Optional[int] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None

    class Config:
        from_attributes = True


class WorkflowSchema(BaseModel):
    workflow_id: str
    workflow_version: int = 1
    template_name: Optional[str] = None
    template_version: Optional[int] = None
    goal: str
    description: Optional[str] = None
    owner_agent: Optional[str] = None
    initiated_by: Optional[str] = None
    priority: int = 0
    status: WorkflowStatus = WorkflowStatus.DRAFT
    approval_required: bool = False
    workflow_metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_metrics: Dict[str, Any] = Field(default_factory=dict)
    audit_log: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    tasks: List[TaskSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True


class WorkflowCreate(BaseModel):
    goal: str
    description: Optional[str] = None
    owner_agent: Optional[str] = None
    initiated_by: Optional[str] = None
    template_name: Optional[str] = None
    approval_required: bool = False
    priority: int = 0
