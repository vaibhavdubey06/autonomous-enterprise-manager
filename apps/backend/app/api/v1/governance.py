from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter(tags=["governance"])

# We'll mock the dependency injection for the router for now.
# In a real app, this would come from a dependency provider.
from app.governance.pipeline.governance_pipeline import GovernancePipeline
from app.governance.risk.risk_engine import RiskEngine
from app.governance.policy.policy_chain import PolicyChain
from app.governance.policy.policy_engine import SecurityPolicy, FinancialPolicy
from app.governance.compliance.compliance_engine import ComplianceEngine
from app.governance.trust.trust_engine import TrustEngine
from app.governance.approvals.approval_runtime import ApprovalRuntime
from app.governance.audit.audit_manager import AuditManager
from app.governance.services.governance_service import GovernanceService

# Singleton instance for the router
_policy_chain = PolicyChain()
_policy_chain.register_policy(SecurityPolicy())
_policy_chain.register_policy(FinancialPolicy())

_pipeline = GovernancePipeline(
    risk_engine=RiskEngine(),
    policy_chain=_policy_chain,
    compliance_engine=ComplianceEngine(),
    trust_engine=TrustEngine(),
    approval_runtime=ApprovalRuntime(),
    audit_manager=AuditManager(),
)
_service = GovernanceService(_pipeline)


def get_governance_service() -> GovernanceService:
    return _service


class ResolveApprovalRequest(BaseModel):
    approved: bool
    resolved_by: str = "Admin"


@router.get("/pending", response_model=List[Dict[str, Any]])
def get_pending_approvals(service: GovernanceService = Depends(get_governance_service)):
    return [r.dict() for r in service.get_pending_approvals()]


@router.post("/approval/{request_id}/resolve")
def resolve_approval(
    request_id: str,
    req: ResolveApprovalRequest,
    service: GovernanceService = Depends(get_governance_service),
):
    success = service.resolve_approval(request_id, req.approved, req.resolved_by)
    if not success:
        raise HTTPException(
            status_code=404, detail="Approval request not found or not pending"
        )
    return {"status": "success"}


@router.get("/audit/{workflow_id}")
def get_audit_chain(
    workflow_id: str, service: GovernanceService = Depends(get_governance_service)
):
    return service.get_audit_chain(workflow_id)


@router.get("/trust")
def get_trust_scores(service: GovernanceService = Depends(get_governance_service)):
    return service.get_trust_scores()
