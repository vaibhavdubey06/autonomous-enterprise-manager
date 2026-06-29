"""LLM Provider Registry, Model Registry, and Routing Engine."""

import logging
import random
from typing import Dict, List, Optional

from app.llm.providers.base import (
    InferenceRequest,
    InferenceResponse,
    LLMProvider,
    ModelCapability,
)

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry of all available LLM providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, LLMProvider] = {}

    def register(self, provider: LLMProvider) -> None:
        self._providers[provider.get_name()] = provider
        logger.info(f"Registered LLM provider: {provider.get_name()}")

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())

    def get_providers_for_capability(
        self, capability: ModelCapability
    ) -> List[LLMProvider]:
        return [
            p for p in self._providers.values() if capability in p.get_capabilities()
        ]


class ModelEntry:
    """Registration entry for a specific model."""

    def __init__(
        self,
        model_id: str,
        provider_name: str,
        capabilities: List[ModelCapability],
        cost_per_1k_tokens: float = 0.0,
        max_context_length: int = 8192,
        is_default: bool = False,
    ):
        self.model_id = model_id
        self.provider_name = provider_name
        self.capabilities = capabilities
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.max_context_length = max_context_length
        self.is_default = is_default


class ModelRegistry:
    """Registry of all available models across providers."""

    def __init__(self) -> None:
        self._models: Dict[str, ModelEntry] = {}

    def register(self, entry: ModelEntry) -> None:
        self._models[entry.model_id] = entry

    def get_model(self, model_id: str) -> Optional[ModelEntry]:
        return self._models.get(model_id)

    def get_default_model(self) -> Optional[ModelEntry]:
        for entry in self._models.values():
            if entry.is_default:
                return entry
        return next(iter(self._models.values()), None)

    def list_models(self) -> List[Dict]:
        return [
            {
                "model_id": m.model_id,
                "provider": m.provider_name,
                "capabilities": [c.value for c in m.capabilities],
                "cost_per_1k_tokens": m.cost_per_1k_tokens,
            }
            for m in self._models.values()
        ]


class RoutingEngine:
    """Routes inference requests to the optimal provider based on capability, cost, and availability."""

    def __init__(
        self,
        provider_registry: ProviderRegistry,
        model_registry: ModelRegistry,
    ) -> None:
        self._provider_registry = provider_registry
        self._model_registry = model_registry
        self._ab_test_groups: Dict[str, List[str]] = {}

    def route(self, request: InferenceRequest) -> InferenceResponse:
        # If a specific model is requested, use it directly
        if request.model_id:
            entry = self._model_registry.get_model(request.model_id)
            if entry:
                provider = self._provider_registry.get_provider(entry.provider_name)
                if provider and provider.is_available():
                    return provider.invoke(request)

        # Route by capability
        providers = self._provider_registry.get_providers_for_capability(
            request.capability
        )
        available = [p for p in providers if p.is_available()]

        if not available:
            raise RuntimeError(
                f"No available provider for capability: {request.capability.value}"
            )

        # A/B test routing
        ab_group = request.metadata.get("ab_group")
        if ab_group and ab_group in self._ab_test_groups:
            target_providers = self._ab_test_groups[ab_group]
            available = [p for p in available if p.get_name() in target_providers]

        # Select provider (round-robin / random for now)
        provider = random.choice(available)

        try:
            return provider.invoke(request)
        except Exception as e:
            logger.warning(
                f"Provider {provider.get_name()} failed: {e}. Attempting fallback."
            )
            # Fallback to next available
            for fallback in available:
                if fallback is not provider:
                    try:
                        return fallback.invoke(request)
                    except Exception:
                        continue
            raise RuntimeError("All LLM providers failed") from e

    def register_ab_test(self, group_name: str, provider_names: List[str]) -> None:
        self._ab_test_groups[group_name] = provider_names
