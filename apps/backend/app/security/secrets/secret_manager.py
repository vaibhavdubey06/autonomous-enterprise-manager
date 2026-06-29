from typing import Optional, Dict
from app.security.secrets.base_secret_provider import BaseSecretProvider
from app.security.secrets.env_secret_provider import EnvSecretProvider


class SecretManager:
    def __init__(self):
        self.providers: Dict[str, BaseSecretProvider] = {"env": EnvSecretProvider()}
        self.default_provider = "env"

    def get_secret(
        self, key: str, provider_name: Optional[str] = None
    ) -> Optional[str]:
        provider = self.providers.get(provider_name or self.default_provider)
        if provider:
            return provider.get_secret(key)
        return None

    def set_secret(
        self, key: str, value: str, provider_name: Optional[str] = None
    ) -> None:
        provider = self.providers.get(provider_name or self.default_provider)
        if provider:
            provider.set_secret(key, value)

    def delete_secret(self, key: str, provider_name: Optional[str] = None) -> None:
        provider = self.providers.get(provider_name or self.default_provider)
        if provider:
            provider.delete_secret(key)


secret_manager = SecretManager()
