import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.repositories.session_repository import SessionRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.summary_repository import SummaryRepository
from app.services.vectorstore.qdrant_service import store_memory_chunk, search
from app.services.llm.llm_service import LLMService

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Coordinates PostgreSQL long-term memory, Semantic Memory, and Working Memory summaries.
    """

    def __init__(
        self,
        session_repo: SessionRepository,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        summary_repo: SummaryRepository,
        memory_repo: Any,  # Avoid circular import if typed strictly, will import at top
        llm_service: LLMService,
        extractor: Any = None,
    ):
        self.session_repo = session_repo
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.summary_repo = summary_repo
        self.memory_repo = memory_repo
        self.llm_service = llm_service
        self.extractor = extractor

    def get_or_create_session(
        self, session_id: Optional[str] = None, user_id: str = "default_user"
    ) -> str:
        if session_id:
            session = self.session_repo.get_session(session_id)
            if session:
                return str(session.id)

        new_session = self.session_repo.create_session(user_id=user_id)
        return str(new_session.id)

    def get_or_create_conversation(
        self, session_id: str, conversation_id: Optional[str] = None
    ) -> str:
        if conversation_id:
            conv = self.conversation_repo.get_conversation(conversation_id)
            if conv:
                return str(conv.id)

        new_conv = self.conversation_repo.create_conversation(session_id=session_id)
        return str(new_conv.id)

    def save_message(
        self, conversation_id: str, role: str, content: str, importance: float = 0.5
    ) -> None:
        """
        Saves raw message to PostgreSQL and embeds it into Qdrant semantic memory.
        """
        logger.info(
            f"Saving {role} message to memory for conversation {conversation_id}"
        )

        # 1. Save to DB
        msg = self.message_repo.add_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            importance=importance,
        )

        # 2. Save to Semantic Memory
        timestamp_str = msg.timestamp.isoformat()
        try:
            store_memory_chunk(
                conversation_id=str(msg.conversation_id),
                message_id=str(msg.id),
                role=msg.role,
                text=msg.content,
                timestamp=timestamp_str,
            )
        except Exception as e:
            logger.error(
                f"Failed to store semantic memory chunk for message {msg.id}: {e}"
            )

    def get_recent_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        messages = self.message_repo.get_recent_messages(
            conversation_id, limit=settings.RECENT_MESSAGE_LIMIT
        )
        return [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "importance": m.importance,
            }
            for m in messages
        ]

    def retrieve_semantic_memory(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieves top K semantic memory chunks for the user's query.
        """
        try:
            results = search(
                query=query,
                limit=settings.MEMORY_SEARCH_TOP_K,
                source_filter="conversation",
            )
            logger.info(f"Retrieved {len(results)} semantic memory chunks.")
            return results
        except Exception as e:
            logger.error(f"Semantic memory retrieval failed: {e}")
            return []

    def get_latest_summary(self, conversation_id: str) -> str:
        summary = self.summary_repo.get_latest_summary(conversation_id)
        return summary.summary if summary else ""

    def build_memory_context(self, conversation_id: str) -> str:
        """
        Builds a composite string of recent messages and the latest summary.
        """
        summary = self.get_latest_summary(conversation_id)
        recent_messages = self.get_recent_messages(conversation_id)

        context_parts = []
        if summary:
            context_parts.append(f"Conversation Summary:\n{summary}\n")

        if recent_messages:
            context_parts.append("Recent Conversation History:")
            for msg in recent_messages:
                context_parts.append(f"{msg['role'].capitalize()}: {msg['content']}")

        return "\n".join(context_parts)

    def generate_summary(self, conversation_id: str):
        """
        Calculates context size and generates a rolling summary if it exceeds the limit.
        Intended to be called as a background task.
        """
        try:
            messages = self.message_repo.get_all_messages(conversation_id)
            if not messages:
                return

            total_chars = sum(len(m.content) for m in messages)

            if total_chars > settings.SUMMARY_TRIGGER_CHARACTERS:
                logger.info(
                    f"Context size {total_chars} exceeds limit {settings.SUMMARY_TRIGGER_CHARACTERS}. Generating summary."
                )

                # Build context to summarize
                history_text = "\n".join([f"{m.role}: {m.content}" for m in messages])
                prompt = (
                    "Summarize the following conversation history concisely, capturing key facts, user preferences, "
                    "and the main topics discussed. This summary will be used as background context for future turns.\n\n"
                    f"{history_text}"
                )

                summary_text = self.llm_service.generate_answer(
                    question=prompt, context=[]
                )

                self.summary_repo.create_summary(conversation_id, summary_text)
                logger.info(
                    f"Successfully generated and stored rolling summary for {conversation_id}."
                )

        except Exception as e:
            logger.error(f"Failed to generate rolling summary: {e}")

    def calculate_importance(self, message_id: str, content: str):
        """
        Placeholder for LLM-based importance calculation.
        Currently just logs since importance is defaulted to 0.5 on creation.
        """
        # A full implementation would prompt the LLM to score the message and update the DB row.

    async def extract_and_store_memories(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
        assistant_response: str,
    ):
        """
        Asynchronously extracts cognitive memories from the recent conversation and stores them.
        """
        if not self.extractor or not settings.MEMORY_EXTRACTION_ENABLED:
            return

        try:
            # Build history string to provide context to the extractor
            history_text = self.build_memory_context(conversation_id)

            # Use the extractor
            self.extractor.process(
                history=history_text,
                user_message=user_message,
                assistant_response=assistant_response,
                context_kwargs={
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                },
            )
            logger.info(
                f"Memory extraction completed for conversation {conversation_id}"
            )
        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")
