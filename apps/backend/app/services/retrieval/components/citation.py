from typing import List
from app.services.retrieval.models import RetrievedChunk

class CitationBuilder:
    def build_citations(self, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """
        Build structured citations for downstream LLM responses.
        Preserves source, document, repository, path.
        """
        for i, chunk in enumerate(chunks):
            # Format: [1] Repository: repo-name | File: file.py (Source: github)
            citation_parts = []
            
            repo = chunk.metadata.get("repository") or chunk.repository
            if repo:
                citation_parts.append(f"Repo: {repo}")
                
            path = chunk.metadata.get("path") or chunk.path
            doc = chunk.metadata.get("document") or chunk.source
            if path:
                citation_parts.append(f"File: {path}")
            elif doc:
                citation_parts.append(f"Doc: {doc}")
                
            source = chunk.metadata.get("source") or chunk.source
            if source:
                citation_parts.append(f"Source: {source}")
                
            citation = " | ".join(citation_parts) if citation_parts else "Unknown Source"
            
            # Format block with citation at the top
            chunk.citation = f"[{i+1}] {citation}"
            # Embed the citation natively in the text block so the LLM easily cites it
            chunk.text = f"--- START EVIDENCE {chunk.citation} ---\n{chunk.text}\n--- END EVIDENCE ---"
            
        return chunks
