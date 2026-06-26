from pydantic import BaseModel

class SearchRequest(BaseModel):
    """
    Schema for semantic search request.
    """
    query: str
