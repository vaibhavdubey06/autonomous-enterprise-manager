from typing import List
from app.services.chunking.base import BaseChunker
from app.services.chunking.models import Chunk, ChunkMetadata
from app.services.chunking.strategies.sentence import SentenceChunker

class SemanticChunker(BaseChunker):
    """
    Tier 3 (Deep): Semantic chunker.
    Uses sentence embeddings to group adjacent sentences with high similarity.
    Does NOT block ingestion - designed to run in background refinement.
    """
    def __init__(self):
        self.sentence_chunker = SentenceChunker()
        self.similarity_threshold = 0.7

    def chunk(self, document_text: str, base_metadata: ChunkMetadata) -> List[Chunk]:
        # Fallback to SentenceChunker if semantic chunking hasn't been implemented yet
        # or if we need a fast pass before background optimization.
        # True semantic chunking requires embedding all sentences and comparing cosines.
        # For this skeleton, we'll return sentence chunks. In a real background job,
        # these would be merged.
        return self.sentence_chunker.chunk(document_text, base_metadata)
