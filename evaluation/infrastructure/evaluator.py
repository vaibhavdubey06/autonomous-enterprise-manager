from typing import List, Dict
from evaluation.models import EvaluationResult


class InfrastructureEvaluator:
    def evaluate(self, results: List[EvaluationResult]) -> Dict[str, float]:
        total = len(results)
        if total == 0:
            return {}

        successful = 0
        failed = 0
        skipped = 0
        provider_failures = 0
        quota_failures = 0
        timeout_failures = 0
        routing_failures = 0
        total_retries = 0

        for r in results:
            if r.execution_status == "SUCCESS":
                successful += 1
            elif r.execution_status == "SKIPPED":
                skipped += 1
            else:
                failed += 1
                cat = r.failure_category or ""
                if cat == "PROVIDER_QUOTA_FAILURE":
                    quota_failures += 1
                elif cat == "PROVIDER_TIMEOUT_FAILURE":
                    timeout_failures += 1
                elif cat == "ROUTING_FAILURE":
                    routing_failures += 1
                elif cat.startswith("PROVIDER"):
                    provider_failures += 1

            total_retries += r.retry_count

        availability = successful / total if total > 0 else 1.0
        provider_availability = (
            total - (provider_failures + quota_failures + timeout_failures)
        ) / total

        return {
            "availability": availability,
            "provider_availability": provider_availability,
            "provider_failure_rate": provider_failures / total,
            "quota_failure_rate": quota_failures / total,
            "timeout_rate": timeout_failures / total,
            "fallback_rate": routing_failures / total,
            "average_retry_count": total_retries / total,
            "infrastructure_completion": (successful + skipped) / total,
            "successful_requests": successful,
            "skipped_requests": skipped,
            "failed_requests": failed,
        }
