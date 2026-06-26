import uuid
from typing import Optional
from sqlalchemy.orm import Session as DBSession

from app.models.memory import ConversationSummary

class SummaryRepository:
    """
    Repository for managing Conversation Summaries in PostgreSQL.
    """

    def __init__(self, db: DBSession):
        self.db = db

    def create_summary(self, conversation_id: str, summary_text: str) -> ConversationSummary:
        summary = ConversationSummary(
            conversation_id=uuid.UUID(conversation_id),
            summary=summary_text
        )
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        return summary

    def get_latest_summary(self, conversation_id: str) -> Optional[ConversationSummary]:
        try:
            uid = uuid.UUID(conversation_id)
        except ValueError:
            return None
            
        return self.db.query(ConversationSummary).filter(
            ConversationSummary.conversation_id == uid
        ).order_by(ConversationSummary.created_at.desc()).first()
