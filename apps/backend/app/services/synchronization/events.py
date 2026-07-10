from typing import Any, Dict
from app.events.base.interfaces import DomainEvent, EventPriority


class SyncEvent(DomainEvent):
    """Base synchronization event."""

    def __init__(
        self,
        payload: Dict[str, Any],
        source: str,
        priority: EventPriority = EventPriority.NORMAL,
    ):
        super().__init__(
            event_type="sync.requested",
            payload=payload,
            source=source,
            priority=priority,
        )


class GitHubPushEvent(SyncEvent):
    """Typed event for GitHub pushes."""

    def __init__(
        self,
        repo_id: str,
        commits: list,
        source: str = "github_connector",
        priority: EventPriority = EventPriority.HIGH,
    ):
        payload = {
            "connector_id": "github",
            "resource_id": repo_id,
            "mode": "push",
            "commits": commits,
        }
        super().__init__(payload=payload, source=source, priority=priority)


class SlackMessageEvent(SyncEvent):
    """Typed event for Slack messages."""

    def __init__(
        self,
        channel_id: str,
        message: dict,
        source: str = "slack_connector",
        priority: EventPriority = EventPriority.NORMAL,
    ):
        payload = {
            "connector_id": "slack",
            "resource_id": channel_id,
            "mode": "push",
            "message": message,
        }
        super().__init__(payload=payload, source=source, priority=priority)


class PollRequestedEvent(SyncEvent):
    """Typed event to trigger a polling sync for a specific resource."""

    def __init__(
        self,
        connector_id: str,
        resource_id: str,
        source: str = "scheduler",
        priority: EventPriority = EventPriority.LOW,
    ):
        payload = {
            "connector_id": connector_id,
            "resource_id": resource_id,
            "mode": "poll",
        }
        super().__init__(payload=payload, source=source, priority=priority)
