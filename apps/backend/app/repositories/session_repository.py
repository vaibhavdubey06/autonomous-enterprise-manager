import uuid
from typing import List, Optional
from sqlalchemy.orm import Session as DBSession

from app.models.memory import Session


class SessionRepository:
    """
    Repository for managing Sessions in PostgreSQL.
    """

    def __init__(self, db: DBSession):
        self.db = db

    def create_session(self, user_id: str) -> Session:
        db_session = Session(user_id=user_id)
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def get_session(self, session_id: str) -> Optional[Session]:
        try:
            uid = uuid.UUID(session_id)
        except ValueError:
            return None
        return self.db.query(Session).filter(Session.id == uid).first()

    def list_sessions(self, user_id: str) -> List[Session]:
        return (
            self.db.query(Session)
            .filter(Session.user_id == user_id)
            .order_by(Session.updated_at.desc())
            .all()
        )
