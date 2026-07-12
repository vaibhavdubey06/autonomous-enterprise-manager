from functools import lru_cache
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings


@lru_cache()
def get_client():
    import os

    if os.environ.get("USE_SQLITE") == "true":
        return QdrantClient(":memory:")
    return QdrantClient(url=settings.QDRANT_URL)


COLLECTION_NAME = "documents"
SEMANTIC_CACHE_COLLECTION = "semantic_cache"


def create_collection():

    collections = [c.name for c in get_client().get_collections().collections]

    if COLLECTION_NAME not in collections:
        get_client().create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE,
            ),
        )

    if SEMANTIC_CACHE_COLLECTION not in collections:
        get_client().create_collection(
            collection_name=SEMANTIC_CACHE_COLLECTION,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE,
            ),
        )


def store_chunks(
    chunks: list, # Now supports both list[dict] and list[Chunk]
    embeddings: list[list[float]],
    document_name: str,
):
    import uuid

    points = []

    for idx, (chunk_item, embedding) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid.uuid4())
        
        if hasattr(chunk_item, "dict_for_qdrant"):
            # It's a Chunk object
            payload = chunk_item.dict_for_qdrant()
            # If the Chunk model doesn't set point_id, we can set it here so next_chunk can refer to it
            # But the chunk model already sets an ID during creation. We should use chunk.id.
            point_id = chunk_item.id
            payload["document"] = document_name # Ensure consistency
        else:
            # Legacy dictionary chunk
            payload = {
                "document": document_name,
                "page": chunk_item.get("page", 1),
                "chunk": idx,
                "text": chunk_item.get("text", ""),
                "source": chunk_item.get("source", "pdf"),
                "repository": chunk_item.get("repository", ""),
                "branch": chunk_item.get("branch", ""),
                "path": chunk_item.get("path", ""),
                "url": chunk_item.get("url", ""),
            }

        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            )
        )

    get_client().upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )


def store_memory_chunk(
    conversation_id: str, message_id: str, role: str, text: str, timestamp: str
):
    """
    Embed and store a single conversation message as semantic memory in the exact same collection.
    """
    from app.services.embeddings.embedding_service import embed_text
    import uuid

    embedding = embed_text(text)

    # Store directly in existing COLLECTION_NAME
    point_id = str(uuid.uuid4())
    get_client().upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "source": "conversation",
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "role": role,
                    "text": text,
                    "timestamp": timestamp,
                },
            )
        ],
    )


def search(
    query: str,
    limit: int = 5,
    source_filter: Optional[str] = None,
    exclude_source: Optional[str] = None,
):
    """
    Perform a semantic search in the Qdrant collection with optional filtering.
    """
    from fastapi import HTTPException
    from app.services.embeddings.embedding_service import embed_text
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    try:
        collections = [c.name for c in get_client().get_collections().collections]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Qdrant connection failure: {e}")

    if COLLECTION_NAME not in collections:
        raise HTTPException(
            status_code=404, detail="Collection not found. Upload documents first."
        )

    try:
        query_vector = embed_text(query)

        # Build filter if provided
        query_filter = None
        if source_filter:
            query_filter = Filter(
                must=[
                    FieldCondition(key="source", match=MatchValue(value=source_filter))
                ]
            )
        elif exclude_source:
            query_filter = Filter(
                must_not=[
                    FieldCondition(key="source", match=MatchValue(value=exclude_source))
                ]
            )

        results = get_client().query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "document": hit.payload.get("document", ""),
                "page": hit.payload.get("page", 1),
                "chunk": hit.payload.get("chunk", 0),
                "text": hit.payload.get("text", "") if hit.payload else "",
                "source": hit.payload.get("source", "pdf"),
                "repository": hit.payload.get("repository", ""),
                "branch": hit.payload.get("branch", ""),
                "path": hit.payload.get("path", ""),
                "url": hit.payload.get("url", ""),
                "conversation_id": hit.payload.get("conversation_id", ""),
                "message_id": hit.payload.get("message_id", ""),
                "role": hit.payload.get("role", ""),
                "timestamp": hit.payload.get("timestamp", ""),
                "previous_chunk": hit.payload.get("previous_chunk", ""),
                "next_chunk": hit.payload.get("next_chunk", ""),
            }
            for hit in results.points
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


def keyword_search(
    query: str,
    limit: int = 5,
    source_filter: Optional[str] = None,
    exclude_source: Optional[str] = None,
):
    """
    Perform a full-text keyword search in the Qdrant collection using MatchText.
    Note: Qdrant scroll API does not natively score by BM25 unless configured with a sparse vector index.
    We return pseudo-scores or rely on RRF downstream.
    """
    from qdrant_client.models import Filter, FieldCondition, MatchText, MatchValue

    if not query or not query.strip():
        return []

    must_conditions = [FieldCondition(key="text", match=MatchText(text=query))]
    if source_filter:
        must_conditions.append(
            FieldCondition(key="source", match=MatchValue(value=source_filter))
        )

    must_not_conditions = []
    if exclude_source:
        must_not_conditions.append(
            FieldCondition(key="source", match=MatchValue(value=exclude_source))
        )

    query_filter = Filter(
        must=must_conditions,
        must_not=must_not_conditions if must_not_conditions else None,
    )

    try:
        # Use scroll to get points matching the text filter
        results, _ = get_client().scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=query_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        # We assign a pseudo-score of 1.0 since scroll doesn't score. RRF will rank by position.
        return [
            {
                "score": 1.0,
                "document": hit.payload.get("document", ""),
                "page": hit.payload.get("page", 1),
                "chunk": hit.payload.get("chunk", 0),
                "text": hit.payload.get("text", "") if hit.payload else "",
                "source": hit.payload.get("source", "pdf"),
                "repository": hit.payload.get("repository", ""),
                "branch": hit.payload.get("branch", ""),
                "path": hit.payload.get("path", ""),
                "url": hit.payload.get("url", ""),
                "conversation_id": hit.payload.get("conversation_id", ""),
                "message_id": hit.payload.get("message_id", ""),
                "role": hit.payload.get("role", ""),
                "timestamp": hit.payload.get("timestamp", ""),
            }
            for hit in results
        ]
    except Exception as e:
        import logging

        logging.error(f"Keyword search failed: {e}")
        return []

def get_chunks_by_ids(ids: list[str]):
    """
    Retrieve specific chunks by their UUIDs.
    Useful for Neighbor Expansion.
    """
    if not ids:
        return []
    try:
        results = get_client().retrieve(
            collection_name=COLLECTION_NAME,
            ids=ids,
            with_payload=True,
            with_vectors=False,
        )
        return [
            {
                "id": hit.id,
                "text": hit.payload.get("text", "") if hit.payload else "",
                "document": hit.payload.get("document", ""),
                "page": hit.payload.get("page", 1),
                "chunk": hit.payload.get("chunk", 0),
                "source": hit.payload.get("source", "pdf"),
                "repository": hit.payload.get("repository", ""),
                "branch": hit.payload.get("branch", ""),
                "path": hit.payload.get("path", ""),
                "url": hit.payload.get("url", ""),
            }
            for hit in results
        ]
    except Exception as e:
        import logging
        logging.error(f"Failed to get chunks by ids: {e}")
        return []

