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
            pairs = [(query, chunk.get("text", "")) for chunk in chunks]

            # Predict scores using the cross-encoder
            scores = self.model.predict(pairs)

            # Attach scores to the original chunks
            for idx, chunk in enumerate(chunks):
                chunk["rerank_score"] = float(scores[idx])

            # Sort descending by rerank_score
            reranked_chunks = sorted(
                chunks, key=lambda x: x["rerank_score"], reverse=True
            )

            # Select the top_k
            selected_chunks = reranked_chunks[:top_k]

            reranking_time = time.time() - start_time

            # Logging
            logger.info(f"Reranking completed in {reranking_time:.4f}s")
            logger.info(
                f"Original chunks: {len(chunks)} -> Selected chunks: {len(selected_chunks)}"
            )
            for idx, chunk in enumerate(selected_chunks):
                logger.info(
                    f"Rank {idx+1}: Score={chunk['rerank_score']:.4f}, Document={chunk.get('document', 'Unknown')}, Page={chunk.get('page', 1)}, Chunk={chunk.get('chunk', 0)}"
                )

            return selected_chunks

        except Exception as e:
            logger.error(f"Error during reranking process: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to rerank search results."
            )
