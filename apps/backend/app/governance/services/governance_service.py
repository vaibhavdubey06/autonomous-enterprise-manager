from typing import List, Dict, Any
from app.governance.pipeline.governance_pipeline import GovernancePipeline
from app.governance.approvals.approval_runtime import ApprovalRequest


class GovernanceService:
    def __init__(self, pipeline: GovernancePipeline):
        self.pipeline = pipeline

    def get_pending_approvals(self) -> List[ApprovalRequest]:
        return self.pipeline.approvals.get_pending_requests()

    def resolve_approval(
        self, request_id: str, approved: bool, resolved_by: str
    ) -> bool:
        req = self.pipeline.approvals.resolve_request(request_id, approved, resolved_by)
        return req is not None

    def get_audit_chain(self, workflow_id: str) -> List[Dict[str, Any]]:
        return [r.dict() for r in self.pipeline.audit.get_audit_chain(workflow_id)]

    def get_trust_scores(self) -> Dict[str, float]:
        return self.pipeline.trust.trust_scores
