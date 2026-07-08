from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.integrations.schemas.connector_models import (
    ConnectorHealthStatus,
    ConnectorMetadata,
    ConnectorProfile,
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

    # --- Synchronization Interface ---
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate connection and permissions for synchronization."""
        pass

    @abstractmethod
    def handle_webhook(self, payload: Dict[str, Any]) -> Any:
        """Process incoming webhook payloads into sync events."""
        pass

    @abstractmethod
    def poll_changes(self, last_checkpoint: Any) -> List[Any]:
        """Poll external system for changes since the last checkpoint."""
        pass

    @abstractmethod
    def fetch_document(self, document_id: str) -> Any:
        """Fetch a specific document's content and metadata."""
        pass

    @abstractmethod
    def fetch_incremental_changes(self, resource_id: str, since: Any) -> List[Any]:
        """Fetch only the changes that occurred after a given timestamp or cursor."""
        pass

    @abstractmethod
    def checkpoint(self, state: Any) -> None:
        """Save the current synchronization checkpoint."""
        pass

    @abstractmethod
    def sync(self) -> None:
        """Trigger a full or incremental synchronization."""
        pass

    # --- Standardized Aliases (Thin Adapter Interface) ---

    def metadata(self) -> ConnectorProfile:
        """Returns the full ConnectorProfile."""
        return ConnectorProfile(
            metadata=self.get_metadata(),
            health_status=self.health_check()
        )

    def webhook(self, payload: Dict[str, Any]) -> Any:
        """Formal alias for handle_webhook."""
        return self.handle_webhook(payload)

    def poll(self, last_checkpoint: Any = None) -> List[Any]:
        """Formal alias for poll_changes."""
        return self.poll_changes(last_checkpoint)

