from sqlalchemy import Column, String, JSON, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
import datetime
from app.core.database import Base

class SessionPhase(str, enum.Enum):
    CREATED = "Created"
    PLANNING = "Planning"
    TEAM_FORMATION = "Team Formation"
    DELEGATION = "Delegation"
    EXECUTION = "Execution"
    NEGOTIATION = "Negotiation"
    CONSENSUS = "Consensus"
    VERIFICATION = "Verification"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    FAILED = "Failed"

class CollaborationSession(Base):
    __tablename__ = "collaboration_sessions"

    session_id = Column(String, primary_key=True, index=True)
    workflow_id = Column(String, nullable=True) # Optional link to a workflow
    objective = Column(String, nullable=False)
    
    participants = Column(JSON, default=list) # List of agent names/IDs
    leader = Column(String, nullable=True)
    
    current_phase = Column(Enum(SessionPhase), default=SessionPhase.CREATED)
    
    # Workspace and state fields stored as JSON for simplicity, or we can use relations
    shared_workspace = Column(JSON, default=dict)
    decisions = Column(JSON, default=list)
    conflicts = Column(JSON, default=list)
    negotiations = Column(JSON, default=list)
    
    audit_log = Column(JSON, default=list)
    metrics = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
