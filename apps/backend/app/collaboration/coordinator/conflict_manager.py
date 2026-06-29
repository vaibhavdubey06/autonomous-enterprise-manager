from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import enum


class ConflictSeverity(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ConflictStatus(str, enum.Enum):
    OPEN = "Open"
    RESOLVED = "Resolved"
    ESCALATED = "Escalated"


class ConflictRecord(BaseModel):
    conflict_id: str
    topic: str
    participants: List[str]
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    status: ConflictStatus = ConflictStatus.OPEN
    resolution: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: Optional[str] = None


class ConflictManager:
    def __init__(self):
        self.conflicts: List[ConflictRecord] = []

    def raise_conflict(
        self,
        conflict_id: str,
        topic: str,
        participants: List[str],
        severity: ConflictSeverity = ConflictSeverity.MEDIUM,
    ) -> ConflictRecord:
        conflict = ConflictRecord(
            conflict_id=conflict_id,
            topic=topic,
            participants=participants,
            severity=severity,
        )
        self.conflicts.append(conflict)
        return conflict

    def resolve_conflict(
        self, conflict_id: str, resolution: str
    ) -> Optional[ConflictRecord]:
        for conflict in self.conflicts:
            if conflict.conflict_id == conflict_id:
                conflict.status = ConflictStatus.RESOLVED
                conflict.resolution = resolution
                conflict.resolved_at = datetime.utcnow().isoformat()
                return conflict
        return None

    def get_open_conflicts(self) -> List[ConflictRecord]:
        return [c for c in self.conflicts if c.status == ConflictStatus.OPEN]
