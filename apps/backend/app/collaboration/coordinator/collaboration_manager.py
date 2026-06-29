import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.collaboration.session.session_repository import SessionRepository
from app.collaboration.session.collaboration_session import (
    CollaborationSession,
    SessionPhase,
)
from app.collaboration.teams.team_builder import TeamBuilder
from app.collaboration.teams.team_registry import TeamRegistry
from app.collaboration.workspace.workspace_repository import WorkspaceRepository
from app.collaboration.coordinator.delegation_manager import DelegationManager
from app.collaboration.coordinator.negotiation_manager import NegotiationManager
from app.collaboration.coordinator.consensus_manager import (
    ConsensusManager,
    MajorityVote,
)
from app.collaboration.coordinator.conflict_manager import ConflictManager
from app.collaboration.memory.collaboration_memory import CollaborationMemory


class CollaborationManager:
    """
    Central orchestration class for the Collaboration Runtime.
    Supervisor interacts exclusively with this class.
    """

    def __init__(
        self, db: Session, team_registry: TeamRegistry, governance_pipeline=None
    ):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.workspace_repo = WorkspaceRepository(db)
        self.team_builder = TeamBuilder(team_registry)
        self.delegation = DelegationManager()
        self.negotiation = NegotiationManager()
        self.consensus = ConsensusManager(MajorityVote())
        self.conflict = ConflictManager()
        self.memory = CollaborationMemory(db)
        self.governance_pipeline = governance_pipeline

    def create_session(
        self, objective: str, workflow_id: Optional[str] = None
    ) -> CollaborationSession:
        sid = str(uuid.uuid4())
        session = self.session_repo.create_session(sid, objective, workflow_id)
        return session

    def form_team(self, session_id: str) -> CollaborationSession:
        session = self.session_repo.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        self.session_repo.update_phase(session_id, SessionPhase.TEAM_FORMATION)

        team = self.team_builder.build_team(session.objective)
        participants = [a.agent_id for a in team]
        leader = next(
            (a.agent_id for a in team if getattr(a, "assigned_role", None) == "Leader"),
            None,
        )

        updated = self.session_repo.update_session(
            session_id, {"participants": participants, "leader": leader}
        )

        self.session_repo.update_phase(session_id, SessionPhase.PLANNING)
        return updated

    def execute(self, session_id: str) -> None:
        self.session_repo.update_phase(session_id, SessionPhase.EXECUTION)

    async def complete_session(self, session_id: str) -> None:
        self.session_repo.update_phase(session_id, SessionPhase.COMPLETED)
        session = self.session_repo.get_session(session_id)

        if self.governance_pipeline and session:
            from app.governance.context.governance_context import GovernanceContext

            gov_context = GovernanceContext(
                workflow_id=session.workflow_id or f"collab_{session_id}",
                workflow_goal=session.objective,
                collaboration_session_id=session_id,
            )
            self.governance_pipeline.evaluate(gov_context)
            # We don't block the session itself, but the audit records and metrics are updated.

        await self.memory.extract_session_memory(session_id)
