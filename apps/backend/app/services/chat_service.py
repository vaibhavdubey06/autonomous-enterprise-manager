import logging
import time
from typing import Dict, Any, List
from fastapi import HTTPException

from app.core.config import settings
from app.services.vectorstore.qdrant_service import search
from app.services.llm.llm_service import LLMService
from app.services.reranking.cross_encoder_service import CrossEncoderService

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, llm_service: LLMService, reranker_service: CrossEncoderService):
        self.llm_service = llm_service
        self.reranker_service = reranker_service

    def chat(self, question: str) -> Dict[str, Any]:
        """
        Orchestrates semantic search, reranking, and LLM generation.
        """
        logger.info(f"Processing chat question: {question}")
        
        # 1. Search Qdrant for top QDRANT_TOP_K chunks
        try:
            start_retrieval = time.time()
            search_results = search(query=question, limit=settings.QDRANT_TOP_K)
            retrieval_time = time.time() - start_retrieval
            logger.info(f"Qdrant retrieval completed in {retrieval_time:.4f}s. Found {len(search_results)} chunks.")
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve context for the question.")

        # 2. Rerank the chunks
        try:
            reranked_results = self.reranker_service.rerank_chunks(
                query=question,
                chunks=search_results,
                top_k=settings.RERANK_TOP_K
            )
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            raise HTTPException(status_code=500, detail="Failed to rerank the retrieved chunks.")

        # 3. Prepare Context and Sources from Reranked Results
        context_texts = []
        sources = []
        
        for result in reranked_results:
            text = result.get("text", "")
            if text:
                context_texts.append(text)
                
                source_data = {
                    "source": result.get("source", "pdf"),
                    "rerank_score": result.get("rerank_score")
                }
                
                if source_data["source"] == "github":
                    source_data.update({
                        "repository": result.get("repository", ""),
                        "branch": result.get("branch", ""),
                        "path": result.get("path", ""),
                        "url": result.get("url", "")
                    })
                else:
                    source_data.update({
                        "document": result.get("document", "Unknown"),
                        "page": result.get("page", 1),
                        "chunk": result.get("chunk", 0)
                    })
                    
                sources.append(source_data)
        
        # 4. Build Prompt Template
        prompt = (
            "You are an enterprise assistant.\n"
            "Only answer using the provided context.\n"
            "Do not invent information.\n"
            "If the answer cannot be found, reply exactly:\n"
            "'I couldn't find this information in the uploaded documents.'\n"
            "Always cite which retrieved chunks were used.\n\n"
            f"Question: {question}\n\n"
            f"Context: {' '.join(context_texts)}"
        )
        
        # 5. Generate LLM Answer
        try:
            answer = self.llm_service.generate_answer(
                question=prompt, 
                context=context_texts
            )
        except Exception as e:
            logger.error(f"Error generating LLM answer: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate an answer.")

        # 6. Return Answer + Sources
        return {
            "answer": answer,
            "sources": sources
        }
