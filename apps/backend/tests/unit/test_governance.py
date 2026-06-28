import pytest
from app.governance.pipeline.governance_pipeline import GovernancePipeline
from app.governance.risk.risk_engine import RiskEngine
from app.governance.policy.policy_chain import PolicyChain
from app.governance.policy.policy_engine import SecurityPolicy, FinancialPolicy
from app.governance.compliance.compliance_engine import ComplianceEngine
from app.governance.trust.trust_engine import TrustEngine
from app.governance.approvals.approval_runtime import ApprovalRuntime
from app.governance.audit.audit_manager import AuditManager
from app.governance.context.governance_context import GovernanceContext
from app.workflows.models.workflow import WorkflowStatus

@pytest.fixture
def pipeline():
    policy_chain = PolicyChain()
    policy_chain.register_policy(SecurityPolicy())
    policy_chain.register_policy(FinancialPolicy())
    
    return GovernancePipeline(
        risk_engine=RiskEngine(),
        policy_chain=policy_chain,
        compliance_engine=ComplianceEngine(),
        trust_engine=TrustEngine(),
        approval_runtime=ApprovalRuntime(),
        audit_manager=AuditManager()
    )

def test_scenario_1_high_risk_deployment(pipeline):
    context = GovernanceContext(
        workflow_id="wf_123",
        workflow_goal="Deploy to production",
        capability_name="deploy_production"
    )
    decision = pipeline.evaluate(context)
    
    assert decision.risk_level == "CRITICAL"
    assert decision.approval_required is True
    assert decision.next_state == WorkflowStatus.WAITING_FOR_APPROVAL
    
    # Resolve approval
    requests = pipeline.approvals.get_pending_requests()
    assert len(requests) == 1
    
    req = requests[0]
    pipeline.approvals.resolve_request(req.request_id, True, "Admin")
    
    resolved = pipeline.approvals.requests[req.request_id]
    assert resolved.status == "APPROVED"

def test_scenario_2_low_risk_auto_approve(pipeline):
    context = GovernanceContext(
        workflow_id="wf_124",
        workflow_goal="Review repository code",
        capability_name="github_read"
    )
    decision = pipeline.evaluate(context)
    
    assert decision.risk_level == "LOW"
    assert decision.approval_required is False
    assert decision.next_state == WorkflowStatus.RUNNING

def test_scenario_3_compliance_pii(pipeline):
    context = GovernanceContext(
        workflow_id="wf_125",
        workflow_goal="Process customer social security numbers",
        capability_name="read_file"
    )
    decision = pipeline.evaluate(context)
    
    assert len(decision.compliance_results) > 0
    assert decision.compliance_results[0]["detector"] == "PII Detector"
    assert decision.approval_required is True
    assert decision.next_state == WorkflowStatus.WAITING_FOR_APPROVAL

def test_scenario_4_policy_conflict_trust_failure(pipeline):
    context = GovernanceContext(
        workflow_id="wf_126",
        workflow_goal="Delete database completely",
        capability_name="delete_database",
        executive_agent="delete_database" # Forcing trust to 0.1
    )
    decision = pipeline.evaluate(context)
    
    assert decision.trust_score < 0.5
    assert decision.blocked is True
    assert decision.next_state == WorkflowStatus.BLOCKED
