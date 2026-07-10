from abc import ABC, abstractmethod
from typing import AsyncGenerator
from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.router.provider_profile import ProviderProfile


class AbstractLLMProvider(ABC):
    """Abstract interface for all LLM providers."""

    @abstractmethod
    def get_profile(self) -> ProviderProfile:
        """Returns the structured metadata and capabilities for this provider."""
        pass

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a text response."""
        pass

    @abstractmethod
    def generate_structured(self, request: LLMRequest) -> LLMResponse:
        """Generate a structured response adhering to request.schema."""
        pass

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream a text response."""
        pass
