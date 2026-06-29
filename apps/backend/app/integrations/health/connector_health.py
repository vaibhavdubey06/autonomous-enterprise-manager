from app.integrations.schemas.connector_models import ConnectorHealthStatus


class HealthManager:
    def check_health(self, connector) -> ConnectorHealthStatus:
        try:
            status = connector.health_check()
            return status
        except Exception:
            return ConnectorHealthStatus.ERROR

    def report_health_to_operations(
        self, connector_id: str, tenant_id: str, status: ConnectorHealthStatus
    ):
        # Emits to operations platform
        # e.g., operations_event_bus.publish("connector.health", {"connector_id": connector_id, "status": status.value})
        pass


health_manager = HealthManager()
