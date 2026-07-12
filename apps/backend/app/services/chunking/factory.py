from typing import Type
from app.services.chunking.base import BaseChunker

class ChunkerFactory:
    """
    Lazy factory for chunkers to avoid importing heavy libraries (like NLTK or BeautifulSoup)
    unless a specific chunker is requested by the Router.
    """
    
    @staticmethod
    def get_chunker(strategy_name: str) -> BaseChunker:
        if strategy_name == "FixedChunker":
            from app.services.chunking.strategies.fixed import FixedChunker
            return FixedChunker()
        elif strategy_name == "SentenceChunker":
            from app.services.chunking.strategies.sentence import SentenceChunker
            return SentenceChunker()
        elif strategy_name == "ParagraphChunker":
            from app.services.chunking.strategies.paragraph import ParagraphChunker
            return ParagraphChunker()
        elif strategy_name == "MarkdownChunker":
            from app.services.chunking.strategies.markdown import MarkdownChunker
            return MarkdownChunker()
        elif strategy_name == "CodeChunker":
            from app.services.chunking.strategies.code import CodeChunker
            return CodeChunker()
        elif strategy_name == "HTMLChunker":
            from app.services.chunking.strategies.html import HTMLChunker
            return HTMLChunker()
        elif strategy_name == "JSONChunker":
            from app.services.chunking.strategies.json import JSONChunker
            return JSONChunker()
        elif strategy_name == "NotebookChunker":
            from app.services.chunking.strategies.notebook import NotebookChunker
            return NotebookChunker()
        elif strategy_name == "RecursiveChunker":
            from app.services.chunking.strategies.recursive import RecursiveChunker
            return RecursiveChunker()
        elif strategy_name == "SemanticChunker":
            from app.services.chunking.strategies.semantic import SemanticChunker
            return SemanticChunker()
        else:
            # Fallback to FixedChunker
            from app.services.chunking.strategies.fixed import FixedChunker
            return FixedChunker()
