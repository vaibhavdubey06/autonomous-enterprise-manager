from typing import Set, Dict, List


class PermissionRegistry:
    def __init__(self):
        self._permissions: Set[str] = set()
        self._capability_requirements: Dict[str, List[str]] = {}

    def register_permission(self, permission: str):
        self._permissions.add(permission)

    def register_capability_permissions(
        self, capability: str, required_permissions: List[str]
    ):
        self._capability_requirements[capability] = required_permissions
        for p in required_permissions:
            self.register_permission(p)

    def get_capability_permissions(self, capability: str) -> List[str]:
        return self._capability_requirements.get(capability, [])

    def is_registered(self, permission: str) -> bool:
        return permission in self._permissions

    def all_permissions(self) -> List[str]:
        return list(self._permissions)


permission_registry = PermissionRegistry()

# Standard generic permissions
permission_registry.register_permission("workflow.execute")
permission_registry.register_permission("workflow.pause")
permission_registry.register_permission("workflow.cancel")
permission_registry.register_permission("memory.read")
permission_registry.register_permission("memory.write")
permission_registry.register_permission("governance.approve")
permission_registry.register_permission("operations.read")
permission_registry.register_permission("security.manage")

# Capability specifics
permission_registry.register_capability_permissions(
    "github", ["github.read", "github.write"]
)
