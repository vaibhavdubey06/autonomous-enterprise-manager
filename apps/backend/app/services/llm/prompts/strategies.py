import string
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Optional

from app.services.llm.prompts.models import PromptAsset, CompiledPrompt
from app.services.llm.context.models import EnterpriseContext


class PromptStrategy(ABC):
    """Abstract base class for prompt assembly strategies."""
    
    @abstractmethod
    def assemble(self, asset: PromptAsset, context: EnterpriseContext, variables: Dict[str, Any]) -> CompiledPrompt:
        """Assembles a final CompiledPrompt from an asset, context, and variables."""
        pass


class DefaultStrategy(PromptStrategy):
    """A basic strategy that interpolates variables and appends context at the end."""
    
    def assemble(self, asset: PromptAsset, context: EnterpriseContext, variables: Dict[str, Any]) -> CompiledPrompt:
        # Standard Python string template rendering
        template = string.Template(asset.template)
        try:
            rendered_text = template.safe_substitute(**variables)
        except Exception:
            # Fallback for simple .format or unformatted
            try:
                rendered_text = asset.template.format(**variables)
            except KeyError:
                rendered_text = asset.template

        context_str = context.to_formatted_string()
        if context_str:
            final_text = f"{rendered_text}\n\n{context_str}"
        else:
            final_text = rendered_text
            
        return CompiledPrompt(
            text=final_text,
            asset_id=asset.id,
            variables_injected=variables,
            metadata={"strategy": "default"}
        )


class ChatStrategy(PromptStrategy):
    """A strategy optimized for chat interactions."""
    
    def assemble(self, asset: PromptAsset, context: EnterpriseContext, variables: Dict[str, Any]) -> CompiledPrompt:
        template = string.Template(asset.template)
        try:
            rendered_text = template.safe_substitute(**variables)
        except Exception:
            rendered_text = asset.template
            
        context_str = context.to_formatted_string()
        if context_str:
            final_text = f"System Context:\n{context_str}\n\nInstructions:\n{rendered_text}"
        else:
            final_text = rendered_text
            
        return CompiledPrompt(
            text=final_text,
            asset_id=asset.id,
            variables_injected=variables,
            metadata={"strategy": "chat"}
        )


class PromptStrategyRegistry:
    """Registry for prompt strategies."""
    
    def __init__(self):
        self._strategies: Dict[str, PromptStrategy] = {}
        # Register default strategies
        self.register("default", DefaultStrategy())
        self.register("chat", ChatStrategy())
        
    def register(self, name: str, strategy: PromptStrategy) -> None:
        self._strategies[name] = strategy
        
    def get(self, name: str) -> PromptStrategy:
        return self._strategies.get(name, self._strategies["default"])

strategy_registry = PromptStrategyRegistry()
