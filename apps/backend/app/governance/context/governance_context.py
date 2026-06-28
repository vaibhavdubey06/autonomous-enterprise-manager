from pydantic import BaseModel
from typing import Any, Dict, Optional
from app.workflows.models.workflow import Workflow
from app.workflows.models.task import Task
from app.collaboration.session.collaboration_session import CollaborationSession

class GovernanceContext(BaseModel):
    workflow_id: str
    task_id: Optional[str] = None
    capability_name: Optional[str] = None
    
    # Metadata extracted from runtime objects
    workflow_goal: str
    task_description: Optional[str] = None
    
    user_id: Optional[str] = None
    executive_agent: Optional[str] = None
    collaboration_session_id: Optional[str] = None
    
    memory_context: Dict[str, Any] = {}
    risk_context: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    audit_context: Dict[str, Any] = {}

    @classmethod
    def from_workflow_task(cls, workflow: Workflow, task: Task) -> "GovernanceContext":
        return cls(
            workflow_id=workflow.workflow_id,
            task_id=task.task_id,
            capability_name=task.required_capability,
            workflow_goal=workflow.goal,
            task_description=task.description,
            user_id=workflow.initiated_by,
            executive_agent=task.assigned_agent,
        )
