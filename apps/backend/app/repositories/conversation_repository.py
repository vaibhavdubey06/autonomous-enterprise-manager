import uuid
from typing import List, Optional
from sqlalchemy.orm import Session as DBSession

from app.models.memory import Conversation


class ConversationRepository:
    """
    Repository for managing Conversations in PostgreSQL.
    """

    def __init__(self, db: DBSession):
        self.db = db

    def create_conversation(
        self, session_id: str, title: str = "New Conversation"
    ) -> Conversation:
        db_conversation = Conversation(session_id=uuid.UUID(session_id), title=title)
        self.db.add(db_conversation)
        self.db.commit()
        self.db.refresh(db_conversation)
        return db_conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        try:
            uid = uuid.UUID(conversation_id)
        except ValueError:
            return None
        return self.db.query(Conversation).filter(Conversation.id == uid).first()

    def list_conversations(self, session_id: str) -> List[Conversation]:
        try:
            uid = uuid.UUID(session_id)
        except ValueError:
            return []
        return (
            self.db.query(Conversation)
            .filter(Conversation.session_id == uid)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    def delete_conversation(self, conversation_id: str) -> bool:
        try:
            uid = uuid.UUID(conversation_id)
        except ValueError:
            return False

        conversation = (
            self.db.query(Conversation).filter(Conversation.id == uid).first()
        )
        if conversation:
            self.db.delete(conversation)
            self.db.commit()
            return True
        return False
