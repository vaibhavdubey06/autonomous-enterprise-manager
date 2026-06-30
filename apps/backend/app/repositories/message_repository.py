import uuid
from typing import List
from sqlalchemy.orm import Session as DBSession

from app.models.memory import Message
from app.core.config import settings


class MessageRepository:
    """
    Repository for managing Messages in PostgreSQL.
    """

    def __init__(self, db: DBSession):
        self.db = db

    def add_message(
        self, conversation_id: str, role: str, content: str, importance: float = 0.5
    ) -> Message:
        msg = Message(
            conversation_id=uuid.UUID(conversation_id),  # type: ignore
            role=role,
            content=content,
            importance=importance,  # type: ignore
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_recent_messages(
        self, conversation_id: str, limit: int | None = None
    ) -> List[Message]:
        if limit is None:
            limit = settings.RECENT_MESSAGE_LIMIT

        try:
            uid = uuid.UUID(conversation_id)
        except ValueError:
            return []

        # Get latest messages and order by timestamp ascending
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == uid)
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(messages))

    def get_all_messages(self, conversation_id: str) -> List[Message]:
        try:
            uid = uuid.UUID(conversation_id)
        except ValueError:
            return []

        return (
            self.db.query(Message)
            .filter(Message.conversation_id == uid)
            .order_by(Message.timestamp.asc())
            .all()
        )
