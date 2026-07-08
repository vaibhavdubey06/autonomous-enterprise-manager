from typing import List
from pydantic import BaseModel, Field
from app.agents.base.capabilities import Capability


class AgentProfile(BaseModel):
    """
    Profile representing the metadata and capabilities of an Executive Agent.
    """

    agent_name: str
    title: str
    domain: str
    description: str
    capabilities: List[Capability] = Field(default_factory=list)
    supported_task_types: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    supported_sources: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    decision_authority: List[str] = Field(default_factory=list)
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    memory_requirements: List[str] = Field(default_factory=list)
    approval_requirements: List[str] = Field(default_factory=list)
    delegation_strategy: str = ""
    escalation_rules: List[str] = Field(default_factory=list)
    
    # Legacy fields mapping
    decision_boundaries: List[str] = Field(default_factory=list)
    memory_usage: str = ""
    prompt_strategy: str = ""
    supervisor_interaction: str = ""
    governance_interaction: str = ""
    workflow_engine_interaction: str = ""
