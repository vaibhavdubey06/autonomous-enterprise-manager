from app.services.chunking.strategies.recursive import RecursiveChunker

class JSONChunker(RecursiveChunker):
    """Fallback chunker for JSON"""
    pass
