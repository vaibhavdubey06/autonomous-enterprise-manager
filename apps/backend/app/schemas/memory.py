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
