from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid
import datetime


class RuntimeState(str, Enum):
    CREATED = "CREATED"
    INITIALIZED = "INITIALIZED"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    WAITING = "WAITING"
    RECOVERING = "RECOVERING"
    REFLECTING = "REFLECTING"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"


class RuntimeSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_session_id: str
    conversation_id: str
    workflow_id: Optional[str] = None
    state: RuntimeState = RuntimeState.CREATED

    # Contexts
    planner_state: Dict[str, Any] = Field(default_factory=dict)
    execution_state: Dict[str, Any] = Field(default_factory=dict)
    decision_context: Dict[str, Any] = Field(default_factory=dict)
    reflection_context: Dict[str, Any] = Field(default_factory=dict)
    evaluation_context: Dict[str, Any] = Field(default_factory=dict)
    telemetry_context: Dict[str, Any] = Field(default_factory=dict)

    # Active References
    checkpoint_references: List[str] = Field(default_factory=list)
    active_agents: List[str] = Field(default_factory=list)
    active_connectors: List[str] = Field(default_factory=list)
    mcp_sessions: List[str] = Field(default_factory=list)
    a2a_sessions: List[str] = Field(default_factory=list)

    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
