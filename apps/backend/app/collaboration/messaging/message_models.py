from sqlalchemy import Column, String, JSON, DateTime, Enum, ForeignKey
import enum
import datetime
from app.core.database import Base

class MessageType(str, enum.Enum):
    QUESTION = "Question"
    ANSWER = "Answer"
    PROPOSAL = "Proposal"
    COUNTER_PROPOSAL = "Counter Proposal"
    DECISION = "Decision"
    APPROVAL = "Approval"
    NOTIFICATION = "Notification"
    WARNING = "Warning"
    EVIDENCE = "Evidence"
    INFORMATION = "Information"

class CollaborationMessage(Base):
    __tablename__ = "collaboration_messages"

    message_id = Column(String, primary_key=True, index=True)
    collaboration_id = Column(String, ForeignKey("collaboration_sessions.session_id"), index=True)
    workflow_id = Column(String, nullable=True)
    
    sender = Column(String, nullable=False)
    receiver = Column(String, nullable=True) # None for broadcast
    
    message_type = Column(Enum(MessageType), default=MessageType.INFORMATION)
    priority = Column(String, default="Normal")
    
    payload = Column(JSON, default=dict)
    status = Column(String, default="Sent")
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
