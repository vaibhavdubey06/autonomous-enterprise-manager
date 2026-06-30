from functools import lru_cache
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings


@lru_cache()
def get_client():
    return QdrantClient(url=settings.QDRANT_URL)


COLLECTION_NAME = "documents"


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


def store_chunks(
    chunks: list[dict],
    embeddings: list[list[float]],
    document_name: str,
):
    import uuid

    points = []

    for idx, (chunk_dict, embedding) in enumerate(zip(chunks, embeddings)):
        # Generate a more robust ID if needed, or just use a random UUID
        point_id = str(uuid.uuid4())

        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "document": document_name,
                    "page": chunk_dict.get("page", 1),
                    "chunk": idx,
                    "text": chunk_dict.get("text", ""),
                    "source": chunk_dict.get("source", "pdf"),
                    "repository": chunk_dict.get("repository", ""),
                    "branch": chunk_dict.get("branch", ""),
                    "path": chunk_dict.get("path", ""),
                    "url": chunk_dict.get("url", ""),
                },
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
            }
            for hit in results.points
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")
