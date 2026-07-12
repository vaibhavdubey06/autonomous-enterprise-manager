import hashlib
from typing import Optional

def get_semantic_hash(text: str) -> str:
    """
    Computes a stable hash for a chunk of text.
    Used for the Chunking Cache to skip unchanged chunks during incremental ingestion.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def estimate_tokens(text: str) -> int:
    """
    Estimates the number of tokens in a string.
    Since loading tiktoken can be slightly expensive on boot, we fall back to a naive word count 
    multiplier if tiktoken is not available.
    """
    try:
        import tiktoken
        # Try fetching a common encoding (e.g. cl100k_base for GPT-4 / new embeddings)
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text, disallowed_special=()))
    except Exception:
        # Fallback: average English word is ~1.3 tokens
        return int(len(text.split()) * 1.3)
