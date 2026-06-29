from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.collaboration.session.collaboration_session import (
    CollaborationSession,
    SessionPhase,
)
from app.collaboration.session.session_state_machine import SessionStateMachine
from datetime import datetime


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self, session_id: str, objective: str, workflow_id: Optional[str] = None
    ) -> CollaborationSession:
        cs = CollaborationSession(
            session_id=session_id,
            objective=objective,
            workflow_id=workflow_id,
            current_phase=SessionPhase.CREATED,
        )
        self.db.add(cs)
        self.db.commit()
        self.db.refresh(cs)
        return cs

    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        return (
            self.db.query(CollaborationSession)
            .filter(CollaborationSession.session_id == session_id)
            .first()
        )

    def update_phase(
        self, session_id: str, target_phase: SessionPhase
    ) -> CollaborationSession:
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        SessionStateMachine.validate_transition(session.current_phase, target_phase)
        session.current_phase = target_phase

        if target_phase in (
            SessionPhase.COMPLETED,
            SessionPhase.FAILED,
            SessionPhase.CANCELLED,
        ):
            session.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)
        return session

    def update_session(
        self, session_id: str, updates: Dict[str, Any]
    ) -> CollaborationSession:
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        for k, v in updates.items():
            if hasattr(session, k) and k != "current_phase":
                setattr(session, k, v)

        self.db.commit()
        self.db.refresh(session)
        return session
