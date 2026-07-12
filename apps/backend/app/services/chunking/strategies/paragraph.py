import re
from typing import List
from app.services.chunking.base import BaseChunker
from app.services.chunking.models import Chunk, ChunkMetadata
from app.services.chunking.config import TARGET_TOKENS
from app.services.chunking.utils import estimate_tokens

class ParagraphChunker(BaseChunker):
    """
    Tier 1 (Fast): Token-aware paragraph boundary chunker.
    Splits by double newline.
    """
    def __init__(self):
        self.min_tokens, self.max_tokens, self.overlap = TARGET_TOKENS.get("default", (300, 500, 50))

    def chunk(self, document_text: str, base_metadata: ChunkMetadata) -> List[Chunk]:
        paragraphs = re.split(r'\n\s*\n', document_text.strip())
        
        chunks = []
        current_text = ""
        current_tokens = 0
        
        for para in paragraphs:
            if not para.strip():
                continue
                
            para_tokens = estimate_tokens(para)
            
            if current_tokens + para_tokens > self.max_tokens and current_text:
                meta = base_metadata.model_copy()
                meta.token_estimate = current_tokens
                chunks.append(self._create_chunk(current_text.strip(), meta))
                current_text = para
                current_tokens = para_tokens
            else:
                current_text += ("\n\n" if current_text else "") + para
                current_tokens += para_tokens
                
        if current_text:
            meta = base_metadata.model_copy()
            meta.token_estimate = current_tokens
            chunks.append(self._create_chunk(current_text.strip(), meta))
            
        return chunks
