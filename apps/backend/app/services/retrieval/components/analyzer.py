from typing import Dict, Any
from app.services.capability.service import CapabilityInferenceService
from app.services.retrieval.models import QueryContext


class QueryAnalyzer:
    def __init__(self):
        self.capability_service = CapabilityInferenceService()

    def analyze(self, raw_query: str, filters: Dict[str, Any]) -> QueryContext:
        """
        Determine intent, required capability, and document type using the
        existing Capability Inference Service and rule-based workflow classification.
        """
        # 1. Reuse Capability Inference
        decision = self.capability_service.infer(raw_query)
        primary_cap = decision.required_capability

        # 2. Rule-based workflow classification
        intent = "general_knowledge"
        q_lower = raw_query.lower()
        if any(w in q_lower for w in ["how to", "guide", "tutorial", "step"]):
            intent = "how_to"
        elif any(
            w in q_lower for w in ["error", "exception", "bug", "fail", "traceback"]
        ):
            intent = "troubleshooting"
        elif any(w in q_lower for w in ["architecture", "design", "system"]):
            intent = "architecture"
        elif any(w in q_lower for w in ["code", "function", "class", "api"]):
            intent = "code_search"

        # 3. Assess complexity
        is_complex = len(raw_query.split()) > 15 or intent in [
            "architecture",
            "troubleshooting",
        ]

        # 4. We defer Dynamic Top K computation to the Strategy component, but set a default here
        from .dynamic_k import compute_dynamic_k

        top_k = compute_dynamic_k(intent, is_complex, decision.confidence)

        return QueryContext(
            raw_query=raw_query,
            intent=intent,
            inferred_capabilities=[primary_cap],
            filters=filters,
            dynamic_top_k=top_k,
            is_complex=is_complex,
        )
