from typing import Dict, Type, List, Optional
from app.integrations.base.base_connector import BaseConnector
from app.integrations.schemas.connector_models import ConnectorMetadata


class ConnectorRegistry:
    def __init__(self):
        self._connectors: Dict[str, Type[BaseConnector]] = {}

    def register(self, connector_class: Type[BaseConnector]) -> None:
        metadata = connector_class.get_metadata()
        self._connectors[metadata.name] = connector_class

    def get_connector_class(self, name: str) -> Optional[Type[BaseConnector]]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[ConnectorMetadata]:
        return [cls.get_metadata() for cls in self._connectors.values()]


connector_registry = ConnectorRegistry()
