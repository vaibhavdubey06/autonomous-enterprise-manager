import re
from typing import List
from app.services.chunking.base import BaseChunker
from app.services.chunking.models import Chunk, ChunkMetadata
from app.services.chunking.config import TARGET_TOKENS
from app.services.chunking.utils import estimate_tokens

class CodeChunker(BaseChunker):
    """
    Tier 2 (Balanced): Code chunker.
    Attempts to split by function/class boundaries based on common patterns.
    Uses regex for speed rather than a full AST parser to meet latency budgets.
    """
    def __init__(self):
        self.min_tokens, self.max_tokens, self.overlap = TARGET_TOKENS.get("code", (100, 1000, 0))

    def chunk(self, document_text: str, base_metadata: ChunkMetadata) -> List[Chunk]:
        # Fast regex for top-level functions and classes in common languages
        # Matches ^class or ^def or ^func or ^type or ^interface
        # (This is a heuristic. A real AST parser is better but slower)
        blocks = re.split(r'(?m)^(class\s+|def\s+|func\s+|type\s+|interface\s+)', document_text)
        
        chunks = []
        
        # Element 0 is imports/module-level docstrings
        if blocks[0].strip():
            meta = base_metadata.model_copy()
            meta.token_estimate = estimate_tokens(blocks[0])
            chunks.append(self._create_chunk(blocks[0].strip(), meta))
            
        for i in range(1, len(blocks), 2):
            keyword = blocks[i]
            body = blocks[i+1] if i+1 < len(blocks) else ""
            
            full_block = keyword + body
            meta = base_metadata.model_copy()
            
            # Simple heuristic for heading: extract the name
            # e.g. 'class MyClass:' -> 'MyClass'
            first_line = full_block.split('\n')[0]
            name_match = re.search(r'(?:class|def|func|type|interface)\s+([a-zA-Z0-9_]+)', first_line)
            if name_match:
                meta.heading = name_match.group(1)
                
            meta.token_estimate = estimate_tokens(full_block)
            
            # Note: If the function is massive, we don't split it (as per requirements: "never split inside a function body")
            # We just accept the large token estimate.
            
            chunks.append(self._create_chunk(full_block.strip(), meta))
            
        return chunks
