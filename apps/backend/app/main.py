from fastapi import FastAPI

from app.api.v1.upload import router as upload_router
from app.api.v1.search import router as search_router
from app.api.v1.chat import router as chat_router
from app.services.embeddings.embedding_service import embed_text

app = FastAPI(
    title="Autonomous Enterprise Manager",
    version="0.1.0"
)


@app.get("/")
async def root():
    return {
        "message": "Autonomous Enterprise Manager API"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.get("/embedding-test")
async def embedding_test():

    vector = embed_text(
        "Hello Enterprise Manager"
    )

    return {
        "dimensions": len(vector)
    }


from app.api.v1.github import router as github_router
from app.api.v1.memory import router as memory_router
from app.api.v1.agent import router as agent_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.collaboration import router as collaboration_router
from app.api.v1.governance import router as governance_router

app.include_router(github_router, prefix="/api/v1/github", tags=["github"])
app.include_router(memory_router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(agent_router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(workflows_router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(collaboration_router, prefix="/api/v1/collaboration", tags=["collaboration"])
app.include_router(governance_router, prefix="/api/v1/governance", tags=["governance"])
from app.core.database import Base, engine

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(upload_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(github_router)
app.include_router(memory_router)
app.include_router(agent_router)