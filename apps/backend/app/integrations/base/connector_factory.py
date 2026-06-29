from typing import Optional
from app.integrations.base.base_connector import BaseConnector
from app.integrations.base.connector_registry import connector_registry


class ConnectorFactory:
    @staticmethod
    def create_connector(
        connector_type: str, tenant_id: str, connector_id: str
    ) -> Optional[BaseConnector]:
        cls = connector_registry.get_connector_class(connector_type)
        if not cls:
            return None
        return cls(tenant_id=tenant_id, connector_id=connector_id)
