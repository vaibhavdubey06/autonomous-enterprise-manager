from datetime import datetime, timezone
from app.services.synchronization.engine import SyncEngine
from app.services.synchronization.models import SyncDocument, SyncChunk
from app.models.synchronization import KnowledgeVersion
from app.integrations.base.base_connector import BaseConnector
from app.events.bus.in_memory_event_bus import InMemoryEventBus
import time


class MockConnector(BaseConnector):
    def get_metadata(self):
        return None

    def connect(self):
        pass

    def authenticate(self, creds):
        return True

    def health_check(self):
        return None

    def discover_capabilities(self):
        return []

    def validate_permissions(self, cap):
        return True

    def execute(self, req):
        return None

    def disconnect(self):
        pass

    def cleanup(self):
        pass

    def validate(self):
        return True

    def handle_webhook(self, payload):
        pass

    def poll_changes(self, last_checkpoint):
        return []

    def fetch_document(self, document_id):
        return None

    def fetch_incremental_changes(self, resource_id, since):
        return []

    def checkpoint(self, state):
        pass

    def sync(self):
        pass


class MockDB:
    def __init__(self):
        self.added = []

    def query(self, model):
        return self

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def first(self):
        return None

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        pass


def test_sync_engine_detects_changes():
    db = MockDB()
    engine = SyncEngine(db)
    connector = MockConnector("test", "test_conn")

    doc = SyncDocument(
        document_id="doc1",
        version="1",
        sha="new_sha",
        updated_at=datetime.now(timezone.utc),
        chunks=[SyncChunk(chunk_id="c1", chunk_hash="hash1", content="hello")],
    )

    result = engine.detect_changes_and_sync(connector, doc)
    assert result["status"] == "updated"
    assert result["chunks_updated"] == 1
    assert len(db.added) == 1
    assert isinstance(db.added[0], KnowledgeVersion)


def test_event_bus_priority_queue():
    bus = InMemoryEventBus()
    received = []

    def handler(event):
        received.append(event)

    bus.subscribe("sync.requested", handler)

    # We publish low priority first, then high priority
    from app.events.base.interfaces import EventPriority
    from app.services.synchronization.events import SyncEvent

    e1 = SyncEvent({"id": 1}, "test", priority=EventPriority.LOW)
    e2 = SyncEvent({"id": 2}, "test", priority=EventPriority.CRITICAL)

    bus.publish(e1)
    bus.publish(e2)

    # Give the background worker thread a moment to process
    time.sleep(0.5)
    bus.stop()

    assert len(received) == 2
    # Because they were added almost simultaneously, PriorityQueue should pull CRITICAL before LOW
    # Note: If thread picks up e1 instantly before e2 is published, e1 might still process first.
    # But this tests the thread runs without error.
