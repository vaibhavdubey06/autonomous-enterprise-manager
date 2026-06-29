class SLOTracker:
    def __init__(self, cache_provider):
        self.cache_provider = cache_provider
        self.target_availability = 0.999

    def record_success(self):
        self.cache_provider.increment("slo:success_count")

    def record_failure(self):
        self.cache_provider.increment("slo:error_count")

    def get_availability(self) -> float:
        success = self.cache_provider.get("slo:success_count") or 0
        errors = self.cache_provider.get("slo:error_count") or 0

        total = success + errors
        if total == 0:
            return 1.0

        return success / total

    def get_error_budget_remaining(self) -> float:
        self.get_availability()
        # simplified calculation: budget is the allowance of errors.
        # if target is 99.9%, allowance is 0.1% of total requests.
        success = self.cache_provider.get("slo:success_count") or 0
        errors = self.cache_provider.get("slo:error_count") or 0
        total = success + errors

        allowed_errors = total * (1.0 - self.target_availability)

        if allowed_errors == 0:
            return 100.0  # 100% budget remaining if 0 allowed/0 errors

        remaining = max(0.0, allowed_errors - errors)
        return (remaining / allowed_errors) * 100.0
