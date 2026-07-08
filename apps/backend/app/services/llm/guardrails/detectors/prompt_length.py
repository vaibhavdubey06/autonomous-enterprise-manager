from typing import List, Optional, Any, Dict

from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.guardrails.base import BaseDetector
from app.services.llm.guardrails.models import GuardrailFinding, Severity

class PromptLengthDetector(BaseDetector):
    def __init__(self, max_length: int = 100000):
        self.max_length = max_length

    @property
    def name(self) -> str:
        return "prompt_length"

    def analyze(self, request: LLMRequest, response: Optional[LLMResponse] = None, context: Optional[Dict[str, Any]] = None) -> List[GuardrailFinding]:
        findings = []
        
        prompt_length = len(request.prompt)
        if prompt_length > self.max_length:
            findings.append(GuardrailFinding(
                detector_name=self.name,
                message=f"Prompt length ({prompt_length}) exceeds maximum allowed length ({self.max_length}).",
                severity=Severity.LOW,
                score=0.2
            ))
            
        return findings
