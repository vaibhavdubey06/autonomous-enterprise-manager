from sqlalchemy.orm import Session
from app.collaboration.session.collaboration_session import CollaborationSession
from app.collaboration.workspace.shared_workspace import SharedWorkspace


class WorkspaceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_workspace(self, session_id: str) -> SharedWorkspace:
        session_obj = (
            self.db.query(CollaborationSession)
            .filter(CollaborationSession.session_id == session_id)
            .first()
        )
        if not session_obj:
            raise ValueError(f"CollaborationSession {session_id} not found")
        return SharedWorkspace(**session_obj.shared_workspace)

    def save_workspace(self, session_id: str, workspace: SharedWorkspace) -> None:
        session_obj = (
            self.db.query(CollaborationSession)
            .filter(CollaborationSession.session_id == session_id)
            .first()
        )
        if not session_obj:
            raise ValueError(f"CollaborationSession {session_id} not found")

        session_obj.shared_workspace = workspace.model_dump()
        self.db.commit()
