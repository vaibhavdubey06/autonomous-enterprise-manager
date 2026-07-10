import re
from typing import List, Optional, Any, Dict

from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.guardrails.base import BaseDetector
from app.services.llm.guardrails.models import GuardrailFinding, Severity


class PIIDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "pii"

    def analyze(
        self,
        request: LLMRequest,
        response: Optional[LLMResponse] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[GuardrailFinding]:
        findings = []

        pii_patterns = [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            r"\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",  # Phone (US)
            r"\b(?:\d[ -]*?){13,16}\b",  # Credit card
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        ]

        text_to_analyze = request.prompt

        for pattern in pii_patterns:
            if re.search(pattern, text_to_analyze):
                findings.append(
                    GuardrailFinding(
                        detector_name=self.name,
                        message="Detected potential PII (Personally Identifiable Information) in prompt.",
                        severity=Severity.MEDIUM,
                        score=0.6,
                    )
                )
                break

        return findings
