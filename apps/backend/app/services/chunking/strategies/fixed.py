from typing import List
from app.services.chunking.base import BaseChunker
from app.services.chunking.models import Chunk, ChunkMetadata
from app.services.chunking.config import TARGET_TOKENS

class FixedChunker(BaseChunker):
    """
    Tier 1 (Fast): Backward compatible sliding window chunker.
    Splits by fixed character limits.
    """
    def __init__(self):
        # We still use characters for the fixed chunker to be 100% backward compatible
        self.chunk_size = 500
        self.overlap = 50

    def chunk(self, document_text: str, base_metadata: ChunkMetadata) -> List[Chunk]:
        chunks = []
        start = 0
        
        while start < len(document_text):
            end = start + self.chunk_size
            text_slice = document_text[start:end]
            
            meta = base_metadata.model_copy()
            # Estimate tokens roughly
            meta.token_estimate = int(len(text_slice) / 4)
            
            chunk = self._create_chunk(text_slice, meta)
            chunks.append(chunk)
            
            start += self.chunk_size - self.overlap
            
        return chunks
