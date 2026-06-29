from pydantic import BaseModel, Field
from typing import List, Dict, Any


class Identity(BaseModel):
    id: str
    tenant_id: str
    identity_type: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    groups: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HumanUser(Identity):
    identity_type: str = "human"
    email: str


class ServiceAccount(Identity):
    identity_type: str = "service_account"
    name: str


class ExecutiveAgent(Identity):
    identity_type: str = "agent"
    agent_name: str


class CapabilityIdentity(Identity):
    identity_type: str = "capability"
    capability_name: str


class WorkflowIdentity(Identity):
    identity_type: str = "workflow"
    workflow_id: str
