import logging
import time
from datetime import datetime

from app.services.memory.strategy import MemoryExtractionStrategy
from app.services.memory.normalizer import MemoryNormalizer
from app.services.memory.scorer import ImportanceScorer
from app.services.memory.deduplicator import MemoryDeduplicator
from app.repositories.memory_repository import MemoryRepository

logger = logging.getLogger(__name__)


class MemoryExtractor:
    """
    Orchestrates the cognitive memory extraction pipeline:
    Strategy (Extractor) -> Normalizer -> Scorer -> Deduplicator -> Store
    """

    def __init__(
        self,
        strategy: MemoryExtractionStrategy,
        normalizer: MemoryNormalizer,
        scorer: ImportanceScorer,
        deduplicator: MemoryDeduplicator,
        repository: MemoryRepository,
        qdrant_search_callback=None,
        qdrant_store_callback=None,
        importance_threshold: float = 0.55,
    ):
        self.strategy = strategy
        self.normalizer = normalizer
        self.scorer = scorer
        self.deduplicator = deduplicator
        self.repository = repository
        self.qdrant_search_callback = qdrant_search_callback
        self.qdrant_store_callback = qdrant_store_callback
        self.importance_threshold = importance_threshold

    def process(
        self,
        history: str,
        user_message: str,
        assistant_response: str,
        context_kwargs: dict = {},
    ):
        start_time = time.time()
        conversation_id = context_kwargs.get("conversation_id")
        user_id = context_kwargs.get("user_id", "system")
        message_id = context_kwargs.get("message_id")

        # 1. Extractor (Strategy)
        extracted_memories = self.strategy.extract(
            history, user_message, assistant_response
        )

        discarded = 0
        deduplicated_count = 0
        stored_count = 0
        importance_scores = []
        memory_types = []

        for em in extracted_memories:
            # 2. Normalizer
            em = self.normalizer.normalize(em)

            # 3. Importance Scorer
            score = self.scorer.score(em)
            importance_scores.append(score)

            # Use dynamic importance assignment back to the object so deduplicator uses it
            setattr(em, "importance", score)
            setattr(em, "confidence", 0.8)  # Default confidence for new extraction

            if score < self.importance_threshold:
                discarded += 1
                continue

            # 4. Deduplicator
            existing_similar = []
            if self.qdrant_search_callback:
                try:
                    # Find similar semantic memories in Qdrant
                    search_results = self.qdrant_search_callback(
                        em.content, limit=3, source_filter="memory_object"
                    )
                    existing_similar = search_results
                except Exception as e:
                    logger.error(f"Error searching Qdrant for deduplication: {e}")

            dedup_id = self.deduplicator.deduplicate(em, existing_similar)

            if dedup_id:
                deduplicated_count += 1
            else:
                # 5. Store new
                memory_types.append(em.memory_type)
                try:
                    memory_data = {
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "memory_type": em.memory_type,
                        "title": em.title,
                        "content": em.content,
                        "importance": score,
                        "confidence": getattr(em, "confidence", 0.8),
                        "memory_status": "NEW",
                        "source": "conversation",
                        "source_message_id": message_id,
                        "source_conversation_id": conversation_id,
                        "extracted_by": getattr(
                            self.strategy, "strategy_name", "Unknown"
                        ),
                        "extraction_version": getattr(self.strategy, "version", "1.0"),
                        "retrieval_count": 0,
                        "last_accessed": datetime.utcnow(),
                        "metadata_": em.metadata_,
                        "tags": em.tags,
                        "embedding_required": True,
                    }
                    db_memory = self.repository.add_memory(memory_data)
                    stored_count += 1

                    # Store in Qdrant as MemoryObject layer
                    if self.qdrant_store_callback:
                        payload = {
                            "source": "memory_object",
                            "memory_id": str(db_memory.id),
                            "memory_type": db_memory.memory_type,
                            "importance": db_memory.importance,
                            "confidence": db_memory.confidence,
                            "memory_status": db_memory.memory_status,
                            "conversation_id": db_memory.conversation_id,
                            "user_id": db_memory.user_id,
                            "tags": db_memory.tags,
                        }
                        self.qdrant_store_callback(db_memory.content, payload)

                except Exception as e:
                    logger.error(f"Failed to store memory object: {e}")

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Observability Improvements
        logger.info(
            f"[Memory Extraction] strategy={getattr(self.strategy, 'strategy_name', 'Unknown')} "
            f"conversation_id={conversation_id} time_ms={elapsed_ms} "
            f"extracted={len(extracted_memories)} discarded={discarded} "
            f"deduplicated={deduplicated_count} stored={stored_count} "
            f"types={memory_types} scores={importance_scores}"
        )
