from abc import ABC, abstractmethod
from typing import Optional


class BaseSecretProvider(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set_secret(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def delete_secret(self, key: str) -> None:
        pass
