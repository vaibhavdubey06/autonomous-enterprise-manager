import logging
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.github import GitHubIndexRequest
from app.services.connectors.github.connector import GitHubConnector
from app.services.ingestion.text_chunker import chunk_text
from app.services.embeddings.embedding_service import embed_batch
from app.services.vectorstore.qdrant_service import create_collection, store_chunks

router = APIRouter()
logger = logging.getLogger(__name__)


def get_github_connector() -> GitHubConnector:
    return GitHubConnector()


@router.post("/github/index")
async def index_github_repository(
    request: GitHubIndexRequest,
    connector: GitHubConnector = Depends(get_github_connector),
):
    """
    Index a GitHub repository into the vector database.
    """
    repository_name = request.repository
    logger.info(f"Starting to index GitHub repository: {repository_name}")

    create_collection()

    total_chunks = 0
    total_docs = 0

    try:
        for doc in connector.fetch_documents(repository_name):
            # Wrap text in the format expected by chunk_text
            pages_data = [{"page": 1, "text": doc["text"]}]

            # Chunk the document
            doc_chunks = chunk_text(pages_data)

            # Inject GitHub metadata into each chunk
            for c in doc_chunks:
                c["source"] = doc["source"]
                c["repository"] = doc["repository"]
                c["branch"] = doc["branch"]
                c["path"] = doc["path"]
                c["url"] = doc["url"]

            if not doc_chunks:
                continue

            # Generate embeddings
            chunk_texts = [c["text"] for c in doc_chunks]
            embeddings = embed_batch(chunk_texts)

            # Store in Qdrant
            # Pass document_name as the path so it displays cleanly in citations
            store_chunks(
                chunks=doc_chunks, embeddings=embeddings, document_name=doc["path"]
            )

            total_chunks += len(doc_chunks)
            total_docs += 1

        logger.info(
            f"Successfully indexed {repository_name}: {total_docs} docs, {total_chunks} chunks."
        )

        return {
            "repository": repository_name,
            "documents_indexed": total_docs,
            "chunks_stored": total_chunks,
            "status": "success",
        }

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error indexing {repository_name}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to index GitHub repository."
        )
