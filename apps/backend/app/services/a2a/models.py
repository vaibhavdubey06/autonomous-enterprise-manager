from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.agents.base.profile import AgentProfile


class TrustLevel(str, Enum):
    TRUSTED = "Trusted"
    PARTNER = "Partner"
    UNKNOWN = "Unknown"
    RESTRICTED = "Restricted"
    UNTRUSTED = "Untrusted"


class RemoteAgentProfile(AgentProfile):
    """
    Standardized profile for remote agents discovered via A2A.
    Extends the native AgentProfile so the Planner can route to it naturally.
    """

    agent_id: str = Field(..., description="Unique ID of the agent")
    organization: str = Field(..., description="Organization hosting this agent")
    version: str = Field("1.0", description="Agent version")
    health: str = Field("Healthy", description="Agent health status")
    availability: str = Field("Available", description="Current availability")
    trust_score: float = Field(0.0, description="Computed trust score (0.0 to 1.0)")
    trust_level: TrustLevel = Field(
        TrustLevel.UNKNOWN, description="Configured trust level"
    )
    latency_ms: float = Field(0.0, description="Average response latency")
    cost_per_task: float = Field(0.0, description="Estimated cost per task")
    endpoint_url: str = Field(..., description="A2A endpoint to reach this agent")


class OrganizationProfile(BaseModel):
    org_id: str
    name: str
    trust_level: TrustLevel
    endpoints: List[str] = Field(default_factory=list)
    agents: List[RemoteAgentProfile] = Field(default_factory=list)


class A2ATaskRequest(BaseModel):
    task_id: str
    target_agent_id: str
    task_description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    requester_org: str
    requester_agent: str


class A2ATaskResponse(BaseModel):
    task_id: str
    status: str
    summary: str
    reasoning: str
    recommendations: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class A2ANegotiationProposal(BaseModel):
    negotiation_id: str
    topic: str
    proposer_org: str
    proposer_agent: str
    content: str
