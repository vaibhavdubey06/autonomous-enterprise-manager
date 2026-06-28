from typing import Any, Dict
from sqlalchemy.orm import Session
from app.services.memory_service import MemoryService
from app.collaboration.session.collaboration_session import CollaborationSession
from app.collaboration.workspace.workspace_repository import WorkspaceRepository

class CollaborationMemory:
    """
    Integrates the Collaboration Runtime with the existing Cognitive Memory system.
    """
    def __init__(self, db: Session):
        self.db = db
        self.memory_service = MemoryService(db)
        self.workspace_repo = WorkspaceRepository(db)

    async def extract_session_memory(self, session_id: str) -> None:
        session = self.db.query(CollaborationSession).filter(CollaborationSession.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")
            
        workspace = self.workspace_repo.get_workspace(session_id)
        
        # Format the memory context
        context = {
            "objective": session.objective,
            "participants": session.participants,
            "decisions": [d.model_dump() for d in workspace.decisions],
            "action_items": workspace.action_items,
            "reports": workspace.reports
        }
        
        user_message = f"Collaboration Session {session_id} - Objective: {session.objective}"
        assistant_response = f"Collaboration completed. Summary of decisions and outcomes: {context}"
        
        await self.memory_service.extract_and_store_memories(
            conversation_id=session_id,
            user_id="CollaborationRuntime",
            user_message=user_message,
            assistant_response=assistant_response
        )
