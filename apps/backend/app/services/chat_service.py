import logging
import time
from typing import Dict, Any, Optional
from fastapi import HTTPException, BackgroundTasks

from app.core.config import settings
from app.services.vectorstore.qdrant_service import search
from app.services.llm.gateway import LLMGateway
from app.services.reranking.cross_encoder_service import CrossEncoderService
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        llm_service: LLMGateway,
        reranker_service: CrossEncoderService,
        memory_service: MemoryService,
    ):
        self.llm_service = llm_service
        self.reranker_service = reranker_service
        self.memory_service = memory_service

    def chat(
        self,
        question: str,
        session_id: str | None = None,
        conversation_id: str | None = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrates full RAG pipeline with Semantic Memory and Enterprise Retrieval.
        """
        logger.info(f"Processing chat question: {question}")

        # 1. Init Memory Context
        session_id = self.memory_service.get_or_create_session(session_id)
        conversation_id = self.memory_service.get_or_create_conversation(
            session_id, conversation_id
        )

        # Save User Message
        self.memory_service.save_message(conversation_id, "user", question)

        # Build Recent Working Memory Context
        memory_context_text = self.memory_service.build_memory_context(conversation_id)

        # 2. Retrieve Candidate Contexts (Semantic Memory + Enterprise Knowledge)
        start_retrieval = time.time()

        # Fetch Semantic Memory (source == conversation)
        semantic_memories = self.memory_service.retrieve_semantic_memory(question)

        # Fetch Enterprise Knowledge (source != conversation)
        enterprise_chunks = search(
            query=question, limit=settings.QDRANT_TOP_K, exclude_source="conversation"
        )

        retrieval_time = time.time() - start_retrieval
        logger.info(
            f"Retrieval complete in {retrieval_time:.4f}s. "
            f"Semantic Memories: {len(semantic_memories)}, Enterprise Chunks: {len(enterprise_chunks)}."
        )

        # Merge Candidates
        candidate_contexts = semantic_memories + enterprise_chunks

        # 3. Rerank Merged Candidates
        try:
            reranked_results = self.reranker_service.rerank_chunks(
                query=question, chunks=candidate_contexts, top_k=settings.RERANK_TOP_K
            )
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to rerank candidate contexts."
            )

        # 4. Prepare Context and Sources
        context_texts = []
        sources = []

        for result in reranked_results:
            text = result.get("text", "")
            if text:
                context_texts.append(text)

                source_data = {
                    "source": result.get("source", "unknown"),
                    "rerank_score": result.get("rerank_score"),
                }

                if source_data["source"] == "conversation":
                    source_data.update(
                        {
                            "conversation_id": result.get("conversation_id", ""),
                            "message_id": result.get("message_id", ""),
                            "role": result.get("role", ""),
                            "timestamp": result.get("timestamp", ""),
                        }
                    )
                elif source_data["source"] == "github":
                    source_data.update(
                        {
                            "repository": result.get("repository", ""),
                            "branch": result.get("branch", ""),
                            "path": result.get("path", ""),
                            "url": result.get("url", ""),
                        }
                    )
                else:
                    source_data.update(
                        {
                            "document": result.get("document", "Unknown"),
                            "page": result.get("page", 1),
                            "chunk": result.get("chunk", 0),
                        }
                    )

                sources.append(source_data)

        # 5. Build Prompt Template
        # Inject the Memory Context into the prompt along with the reranked semantic context.
        prompt = (
            "You are an enterprise assistant.\n"
            "Use the provided Conversation History and Context to answer the user's question.\n"
            "Do not invent information. If the answer cannot be found, say so.\n"
            "Always cite which retrieved chunks were used.\n\n"
        )

        if memory_context_text:
            prompt += f"--- WORKING MEMORY ---\n{memory_context_text}\n\n"

        prompt += (
            f"--- RERANKED CONTEXT ---\n{' '.join(context_texts)}\n\n"
            f"Question: {question}"
        )

        # 6. Generate LLM Answer
        try:
            start_gen = time.time()
            answer = self.llm_service.generate_answer(
                question=prompt, context=context_texts
            )
            gen_time = time.time() - start_gen
            logger.info(f"Generation complete in {gen_time:.4f}s.")
        except Exception as e:
            logger.error(f"Error generating LLM answer: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate an answer.")

        # 7. Save Assistant Answer and Trigger Optional Summary
        self.memory_service.save_message(conversation_id, "assistant", answer)

        if background_tasks:
            background_tasks.add_task(
                self.memory_service.generate_summary, conversation_id
            )
            background_tasks.add_task(
                self.memory_service.extract_and_store_memories,
                conversation_id=conversation_id,
                user_id=session_id or "default_user",
                user_message=question,
                assistant_response=answer,
            )

        # 8. Return Answer + Sources
        return {
            "session_id": session_id,
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": sources,
        }
