from typing import Dict, Optional
from app.services.llm.prompts.models import PromptAsset

class PromptRegistry:
    """Registry for managing and retrieving PromptAssets."""
    
    def __init__(self):
        self._assets: Dict[str, PromptAsset] = {}
        
    def register(self, asset: PromptAsset) -> None:
        """Registers a PromptAsset."""
        self._assets[asset.id] = asset
        
    def get(self, asset_id: str) -> Optional[PromptAsset]:
        """Retrieves a PromptAsset by ID."""
        return self._assets.get(asset_id)
        
    def list_all(self) -> list[PromptAsset]:
        """Lists all registered PromptAssets."""
        return list(self._assets.values())
        
# Global registry instance
prompt_registry = PromptRegistry()
