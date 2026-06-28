from pydantic import BaseModel
from typing import List, Optional
from app.collaboration.session.collaboration_session import SessionPhase

class CollaborationSessionCreate(BaseModel):
    objective: str
    workflow_id: Optional[str] = None
    
class CollaborationSessionResponse(BaseModel):
    session_id: str
    objective: str
    workflow_id: Optional[str]
    current_phase: SessionPhase
    participants: List[str]
    leader: Optional[str]

class DelegateRequest(BaseModel):
    description: str
    assignee: Optional[str] = None
    
class NegotiateRequest(BaseModel):
    topic: str
    proposer: str
    content: str
    
class ConsensusRequest(BaseModel):
    topic: str
    agent_id: str
    option: str
    
class ConflictRequest(BaseModel):
    topic: str
    participants: List[str]
    severity: str = "Medium"
