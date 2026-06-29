from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ExecutiveResult(BaseModel):
    """
    Standardized result structure returned by any Executive Agent.
    """

    task_id: str
    agent: str
    summary: str
    reasoning: str
    recommendations: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    execution_metrics: Dict[str, Any] = Field(default_factory=dict)
