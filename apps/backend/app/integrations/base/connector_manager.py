from typing import Dict, Optional
from app.integrations.base.connector_factory import ConnectorFactory
from app.integrations.authentication.credential_manager import credential_manager
from app.integrations.lifecycle.lifecycle_manager import lifecycle_manager
from app.integrations.health.connector_health import health_manager
from app.integrations.policies.connector_policy import connector_policy_manager
from app.integrations.schemas.connector_models import (
    ConnectorConfig,
    ConnectorState,
    ExecutionRequest,
    ExecutionResponse,
)
from app.integrations.base.base_connector import BaseConnector


class ConnectorManager:
    def __init__(self):
        # In a real system, configurations are persisted. For now we use an in-memory map.
        self._configs: Dict[str, ConnectorConfig] = {}
        self._instances: Dict[str, BaseConnector] = {}

    def _get_cache_key(self, tenant_id: str, connector_id: str) -> str:
        return f"{tenant_id}:{connector_id}"

    def register_connector(self, config: ConnectorConfig) -> None:
        lifecycle_manager.register(config)
        self._configs[self._get_cache_key(config.tenant_id, config.connector_id)] = (
            config
        )

    def get_config(
        self, tenant_id: str, connector_id: str
    ) -> Optional[ConnectorConfig]:
        return self._configs.get(self._get_cache_key(tenant_id, connector_id))

    def initialize_connector(
        self, tenant_id: str, connector_id: str
    ) -> Optional[BaseConnector]:
        config = self.get_config(tenant_id, connector_id)
        if not config:
            return None

        # Check policy
        if not connector_policy_manager.evaluate_policy(
            tenant_id, connector_id, "initialize"
        ):
            raise PermissionError("Policy denied connector initialization")

        # 1. Instantiate via Factory
        connector = ConnectorFactory.create_connector(
            config.connector_type, tenant_id, connector_id
        )
        if not connector:
            return None

        # 2. Connect (Configure state)
        connector.connect()
        lifecycle_manager.configure(config)

        # 3. Authenticate
        creds = credential_manager.get_credentials(
            tenant_id, connector_id, config.auth_type
        )
        if creds:
            if lifecycle_manager.authenticate(config, connector, creds):
                # 4. Check Health & transition to Ready
                lifecycle_manager.check_health(config, connector)
            else:
                health_manager.report_health_to_operations(
                    connector_id, tenant_id, config.health
                )

        self._instances[self._get_cache_key(tenant_id, connector_id)] = connector
        return connector

    def execute_capability(
        self, tenant_id: str, connector_id: str, request: ExecutionRequest
    ) -> ExecutionResponse:
        config = self.get_config(tenant_id, connector_id)
        if not config:
            return ExecutionResponse(
                success=False, data=None, error_message="Connector not configured"
            )

        if config.state != ConnectorState.READY:
            # Try to initialize
            connector = self.initialize_connector(tenant_id, connector_id)
            if not connector or config.state != ConnectorState.READY:
                return ExecutionResponse(
                    success=False,
                    data=None,
                    error_message=f"Connector not ready. State: {config.state}",
                )
        else:
            connector = self._instances.get(
                self._get_cache_key(tenant_id, connector_id)
            )

        if not connector:
            return ExecutionResponse(
                success=False,
                data=None,
                error_message="Connector not initialized",
            )

        # Governance Check
        if not connector_policy_manager.evaluate_policy(
            tenant_id, connector_id, request.capability
        ):
            return ExecutionResponse(
                success=False,
                data=None,
                error_message="Governance policy denied execution",
            )

        if not connector.validate_permissions(request.capability):
            return ExecutionResponse(
                success=False,
                data=None,
                error_message="Identity does not have permission for this capability",
            )

        # Emitting Operations Telemetry happens implicitly (can be added as decorators or wrappers here)
        # execution
        try:
            return connector.execute(request)
        except Exception as e:
            # Emit error telemetry
            return ExecutionResponse(success=False, data=None, error_message=str(e))

    def disconnect_connector(self, tenant_id: str, connector_id: str) -> None:
        config = self.get_config(tenant_id, connector_id)
        connector = self._instances.get(self._get_cache_key(tenant_id, connector_id))
        if config and connector:
            lifecycle_manager.disconnect(config, connector)


connector_manager = ConnectorManager()
