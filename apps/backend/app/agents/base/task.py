from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
import datetime
from app.agents.base.capabilities import Capability


class ExecutiveTask(BaseModel):
    """
    Represents a specific unit of work assigned to an Executive Agent.
    """

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    description: str
    priority: int = 1
    deadline: Optional[datetime.datetime] = None
    dependencies: List[str] = Field(default_factory=list)
    assigned_agent: Optional[str] = None
    required_capabilities: List[Capability] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)
