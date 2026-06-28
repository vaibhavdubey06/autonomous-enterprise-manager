from typing import List
from app.governance.context.governance_context import GovernanceContext
from app.governance.policy.policy_engine import BasePolicy
from app.governance.policy.policy_models import PolicyEvaluationResult

class PolicyChain:
    def __init__(self):
        self.policies: List[BasePolicy] = []

    def register_policy(self, policy: BasePolicy):
        self.policies.append(policy)

    def evaluate_all(self, context: GovernanceContext) -> List[PolicyEvaluationResult]:
        results = []
        for policy in self.policies:
            res = policy.evaluate(context)
            results.append(res)
            # Short-circuit logic can be added here if a policy explicitly blocks without approval.
            # For now, we evaluate all to generate a comprehensive report.
        return results
