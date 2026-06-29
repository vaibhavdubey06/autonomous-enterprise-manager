from typing import Dict, Any
from app.security.identity.identity_models import Identity


class ABACEngine:
    def evaluate(
        self,
        identity: Identity,
        resource_attributes: Dict[str, Any],
        required_attributes: Dict[str, Any],
    ) -> bool:
        if not required_attributes:
            return True

        # Example ABAC rules:
        # If the required attribute is "owner_id", check if it matches the identity.id
        if "owner_id" in required_attributes:
            if required_attributes["owner_id"] != identity.id:
                return False

        # If the required attribute is "tenant_id", check if it matches identity.tenant_id
        if "tenant_id" in required_attributes:
            if required_attributes["tenant_id"] != identity.tenant_id:
                return False

        return True


abac_engine = ABACEngine()
