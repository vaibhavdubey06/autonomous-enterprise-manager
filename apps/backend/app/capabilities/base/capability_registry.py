import logging
from typing import Dict, List, Optional
from app.capabilities.base.base_capability import BaseCapability
from app.capabilities.base.schemas import Capability

logger = logging.getLogger(__name__)

class CapabilityRegistry:
    """
    Registry for tracking all registered Enterprise Capabilities.
    """
    def __init__(self):
        self._capabilities: Dict[str, BaseCapability] = {}

    def register(self, capability: BaseCapability):
        """Registers a new capability."""
        metadata = capability.get_metadata()
        self._capabilities[metadata.capability_id] = capability
        logger.info(f"Registered Capability: {metadata.name} ({metadata.capability_id})")

    def unregister(self, capability_id: str):
        """Unregisters an existing capability."""
        if capability_id in self._capabilities:
            del self._capabilities[capability_id]
            logger.info(f"Unregistered Capability: {capability_id}")

    def get(self, capability_id: str) -> Optional[BaseCapability]:
        """Retrieves a capability by its ID."""
        return self._capabilities.get(capability_id)

    def list(self) -> List[Capability]:
        """Lists all registered capabilities."""
        return [cap.get_metadata() for cap in self._capabilities.values()]

    def find_by_agent(self, agent_name: str) -> List[BaseCapability]:
        """Finds all capabilities authorized for a specific agent."""
        matching = []
        for cap in self._capabilities.values():
            meta = cap.get_metadata()
            if agent_name in meta.supported_agents or "*" in meta.supported_agents:
                matching.append(cap)
        return matching

    def find_by_action(self, action: str) -> List[BaseCapability]:
        """Finds all capabilities that support a specific action."""
        matching = []
        for cap in self._capabilities.values():
            meta = cap.get_metadata()
            if action in meta.supported_actions:
                matching.append(cap)
        return matching
