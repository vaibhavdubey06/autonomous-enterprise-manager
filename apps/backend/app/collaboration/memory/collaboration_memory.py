from sqlalchemy.orm import Session
from app.services.memory_service import MemoryService
from app.collaboration.session.collaboration_session import CollaborationSession
from app.collaboration.workspace.workspace_repository import WorkspaceRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.summary_repository import SummaryRepository
from app.repositories.memory_repository import MemoryRepository
from app.services.llm.gateway import LLMGateway


class CollaborationMemory:
    """
    Integrates the Collaboration Runtime with the existing Cognitive Memory system.
    """

    def __init__(self, db: Session):
        self.db = db
        session_repo = SessionRepository(db)
        conversation_repo = ConversationRepository(db)
        message_repo = MessageRepository(db)
        summary_repo = SummaryRepository(db)
        memory_repo = MemoryRepository(db)
        llm_service = LLMGateway()
        self.memory_service = MemoryService(
            session_repo,
            conversation_repo,
            message_repo,
            summary_repo,
            memory_repo,
            llm_service,
        )
        self.workspace_repo = WorkspaceRepository(db)

    async def extract_session_memory(self, session_id: str) -> None:
        session = (
            self.db.query(CollaborationSession)
            .filter(CollaborationSession.session_id == session_id)
            .first()
        )
        if not session:
            raise ValueError("Session not found")

        workspace = self.workspace_repo.get_workspace(session_id)

        # Format the memory context
        context = {
            "objective": session.objective,
            "participants": session.participants,
            "decisions": [d.model_dump() for d in workspace.decisions],
            "action_items": workspace.action_items,
            "reports": workspace.reports,
        }

        user_message = (
            f"Collaboration Session {session_id} - Objective: {session.objective}"
        )
        assistant_response = (
            f"Collaboration completed. Summary of decisions and outcomes: {context}"
        )

        await self.memory_service.extract_and_store_memories(
            conversation_id=session_id,
            user_id="CollaborationRuntime",
            user_message=user_message,
            assistant_response=assistant_response,
        )
