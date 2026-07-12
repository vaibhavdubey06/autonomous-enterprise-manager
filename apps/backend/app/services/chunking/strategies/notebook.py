from app.services.chunking.strategies.recursive import RecursiveChunker

class NotebookChunker(RecursiveChunker):
    """Fallback chunker for Jupyter Notebooks"""
    pass
