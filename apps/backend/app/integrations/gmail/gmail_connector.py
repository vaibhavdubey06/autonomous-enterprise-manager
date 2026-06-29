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


class GmailConnector(BaseConnector):
    @classmethod
    def get_metadata(cls) -> ConnectorMetadata:
        return ConnectorMetadata(
            name="gmail",
            version="1.0.0",
            description="Gmail Integration",
            supported_auth_types=[AuthType.OAUTH2],
            capabilities=["gmail.read_emails", "gmail.send_email"],
        )

    def connect(self) -> None:
        pass

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        return True

    def health_check(self) -> ConnectorHealthStatus:
        return ConnectorHealthStatus.HEALTHY

    def discover_capabilities(self) -> List[str]:
        return self.get_metadata().capabilities

    def validate_permissions(self, capability: str) -> bool:
        return capability in self.discover_capabilities()

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        return ExecutionResponse(success=True, data={"emails": []})

    def disconnect(self) -> None:
        pass

    def cleanup(self) -> None:
        pass


connector_registry.register(GmailConnector)
