from pydantic import BaseModel
from typing import Dict, Any


class PolicyEvaluationResult(BaseModel):
    policy_name: str
    allowed: bool
    requires_approval: bool = False
    reason: str = ""
    metadata: Dict[str, Any] = {}
