from typing import Dict, Any

from app.services.llm.models import LLMRequest
from app.services.llm.context.models import EnterpriseContext
from app.services.llm.prompts.models import PromptAsset, CompiledPrompt
from app.services.llm.prompts.registry import prompt_registry
from app.services.llm.prompts.strategies import strategy_registry

class PromptCompiler:
    """Compiles prompt assets and context into a final LLM-ready string."""
    
    def compile(self, request: LLMRequest, context: EnterpriseContext, variables: Dict[str, Any] = None) -> CompiledPrompt:
        """
        Compiles the final prompt.
        If request.metadata["template_id"] is set, uses the registry.
        Otherwise, creates an anonymous asset from request.prompt.
        """
        variables = variables or {}
        
        # Merge any request-level variables
        req_vars = request.metadata.get("variables", {})
        variables.update(req_vars)
        
        template_id = request.metadata.get("template_id")
        
        if template_id:
            asset = prompt_registry.get(template_id)
            if not asset:
                raise ValueError(f"PromptAsset with id '{template_id}' not found in registry.")
        else:
            # Create an anonymous asset from the raw prompt for backward compatibility
            asset = PromptAsset(
                id="anonymous",
                description="Anonymous prompt from raw string.",
                template=request.prompt
            )
            
        strategy_name = request.metadata.get("prompt_strategy", "default")
        strategy = strategy_registry.get(strategy_name)
        
        compiled = strategy.assemble(asset, context, variables)
        return compiled
