from typing import List, Optional, Any, Dict

from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.guardrails.base import BaseDetector
from app.services.llm.guardrails.models import GuardrailFinding, Severity

class HallucinationValidator(BaseDetector):
    """
    Placeholder for future LLM-based Hallucination detection.
    """
    @property
    def name(self) -> str:
        return "hallucination"

    @property
    def applies_to_request(self) -> bool:
        return False
        
    @property
    def applies_to_response(self) -> bool:
        return True

    def analyze(self, request: LLMRequest, response: Optional[LLMResponse] = None, context: Optional[Dict[str, Any]] = None) -> List[GuardrailFinding]:
        # Implement interface only. Do NOT build LLM-based hallucination detection yet.
        return []
