from typing import List, Dict, Optional
from pydantic import BaseModel
import uuid
import datetime

import enum

class NegotiationStatus(str, enum.Enum):
    OPEN = "Open"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"

class Proposal(BaseModel):
    proposal_id: str
    topic: str
    proposer: str
    content: str
    created_at: str

class NegotiationRecord(BaseModel):
    negotiation_id: str
    topic: str
    proposals: List[Proposal] = []
    status: NegotiationStatus = NegotiationStatus.OPEN
    final_proposal_id: Optional[str] = None

class NegotiationManager:
    def __init__(self):
        self.negotiations: Dict[str, NegotiationRecord] = {}

    def start_negotiation(self, topic: str) -> str:
        nid = str(uuid.uuid4())
        self.negotiations[nid] = NegotiationRecord(
            negotiation_id=nid,
            topic=topic
        )
        return nid

    def add_proposal(self, negotiation_id: str, proposer: str, content: str) -> Proposal:
        if negotiation_id not in self.negotiations:
            raise ValueError("Negotiation not found")
            
        proposal = Proposal(
            proposal_id=str(uuid.uuid4()),
            topic=self.negotiations[negotiation_id].topic,
            proposer=proposer,
            content=content,
            created_at=datetime.datetime.utcnow().isoformat()
        )
        self.negotiations[negotiation_id].proposals.append(proposal)
        return proposal

    def accept_proposal(self, negotiation_id: str, proposal_id: str) -> NegotiationRecord:
        if negotiation_id not in self.negotiations:
            raise ValueError("Negotiation not found")
        
        neg = self.negotiations[negotiation_id]
        neg.status = NegotiationStatus.ACCEPTED
        neg.final_proposal_id = proposal_id
        return neg

    def reject_negotiation(self, negotiation_id: str) -> NegotiationRecord:
        if negotiation_id not in self.negotiations:
            raise ValueError("Negotiation not found")
        
        neg = self.negotiations[negotiation_id]
        neg.status = NegotiationStatus.REJECTED
        return neg
