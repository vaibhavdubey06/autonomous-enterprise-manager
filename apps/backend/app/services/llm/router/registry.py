from typing import Dict, List, Type, Optional
from app.services.llm.providers.base import AbstractLLMProvider

class ProviderRegistry:
    """Dynamic registry for LLM Providers."""
    
    def __init__(self):
        # We store the instantiated providers mapped by their provider_name
        self._providers: Dict[str, AbstractLLMProvider] = {}
        
    def register(self, provider: AbstractLLMProvider) -> None:
        """Register a provider instance."""
        profile = provider.get_profile()
        self._providers[profile.provider_name] = provider
        
    def get(self, provider_name: str) -> Optional[AbstractLLMProvider]:
        """Get a specific provider by name."""
        return self._providers.get(provider_name)
        
    def get_all(self) -> List[AbstractLLMProvider]:
        """Get all registered providers."""
        return list(self._providers.values())
        
    def remove(self, provider_name: str) -> None:
        """Remove a provider from the registry."""
        if provider_name in self._providers:
            del self._providers[provider_name]

# Singleton registry
provider_registry = ProviderRegistry()
