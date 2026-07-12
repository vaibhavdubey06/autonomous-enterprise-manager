import re
from typing import List
from app.services.chunking.base import BaseChunker
from app.services.chunking.models import Chunk, ChunkMetadata
from app.services.chunking.config import TARGET_TOKENS
from app.services.chunking.utils import estimate_tokens

class SentenceChunker(BaseChunker):
    """
    Tier 1 (Fast): Token-aware sentence boundary chunker.
    Splits by punctuation. Never cuts a sentence in half.
    """
    def __init__(self):
        self.min_tokens, self.max_tokens, self.overlap = TARGET_TOKENS.get("default", (300, 500, 50))

    def chunk(self, document_text: str, base_metadata: ChunkMetadata) -> List[Chunk]:
        # Fast regex split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', document_text.strip())
        
        chunks = []
        current_text = ""
        current_tokens = 0
        
        for sentence in sentences:
            if not sentence:
                continue
                
            sentence_tokens = estimate_tokens(sentence)
            
            # If a single sentence is larger than max_tokens, we have no choice but to keep it
            if current_tokens + sentence_tokens > self.max_tokens and current_text:
                meta = base_metadata.model_copy()
                meta.token_estimate = current_tokens
                chunks.append(self._create_chunk(current_text.strip(), meta))
                
                # Context overlap (sentence aware): keep the last sentence of the previous chunk if under limits
                # But for simplicity in this fast tier, we just start fresh or keep a token overlap
                # (A true sentence overlap would grab the last N sentences until overlap tokens reached)
                # Let's do a simple 1-sentence overlap if it fits the overlap budget
                overlap_text = sentence # default
                if chunks:
                    last_sentence_of_prev = current_text.split('.')[-1] + "."
                    if estimate_tokens(last_sentence_of_prev) <= self.overlap:
                        overlap_text = last_sentence_of_prev + " " + sentence
                
                current_text = overlap_text
                current_tokens = estimate_tokens(overlap_text)
            else:
                current_text += (" " if current_text else "") + sentence
                current_tokens += sentence_tokens
                
        if current_text:
            meta = base_metadata.model_copy()
            meta.token_estimate = current_tokens
            chunks.append(self._create_chunk(current_text.strip(), meta))
            
        return chunks
