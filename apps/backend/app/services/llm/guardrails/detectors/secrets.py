import re
from typing import List, Optional, Any, Dict

from app.services.llm.models import LLMRequest, LLMResponse
from app.services.llm.guardrails.base import BaseDetector
from app.services.llm.guardrails.models import GuardrailFinding, Severity


class SecretDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "secrets"

    def analyze(
        self,
        request: LLMRequest,
        response: Optional[LLMResponse] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[GuardrailFinding]:
        findings = []

        secret_patterns = [
            r"(?i)(?:api_?key|access_?token|secret_?key)[\s=:]+[\"']?[A-Za-z0-9_\-]{16,}[\"']?",
            r"(?i)AKIA[0-9A-Z]{16}",  # AWS access key
            r"(?i)eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",  # JWT
            r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",  # Private keys
        ]

        text_to_analyze = request.prompt

        for pattern in secret_patterns:
            if re.search(pattern, text_to_analyze):
                findings.append(
                    GuardrailFinding(
                        detector_name=self.name,
                        message="Detected potential secret or credential in prompt.",
                        severity=Severity.CRITICAL,
                        score=1.0,
                    )
                )
                break

        return findings
