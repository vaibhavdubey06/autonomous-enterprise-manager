import re
from typing import List, Optional, Any, Dict

from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.guardrails.base import BaseDetector
from app.services.llm.guardrails.models import GuardrailFinding, Severity


class JailbreakDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "jailbreak"

    def analyze(
        self,
        request: LLMRequest,
        response: Optional[LLMResponse] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[GuardrailFinding]:
        findings = []

        jailbreak_patterns = [
            r"(?i)DAN",
            r"(?i)do anything now",
            r"(?i)always provide an answer",
            r"(?i)you are now free",
            r"(?i)break the rules",
            r"(?i)without limits",
            r"(?i)override safety",
            r"(?i)ignore safety",
        ]

        text_to_analyze = request.prompt

        for pattern in jailbreak_patterns:
            if re.search(pattern, text_to_analyze):
                findings.append(
                    GuardrailFinding(
                        detector_name=self.name,
                        message="Detected potential jailbreak pattern.",
                        severity=Severity.HIGH,
                        score=0.9,
                    )
                )
                break

        return findings
