import uuid
from app.workflows.models.workflow import WorkflowStatus
from app.governance.context.governance_context import GovernanceContext
from app.governance.decision.governance_decision import GovernanceDecision
from app.governance.risk.risk_engine import RiskEngine
from app.governance.policy.policy_chain import PolicyChain
from app.governance.compliance.compliance_engine import ComplianceEngine
from app.governance.trust.trust_engine import TrustEngine
from app.governance.approvals.approval_runtime import ApprovalRuntime
from app.governance.audit.audit_manager import AuditManager


class GovernancePipeline:
    def __init__(
        self,
        risk_engine: RiskEngine,
        policy_chain: PolicyChain,
        compliance_engine: ComplianceEngine,
        trust_engine: TrustEngine,
        approval_runtime: ApprovalRuntime,
        audit_manager: AuditManager,
    ):
        self.risk = risk_engine
        self.policy = policy_chain
        self.compliance = compliance_engine
        self.trust = trust_engine
        self.approvals = approval_runtime
        self.audit = audit_manager

    def evaluate(self, context: GovernanceContext) -> GovernanceDecision:
        decision_id = str(uuid.uuid4())

        # 1. Risk
        risk_level = self.risk.evaluate_risk(context)
        self.audit.log_event(
            context.workflow_id, "RISK_EVALUATED", {"risk_level": risk_level}
        )

        # 2. Compliance
        compliance_results = self.compliance.run_compliance_checks(context)
        if compliance_results:
            self.audit.log_event(
                context.workflow_id,
                "COMPLIANCE_DETECTED",
                {"results": compliance_results},
            )

        # 3. Policy
        policy_results = self.policy.evaluate_all(context)
        self.audit.log_event(
            context.workflow_id,
            "POLICY_EVALUATED",
            {"results": [p.dict() for p in policy_results]},
        )

        # 4. Trust
        trust_score = self.trust.evaluate_trust(context)
        self.audit.log_event(
            context.workflow_id, "TRUST_EVALUATED", {"trust_score": trust_score}
        )

        # 5. Determine State
        blocked = False
        requires_approval = False
        reason = "All checks passed."

        # Block if any policy strictly blocks without allowing approval
        for p in policy_results:
            if not p.allowed:
                requires_approval = True
                reason = p.reason
                break

        # Block if compliance detected issues
        if compliance_results:
            requires_approval = True
            reason = "Compliance violation detected."

        if risk_level in ["HIGH", "CRITICAL"]:
            requires_approval = True
            reason = f"Risk level {risk_level} requires approval."

        if trust_score < 0.5:
            blocked = True
            reason = f"Trust score {trust_score} is below threshold."

        if blocked:
            next_state = WorkflowStatus.BLOCKED
        elif requires_approval:
            next_state = WorkflowStatus.WAITING_FOR_APPROVAL
            self.approvals.request_approval(
                context.workflow_id, reason, context.task_id
            )
        else:
            next_state = WorkflowStatus.RUNNING

        decision = GovernanceDecision(
            decision_id=decision_id,
            allowed=not blocked and not requires_approval,
            blocked=blocked,
            approval_required=requires_approval,
            risk_level=risk_level,
            trust_score=trust_score,
            policy_results=[p.dict() for p in policy_results],
            compliance_results=compliance_results,
            reason=reason,
            next_state=next_state,
        )

        self.audit.log_event(
            context.workflow_id, "GOVERNANCE_DECISION", decision.dict()
        )

        return decision
