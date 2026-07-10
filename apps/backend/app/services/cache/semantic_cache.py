import asyncio
from typing import Optional, Dict, Any
from app.services.cache.models import CacheKey, CacheMetadata, CacheEntry
from app.services.cache.cache_manager import cache_manager
from app.operations.tracing.trace_manager import TraceManager


class SemanticCacheService:
    """
    High level service to interact with the cache manager and emit telemetry.
    """

    def __init__(self):
        self.manager = cache_manager
        self.trace_manager = TraceManager()

    def lookup(
        self, key: CacheKey, trace_id: Optional[str] = None
    ) -> Optional[CacheEntry]:
        import time

        start = time.time()

        span = self.trace_manager.start_span(
            trace_id=trace_id or "cache_lookup",
            operation="cache_lookup",
            tenant_id=key.tenant_id,
        )

        entry = self.manager.lookup(key)

        latency = (time.time() - start) * 1000
        span.attributes["lookup_latency_ms"] = latency

        if entry:
            span.attributes["cache_hit"] = True
            span.attributes["cache_saved_tokens"] = entry.metadata.token_usage
            span.attributes["cache_saved_cost"] = entry.metadata.estimated_cost
            self.trace_manager.end_span(span, "OK")
            # Also emit a specific cache_hit event for evaluation mapping
            hit_span = self.trace_manager.start_span(
                trace_id=trace_id or "cache_hit", operation="cache_hit"
            )
            hit_span.attributes.update(span.attributes)
            self.trace_manager.end_span(hit_span, "OK")
        else:
            span.attributes["cache_hit"] = False
            self.trace_manager.end_span(span, "OK")
            miss_span = self.trace_manager.start_span(
                trace_id=trace_id or "cache_miss", operation="cache_miss"
            )
            self.trace_manager.end_span(miss_span, "OK")

        return entry

    def store_async(
        self,
        key: CacheKey,
        question: str,
        response: str,
        metadata: CacheMetadata,
        trace_id: Optional[str] = None,
    ):
        """
        Fire and forget cache storage so it does not block the user response.
        """

        def _store():
            import time

            start = time.time()
            span = self.trace_manager.start_span(
                trace_id=trace_id or "cache_store", operation="cache_store"
            )
            try:
                self.manager.store_entry(key, question, response, metadata)
                latency = (time.time() - start) * 1000
                span.attributes["storage_latency_ms"] = latency
                self.trace_manager.end_span(span, "OK")
            except Exception as e:
                span.attributes["error"] = str(e)
                self.trace_manager.end_span(span, "ERROR")

        import threading

        threading.Thread(target=_store, daemon=True).start()
