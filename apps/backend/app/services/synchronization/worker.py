import logging
from typing import Dict, Any, Type
from app.events.base.interfaces import DomainEvent, EventBus
from app.services.synchronization.engine import SyncEngine
from app.integrations.base.connector_registry import connector_registry
from app.core.database import SessionLocal
from app.operations.tracing.trace_manager import TraceManager
import time

logger = logging.getLogger(__name__)
trace_manager = TraceManager()

class SyncWorker:
    """Background worker that listens to SyncEvents and orchestrates the SyncEngine."""
    
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.bus.subscribe("sync.requested", self.handle_sync_request)
        
    def handle_sync_request(self, event: DomainEvent) -> None:
        start_time = time.time()
        payload = event.payload
        connector_id = payload.get("connector_id")
        resource_id = payload.get("resource_id")
        
        with trace_manager.trace("sync_job", connector_id=connector_id, resource_id=resource_id, mode=payload.get("mode")) as span:
            try:
                connector_class = connector_registry.get(connector_id)
                if not connector_class:
                    raise ValueError(f"Connector {connector_id} not found in registry.")
                    
                connector = connector_class(tenant_id="default", connector_id=connector_id)
                
                # Fetch recent changes based on mode
                with trace_manager.span(span.trace_id, "fetch_changes", span.span_id) as fetch_span:
                    if payload.get("mode") == "push":
                        changes = connector.handle_webhook(payload)
                    else:
                        # Polling mode logic here (e.g., getting checkpoint and polling)
                        changes = []
                        
                    fetch_span.attributes["changes_detected"] = len(changes) if changes else 0
                
                if not changes:
                    span.attributes["status"] = "no_changes"
                    return
                    
                # Orchestrate embedding and updating
                with SessionLocal() as db:
                    engine = SyncEngine(db)
                    total_chunks_updated = 0
                    
                    with trace_manager.span(span.trace_id, "process_changes", span.span_id) as process_span:
                        for change in changes:
                            # change should be parsed to a SyncDocument. 
                            # We'll assume the connector returns SyncDocument objects.
                            result = engine.detect_changes_and_sync(connector, change)
                            total_chunks_updated += result.get("chunks_updated", 0)
                            
                        process_span.attributes["documents_processed"] = len(changes)
                        process_span.attributes["total_chunks_updated"] = total_chunks_updated
                        
                span.attributes["status"] = "success"
                
            except Exception as e:
                logger.error(f"Sync worker failed for {connector_id} - {resource_id}: {str(e)}")
                span.attributes["status"] = "failed"
                span.attributes["error"] = str(e)
                raise
            finally:
                duration = time.time() - start_time
                span.attributes["duration_seconds"] = duration
