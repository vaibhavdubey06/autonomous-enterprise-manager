from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class MCPTransportType(str, Enum):
    STDIO = "stdio"
    SSE = "sse"


class MCPServerConfig(BaseModel):
    """Configuration for an external MCP server we want to connect to."""

    server_id: str
    name: str
    transport: MCPTransportType = MCPTransportType.STDIO
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    url: Optional[str] = None  # For SSE


class MCPToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class MCPResourceRequest(BaseModel):
    uri: str


class MCPPromptRequest(BaseModel):
    name: str
    arguments: Dict[str, str] = Field(default_factory=dict)
