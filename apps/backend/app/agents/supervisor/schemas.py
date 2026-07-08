from enum import Enum
from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel, Field
import uuid
import datetime


class ExecutionPolicy(str, Enum):
    CONTINUE = "CONTINUE"
    RETRY = "RETRY"
    ABORT = "ABORT"
    ESCALATE = "ESCALATE"
    IGNORE = "IGNORE"
    # New Adaptive Workflow Policies
    REPLAN = "REPLAN"
    CHANGE_AGENT = "CHANGE_AGENT"
    CHANGE_PROVIDER = "CHANGE_PROVIDER"
    CHANGE_STRATEGY = "CHANGE_STRATEGY"
    REQUEST_USER = "REQUEST_USER"
    SKIP_OPTIONAL = "SKIP_OPTIONAL"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    # New task states
    RECOVERING = "RECOVERING"
    REPLANNING = "REPLANNING"


class AutonomyLevel(int, Enum):
    LEVEL_0 = 0 # Assistant
    LEVEL_1 = 1 # Suggest Plan
    LEVEL_2 = 2 # Auto Execute
    LEVEL_3 = 3 # Auto Recover
    LEVEL_4 = 4 # Continuous Optimization


class ApprovalGate(BaseModel):
    gate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    condition: str  # "Before execution", "Before recovery", "Before escalation", "Before external side effects"
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED
    requested_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    description: str
    priority: int = 1
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)
    required_capability: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""
    dependencies: List[str] = Field(default_factory=list)
    dependents: List[str] = Field(default_factory=list)
    execution_group: int = Field(default=0, description="Topological parallel execution group")
    complexity: float = Field(default=1.0, description="Estimated task complexity (1-10)")
    execution_policy: ExecutionPolicy = Field(default=ExecutionPolicy.CONTINUE, description="Failure handling policy")
    context: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(
        default_factory=list, description="Output artifact paths"
    )
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class WorkflowMetadata(BaseModel):
    version: str = "1.0"
    author: str = "Enterprise Autonomous Framework"
    tags: List[str] = Field(default_factory=list)
    lifecycle_state: str = "active"


class ExecutionPlan(BaseModel):
    goal: str
    tasks: List[Task]
    autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_2
    approval_gates: List[ApprovalGate] = Field(default_factory=list)
    workflow_template: Optional[str] = None
    milestones: List[str] = Field(default_factory=list)
    
    # New Declarative Workflow Pack fields
    metadata: WorkflowMetadata = Field(default_factory=WorkflowMetadata)
    recovery_policies: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    evaluation_metrics: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)


class SupervisorState(TypedDict, total=False):
    """LangGraph state for the Supervisor Agent"""

    # Core inputs
    user_input: str
    session_id: Optional[str]
    conversation_id: Optional[str]

    # State tracking
    goal: str
    memory_context: str
    execution_plan: Optional[ExecutionPlan]
    workflow_state: str  # Planning, Executing, Recovering, etc.
    autonomy_level: int

    # Execution state
    selected_agents: List[str]
    completed_tasks: List[str]
    failed_tasks: List[str]
    task_results: List[Dict[str, Any]]
    
    # Advanced state tracking
    replan_count: int
    recovery_cycles: int
    last_failed_task: Optional[str]
    last_recovery_strategy: Optional[str]

    # Final output
    final_response: str

    # Metrics
    execution_time_ms: float
    use_collaboration: bool
    
    # Executive Council
    executive_decision: Dict[str, Any]
