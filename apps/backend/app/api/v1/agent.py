"""
Agent API — POST /agent/chat

Thin route that initialises GraphState and invokes the LangGraph pipeline.
All business logic stays in services; orchestration stays in graph nodes.
"""

import logging
from functools import lru_cache

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.llm.llm_service import LLMService
from app.services.reranking.cross_encoder_service import CrossEncoderService
from app.services.memory_service import MemoryService
from app.repositories.session_repository import SessionRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.summary_repository import SummaryRepository
from app.graph.dependencies import ServiceContainer
from app.graph.router import GraphRouter
from app.graph import builder as graph_builder
from app.graph.state import GraphState

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Singletons ──────────────────────────────────────────

@lru_cache()
def get_llm_service() -> LLMService:
    return LLMService()


@lru_cache()
def get_cross_encoder_service() -> CrossEncoderService:
    return CrossEncoderService()


# ── Per-request factories ───────────────────────────────

def get_memory_service(
    db: DBSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
) -> MemoryService:
    return MemoryService(
        session_repo=SessionRepository(db),
        conversation_repo=ConversationRepository(db),
        message_repo=MessageRepository(db),
        summary_repo=SummaryRepository(db),
        llm_service=llm_service,
    )


def get_service_container(
    memory_service: MemoryService = Depends(get_memory_service),
    llm_service: LLMService = Depends(get_llm_service),
    cross_encoder_service: CrossEncoderService = Depends(get_cross_encoder_service),
) -> ServiceContainer:
    return ServiceContainer(
        memory_service=memory_service,
        llm_service=llm_service,
        cross_encoder_service=cross_encoder_service,
    )


def get_graph_router(
    container: ServiceContainer = Depends(get_service_container),
) -> GraphRouter:
    return graph_builder.build(container)


# ── Endpoint ────────────────────────────────────────────

@router.post("/agent/chat", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    background_tasks: BackgroundTasks,
    graph_router: GraphRouter = Depends(get_graph_router),
    memory_service: MemoryService = Depends(get_memory_service),
):
    """
    Execute the full LangGraph pipeline for an enterprise AI chat.
    """
    logger.info(f"Agent chat request: {request.question[:80]}")

    # Initialise empty state
    initial_state: GraphState = {
        "question": request.question,
        "session_id": request.session_id,
        "conversation_id": request.conversation_id,
        "execution_trace": [],
        "metrics": {},
        "tool_results": [],
        "sources": [],
        "reranked_chunks": [],
        "semantic_memory": [],
        "recent_memory": [],
    }

    # Run the graph
    final_state = graph_router.run(initial_state)

    # Optionally trigger async summary generation
    conversation_id = final_state.get("conversation_id")
    if conversation_id:
        background_tasks.add_task(memory_service.generate_summary, conversation_id)

    return AgentChatResponse(
        session_id=final_state.get("session_id", ""),
        conversation_id=final_state.get("conversation_id", ""),
        answer=final_state.get("answer", ""),
        sources=final_state.get("sources", []),
        execution_trace=final_state.get("execution_trace", []),
        metrics=final_state.get("metrics", {}),
    )
