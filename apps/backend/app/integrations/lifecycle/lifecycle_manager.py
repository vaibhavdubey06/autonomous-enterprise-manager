from app.integrations.schemas.connector_models import ConnectorState, ConnectorConfig
from app.integrations.base.base_connector import BaseConnector


class LifecycleManager:
    def register(self, config: ConnectorConfig) -> None:
        config.state = ConnectorState.REGISTERED

    def configure(self, config: ConnectorConfig) -> None:
        if config.state == ConnectorState.REGISTERED:
            config.state = ConnectorState.CONFIGURED

    def authenticate(
        self, config: ConnectorConfig, connector: BaseConnector, credentials: dict
    ) -> bool:
        if config.state == ConnectorState.CONFIGURED:
            success = connector.authenticate(credentials)
            if success:
                config.state = ConnectorState.AUTHENTICATED
            else:
                config.state = ConnectorState.ERROR
            return success
        return False

    def check_health(self, config: ConnectorConfig, connector: BaseConnector) -> None:
        from app.integrations.schemas.connector_models import ConnectorHealthStatus

        if config.state == ConnectorState.AUTHENTICATED:
            status = connector.health_check()
            if status == ConnectorHealthStatus.HEALTHY:
                config.state = ConnectorState.READY
            else:
                config.state = ConnectorState.ERROR

    def disconnect(self, config: ConnectorConfig, connector: BaseConnector) -> None:
        connector.disconnect()
        config.state = ConnectorState.DISCONNECTED

    def remove(self, config: ConnectorConfig, connector: BaseConnector) -> None:
        connector.cleanup()
        # Assume DB deletion happens at repository level


lifecycle_manager = LifecycleManager()
