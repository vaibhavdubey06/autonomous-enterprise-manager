import logging
import datetime
import asyncio
from typing import Optional, Dict, Any, List
from app.services.cache.models import CacheKey, CacheEntry, CacheMetadata
from app.services.cache.policies import CachePolicyManager
from app.services.cache.store import SemanticCacheStore, QdrantSemanticCacheStore
from app.services.embeddings.embedding_service import embed_text

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, store: Optional[SemanticCacheStore] = None):
        self.store = store or QdrantSemanticCacheStore()
        self.policy_manager = CachePolicyManager()

    def lookup(self, key: CacheKey) -> Optional[CacheEntry]:
        config = self.policy_manager.get_config(key.tenant_id)
        if not self.policy_manager.allows_read(config):
            return None
            
        try:
            query_vector = embed_text(key.user_question)
            entry = self.store.lookup(query_vector, key, threshold=config.similarity_threshold)
            return entry
        except Exception as e:
            logger.error(f"Semantic Cache Lookup Failed: {e}")
            return None

    def store_entry(self, key: CacheKey, question: str, response: str, metadata: CacheMetadata) -> None:
        config = self.policy_manager.get_config(key.tenant_id)
        if not self.policy_manager.allows_write(config):
            return
            
        try:
            query_vector = embed_text(question)
            
            # Compute expiration
            expires_at = None
            if config.ttl_seconds:
                expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=config.ttl_seconds)
                
            entry = CacheEntry(
                original_question=question,
                prompt_embedding=query_vector,
                response_content=response,
                metadata=metadata,
                expires_at=expires_at
            )
            
            self.store.store(key, entry)
        except Exception as e:
            logger.error(f"Semantic Cache Store Failed: {e}")

    def invalidate_by_metadata(self, metadata_filter: Dict[str, Any]) -> None:
        """
        Invalidate cache entries matching specific metadata 
        (e.g., knowledge_version, document_hash)
        """
        try:
            self.store.invalidate(metadata_filter)
            logger.info(f"Invalidated cache with filter: {metadata_filter}")
        except Exception as e:
            logger.error(f"Semantic Cache Invalidation Failed: {e}")
            
# Singleton for application use
cache_manager = CacheManager()
