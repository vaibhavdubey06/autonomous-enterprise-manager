from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    question: str

class ChatResponse(BaseModel):
    session_id: str
    conversation_id: str
    answer: str
    sources: List[Dict[str, Any]]
