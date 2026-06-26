from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
)

client = QdrantClient(
    url="http://localhost:6333"
)

COLLECTION_NAME = "documents"


def create_collection():

    collections = [
        c.name
        for c in client.get_collections().collections
    ]

    if COLLECTION_NAME not in collections:

        client.create_collection(
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
                    "url": chunk_dict.get("url", "")
                },
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )


def search(query: str, limit: int = 5):
    """
    Perform a semantic search in the Qdrant collection.
    """
    from fastapi import HTTPException
    from app.services.embeddings.embedding_service import embed_text

    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    try:
        collections = [
            c.name
            for c in client.get_collections().collections
        ]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Qdrant connection failure: {e}")

    if COLLECTION_NAME not in collections:
        raise HTTPException(status_code=404, detail="Collection not found. Upload documents first.")

    try:
        query_vector = embed_text(query)
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
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
                "url": hit.payload.get("url", "")
            }
            for hit in results.points
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")