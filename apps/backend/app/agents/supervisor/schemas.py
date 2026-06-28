from enum import Enum
from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel, Field
import uuid
import datetime

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    description: str
    priority: int = 1
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

class ExecutionPlan(BaseModel):
    goal: str
    tasks: List[Task]

class SupervisorState(TypedDict):
    """LangGraph state for the Supervisor Agent"""
    # Core inputs
    user_input: str
    session_id: Optional[str]
    conversation_id: Optional[str]
    
    # State tracking
    goal: str
    execution_plan: Optional[ExecutionPlan]
    
    # Execution state
    selected_agents: List[str]
    completed_tasks: List[str]
    failed_tasks: List[str]
    task_results: List[Dict[str, Any]]
    
    # Final output
    final_response: str
    
    # Metrics
    execution_time_ms: float
    use_collaboration: bool
