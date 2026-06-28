from pydantic import BaseModel, Field
from typing import List, Dict, Any

class DecisionRecord(BaseModel):
    decision_id: str
    topic: str
    alternatives: List[str] = Field(default_factory=list)
    selected_option: str
    reasoning: str
    confidence: float
    participants: List[str] = Field(default_factory=list)
    timestamp: str

class SharedWorkspace(BaseModel):
    """
    Structured Shared Workspace for Collaboration Sessions.
    """
    goals: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    intermediate_findings: List[str] = Field(default_factory=list)
    decisions: List[DecisionRecord] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    reports: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_goal(self, goal: str):
        self.goals.append(goal)
        
    def add_evidence(self, evidence: Dict[str, Any]):
        self.evidence.append(evidence)
        
    def add_decision(self, decision: DecisionRecord):
        self.decisions.append(decision)
