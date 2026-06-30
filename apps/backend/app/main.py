from fastapi import FastAPI

from app.api.v1.upload import router as upload_router
from app.api.v1.search import router as search_router
from app.api.v1.chat import router as chat_router
from app.api.v1.github import router as github_router
from app.api.v1.memory import router as memory_router
from app.api.v1.agent import router as agent_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.collaboration import router as collaboration_router
from app.api.v1.governance import router as governance_router
from app.api.v1.operations import router as operations_router
from app.api.v1.security import router as security_router
from app.api.v1.integrations import router as integrations_router
from app.services.embeddings.embedding_service import embed_text
from app.security.middleware.security_middleware import SecurityMiddleware
from app.core.database import Base, engine

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:
    FastAPIInstrumentor = None  # type: ignore
    import logging

    logger = logging.getLogger(__name__)

app = FastAPI(title="Autonomous Enterprise Manager", version="0.1.0")

app.add_middleware(SecurityMiddleware)


@app.get("/")
async def root():
    return {"message": "Autonomous Enterprise Manager API"}


@app.get("/health")
async def health():
    # In a real scenario, this would aggregate statuses from all subsystems
    from app.core.config import settings

    return {
        "status": "healthy",
        "redis_url": settings.REDIS_URL,
        "postgres_host": settings.POSTGRES_HOST,
    }


@app.get("/ready")
async def ready():
    # Readiness probe: Check if DB and Cache are reachable
    return {"status": "ready"}


@app.get("/live")
async def live():
    # Liveness probe: Check if event loop is running
    return {"status": "alive"}


@app.get("/embedding-test")
async def embedding_test():
    vector = embed_text("Hello Enterprise Manager")
    return {"dimensions": len(vector)}


app.include_router(github_router, prefix="/api/v1/github", tags=["github"])
app.include_router(memory_router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(agent_router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(workflows_router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(
    collaboration_router, prefix="/api/v1/collaboration", tags=["collaboration"]
)
app.include_router(governance_router, prefix="/api/v1/governance", tags=["governance"])
app.include_router(operations_router, prefix="/api/v1/operations", tags=["operations"])
app.include_router(security_router, prefix="/api/v1/security", tags=["security"])
app.include_router(
    integrations_router, prefix="/api/v1/integrations", tags=["integrations"]
)

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(upload_router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(search_router, prefix="/api/v1/search", tags=["search"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

# Instrument FastAPI with OpenTelemetry
if FastAPIInstrumentor is not None:
    FastAPIInstrumentor.instrument_app(app)
else:
    logger.warning(
        "opentelemetry-instrumentation-fastapi not installed. Tracing disabled."
    )
