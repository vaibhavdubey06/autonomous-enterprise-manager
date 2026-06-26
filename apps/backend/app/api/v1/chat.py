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

def get_memory_service(
    db: DBSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service)
) -> MemoryService:
    return MemoryService(
        session_repo=SessionRepository(db),
        conversation_repo=ConversationRepository(db),
        message_repo=MessageRepository(db),
        summary_repo=SummaryRepository(db),
        llm_service=llm_service
    )

def get_chat_service(
    llm_service: LLMService = Depends(get_llm_service),
    reranker_service: CrossEncoderService = Depends(get_cross_encoder_service),
    memory_service: MemoryService = Depends(get_memory_service)
) -> ChatService:
    return ChatService(llm_service=llm_service, reranker_service=reranker_service, memory_service=memory_service)

from fastapi import BackgroundTasks

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    RAG endpoint to generate AI answers based on uploaded documents and long-term memory.
    """
    result = chat_service.chat(
        question=request.question,
        session_id=request.session_id,
        conversation_id=request.conversation_id,
        background_tasks=background_tasks
    )
    return ChatResponse(**result)
