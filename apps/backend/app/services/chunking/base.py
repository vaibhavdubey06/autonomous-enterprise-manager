from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.services.chunking.models import Chunk, ChunkMetadata
import uuid

class BaseChunker(ABC):
    """
    Abstract interface for all chunking strategies.
    Each strategy must implement the chunk() method and guarantee backward compatibility
    by consuming a document string and basic metadata, yielding a list of rich Chunk objects.
    """

    @abstractmethod
    def chunk(self, document_text: str, base_metadata: ChunkMetadata) -> List[Chunk]:
        """
        Split the document_text into Chunks.
        
        Args:
            document_text (str): The raw text of the document.
            base_metadata (ChunkMetadata): The base metadata payload containing document_id, 
                                           document_name, version, etc.
                                           
        Returns:
            List[Chunk]: A list of intelligent chunk objects with delta-metadata attached.
        """
        pass

    def _create_chunk(self, text: str, metadata: ChunkMetadata) -> Chunk:
        """
        Helper to instantiate a Chunk with a unique ID.
        """
        return Chunk(
            id=str(uuid.uuid4()),
            text=text,
            metadata=metadata
        )

    def _link_chunks(self, chunks: List[Chunk]) -> None:
        """
        Helper to establish the Context Graph (previous/next/parent relationships)
        across a list of chunks in-place.
        """
        for i, chunk in enumerate(chunks):
            chunk.metadata.chunk_index = i
            chunk.metadata.total_chunks = len(chunks)
            if i > 0:
                chunk.metadata.previous_chunk = chunks[i - 1].id
            if i < len(chunks) - 1:
                chunk.metadata.next_chunk = chunks[i + 1].id
