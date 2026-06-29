from pydantic import BaseModel
from typing import List, Dict, Any
from app.workflows.models.workflow import WorkflowStatus


class GovernanceDecision(BaseModel):
    decision_id: str
    allowed: bool = False
    blocked: bool = False
    approval_required: bool = False

    risk_level: str = "UNKNOWN"
    trust_score: float = 0.0

    policy_results: List[Dict[str, Any]] = []
    compliance_results: List[Dict[str, Any]] = []

    audit_required: bool = True
    recommendations: List[str] = []
    reason: str = ""

    next_state: WorkflowStatus = WorkflowStatus.RUNNING
