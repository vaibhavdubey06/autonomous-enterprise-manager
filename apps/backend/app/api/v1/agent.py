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

from app.repositories.memory_repository import MemoryRepository
from app.services.memory.extractor import MemoryExtractor
from app.services.memory.strategy import GeminiMemoryExtractionStrategy
from app.services.memory.normalizer import MemoryNormalizer
from app.services.memory.scorer import ImportanceScorer
from app.services.memory.deduplicator import MemoryDeduplicator
from app.services.vectorstore.qdrant_service import store_memory_chunk, search
from app.core.config import settings

def get_memory_service(
    db: DBSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
) -> MemoryService:
    # Set up MemoryExtractor dependencies
    memory_repo = MemoryRepository(db)
    strategy = GeminiMemoryExtractionStrategy(llm_service)
    normalizer = MemoryNormalizer()
    scorer = ImportanceScorer()
    deduplicator = MemoryDeduplicator(memory_repo)
    
    # Store callback to Qdrant (using same storage utility but with 'memory_object' payload in memory_service.py/extractor)
    def qdrant_store_callback(text, payload):
        from app.services.embeddings.embedding_service import embed_text
        import uuid
        from qdrant_client.models import PointStruct
        from app.services.vectorstore.qdrant_service import get_client, COLLECTION_NAME
        embedding = embed_text(text)
        point_id = str(uuid.uuid4())
        get_client().upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(id=point_id, vector=embedding, payload=payload)]
        )
        
    extractor = MemoryExtractor(
        strategy=strategy,
        normalizer=normalizer,
        scorer=scorer,
        deduplicator=deduplicator,
        repository=memory_repo,
        qdrant_search_callback=search,
        qdrant_store_callback=qdrant_store_callback,
        importance_threshold=settings.MEMORY_IMPORTANCE_THRESHOLD
    )

    return MemoryService(
        session_repo=SessionRepository(db),
        conversation_repo=ConversationRepository(db),
        message_repo=MessageRepository(db),
        summary_repo=SummaryRepository(db),
        memory_repo=memory_repo,
        llm_service=llm_service,
        extractor=extractor
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


from app.agents.supervisor.supervisor_agent import SupervisorGraph
from app.agents.supervisor.planner import Planner
from app.agents.supervisor.task_decomposer import TaskDecomposer
from app.agents.supervisor.router import AgentRouter
from app.agents.base.registry import AgentRegistry
from app.agents.executives.cto.agent import CTOAgent

from app.capabilities.base.capability_registry import CapabilityRegistry
from app.capabilities.base.executor import CapabilityExecutor
from app.capabilities.tools.github.tool import GitHubCapability

def get_supervisor_graph(
    llm_service: LLMService = Depends(get_llm_service),
    knowledge_agent_graph: GraphRouter = Depends(get_graph_router)
) -> SupervisorGraph:
    planner = Planner(llm_service)
    task_decomposer = TaskDecomposer()
    
    # Initialize Capability Framework
    cap_registry = CapabilityRegistry()
    cap_registry.register(GitHubCapability())
    cap_executor = CapabilityExecutor(cap_registry)
    
    # Initialize and populate AgentRegistry
    registry = AgentRegistry()
    registry.register_agent(CTOAgent(
        llm_service=llm_service, 
        capability_executor=cap_executor,
        knowledge_agent_graph=knowledge_agent_graph
    ))
    
    agent_router = AgentRouter(agent_registry=registry, knowledge_agent_graph=knowledge_agent_graph)
    
    return SupervisorGraph(
        planner=planner,
        task_decomposer=task_decomposer,
        agent_router=agent_router
    )

# ── Endpoint ────────────────────────────────────────────

@router.post("/agent/chat", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    background_tasks: BackgroundTasks,
    supervisor_graph: SupervisorGraph = Depends(get_supervisor_graph),
    memory_service: MemoryService = Depends(get_memory_service),
):
    """
    Execute the full LangGraph pipeline via the Supervisor orchestrator.
    """
    logger.info(f"Agent chat request: {request.question[:80]}")

    # Initialise Supervisor state
    initial_state = {
        "user_input": request.question,
        "session_id": request.session_id,
        "conversation_id": request.conversation_id,
        "execution_time_ms": 0.0,
        "selected_agents": [],
        "completed_tasks": [],
        "failed_tasks": [],
    }

    # Run the Supervisor graph
    final_state = supervisor_graph.run(initial_state)

    # Optionally trigger async summary and memory extraction
    conversation_id = final_state.get("conversation_id") or request.conversation_id
    if conversation_id:
        background_tasks.add_task(memory_service.generate_summary, conversation_id)
        background_tasks.add_task(
            memory_service.extract_and_store_memories,
            conversation_id=conversation_id,
            user_id=request.session_id or "default_user",
            user_message=request.question,
            assistant_response=final_state.get("final_response") or ""
        )

    # Gather metrics
    metrics = {
        "total_time_ms": final_state.get("execution_time_ms", 0.0),
        "selected_agents": final_state.get("selected_agents", []),
        "completed_tasks": final_state.get("completed_tasks", []),
        "failed_tasks": final_state.get("failed_tasks", []),
    }

    return AgentChatResponse(
        session_id=request.session_id or "",
        conversation_id=conversation_id or "",
        answer=final_state.get("final_response") or "",
        sources=[], # Sources could be extracted from tasks in the future
        execution_trace=[],
        metrics=metrics,
    )
