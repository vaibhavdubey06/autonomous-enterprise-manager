from pydantic import BaseModel
from typing import List

class SourceCitation(BaseModel):
    document: str
    page: int
    chunk: int

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
