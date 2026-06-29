import os
from typing import Optional
from app.security.secrets.base_secret_provider import BaseSecretProvider


class EnvSecretProvider(BaseSecretProvider):
    def get_secret(self, key: str) -> Optional[str]:
        return os.environ.get(key)

    def set_secret(self, key: str, value: str) -> None:
        # In a real environment, setting an env var won't persist across restarts.
        # This is a placeholder behavior.
        os.environ[key] = value

    def delete_secret(self, key: str) -> None:
        if key in os.environ:
            del os.environ[key]
