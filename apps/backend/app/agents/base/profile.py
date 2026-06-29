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
