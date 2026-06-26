from fastapi import APIRouter

from app.schemas.search import SearchRequest
from app.services.vectorstore.qdrant_service import search

router = APIRouter()

@router.post("/search")
async def perform_search(request: SearchRequest):
    """
    Perform a semantic search against the uploaded documents.
    """
    results = search(query=request.query, limit=5)
    return {"results": results}
