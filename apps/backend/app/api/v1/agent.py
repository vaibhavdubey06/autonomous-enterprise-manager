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


# Instantiate globally to prevent httpx client issues with FastAPI threadpools
try:
    _cross_encoder_service = CrossEncoderService()
except Exception as e:
    logger.error(f"Failed to instantiate CrossEncoderService at startup: {e}")
    _cross_encoder_service = None


def get_cross_encoder_service() -> CrossEncoderService:
    global _cross_encoder_service
    if _cross_encoder_service is None:
        _cross_encoder_service = CrossEncoderService()
    return _cross_encoder_service


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
    capability_service: CapabilityInferenceService = Depends(
        get_capability_inference_service
    ),
    knowledge_agent_graph: GraphRouter = Depends(get_graph_router),
) -> SupervisorGraph:
    # Initialize Capability Framework
    cap_registry = CapabilityRegistry()
    cap_registry.register(GitHubCapability())
    cap_executor = CapabilityExecutor(cap_registry)

    registry = build_default_executive_registry(
        llm_service=llm_service,
        capability_executor=cap_executor,
        knowledge_agent_graph=knowledge_agent_graph,
    )

    planner = Planner(llm_service, capability_service, agent_registry=registry)
    task_decomposer = TaskDecomposer()

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
    The API layer remains thin — all validation happens inside EnterpriseRuntime.
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
        supervisor_graph=supervisor_graph,
    )

    # Run via Runtime (includes PreExecution pipeline)
    try:
        final_state = await runtime.start(request.question)
    except Exception as e:
        from app.services.llm.exceptions import GuardrailException
        if isinstance(e, GuardrailException):
            logger.warning(f"Guardrail violation during chat: {e}")
            findings_str = "; ".join([f"{f.message}" for f in e.findings])
            friendly_message = f"Your request was blocked by our security guardrails. {findings_str}"
            if not e.findings:
                friendly_message = "Your request was blocked by our security guardrails."
            
            # Form a state indicating rejection so we return it nicely to the UI
            final_state = {
                "final_response": friendly_message,
                "workflow_state": "REJECTED",
                "execution_time_ms": 0.0,
                "selected_agents": [],
                "completed_tasks": [],
                "failed_tasks": []
            }
        else:
            raise

    # Cleanup session
    runtime_manager.cleanup_session(runtime.session.session_id)

    # Save assistant response
    final_response = final_state.get("final_response") or ""
    memory_service.save_message(conversation_id, "assistant", final_response)

    # ── Background tasks with isolated DB sessions ──────────────
    # Each background task creates its own SessionLocal + MemoryService
    # so a poisoned request-scoped session never cascades.
    final_conversation_id = str(
        final_state.get("conversation_id") or request.conversation_id or conversation_id
    )
    if final_conversation_id:
        background_tasks.add_task(
            _background_generate_summary, final_conversation_id
        )
        background_tasks.add_task(
            _background_extract_memories,
            conversation_id=final_conversation_id,
            user_id=request.session_id or "default_user",
            user_message=request.question,
            assistant_response=final_response,
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
        answer=final_response,
        sources=[],  # Sources could be extracted from tasks in the future
        execution_trace=[],
        metrics=metrics,
    )


# ── Isolated background task helpers ────────────────────────────


def _build_isolated_memory_service():
    """Create a MemoryService with its own DB session, fully independent of the request."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    llm_service = get_llm_service()

    memory_repo = MemoryRepository(db)
    strategy = GeminiMemoryExtractionStrategy(llm_service)
    normalizer = MemoryNormalizer()
    scorer = ImportanceScorer()
    deduplicator = MemoryDeduplicator(memory_repo)

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

    svc = MemoryService(
        session_repo=SessionRepository(db),
        conversation_repo=ConversationRepository(db),
        message_repo=MessageRepository(db),
        summary_repo=SummaryRepository(db),
        memory_repo=memory_repo,
        llm_service=llm_service,
        extractor=extractor,
    )
    return svc, db


def _background_generate_summary(conversation_id: str):
    """Background task: generate rolling summary with an isolated DB session."""
    from app.operations.tracing.trace_manager import TraceManager

    trace_manager = TraceManager()
    span = trace_manager.start_span(
        trace_id=conversation_id,
        operation="background_summary",
    )

    svc, db = _build_isolated_memory_service()
    try:
        svc.generate_summary(conversation_id)
        trace_manager.end_span(span, "OK")
    except Exception as e:
        logger.error(f"Background summary failed (isolated): {e}")
        span.attributes["error"] = str(e)
        trace_manager.end_span(span, "ERROR")
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


async def _background_extract_memories(
    conversation_id: str,
    user_id: str,
    user_message: str,
    assistant_response: str,
):
    """Background task: extract and store memories with an isolated DB session."""
    from app.operations.tracing.trace_manager import TraceManager

    trace_manager = TraceManager()
    span = trace_manager.start_span(
        trace_id=conversation_id,
        operation="background_memory",
    )

    svc, db = _build_isolated_memory_service()
    try:
        await svc.extract_and_store_memories(
            conversation_id=conversation_id,
            user_id=user_id,
            user_message=user_message,
            assistant_response=assistant_response,
        )
        trace_manager.end_span(span, "OK")
    except Exception as e:
        logger.error(f"Background memory extraction failed (isolated): {e}")
        span.attributes["error"] = str(e)
        trace_manager.end_span(span, "ERROR")
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()
