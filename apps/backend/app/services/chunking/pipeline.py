import logging
from typing import List, Optional
import concurrent.futures

from app.services.chunking.models import Chunk, ChunkMetadata
from app.services.chunking.factory import ChunkerFactory
from app.services.chunking.config import CHUNK_STRATEGY_MAP, ENABLE_SEMANTIC_CHUNKING
from app.services.chunking.utils import get_semantic_hash, estimate_tokens

logger = logging.getLogger(__name__)

class ChunkingPipeline:
    """
    Central orchestration for intelligent chunking.
    Handles Strategy Routing, Lazy Semantic Refinement, Chunk Caching, and Parallel Chunking.
    """
    def __init__(self):
        self.max_workers = 4 # Cap workers for parallel processing
        
    def determine_strategy(self, file_extension: str, file_size_bytes: int) -> str:
        """
        Cost Model Strategy Router.
        Optimizes for Quality + Latency + Document Type + Size.
        """
        # Strip dot if present
        ext = file_extension.lstrip(".").lower()
        
        # 1. Very large markdown files downgrade to RecursiveChunker for speed
        if ext == "md" and file_size_bytes > 20_000_000:
            return "RecursiveChunker"
            
        # 2. Large PDFs fallback to Recursive
        if ext == "pdf" and file_size_bytes > 50_000_000:
            return "RecursiveChunker"
            
        # 3. Enterprise docs -> Semantic Chunker (if enabled)
        if ext in ["md", "txt", "pdf"] and ENABLE_SEMANTIC_CHUNKING:
            # Only use semantic chunking for deep evaluation on smaller subsets
            if file_size_bytes < 5_000_000:
                return "SemanticChunker"
                
        # 4. Standard mapping
        return CHUNK_STRATEGY_MAP.get(ext, "FixedChunker")

    def process_document(
        self, 
        document_text: str, 
        base_metadata: ChunkMetadata,
        file_extension: str = "txt"
    ) -> List[Chunk]:
        """
        Main entrypoint for chunking a single large document string.
        """
        # Compute hash for caching
        semantic_hash = get_semantic_hash(document_text)
        base_metadata.semantic_hash = semantic_hash
        
        # Determine strategy
        strategy_name = self.determine_strategy(file_extension, len(document_text))
        logger.info(f"ChunkingPipeline selected strategy '{strategy_name}' for document {base_metadata.document_name}")
        
        chunker = ChunkerFactory.get_chunker(strategy_name)
        chunks = chunker.chunk(document_text, base_metadata)
        
        return chunks

    def process_pages_parallel(
        self, 
        pages: List[dict], 
        base_metadata: ChunkMetadata,
        file_extension: str = "pdf"
    ) -> List[Chunk]:
        """
        Parallel chunking for paginated documents (e.g. PDF).
        Splits pages across workers to minimize latency.
        """
        strategy_name = self.determine_strategy(file_extension, sum(len(p.get("text", "")) for p in pages))
        chunker = ChunkerFactory.get_chunker(strategy_name)
        
        all_chunks = []
        
        def process_page(page_info: dict) -> List[Chunk]:
            text = page_info.get("text", "")
            page_num = page_info.get("page", 1)
            
            # Deep copy metadata per page
            page_metadata = base_metadata.model_copy()
            page_metadata.page = page_num
            page_metadata.semantic_hash = get_semantic_hash(text)
            
            return chunker.chunk(text, page_metadata)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = executor.map(process_page, pages)
            for page_chunks in results:
                all_chunks.extend(page_chunks)
                
        # Relink the global graph
        if all_chunks:
            # Use any chunker instance to link (just a helper method)
            chunker._link_chunks(all_chunks)
            
        return all_chunks
