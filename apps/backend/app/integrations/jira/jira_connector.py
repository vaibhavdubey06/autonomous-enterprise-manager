from typing import Dict, Any, List
from app.integrations.base.base_connector import BaseConnector
from app.integrations.schemas.connector_models import (
    ConnectorHealthStatus,
    ConnectorMetadata,
    ExecutionRequest,
    ExecutionResponse,
    AuthType,
)


class JiraConnector(BaseConnector):
    @classmethod
    def get_metadata(cls) -> ConnectorMetadata:
        return ConnectorMetadata(
            name="jira",
            version="1.0.0",
            description="Jira Integration for Issue Tracking",
            supported_auth_types=[AuthType.OAUTH2, AuthType.API_KEY],
            capabilities=["jira.get_project_status", "jira.create_issue"],
        )

    def connect(self) -> None:
        self.connected = True

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        return True

    def health_check(self) -> ConnectorHealthStatus:
        return ConnectorHealthStatus.HEALTHY

    def discover_capabilities(self) -> List[str]:
        return self.get_metadata().capabilities

    def validate_permissions(self, capability: str) -> bool:
        return capability in self.discover_capabilities()

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        if request.capability == "jira.get_project_status":
            return ExecutionResponse(
                success=True,
                data={"project": "AEM", "status": "On Track", "issues": 42},
            )
        return ExecutionResponse(
            success=False, data=None, error_message="Capability not implemented"
        )

    def disconnect(self) -> None:
        self.connected = False

    def cleanup(self) -> None:
        pass


from app.integrations.base.connector_registry import connector_registry

connector_registry.register(JiraConnector)
