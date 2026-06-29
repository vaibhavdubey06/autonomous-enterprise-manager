from enum import Enum
from pydantic import BaseModel
from typing import List, Optional


class AgentRole(str, Enum):
    LEADER = "Leader"
    CONTRIBUTOR = "Contributor"
    REVIEWER = "Reviewer"
    APPROVER = "Approver"
    OBSERVER = "Observer"


class AgentCollaborationProfile(BaseModel):
    agent_id: str
    expertise: List[str]
    capabilities: List[str]
    confidence: float
    workload: int
    availability: bool
    assigned_role: Optional[AgentRole] = None
