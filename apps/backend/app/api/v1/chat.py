from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.llm.llm_service import LLMService

router = APIRouter()

from functools import lru_cache
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.services.reranking.cross_encoder_service import CrossEncoderService
from app.services.memory_service import MemoryService
from app.repositories.session_repository import SessionRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.summary_repository import SummaryRepository


@lru_cache()
def get_llm_service() -> LLMService:
    return LLMService()


@lru_cache()
def get_cross_encoder_service() -> CrossEncoderService:
    return CrossEncoderService()


from app.repositories.memory_repository import MemoryRepository
from app.services.memory.extractor import MemoryExtractor
from app.services.memory.strategy import GeminiMemoryExtractionStrategy
from app.services.memory.normalizer import MemoryNormalizer
from app.services.memory.scorer import ImportanceScorer
from app.services.memory.deduplicator import MemoryDeduplicator
from app.services.vectorstore.qdrant_service import search
from app.core.config import settings


def get_memory_service(
    db: DBSession = Depends(get_db), llm_service: LLMService = Depends(get_llm_service)
) -> MemoryService:
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

    return MemoryService(
        session_repo=SessionRepository(db),
        conversation_repo=ConversationRepository(db),
        message_repo=MessageRepository(db),
        summary_repo=SummaryRepository(db),
        memory_repo=memory_repo,
        llm_service=llm_service,
        extractor=extractor,
    )


def get_chat_service(
    llm_service: LLMService = Depends(get_llm_service),
    reranker_service: CrossEncoderService = Depends(get_cross_encoder_service),
    memory_service: MemoryService = Depends(get_memory_service),
) -> ChatService:
    return ChatService(
        llm_service=llm_service,
        reranker_service=reranker_service,
        memory_service=memory_service,
    )


from fastapi import BackgroundTasks


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    RAG endpoint to generate AI answers based on uploaded documents and long-term memory.
    """
    result = chat_service.chat(
        question=request.question,
        session_id=request.session_id,
        conversation_id=request.conversation_id,
        background_tasks=background_tasks,
    )
    return ChatResponse(**result)
