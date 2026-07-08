from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class PolicyAction(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"
    AUDIT_ONLY = "AUDIT_ONLY"

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class GuardrailFinding(BaseModel):
    detector_name: str
    message: str
    severity: Severity
    score: float = 0.0  # Optional continuous score 0.0-1.0
    action: PolicyAction = PolicyAction.ALLOW
    details: Dict[str, Any] = Field(default_factory=dict)

class GuardrailResult(BaseModel):
    action: PolicyAction = PolicyAction.ALLOW
    findings: List[GuardrailFinding] = Field(default_factory=list)
    risk_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
