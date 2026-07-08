import logging
from app.capabilities.base.capability_registry import CapabilityRegistry
from app.capabilities.base.executor import CapabilityExecutor
from app.capabilities.tools.github.tool import GitHubCapability
from functools import lru_cache
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session as DBSession
from app.core.database import get_db
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.llm.gateway import LLMGateway
from app.services.reranking.cross_encoder_service import CrossEncoderService
from app.services.memory_service import MemoryService
from app.repositories.session_repository import SessionRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.summary_repository import SummaryRepository
from app.graph.dependencies import ServiceContainer
from app.graph.router import GraphRouter
from app.graph import builder as graph_builder
from app.repositories.memory_repository import MemoryRepository
from app.services.memory.extractor import MemoryExtractor
from app.services.memory.strategy import GeminiMemoryExtractionStrategy
from app.services.memory.normalizer import MemoryNormalizer
from app.services.memory.scorer import ImportanceScorer
from app.services.memory.deduplicator import MemoryDeduplicator
from app.services.vectorstore.qdrant_service import search
from app.core.config import settings
from app.agents.supervisor.supervisor_agent import SupervisorGraph
from app.agents.supervisor.schemas import SupervisorState
from app.agents.supervisor.planner import Planner
from app.agents.supervisor.task_decomposer import TaskDecomposer
from app.agents.supervisor.router import AgentRouter
from app.agents.executives.factory import build_default_executive_registry
from app.collaboration.services.collaboration_service import CollaborationService
from app.services.capability.service import CapabilityInferenceService
from app.runtime.manager import runtime_manager

"""
Agent API — POST /agent/chat

Thin route that initialises GraphState and invokes the LangGraph pipeline.
All business logic stays in services; orchestration stays in graph nodes.
"""


logger = logging.getLogger(__name__)
router = APIRouter()

# ── Singletons ──────────────────────────────────────────


@lru_cache()
def get_llm_service() -> LLMGateway:
    return LLMGateway()


@lru_cache()
def get_cross_encoder_service() -> CrossEncoderService:
    return CrossEncoderService()


# ── Per-request factories ───────────────────────────────


def get_memory_service(
    db: DBSession = Depends(get_db),
    llm_service: LLMGateway = Depends(get_llm_service),
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
            points=[PointStruct(id=point_id, vector=embedding, payload=payload)],
        )

    extractor = MemoryExtractor(
        strategy=strategy,
        normalizer=normalizer,
        scorer=scorer,
        deduplicator=deduplicator,
        repository=memory_repo,
        qdrant_search_callback=search,
        qdrant_store_callback=qdrant_store_callback,
        importance_threshold=settings.MEMORY_IMPORTANCE_THRESHOLD,
    )

    return MemoryService(
        session_repo=SessionRepository(db),
        conversation_repo=ConversationRepository(db),
        message_repo=MessageRepository(db),
        summary_repo=SummaryRepository(db),
        memory_repo=memory_repo,
        llm_service=llm_service,
        extractor=extractor,
    )


def get_service_container(
    memory_service: MemoryService = Depends(get_memory_service),
    llm_service: LLMGateway = Depends(get_llm_service),
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


def get_capability_inference_service() -> CapabilityInferenceService:
    return CapabilityInferenceService()

def get_supervisor_graph(
    db: DBSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service),
    llm_service: LLMGateway = Depends(get_llm_service),
    capability_service: CapabilityInferenceService = Depends(get_capability_inference_service),
    knowledge_agent_graph: GraphRouter = Depends(get_graph_router),
) -> SupervisorGraph:
    planner = Planner(llm_service, capability_service)
    task_decomposer = TaskDecomposer()

    # Initialize Capability Framework
    cap_registry = CapabilityRegistry()
    cap_registry.register(GitHubCapability())
    cap_executor = CapabilityExecutor(cap_registry)

    registry = build_default_executive_registry(
        llm_service=llm_service,
        capability_executor=cap_executor,
        knowledge_agent_graph=knowledge_agent_graph,
    )

    collaboration_manager = CollaborationService(db).manager

    agent_router = AgentRouter(
        agent_registry=registry,
        knowledge_agent_graph=knowledge_agent_graph,
        collaboration_manager=collaboration_manager,
    )

    return SupervisorGraph(
        planner=planner,
        task_decomposer=task_decomposer,
        agent_router=agent_router,
        memory_service=memory_service,
        collaboration_manager=collaboration_manager,
    )


# ── Endpoint ────────────────────────────────────────────


@router.post("/chat", response_model=AgentChatResponse)
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
    session_id = memory_service.get_or_create_session(request.session_id)
    conversation_id = memory_service.get_or_create_conversation(
        session_id, request.conversation_id
    )
    memory_service.save_message(conversation_id, "user", request.question)

    # Use EnterpriseRuntime instead of SupervisorGraph directly
    runtime = runtime_manager.create_session(
        user_session_id=session_id,
        conversation_id=conversation_id,
        supervisor_graph=supervisor_graph
    )
    
    # Run via Runtime
    final_state = await runtime.start(request.question)
    
    # Cleanup session
    runtime_manager.cleanup_session(runtime.session.session_id)

    # Optionally trigger async summary and memory extraction
    final_conversation_id = str(
        final_state.get("conversation_id") or request.conversation_id or conversation_id
    )
    if final_conversation_id:
        background_tasks.add_task(
            memory_service.generate_summary, final_conversation_id
        )
        background_tasks.add_task(
            memory_service.extract_and_store_memories,
            conversation_id=final_conversation_id,
            user_id=request.session_id or "default_user",
            user_message=request.question,
            assistant_response=final_state.get("final_response") or "",
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
        sources=[],  # Sources could be extracted from tasks in the future
        execution_trace=[],
        metrics=metrics,
    )
