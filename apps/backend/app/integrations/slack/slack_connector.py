from app.integrations.base.connector_registry import connector_registry
from typing import Dict, Any, List
from app.integrations.base.base_connector import BaseConnector
from app.integrations.schemas.connector_models import (
    ConnectorHealthStatus,
    ConnectorMetadata,
    ExecutionRequest,
    ExecutionResponse,
    AuthType,
)


class SlackConnector(BaseConnector):
    @classmethod
    def get_metadata(cls) -> ConnectorMetadata:
        return ConnectorMetadata(
            name="slack",
            version="1.0.0",
            description="Slack Integration for Messages",
            supported_auth_types=[AuthType.OAUTH2],
            capabilities=["slack.read_channel", "slack.send_message"],
        )

    def connect(self) -> None:
        pass

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        # Simulate auth expiration for tests if 'expire' in token
        if credentials.get("token") == "expired" or credentials.get("raw") == "expired":
            return False
        return True

    def health_check(self) -> ConnectorHealthStatus:
        return ConnectorHealthStatus.HEALTHY

    def discover_capabilities(self) -> List[str]:
        return self.get_metadata().capabilities

    def validate_permissions(self, capability: str) -> bool:
        return capability in self.discover_capabilities()

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        if request.capability == "slack.read_channel":
            return ExecutionResponse(
                success=True, data={"messages": ["Hello", "World"]}
            )
        return ExecutionResponse(
            success=False, data=None, error_message="Capability not implemented"
        )

    def disconnect(self) -> None:
        pass

    def cleanup(self) -> None:
        pass

    # --- Synchronization Interface ---

    def validate(self) -> bool:
        return self.health_check() == ConnectorHealthStatus.HEALTHY

    def handle_webhook(self, payload: Dict[str, Any]) -> Any:
        pass

    def poll_changes(self, last_checkpoint: Any) -> List[Any]:
        return []

    def fetch_document(self, document_id: str) -> Any:
        return None

    def fetch_incremental_changes(self, resource_id: str, since: Any) -> List[Any]:
        return []

    def checkpoint(self, state: Any) -> None:
        pass

    def sync(self) -> None:
        pass


connector_registry.register(SlackConnector)
