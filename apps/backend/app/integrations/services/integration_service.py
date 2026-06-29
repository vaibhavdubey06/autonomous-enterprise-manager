from typing import List, Dict, Any
from app.integrations.base.connector_manager import connector_manager
from app.integrations.base.connector_registry import connector_registry
from app.integrations.repositories.connector_repository import connector_repository
from app.integrations.schemas.connector_models import (
    ConnectorConfig,
    ExecutionRequest,
    ExecutionResponse,
    ConnectorHealthStatus,
)


class IntegrationService:
    def list_available_connectors(self) -> List[Dict[str, Any]]:
        return [m.dict() for m in connector_registry.list_connectors()]

    def list_tenant_connectors(self, tenant_id: str) -> List[ConnectorConfig]:
        return connector_repository.list_by_tenant(tenant_id)

    def connect(
        self,
        tenant_id: str,
        connector_type: str,
        auth_type: str,
        config_data: Dict[str, Any],
    ) -> ConnectorConfig:
        from app.integrations.schemas.connector_models import AuthType

        connector_id = f"{connector_type}_instance"

        config = ConnectorConfig(
            connector_id=connector_id,
            tenant_id=tenant_id,
            connector_type=connector_type,
            auth_type=AuthType(auth_type),
            config_data=config_data,
        )

        connector_manager.register_connector(config)
        connector_repository.save(config)

        # Initialize (which does connect, auth, health check)
        connector_manager.initialize_connector(tenant_id, connector_id)

        return config

    def disconnect(self, tenant_id: str, connector_id: str) -> bool:
        connector_manager.disconnect_connector(tenant_id, connector_id)
        config = connector_repository.get(tenant_id, connector_id)
        if config:
            from app.integrations.schemas.connector_models import ConnectorState

            config.state = ConnectorState.DISCONNECTED
            connector_repository.save(config)
        return True

    def get_health(self, tenant_id: str, connector_id: str) -> ConnectorHealthStatus:
        config = connector_repository.get(tenant_id, connector_id)
        if not config:
            return ConnectorHealthStatus.DISCONNECTED
        return config.health

    def get_capabilities(self, tenant_id: str, connector_id: str) -> List[str]:
        # To strictly enforce checking from the class vs instance
        cls = connector_registry.get_connector_class(
            connector_id.replace("_instance", "")
        )
        if cls:
            return cls.get_metadata().capabilities
        return []

    def execute(
        self,
        tenant_id: str,
        connector_id: str,
        capability: str,
        parameters: Dict[str, Any],
    ) -> ExecutionResponse:
        req = ExecutionRequest(capability=capability, parameters=parameters)
        return connector_manager.execute_capability(tenant_id, connector_id, req)


integration_service = IntegrationService()
