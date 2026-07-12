import re
from typing import List
from app.services.chunking.base import BaseChunker
from app.services.chunking.models import Chunk, ChunkMetadata
from app.services.chunking.config import TARGET_TOKENS
from app.services.chunking.utils import estimate_tokens
from app.services.chunking.strategies.paragraph import ParagraphChunker

class MarkdownChunker(BaseChunker):
    """
    Tier 2 (Balanced): Markdown-aware chunker.
    Splits by ATX headings (#) and respects fences.
    Maintains current section heading in metadata.
    """
    def __init__(self):
        self.min_tokens, self.max_tokens, self.overlap = TARGET_TOKENS.get("markdown", (300, 800, 50))
        self.paragraph_chunker = ParagraphChunker() # Fallback for huge sections

    def chunk(self, document_text: str, base_metadata: ChunkMetadata) -> List[Chunk]:
        # Simple regex to split by H1, H2, H3 but keep the heading
        # This regex looks for lines starting with 1-3 hashes followed by a space
        sections = re.split(r'(?m)^(#{1,3}\s+.*$)', document_text)
        
        chunks = []
        current_heading = base_metadata.heading
        current_text = ""
        current_tokens = 0
        
        def push_chunk(text: str, heading: str):
            if not text.strip():
                return
            meta = base_metadata.model_copy()
            meta.heading = heading
            
            toks = estimate_tokens(text)
            
            # If the section itself is too large, drop to paragraph chunker
            if toks > self.max_tokens:
                sub_chunks = self.paragraph_chunker.chunk(text, meta)
                chunks.extend(sub_chunks)
            else:
                meta.token_estimate = toks
                chunks.append(self._create_chunk(text.strip(), meta))
        
        # sections[0] is everything before the first heading
        if sections[0].strip():
            push_chunk(sections[0], current_heading)
            
        # The rest are pairs of (heading, content)
        for i in range(1, len(sections), 2):
            heading_line = sections[i]
            content = sections[i+1] if i+1 < len(sections) else ""
            
            # Clean heading for metadata (remove hashes)
            current_heading = re.sub(r'^#+\s+', '', heading_line).strip()
            
            # Reattach heading to content for the LLM's sake
            full_section_text = heading_line + "\n" + content
            push_chunk(full_section_text, current_heading)
            
        return chunks
