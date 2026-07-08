import re
from typing import List, Optional, Any, Dict

from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.guardrails.base import BaseDetector
from app.services.llm.guardrails.models import GuardrailFinding, Severity

class PromptInjectionDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "prompt_injection"

    def analyze(self, request: LLMRequest, response: Optional[LLMResponse] = None, context: Optional[Dict[str, Any]] = None) -> List[GuardrailFinding]:
        findings = []
        
        # Extremely basic heuristics for prompt injection.
        injection_patterns = [
            r"(?i)ignore previous instructions",
            r"(?i)ignore all previous",
            r"(?i)system prompt",
            r"(?i)developer instructions",
            r"(?i)forget everything",
            r"(?i)act as",
            r"(?i)disregard previous",
            r"(?i)bypass restrictions"
        ]
        
        text_to_analyze = request.prompt
        
        for pattern in injection_patterns:
            if re.search(pattern, text_to_analyze):
                findings.append(GuardrailFinding(
                    detector_name=self.name,
                    message=f"Detected potential prompt injection pattern: {pattern}",
                    severity=Severity.HIGH,
                    score=0.9
                ))
                # Break early to avoid duplicate findings for the same core issue
                break
                
        return findings
