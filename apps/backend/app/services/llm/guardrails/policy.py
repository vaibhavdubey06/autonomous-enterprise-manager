from typing import Dict
from app.services.llm.guardrails.models import PolicyAction


class GuardrailPolicy:
    """
    Configurable policy that maps detector names to PolicyActions.
    If a detector is not mapped, it defaults to ALLOW or AUDIT_ONLY based on configuration.
    """

    def __init__(
        self,
        rules: Dict[str, PolicyAction] = None,
        default_action: PolicyAction = PolicyAction.ALLOW,
    ):
        self.rules = rules or {
            "prompt_injection": PolicyAction.BLOCK,
            "jailbreak": PolicyAction.BLOCK,
            "secrets": PolicyAction.BLOCK,
            "pii": PolicyAction.WARN,
            "prompt_length": PolicyAction.ALLOW,  # Maybe warn, but allow by default
            "json_validator": PolicyAction.BLOCK,
            "citation_presence": PolicyAction.WARN,
            "response_length": PolicyAction.ALLOW,
            "hallucination": PolicyAction.AUDIT_ONLY,
        }
        self.default_action = default_action

    def get_action(self, detector_name: str) -> PolicyAction:
        return self.rules.get(detector_name, self.default_action)
