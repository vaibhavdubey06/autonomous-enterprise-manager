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


@router.post("/index")
async def index_github_repository(
    request: GitHubIndexRequest,
    connector: GitHubConnector = Depends(get_github_connector),
):
    """
    Index a GitHub repository into the vector database.
    """
    repository_name = request.repository.strip()
    
    # Strip URL prefixes if user pasted a full URL
    if "github.com/" in repository_name:
        repository_name = repository_name.split("github.com/")[-1]
    
    # Remove any trailing slashes or .git
    repository_name = repository_name.rstrip("/")
    if repository_name.endswith(".git"):
        repository_name = repository_name[:-4]
        
    if "/" not in repository_name or len(repository_name.split("/")) != 2:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid repository format. Expected 'owner/repo', got '{request.repository}'."
        )

    logger.info(f"Starting to index GitHub repository: {repository_name}")

    create_collection()

    total_chunks = 0
    total_docs = 0

    try:
        from app.services.chunking.pipeline import ChunkingPipeline
        from app.services.chunking.models import ChunkMetadata
        
        chunking_pipeline = ChunkingPipeline()
        
        for doc in connector.fetch_documents(repository_name):
            # Parse file extension for the cost model router
            ext = "txt"
            if "." in doc["path"]:
                ext = doc["path"].split(".")[-1]

            base_metadata = ChunkMetadata(
                document_id=doc["url"],
                document_name=doc["path"],
                repository=doc["repository"],
                branch=doc["branch"],
                file_path=doc["path"],
                source_url=doc["url"],
                source=doc["source"]
            )

            # Chunk the document through the intelligent pipeline
            doc_chunks = chunking_pipeline.process_document(
                document_text=doc["text"],
                base_metadata=base_metadata,
                file_extension=ext
            )

            if not doc_chunks:
                continue

            # Generate embeddings
            chunk_texts = [c.text for c in doc_chunks]
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
