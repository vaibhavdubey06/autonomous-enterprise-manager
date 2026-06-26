from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.llm.llm_service import LLMService

router = APIRouter()

from functools import lru_cache
from app.services.reranking.cross_encoder_service import CrossEncoderService

@lru_cache()
def get_llm_service() -> LLMService:
    return LLMService()

@lru_cache()
def get_cross_encoder_service() -> CrossEncoderService:
    return CrossEncoderService()

def get_chat_service(
    llm_service: LLMService = Depends(get_llm_service),
    reranker_service: CrossEncoderService = Depends(get_cross_encoder_service)
) -> ChatService:
    return ChatService(llm_service=llm_service, reranker_service=reranker_service)

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)):
    """
    RAG endpoint to generate AI answers based on uploaded documents.
    """
    result = chat_service.chat(request.question)
    return ChatResponse(**result)
