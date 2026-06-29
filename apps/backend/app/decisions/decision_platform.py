"""Enterprise Decision Intelligence Platform - Decision records as first-class knowledge."""

import logging
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DecisionStatus(Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    SUPERSEDED = "superseded"


class DecisionCategory(Enum):
    TECHNOLOGY = "technology"
    ARCHITECTURE = "architecture"
    BUDGET = "budget"
    GOVERNANCE = "governance"
    RISK = "risk"
    STRATEGY = "strategy"
    OPERATIONAL = "operational"


class DecisionRecord:
    """An enterprise decision captured as a first-class knowledge asset."""

    def __init__(
        self,
        title: str,
        category: DecisionCategory,
        context: str,
        problem: str,
        decision: str,
        rationale: str,
        alternatives: Optional[List[str]] = None,
        confidence: float = 0.8,
        owner: str = "",
        stakeholders: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.decision_id = str(uuid.uuid4())
        self.title = title
        self.category = category
        self.context = context
        self.problem = problem
        self.decision = decision
        self.rationale = rationale
        self.alternatives = alternatives or []
        self.confidence = confidence
        self.owner = owner
        self.stakeholders = stakeholders or []
        self.status = DecisionStatus.PROPOSED
        self.outcome: Optional[str] = None
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.updated_at = time.time()
        self.relationships: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "category": self.category.value,
            "context": self.context,
            "problem": self.problem,
            "decision": self.decision,
            "rationale": self.rationale,
            "alternatives": self.alternatives,
            "confidence": self.confidence,
            "status": self.status.value,
            "outcome": self.outcome,
            "owner": self.owner,
            "stakeholders": self.stakeholders,
            "created_at": self.created_at,
        }


class DecisionRegistry:
    """Central registry for enterprise decision records."""

    def __init__(self) -> None:
        self._decisions: Dict[str, DecisionRecord] = {}

    def create(self, record: DecisionRecord) -> str:
        self._decisions[record.decision_id] = record
        logger.info(f"Decision recorded: {record.title}")
        return record.decision_id

    def get(self, decision_id: str) -> Optional[Dict[str, Any]]:
        record = self._decisions.get(decision_id)
        return record.to_dict() if record else None

    def update_status(self, decision_id: str, status: DecisionStatus) -> bool:
        record = self._decisions.get(decision_id)
        if record:
            record.status = status
            record.updated_at = time.time()
            return True
        return False

    def record_outcome(self, decision_id: str, outcome: str) -> bool:
        record = self._decisions.get(decision_id)
        if record:
            record.outcome = outcome
            record.status = DecisionStatus.IMPLEMENTED
            record.updated_at = time.time()
            return True
        return False

    def search(
        self,
        category: Optional[DecisionCategory] = None,
        status: Optional[DecisionStatus] = None,
        owner: Optional[str] = None,
        query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = list(self._decisions.values())
        if category:
            results = [d for d in results if d.category == category]
        if status:
            results = [d for d in results if d.status == status]
        if owner:
            results = [d for d in results if d.owner == owner]
        if query:
            q = query.lower()
            results = [
                d
                for d in results
                if q in d.title.lower()
                or q in d.context.lower()
                or q in d.decision.lower()
            ]
        return [d.to_dict() for d in results]

    def list_all(self) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._decisions.values()]

    def add_relationship(self, decision_id: str, related_decision_id: str) -> bool:
        record = self._decisions.get(decision_id)
        if record and related_decision_id in self._decisions:
            record.relationships.append(related_decision_id)
            return True
        return False
