from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ConnectorState(str, Enum):
    REGISTERED = "registered"
    CONFIGURED = "configured"
    AUTHENTICATED = "authenticated"
    READY = "ready"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class ConnectorHealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    AUTH_FAILED = "auth_failed"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    DISCONNECTED = "disconnected"


class AuthType(str, Enum):
    OAUTH2 = "oauth2"
    PAT = "pat"
    API_KEY = "api_key"
    SERVICE_ACCOUNT = "service_account"
    NONE = "none"


class ConnectorMetadata(BaseModel):
    name: str
    version: str
    description: str
    supported_auth_types: List[AuthType]
    capabilities: List[str]


class ConnectorProfile(BaseModel):
    metadata: ConnectorMetadata
    health_status: ConnectorHealthStatus = ConnectorHealthStatus.HEALTHY
    rate_limit_remaining: int = 1000
    cost_per_execution: float = 0.0
    latency_ms: float = 0.0


class ConnectorConfig(BaseModel):
    connector_id: str
    tenant_id: str
    connector_type: str
    auth_type: AuthType
    config_data: Dict[str, Any] = Field(default_factory=dict)
    state: ConnectorState = ConnectorState.REGISTERED
    health: ConnectorHealthStatus = ConnectorHealthStatus.DISCONNECTED


class ConnectorOperation(str, Enum):
    READ = "read"
    WRITE = "write"
    SEARCH = "search"
    EXECUTE = "execute"
    SYNC = "sync"


class ExecutionRequest(BaseModel):
    capability: str
    operation: Optional[ConnectorOperation] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    success: bool
    data: Any
    error_message: Optional[str] = None
