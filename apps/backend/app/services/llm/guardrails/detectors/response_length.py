from typing import List, Optional, Any, Dict

from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.guardrails.base import BaseDetector
from app.services.llm.guardrails.models import GuardrailFinding, Severity

class ResponseLengthValidator(BaseDetector):
    def __init__(self, max_length: int = 50000):
        self.max_length = max_length

    @property
    def name(self) -> str:
        return "response_length"

    @property
    def applies_to_request(self) -> bool:
        return False
        
    @property
    def applies_to_response(self) -> bool:
        return True

    def analyze(self, request: LLMRequest, response: Optional[LLMResponse] = None, context: Optional[Dict[str, Any]] = None) -> List[GuardrailFinding]:
        findings = []
        
        response_length = len(response.content)
        if response_length > self.max_length:
            findings.append(GuardrailFinding(
                detector_name=self.name,
                message=f"Response length ({response_length}) exceeds maximum allowed length ({self.max_length}).",
                severity=Severity.LOW,
                score=0.2
            ))
            
        return findings
