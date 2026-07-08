import json
from typing import List, Optional, Any, Dict

from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.guardrails.base import BaseDetector
from app.services.llm.guardrails.models import GuardrailFinding, Severity

class JSONValidator(BaseDetector):
    """
    Lightweight JSON structural validator for Guardrails safety.
    Note: SchemaValidatorMiddleware handles application-level Pydantic schema validation.
    This detector only checks if the output is structurally sound JSON when required.
    """
    
    @property
    def name(self) -> str:
        return "json_validator"
        
    @property
    def applies_to_request(self) -> bool:
        return False
        
    @property
    def applies_to_response(self) -> bool:
        return True

    def analyze(self, request: LLMRequest, response: Optional[LLMResponse] = None, context: Optional[Dict[str, Any]] = None) -> List[GuardrailFinding]:
        findings = []
        
        # Only validate if the request explicitly asks for JSON
        if request.schema:
            content = response.content.strip()
            # Strip markdown block if present
            if content.startswith("```json"):
                content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
            content = content.strip()
            
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                findings.append(GuardrailFinding(
                    detector_name=self.name,
                    message=f"Output is not valid JSON structure: {e}",
                    severity=Severity.HIGH,
                    score=1.0
                ))
                
        return findings
