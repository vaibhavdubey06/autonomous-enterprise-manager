from typing import Dict, Any


class OAuthManager:
    def get_authorization_url(self, connector_id: str, tenant_id: str) -> str:
        # Generate OAuth URL for a connector
        return f"https://auth.example.com/authorize?client_id={connector_id}&state={tenant_id}"

    def handle_callback(
        self, connector_id: str, tenant_id: str, code: str
    ) -> Dict[str, Any]:
        # Exchange code for token
        return {"token": f"oauth_token_for_{code}"}


oauth_manager = OAuthManager()
