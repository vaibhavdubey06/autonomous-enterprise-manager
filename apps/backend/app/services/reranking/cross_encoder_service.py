import logging
import time
from typing import List, Dict, Any
from fastapi import HTTPException
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class CrossEncoderService:
    """
    Service for reranking retrieved chunks using a Cross-Encoder.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        logger.info(f"Initializing CrossEncoder with model: {model_name}")
        try:
            self.model = CrossEncoder(model_name)
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder model {model_name}: {e}")
            raise RuntimeError(f"Could not load reranker model: {e}")

    def rerank_chunks(
        self, query: str, chunks: List[Dict[str, Any]], top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of chunks based on semantic similarity to the query.
        """
        if not chunks:
            return []

        start_time = time.time()

        try:
            # Construct pairs of (query, chunk_text)
            pairs = []
            for chunk in chunks:
                if isinstance(chunk, dict):
                    pairs.append((query, chunk.get("text", "")))
                else:
                    pairs.append((query, getattr(chunk, "text", "")))

            # Predict scores using the cross-encoder
            scores = self.model.predict(pairs)

            # Attach scores to the original chunks
            reranked_chunks = []
            for idx, chunk in enumerate(chunks):
                if isinstance(chunk, dict):
                    chunk_copy = chunk.copy()
                    chunk_copy["rerank_score"] = float(scores[idx])
                    reranked_chunks.append(chunk_copy)
                else:
                    # chunk is a RetrievedChunk (Pydantic model)
                    if hasattr(chunk, "metadata") and isinstance(chunk.metadata, dict):
                        chunk.metadata["rerank_score"] = float(scores[idx])
                    reranked_chunks.append(chunk)

            # Sort descending by rerank_score
            def get_score(x):
                if isinstance(x, dict):
                    return x.get("rerank_score", 0.0)
                if hasattr(x, "metadata") and isinstance(x.metadata, dict):
                    return x.metadata.get("rerank_score", 0.0)
                return 0.0

            reranked_chunks.sort(key=get_score, reverse=True)

            # Select the top_k
            selected_chunks = reranked_chunks[:top_k]

            reranking_time = time.time() - start_time

            # Logging
            logger.info(f"Reranking completed in {reranking_time:.4f}s")
            logger.info(
                f"Original chunks: {len(chunks)} -> Selected chunks: {len(selected_chunks)}"
            )
            for idx, chunk in enumerate(selected_chunks):
                if isinstance(chunk, dict):
                    doc = chunk.get('document', 'Unknown')
                    page = chunk.get('page', 1)
                    c_id = chunk.get('chunk', 0)
                    score = chunk.get('rerank_score', 0.0)
                else:
                    doc = getattr(chunk, 'path', '') or getattr(chunk, 'repository', 'Unknown')
                    page = 1
                    c_id = getattr(chunk, 'id', 0)
                    score = chunk.metadata.get("rerank_score", 0.0) if hasattr(chunk, "metadata") else 0.0
                
                logger.info(
                    f"Rank {idx+1}: Score={score:.4f}, Document={doc}, Page={page}, Chunk={c_id}"
                )

            return selected_chunks

        except Exception as e:
            logger.error(f"Error during reranking process: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to rerank search results."
            )
