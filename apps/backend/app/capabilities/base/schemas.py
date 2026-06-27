from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CapabilityType(str, Enum):
    TOOL = "TOOL"
    API = "API"
    WORKFLOW = "WORKFLOW"
    MCP_SERVER = "MCP_SERVER"
    INTERNAL_SERVICE = "INTERNAL_SERVICE"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"

class Capability(BaseModel):
    """
    Metadata defining a specific capability.
    """
    capability_id: str
    name: str
    description: str
    type: CapabilityType
    supported_actions: List[str] = Field(default_factory=list)
    required_permissions: List[str] = Field(default_factory=list)
    supported_agents: List[str] = Field(default_factory=list)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)

class CapabilityResult(BaseModel):
    """
    Standardized response from any Capability execution.
    """
    success: bool
    capability_name: str
    action: str
    status: str
    execution_time_ms: float = 0.0
    artifacts: List[str] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    data: Optional[Dict[str, Any]] = None
