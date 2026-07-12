from typing import List, Dict, Any
from app.services.chunking.models import Chunk
from app.services.chunking.utils import estimate_tokens

class ChunkQualityEvaluator:
    """
    Offline quality engine to measure chunk attributes.
    """
    @staticmethod
    def evaluate_chunks(chunks: List[Chunk]) -> Dict[str, float]:
        if not chunks:
            return {}
            
        total_chunks = len(chunks)
        total_tokens = sum(estimate_tokens(c.text) for c in chunks)
        avg_tokens = total_tokens / total_chunks
        
        # Count headers preserved
        headers_preserved = sum(1 for c in chunks if c.metadata.heading)
        
        # Token density variance
        token_variance = sum((estimate_tokens(c.text) - avg_tokens) ** 2 for c in chunks) / total_chunks
        
        return {
            "chunk_count": float(total_chunks),
            "avg_tokens": avg_tokens,
            "header_preservation_rate": headers_preserved / total_chunks,
            "token_variance": token_variance
        }
