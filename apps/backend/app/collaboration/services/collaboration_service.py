from sqlalchemy.orm import Session
from app.collaboration.coordinator.collaboration_manager import CollaborationManager
from app.collaboration.teams.team_registry import TeamRegistry
from app.collaboration.teams.agent_roles import AgentCollaborationProfile
from app.collaboration.schemas.collaboration import (
    CollaborationSessionCreate,
    DelegateRequest,
    NegotiateRequest,
    ConsensusRequest,
    ConflictRequest,
)
from app.collaboration.session.collaboration_session import CollaborationSession


class CollaborationService:
    def __init__(self, db: Session):
        self.db = db
        # In a real app, registry should be singleton or populated from DB
        self.registry = TeamRegistry()
        self.registry.register_agent(
            AgentCollaborationProfile(
                agent_id="CTO",
                expertise=["Architecture", "Engineering"],
                capabilities=[],
                confidence=0.9,
                workload=1,
                availability=True,
            )
        )
        self.registry.register_agent(
            AgentCollaborationProfile(
                agent_id="CFO",
                expertise=["Finance", "Cost"],
                capabilities=[],
                confidence=0.9,
                workload=1,
                availability=True,
            )
        )
        self.registry.register_agent(
            AgentCollaborationProfile(
                agent_id="HR",
                expertise=["HR"],
                capabilities=[],
                confidence=0.9,
                workload=1,
                availability=True,
            )
        )
        self.manager = CollaborationManager(db, self.registry)

    def create_session(self, req: CollaborationSessionCreate) -> CollaborationSession:
        return self.manager.create_session(req.objective, req.workflow_id)

    def get_session(self, session_id: str) -> CollaborationSession:
        return self.manager.session_repo.get_session(session_id)

    def form_team(self, session_id: str) -> CollaborationSession:
        return self.manager.form_team(session_id)

    def delegate(self, session_id: str, req: DelegateRequest):
        return self.manager.delegation.delegate_task(req.description, req.assignee)

    def negotiate(self, session_id: str, req: NegotiateRequest):
        nid = self.manager.negotiation.start_negotiation(req.topic)
        prop = self.manager.negotiation.add_proposal(nid, req.proposer, req.content)
        return {"negotiation_id": nid, "proposal_id": prop.proposal_id}

    def start_consensus(self, session_id: str, req: ConsensusRequest):
        self.manager.consensus.start_consensus(req.topic, [req.option, "Alternate"])
        self.manager.consensus.cast_vote(req.topic, req.agent_id, req.option)
        return {"status": "Vote cast"}

    def raise_conflict(self, session_id: str, req: ConflictRequest):
        import uuid

        cid = str(uuid.uuid4())
        return self.manager.conflict.raise_conflict(
            cid, req.topic, req.participants, req.severity
        )
