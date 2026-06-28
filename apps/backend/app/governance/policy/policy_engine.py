from abc import ABC, abstractmethod
from app.governance.context.governance_context import GovernanceContext
from app.governance.policy.policy_models import PolicyEvaluationResult

class BasePolicy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def evaluate(self, context: GovernanceContext) -> PolicyEvaluationResult:
        pass

class SecurityPolicy(BasePolicy):
    @property
    def name(self) -> str:
        return "Security Policy"

    def evaluate(self, context: GovernanceContext) -> PolicyEvaluationResult:
        if context.capability_name == "delete_database":
            return PolicyEvaluationResult(
                policy_name=self.name,
                allowed=False,
                requires_approval=True,
                reason="Destructive operations require explicit approval."
            )
        return PolicyEvaluationResult(policy_name=self.name, allowed=True)

class FinancialPolicy(BasePolicy):
    @property
    def name(self) -> str:
        return "Financial Policy"

    def evaluate(self, context: GovernanceContext) -> PolicyEvaluationResult:
        if "budget" in context.workflow_goal.lower():
            return PolicyEvaluationResult(
                policy_name=self.name,
                allowed=False,
                requires_approval=True,
                reason="Budget modifications require CFO approval."
            )
        return PolicyEvaluationResult(policy_name=self.name, allowed=True)
