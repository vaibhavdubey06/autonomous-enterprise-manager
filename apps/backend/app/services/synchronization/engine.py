import hashlib
import logging
from typing import Any, Dict
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.services.synchronization.models import SyncDocument
from app.models.synchronization import KnowledgeVersion
from app.integrations.base.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class SyncEngine:
    """Core orchestration engine for Knowledge Synchronization Platform."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def _compute_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def detect_changes_and_sync(
        self, connector: BaseConnector, document: SyncDocument
    ) -> Dict[str, Any]:
        """
        Determines which chunks have changed and orchestrates their re-embedding.
        """
        existing_version = (
            self.db.query(KnowledgeVersion)
            .filter(
                KnowledgeVersion.document_id == document.document_id,
                KnowledgeVersion.connector_id == connector.connector_id,
            )
            .order_by(KnowledgeVersion.id.desc())
            .first()
        )

        # Document-level deduplication
        if existing_version and existing_version.version_hash == document.sha:
            logger.info(f"Document {document.document_id} is unchanged. Skipping.")
            return {"status": "skipped", "reason": "unchanged"}

        # Chunk-level diffing
        existing_chunks = {}
        if existing_version and existing_version.metadata_snapshot:
            for chunk_data in existing_version.metadata_snapshot.get("chunks", []):
                existing_chunks[chunk_data["chunk_id"]] = chunk_data["chunk_hash"]

        chunks_to_embed = []
        for chunk in document.chunks:
            if (
                chunk.chunk_id not in existing_chunks
                or existing_chunks[chunk.chunk_id] != chunk.chunk_hash
            ):
                chunks_to_embed.append(chunk)

        if chunks_to_embed:
            logger.info(
                f"Re-embedding {len(chunks_to_embed)} changed chunks for {document.document_id}."
            )

        # Save new KnowledgeVersion
        new_version = KnowledgeVersion(
            document_id=document.document_id,
            connector_id=connector.connector_id,
            version_hash=document.sha,
            updated_at=datetime.now(timezone.utc),
            metadata_snapshot={
                "chunks": [
                    {"chunk_id": c.chunk_id, "chunk_hash": c.chunk_hash}
                    for c in document.chunks
                ],
                "source_metadata": document.metadata,
            },
        )
        self.db.add(new_version)
        self.db.commit()

        return {
            "status": "updated",
            "chunks_updated": len(chunks_to_embed),
            "total_chunks": len(document.chunks),
        }
