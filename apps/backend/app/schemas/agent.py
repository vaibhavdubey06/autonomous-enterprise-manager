"""
Agent Schemas — Request/Response models for the /agent/ endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class AgentChatRequest(BaseModel):
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    question: str


class AgentChatResponse(BaseModel):
    session_id: str
    conversation_id: str
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
