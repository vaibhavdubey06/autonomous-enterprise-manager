"""Pre-defined domain events emitted by major subsystems."""

from typing import Any, Dict, Optional

from app.events.base.interfaces import DomainEvent, EventPriority


class WorkflowCompletedEvent(DomainEvent):
    def __init__(
        self,
        workflow_id: str,
        result: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        super().__init__(
            event_type="workflow.completed",
            payload={"workflow_id": workflow_id, "result": result},
            source="workflow_runtime",
            correlation_id=correlation_id,
        )


class PolicyViolationEvent(DomainEvent):
    def __init__(
        self, policy_id: str, violation: str, correlation_id: Optional[str] = None
    ):
        super().__init__(
            event_type="governance.policy_violation",
            payload={"policy_id": policy_id, "violation": violation},
            source="governance_runtime",
            correlation_id=correlation_id,
            priority=EventPriority.HIGH,
        )


class ConnectorHealthChangedEvent(DomainEvent):
    def __init__(
        self, connector_id: str, status: str, correlation_id: Optional[str] = None
    ):
        super().__init__(
            event_type="integration.connector_health_changed",
            payload={"connector_id": connector_id, "status": status},
            source="integration_platform",
            correlation_id=correlation_id,
        )


class MemoryCreatedEvent(DomainEvent):
    def __init__(
        self, memory_id: str, memory_type: str, correlation_id: Optional[str] = None
    ):
        super().__init__(
            event_type="memory.created",
            payload={"memory_id": memory_id, "memory_type": memory_type},
            source="memory_platform",
            correlation_id=correlation_id,
        )


class SecurityIncidentEvent(DomainEvent):
    def __init__(
        self,
        incident_type: str,
        details: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        super().__init__(
            event_type="security.incident",
            payload={"incident_type": incident_type, "details": details},
            source="security_platform",
            correlation_id=correlation_id,
            priority=EventPriority.CRITICAL,
        )
