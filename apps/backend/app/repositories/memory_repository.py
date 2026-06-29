from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
from datetime import datetime
from uuid import UUID

from app.models.memory import MemoryObject


class MemoryRepository:
    """
    Repository for managing MemoryObjects in PostgreSQL.
    """

    def __init__(self, db: DBSession):
        self.db = db

    def add_memory(self, memory_data: dict) -> MemoryObject:
        db_memory = MemoryObject(**memory_data)
        self.db.add(db_memory)
        self.db.commit()
        self.db.refresh(db_memory)
        return db_memory

    def update_memory(self, memory_id: str, updates: dict) -> Optional[MemoryObject]:
        try:
            uid = UUID(memory_id)
        except ValueError:
            return None

        memory = self.db.query(MemoryObject).filter(MemoryObject.id == uid).first()
        if memory:
            for key, value in updates.items():
                setattr(memory, key, value)
            memory.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(memory)
        return memory

    def get_memory(self, memory_id: str) -> Optional[MemoryObject]:
        try:
            uid = UUID(memory_id)
        except ValueError:
            return None
        return self.db.query(MemoryObject).filter(MemoryObject.id == uid).first()

    def find_similar_memories(
        self, query: str, user_id: str, limit: int = 5
    ) -> List[MemoryObject]:
        """
        Placeholder for semantic search directly in DB if we used pgvector,
        but since we use Qdrant for semantics, this method might just do exact/like matching
        if needed, or we rely on Qdrant in the service layer.
        For phase 2.1, the service layer will call Qdrant, get IDs, and then we fetch them here.
        """
        pass

    def get_memories_by_ids(self, memory_ids: List[str]) -> List[MemoryObject]:
        uids = []
        for mid in memory_ids:
            try:
                uids.append(UUID(mid))
            except ValueError:
                pass
        return self.db.query(MemoryObject).filter(MemoryObject.id.in_(uids)).all()


class MemoryEntityRepository:
    """Placeholder for future Knowledge Graph evolution."""

    def __init__(self, db: DBSession):
        self.db = db


class MemoryRelationshipRepository:
    """Placeholder for future Knowledge Graph evolution."""

    def __init__(self, db: DBSession):
        self.db = db
