from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from app.services.cache.models import CacheEntry, CacheKey
import uuid

class SemanticCacheStore(ABC):
    @abstractmethod
    def store(self, key: CacheKey, entry: CacheEntry) -> None:
        pass
        
    @abstractmethod
    def lookup(self, query_vector: List[float], key: CacheKey, threshold: float = 0.95) -> Optional[CacheEntry]:
        pass
        
    @abstractmethod
    def invalidate(self, metadata_filter: Dict[str, Any]) -> None:
        pass

class QdrantSemanticCacheStore(SemanticCacheStore):
    def store(self, key: CacheKey, entry: CacheEntry) -> None:
        from app.services.vectorstore.qdrant_service import get_client, SEMANTIC_CACHE_COLLECTION
        from qdrant_client.models import PointStruct
        
        payload = entry.dict()
        # Flatten key into payload for filtering
        payload["key_tenant_id"] = key.tenant_id
        payload["key_org_id"] = key.org_id
        payload["key_workspace"] = key.workspace
        payload["key_project"] = key.project
        payload["key_prompt_template_version"] = key.prompt_template_version
        payload["key_knowledge_version"] = key.knowledge_version
        payload["key_retrieved_chunk_ids"] = key.retrieved_chunk_ids
        payload["key_retrieved_chunk_hashes"] = key.retrieved_chunk_hashes
        payload["key_workflow_pack_version"] = key.workflow_pack_version
        payload["key_model_family"] = key.model_family
        payload["key_embedding_model_version"] = key.embedding_model_version
        
        get_client().upsert(
            collection_name=SEMANTIC_CACHE_COLLECTION,
            points=[
                PointStruct(
                    id=entry.entry_id,
                    vector=entry.prompt_embedding,
                    payload=payload
                )
            ]
        )

    def lookup(self, query_vector: List[float], key: CacheKey, threshold: float = 0.95) -> Optional[CacheEntry]:
        from app.services.vectorstore.qdrant_service import get_client, SEMANTIC_CACHE_COLLECTION
        from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
        
        must_conditions = [
            FieldCondition(key="key_tenant_id", match=MatchValue(value=key.tenant_id)),
            FieldCondition(key="key_knowledge_version", match=MatchValue(value=key.knowledge_version))
        ]
        
        # We enforce chunk exact match if there are chunks
        if key.retrieved_chunk_hashes:
            # MatchAny acts as "IN", but we actually want exact array match or superset.
            # Qdrant supports exact match on array values if we just use MatchValue for each.
            for ch in key.retrieved_chunk_hashes:
                must_conditions.append(FieldCondition(key="key_retrieved_chunk_hashes", match=MatchValue(value=ch)))
        
        query_filter = Filter(must=must_conditions)
        
        results = get_client().query_points(
            collection_name=SEMANTIC_CACHE_COLLECTION,
            query=query_vector,
            query_filter=query_filter,
            limit=1
        )
        
        if results.points and results.points[0].score >= threshold:
            payload = results.points[0].payload
            if payload:
                # Reconstruct CacheEntry
                from app.services.cache.models import CacheMetadata
                import datetime
                
                # Check expiration
                expires_at_str = payload.get("expires_at")
                if expires_at_str:
                    expires_at = datetime.datetime.fromisoformat(expires_at_str)
                    if datetime.datetime.now(datetime.timezone.utc) > expires_at:
                        return None
                        
                metadata = payload.get("metadata", {})
                return CacheEntry(
                    entry_id=payload.get("entry_id", str(uuid.uuid4())),
                    original_question=payload.get("original_question", ""),
                    prompt_embedding=payload.get("prompt_embedding", []),
                    response_content=payload.get("response_content", ""),
                    metadata=CacheMetadata(**metadata),
                    created_at=datetime.datetime.fromisoformat(payload.get("created_at")) if payload.get("created_at") else datetime.datetime.now(datetime.timezone.utc),
                    expires_at=datetime.datetime.fromisoformat(expires_at_str) if expires_at_str else None
                )
        return None

    def invalidate(self, metadata_filter: Dict[str, Any]) -> None:
        from app.services.vectorstore.qdrant_service import get_client, SEMANTIC_CACHE_COLLECTION
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        must_conditions = []
        for k, v in metadata_filter.items():
            must_conditions.append(FieldCondition(key=f"metadata.{k}", match=MatchValue(value=v)))
            
        if must_conditions:
            query_filter = Filter(must=must_conditions)
            get_client().delete(
                collection_name=SEMANTIC_CACHE_COLLECTION,
                points_selector=query_filter
            )
