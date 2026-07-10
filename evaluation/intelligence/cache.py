from evaluation.models import EvaluationResult


class CacheEvaluator:
    def evaluate(self, result: EvaluationResult) -> dict:
        total_lookups = 0
        cache_hits = 0
        tokens_saved = 0
        cost_saved = 0.0
        lookup_latencies = []
        storage_latencies = []

        for span in result.traces:
            if span.get("operation") == "cache_lookup":
                total_lookups += 1
                attrs = span.get("attributes", {})
                lookup_latencies.append(attrs.get("lookup_latency_ms", 0.0))

                if attrs.get("cache_hit") is True:
                    cache_hits += 1
                    tokens_saved += attrs.get("cache_saved_tokens", 0)
                    cost_saved += attrs.get("cache_saved_cost", 0.0)

            elif span.get("operation") == "cache_store":
                attrs = span.get("attributes", {})
                storage_latencies.append(attrs.get("storage_latency_ms", 0.0))

        cache_hit_rate = (cache_hits / total_lookups) if total_lookups > 0 else 0.0
        avg_lookup_latency = (
            sum(lookup_latencies) / len(lookup_latencies) if lookup_latencies else 0.0
        )
        avg_storage_latency = (
            sum(storage_latencies) / len(storage_latencies)
            if storage_latencies
            else 0.0
        )

        return {
            "cache_hit_rate": cache_hit_rate,
            "cache_miss_rate": 1.0 - cache_hit_rate if total_lookups > 0 else 0.0,
            "total_lookups": total_lookups,
            "cache_hits": cache_hits,
            "tokens_saved": tokens_saved,
            "cost_saved": cost_saved,
            "avg_lookup_latency": avg_lookup_latency,
            "avg_storage_latency": avg_storage_latency,
        }
