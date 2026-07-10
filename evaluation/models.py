from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    SKIPPED = "SKIPPED"
    NOT_REQUIRED = "NOT_REQUIRED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class FailureCategory(str, Enum):
    PROVIDER = "PROVIDER"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    PLANNER = "PLANNER"
    ROUTING = "ROUTING"
    KNOWLEDGE = "KNOWLEDGE"
    MEMORY = "MEMORY"
    GUARDRAIL = "GUARDRAIL"
    TOOL = "TOOL"
    REFLECTION = "REFLECTION"
    UNKNOWN = "UNKNOWN"
    NONE = "NONE"


class MetricState(str, Enum):
    VALID = "VALID"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_EXECUTED = "NOT_EXECUTED"
    SKIPPED = "SKIPPED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ScoreModel(BaseModel):
    value: float = 0.0
    state: MetricState = MetricState.NOT_EXECUTED
    confidence: str = "LOW"


class EvaluationResult(BaseModel):
    """Normalized structured data representing a single scenario execution."""

    scenario_id: str
    query: str
    ground_truth: str

    expected_capability: str = "unknown"
    expected_agent: str = "unknown"
    expected_provider: str = "unknown"
    expected_tools: List[str] = Field(default_factory=list)
    expected_guardrails: List[str] = Field(default_factory=list)

    success: bool = False
    execution_status: ExecutionStatus = ExecutionStatus.SKIPPED
    failure_category: FailureCategory = FailureCategory.NONE
    failure_reason: Optional[str] = None
    retry_count: int = 0
    provider: Optional[str] = None
    error: Optional[str] = None

    actual_answer: str = ""
    latency_ms: float = 0.0

    traces: List[Dict[str, Any]] = Field(default_factory=list)
