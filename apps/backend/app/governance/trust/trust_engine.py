from typing import Dict
from app.governance.context.governance_context import GovernanceContext


class TrustEngine:
    def __init__(self):
        # Mocked trust scores. In production, this would be backed by DB/Memory.
        self.trust_scores: Dict[str, float] = {
            "CTO": 0.95,
            "CFO": 0.98,
            "CEO": 0.99,
            "delete_database": 0.1,
            "deploy_production": 0.5,
        }

    def evaluate_trust(self, context: GovernanceContext) -> float:
        """
        Returns a trust score between 0.0 and 1.0 based on the agent and capability.
        """
        base_trust = 0.8  # Default trust

        if context.executive_agent and context.executive_agent in self.trust_scores:
            base_trust = self.trust_scores[context.executive_agent]

        if context.capability_name and context.capability_name in self.trust_scores:
            cap_trust = self.trust_scores[context.capability_name]
            # Capability trust heavily penalizes overall trust if low
            base_trust = min(base_trust, cap_trust)

        return base_trust
