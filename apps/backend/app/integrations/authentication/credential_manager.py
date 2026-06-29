from typing import Dict, Any, Optional
from app.integrations.schemas.connector_models import AuthType

# Reuse Enterprise Security Platform Secret Manager
# In Phase 11, we built app.security.secrets.secret_manager
from app.security.secrets.secret_manager import secret_manager


class CredentialManager:
    def get_credentials(
        self, tenant_id: str, connector_id: str, auth_type: AuthType
    ) -> Optional[Dict[str, Any]]:
        # Key convention: {tenant_id}_{connector_id}_CREDENTIALS
        key = f"{tenant_id}_{connector_id}_CREDENTIALS"

        # Read from Secret Manager
        secret_value = secret_manager.get_secret(key)

        if not secret_value:
            # Fallback for dev: check if there's a global one
            fallback_key = f"{connector_id.upper()}_TOKEN"
            fallback_secret = secret_manager.get_secret(fallback_key)
            if fallback_secret:
                return {"token": fallback_secret}
            return None

        # In a real app, this might be JSON parsed.
        # Here we just assume it's a token string for simplicity if it's PAT or API_KEY
        if auth_type in [AuthType.PAT, AuthType.API_KEY, AuthType.SERVICE_ACCOUNT]:
            return {"token": secret_value}

        return {"raw": secret_value}

    def set_credentials(
        self, tenant_id: str, connector_id: str, credentials: str
    ) -> None:
        key = f"{tenant_id}_{connector_id}_CREDENTIALS"
        secret_manager.set_secret(key, credentials)


credential_manager = CredentialManager()
