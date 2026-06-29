from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SessionSchema(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class ConversationSchema(BaseModel):
    id: str
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageSchema(BaseModel):
    id: str
    role: str
    content: str
    importance: float
    timestamp: datetime


class ConversationDetailSchema(ConversationSchema):
    messages: List[MessageSchema]


class KnowledgeItemSchema(BaseModel):
    id: Optional[str] = None


class MemoryObjectSchema(KnowledgeItemSchema):
    conversation_id: Optional[str] = None
    user_id: str
    memory_type: str
    title: str
    content: str
    importance: float = 0.5
    confidence: float = 0.5
    memory_status: str = "NEW"

    source: Optional[str] = None
    source_message_id: Optional[str] = None
    source_conversation_id: Optional[str] = None
    source_document_id: Optional[str] = None
    source_type: Optional[str] = None
    extracted_by: Optional[str] = None
    extraction_version: Optional[str] = None

    retrieval_count: int = 0
    last_accessed: Optional[datetime] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    metadata_: dict = {}
    tags: List[str] = []
    embedding_required: bool = True
