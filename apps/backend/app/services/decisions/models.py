from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid
import datetime

class DecisionType(str, Enum):
    PLANNING = "PLANNING"
    ROUTING = "ROUTING"
    RETRIEVAL = "RETRIEVAL"
    RECOVERY = "RECOVERY"
    CAPABILITY = "CAPABILITY"

class Explanation(BaseModel):
    summary: str
    factors: List[str] = Field(default_factory=list)

class DecisionRecord(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: Optional[str] = None
    trace_id: Optional[str] = None
    decision_type: DecisionType
    component: str
    selected_option: str
    alternative_options: List[str] = Field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0
    risk: float = 0.0        # 0.0 to 1.0
    reasoning: Explanation
    latency_ms: float = 0.0
    cost: float = 0.0
    
    # Execution outcomes (populated later by reflection)
    success: Optional[bool] = None
    final_outcome: Optional[str] = None
    
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    
    context: Dict[str, Any] = Field(default_factory=dict)
