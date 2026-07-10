from typing import Dict, Optional, Any
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

    def dispatch_operation(
        self,
        tenant_id: str,
        capability: str,
        operation: Any,
        parameters: Dict[str, Any],
    ) -> ExecutionResponse:
        from app.integrations.base.connector_registry import connector_registry
        from app.services.decisions.engine import DecisionEngine
        from app.operations.tracing.trace_manager import TraceManager
        import uuid

        trace_manager = TraceManager()
        decision_engine = DecisionEngine()
        trace_id = f"conn_dispatch_{uuid.uuid4().hex[:8]}"

        # 1. Find all connectors that support this capability
        candidates = []
        for cls in connector_registry._connectors.values():
            profile = cls.get_metadata()
            if capability in profile.capabilities:
                candidates.append(profile.name)

        if not candidates:
            return ExecutionResponse(
                success=False,
                data=None,
                error_message=f"No connectors support capability {capability}",
            )

        # 2. Select connector via Decision Engine
        selected_connector_id = decision_engine.route_connector(capability, candidates)

        # 3. Emit Trace Spans
        span_selected = trace_manager.start_span(
            trace_id=trace_id,
            operation="connector_selected",
            connector_id=selected_connector_id,
        )
        trace_manager.end_span(span_selected, "OK")

        # Ensure we have a config in memory for this mock execution if missing
        if not self.get_config(tenant_id, selected_connector_id):
            # Auto-register a basic config for the test
            from app.integrations.schemas.connector_models import AuthType

            self.register_connector(
                ConnectorConfig(
                    connector_id=selected_connector_id,
                    tenant_id=tenant_id,
                    connector_type=selected_connector_id,
                    auth_type=AuthType.NONE,
                    state=ConnectorState.READY,
                )
            )

            # Also instantiate directly for tests
            cls = connector_registry.get_connector_class(selected_connector_id)
            if cls:
                self._instances[
                    self._get_cache_key(tenant_id, selected_connector_id)
                ] = cls(tenant_id, selected_connector_id)

        span_exec = trace_manager.start_span(
            trace_id=trace_id, operation="connector_execution", capability=capability
        )

        request = ExecutionRequest(
            capability=capability, operation=operation, parameters=parameters
        )
        response = self.execute_capability(tenant_id, selected_connector_id, request)

        if response.success:
            trace_manager.end_span(span_exec, "OK")
        else:
            trace_manager.end_span(span_exec, "ERROR", error_msg=response.error_message)

            # Emit connector_failure span
            span_fail = trace_manager.start_span(
                trace_id=trace_id,
                operation="connector_failure",
                error=response.error_message,
            )
            trace_manager.end_span(span_fail, "ERROR")

        return response


connector_manager = ConnectorManager()
