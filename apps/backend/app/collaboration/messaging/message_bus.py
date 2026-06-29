import asyncio
import logging
from typing import Callable, Dict, List
from sqlalchemy.orm import Session
from app.collaboration.messaging.message_models import CollaborationMessage

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Asynchronous message bus for Enterprise Collaboration Runtime.
    Handles pub/sub messaging and persistence.
    """

    def __init__(self, db: Session):
        self.db = db
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, topic: str, callback: Callable):
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
        logger.debug(f"Subscribed to topic: {topic}")

    async def publish(self, message: CollaborationMessage):
        """Publish a message to the bus and persist it."""
        # Persist
        self.db.add(message)
        try:
            self.db.commit()
            self.db.refresh(message)
        except Exception as e:
            logger.error(f"Failed to persist message {message.message_id}: {e}")
            self.db.rollback()
            raise e

        # Determine topics (e.g., specific receiver, all in collaboration, or all)
        topics = [f"collaboration:{message.collaboration_id}", "all"]
        if message.receiver:
            topics.append(f"agent:{message.receiver}")

        # Dispatch to subscribers
        callbacks = []
        for topic in topics:
            if topic in self._subscribers:
                callbacks.extend(self._subscribers[topic])

        if callbacks:
            # Execute all callbacks concurrently
            await asyncio.gather(
                *(cb(message) for cb in callbacks), return_exceptions=True
            )

    def get_messages_for_session(
        self, collaboration_id: str
    ) -> List[CollaborationMessage]:
        return (
            self.db.query(CollaborationMessage)
            .filter(CollaborationMessage.collaboration_id == collaboration_id)
            .order_by(CollaborationMessage.timestamp.asc())
            .all()
        )
