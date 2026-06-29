from typing import Dict, List, Optional
from app.integrations.schemas.connector_models import ConnectorConfig


class ConnectorRepository:
    def __init__(self):
        # tenant_id:connector_id -> ConnectorConfig
        self._store: Dict[str, ConnectorConfig] = {}

    def _key(self, tenant_id: str, connector_id: str) -> str:
        return f"{tenant_id}:{connector_id}"

    def save(self, config: ConnectorConfig) -> None:
        self._store[self._key(config.tenant_id, config.connector_id)] = config

    def get(self, tenant_id: str, connector_id: str) -> Optional[ConnectorConfig]:
        return self._store.get(self._key(tenant_id, connector_id))

    def list_by_tenant(self, tenant_id: str) -> List[ConnectorConfig]:
        return [c for c in self._store.values() if c.tenant_id == tenant_id]

    def delete(self, tenant_id: str, connector_id: str) -> None:
        key = self._key(tenant_id, connector_id)
        if key in self._store:
            del self._store[key]


connector_repository = ConnectorRepository()
