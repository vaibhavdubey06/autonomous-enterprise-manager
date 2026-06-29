from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.integrations.schemas.connector_models import (
    ConnectorHealthStatus,
    ConnectorMetadata,
    ExecutionRequest,
    ExecutionResponse,
)


class BaseConnector(ABC):
    def __init__(self, tenant_id: str, connector_id: str):
        self.tenant_id = tenant_id
        self.connector_id = connector_id

    @classmethod
    @abstractmethod
    def get_metadata(cls) -> ConnectorMetadata:
        """Return static metadata for this connector type."""
        pass

    @abstractmethod
    def connect(self) -> None:
        """Establish underlying connection."""
        pass

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with the external system."""
        pass

    @abstractmethod
    def health_check(self) -> ConnectorHealthStatus:
        """Check the health of the connection to the external system."""
        pass

    @abstractmethod
    def discover_capabilities(self) -> List[str]:
        """Return a list of capabilities this connector can currently perform."""
        pass

    @abstractmethod
    def validate_permissions(self, capability: str) -> bool:
        """Check if the authenticated identity has permissions on the external system for this capability."""
        pass

    @abstractmethod
    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Execute a capability on the external system."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Gracefully disconnect from the external system."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up any temporary resources."""
        pass
