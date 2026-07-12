from typing import List
from app.services.chunking.base import BaseChunker
from app.services.chunking.models import Chunk, ChunkMetadata
from app.services.chunking.config import TARGET_TOKENS
from app.services.chunking.utils import estimate_tokens
from app.services.chunking.strategies.paragraph import ParagraphChunker
from app.services.chunking.strategies.sentence import SentenceChunker
from app.services.chunking.strategies.fixed import FixedChunker

class RecursiveChunker(BaseChunker):
    """
    Tier 2 (Balanced): Recursive chunker.
    Tries Paragraph -> Sentence -> Fixed if limits are exceeded.
    Used for PDFs and massive unformatted text.
    """
    def __init__(self):
        self.min_tokens, self.max_tokens, self.overlap = TARGET_TOKENS.get("pdf", (400, 1000, 50))
        self.paragraph_chunker = ParagraphChunker()
        self.sentence_chunker = SentenceChunker()
        self.fixed_chunker = FixedChunker()

    def chunk(self, document_text: str, base_metadata: ChunkMetadata) -> List[Chunk]:
        # Try paragraph
        para_chunks = self.paragraph_chunker.chunk(document_text, base_metadata)
        
        final_chunks = []
        for p_chunk in para_chunks:
            if p_chunk.metadata.token_estimate > self.max_tokens:
                # Fallback to sentence
                sent_chunks = self.sentence_chunker.chunk(p_chunk.text, base_metadata)
                for s_chunk in sent_chunks:
                    if s_chunk.metadata.token_estimate > self.max_tokens:
                        # Fallback to fixed
                        fixed_chunks = self.fixed_chunker.chunk(s_chunk.text, base_metadata)
                        final_chunks.extend(fixed_chunks)
                    else:
                        final_chunks.append(s_chunk)
            else:
                final_chunks.append(p_chunk)
                
        return final_chunks
