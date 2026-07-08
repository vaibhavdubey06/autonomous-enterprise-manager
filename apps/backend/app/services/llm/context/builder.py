from typing import Any, Dict, List
from app.services.llm.models import LLMRequest
from app.services.llm.context.models import EnterpriseContext

class ContextBuilder:
    """Builds an EnterpriseContext structured object from an LLMRequest and other sources."""
    
    def build_context(self, request: LLMRequest, additional_metadata: Dict[str, Any]) -> EnterpriseContext:
        """
        Gathers contextual information into a structured model.
        In a full implementation, this would query MemoryService, Governance, etc.
        For now, it bridges the LLMRequest and metadata into the EnterpriseContext.
        """
        ctx = EnterpriseContext()
        
        # Pull legacy string context array from LLMRequest
        if request.context:
            ctx.retrieved_documents.extend(request.context)
            
        # Extract from Request Metadata
        if "conversation_history" in request.metadata:
            ctx.conversation_history = request.metadata["conversation_history"]
        if "semantic_memory" in request.metadata:
            ctx.semantic_memory = request.metadata["semantic_memory"]
        if "workflow_state" in request.metadata:
            ctx.workflow_state = request.metadata["workflow_state"]
        if "execution_context" in request.metadata:
            ctx.execution_context = request.metadata["execution_context"]
        if "governance_policies" in request.metadata:
            ctx.governance_policies = request.metadata["governance_policies"]
        if "agent_profile" in request.metadata:
            ctx.agent_profile = request.metadata["agent_profile"]
            
        # Extract from pipeline metadata (additional_metadata)
        for key in ["workflow_state", "execution_context", "agent_profile"]:
            if key in additional_metadata:
                setattr(ctx, key, additional_metadata[key])

        return ctx
