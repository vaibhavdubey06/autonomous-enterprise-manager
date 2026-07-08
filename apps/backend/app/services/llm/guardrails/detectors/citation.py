from typing import List, Optional, Any, Dict
import re

from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.guardrails.base import BaseDetector
from app.services.llm.guardrails.models import GuardrailFinding, Severity

class CitationPresenceValidator(BaseDetector):
    @property
    def name(self) -> str:
        return "citation_presence"

    @property
    def applies_to_request(self) -> bool:
        return False
        
    @property
    def applies_to_response(self) -> bool:
        return True

    def analyze(self, request: LLMRequest, response: Optional[LLMResponse] = None, context: Optional[Dict[str, Any]] = None) -> List[GuardrailFinding]:
        findings = []
        
        # If the request context implies citations are required, check for bracketed citations like [1]
        # In a real enterprise system, this might check specific metadata tags
        if "cite your sources" in request.prompt.lower():
            if not re.search(r"\[\d+\]", response.content):
                findings.append(GuardrailFinding(
                    detector_name=self.name,
                    message="Required citations are missing from the response.",
                    severity=Severity.MEDIUM,
                    score=0.7
                ))
                
        return findings
