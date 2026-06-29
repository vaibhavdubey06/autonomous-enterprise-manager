from datetime import datetime
import logging
from app.services.memory.models import ExtractedMemory
from app.repositories.memory_repository import MemoryRepository

logger = logging.getLogger(__name__)


class MemoryDeduplicator:
    """
    Deduplicates incoming extracted memory against existing memory objects.
    """

    def __init__(self, memory_repository: MemoryRepository):
        self.memory_repository = memory_repository

    def deduplicate(
        self, incoming_memory: ExtractedMemory, existing_similar_memories: list
    ) -> dict | None:
        """
        Receives an ExtractedMemory and a list of semantically similar existing MemoryObjects (from Qdrant).
        Returns the ID of the updated memory if deduplicated, or None if it's genuinely new.
        """
        for similar in existing_similar_memories:
            # We assume similar is a dict returned from Qdrant search, or a DB object.
            # Let's say it's a dict from Qdrant search results with score.
            score = similar.get("score", 0.0)
            if score > 0.85:
                memory_id = similar.get("memory_id")
                if not memory_id:
                    continue

                # Fetch full object from DB
                existing_obj = self.memory_repository.get_memory(memory_id)
                if not existing_obj:
                    continue

                # Compare quality
                # Example: higher importance, higher confidence, or just more recent with similar importance
                incoming_importance = getattr(incoming_memory, "importance", 0.5)
                incoming_confidence = getattr(incoming_memory, "confidence", 0.5)

                existing_importance = existing_obj.importance or 0.5
                existing_confidence = existing_obj.confidence or 0.5

                # A simple heuristic: if incoming is strictly better in importance/confidence
                if (
                    incoming_importance >= existing_importance
                    and incoming_confidence >= existing_confidence
                ):
                    updates = {
                        "content": incoming_memory.content,
                        "confidence": min(existing_confidence + 0.1, 1.0),
                        "importance": incoming_importance,
                        "last_accessed": datetime.utcnow(),
                    }
                    self.memory_repository.update_memory(memory_id, updates)
                    logger.info(
                        f"Deduplicated and updated memory {memory_id} with better quality."
                    )
                    return memory_id
                else:
                    # Just increase confidence of existing and mark as accessed
                    updates = {
                        "confidence": min(existing_confidence + 0.05, 1.0),
                        "last_accessed": datetime.utcnow(),
                    }
                    self.memory_repository.update_memory(memory_id, updates)
                    logger.info(
                        f"Deduplicated memory {memory_id}, only updated confidence/last_accessed."
                    )
                    return memory_id

        return None
