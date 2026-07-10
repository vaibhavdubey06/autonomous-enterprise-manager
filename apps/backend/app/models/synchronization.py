from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime, timezone
from app.core.database import Base


class SyncCheckpoint(Base):
    __tablename__ = "sync_checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    connector_id = Column(String, index=True, nullable=False)
    resource_id = Column(String, index=True, nullable=False)
    last_synced_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    state = Column(JSON, nullable=True)  # Store cursor/etag/sha


class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, index=True, nullable=False)
    connector_id = Column(String, index=True, nullable=False)
    version_hash = Column(String, nullable=False)
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    metadata_snapshot = Column(JSON, nullable=True)
