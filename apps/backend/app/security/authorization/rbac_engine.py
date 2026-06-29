from typing import List
from app.security.identity.identity_models import Identity


class RBACEngine:
    def evaluate(self, identity: Identity, required_permissions: List[str]) -> bool:
        if not required_permissions:
            return True

        # If the identity has a wildcard or super admin role, we can short circuit
        if "admin" in identity.roles or "*" in identity.permissions:
            return True

        user_perms = set(identity.permissions)

        # Check if all required permissions are met
        for req_perm in required_permissions:
            if req_perm not in user_perms:
                return False

        return True


rbac_engine = RBACEngine()
