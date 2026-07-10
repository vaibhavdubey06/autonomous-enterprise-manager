from typing import Dict, List, Optional
from app.services.synchronization.models import ResourceRegistryEntry


class ResourceRegistry:
    """Registry to uniformly expose resources (repos, channels, folders) across all connectors."""

    def __init__(self):
        self._resources: Dict[str, ResourceRegistryEntry] = {}

    def register(self, resource: ResourceRegistryEntry) -> None:
        """Register a new resource."""
        self._resources[resource.resource_id] = resource

    def get(self, resource_id: str) -> Optional[ResourceRegistryEntry]:
        """Get a resource by ID."""
        return self._resources.get(resource_id)

    def list_by_connector(self, connector_id: str) -> List[ResourceRegistryEntry]:
        """List all resources belonging to a specific connector."""
        return [r for r in self._resources.values() if r.connector_id == connector_id]

    def list_all(self) -> List[ResourceRegistryEntry]:
        """List all registered resources."""
        return list(self._resources.values())


resource_registry = ResourceRegistry()
