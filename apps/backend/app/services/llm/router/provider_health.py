from typing import Dict
from pydantic import BaseModel
import time

class HealthStats(BaseModel):
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    rate_limit_count: int = 0
    retry_count: int = 0
    fallback_count: int = 0
    total_latency_ms: float = 0.0
    latencies: list[float] = []
    total_tokens: int = 0
    total_cost: float = 0.0
    
    @property
    def total_requests(self) -> int:
        return self.success_count + self.failure_count + self.timeout_count + self.rate_limit_count
        
    @property
    def average_latency(self) -> float:
        if self.success_count == 0:
            return 0.0
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0
        
    @property
    def p50_latency(self) -> float:
        if not self.latencies: return 0.0
        return sorted(self.latencies)[len(self.latencies)//2]
        
    @property
    def p95_latency(self) -> float:
        if not self.latencies: return 0.0
        idx = int(len(self.latencies) * 0.95)
        return sorted(self.latencies)[min(idx, len(self.latencies)-1)]
        
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.success_count / self.total_requests
        
    @property
    def health_score(self) -> float:
        """Calculate a generic health score between 0.0 and 1.0"""
        # Penalize for timeouts and rate limits, highly penalize failures
        if self.total_requests == 0:
            return 1.0
            
        penalty = (
            (self.failure_count * 1.0) +
            (self.timeout_count * 0.5) +
            (self.rate_limit_count * 0.3)
        )
        
        score = 1.0 - (penalty / self.total_requests)
        return max(0.0, score)
        
    @property
    def availability(self) -> str:
        score = self.health_score
        if score > 0.95:
            return "healthy"
        if score > 0.7:
            return "degraded"
        return "offline"


class ProviderHealthService:
    """Service to track rolling statistics for each LLM provider."""
    
    def __init__(self):
        self._stats: Dict[str, HealthStats] = {}
        
    def _get_stats(self, provider_name: str) -> HealthStats:
        if provider_name not in self._stats:
            self._stats[provider_name] = HealthStats()
        return self._stats[provider_name]
        
    def record_success(self, provider_name: str, latency_ms: float, tokens: int = 0, cost: float = 0.0) -> None:
        stats = self._get_stats(provider_name)
        stats.success_count += 1
        stats.total_latency_ms += latency_ms
        stats.latencies.append(latency_ms)
        stats.total_tokens += tokens
        stats.total_cost += cost
        
    def record_failure(self, provider_name: str, error_type: str = "general") -> None:
        stats = self._get_stats(provider_name)
        if error_type == "timeout":
            stats.timeout_count += 1
        elif error_type == "rate_limit":
            stats.rate_limit_count += 1
        else:
            stats.failure_count += 1
            
    def record_retry(self, provider_name: str) -> None:
        stats = self._get_stats(provider_name)
        stats.retry_count += 1
        
    def record_fallback(self, provider_name: str) -> None:
        stats = self._get_stats(provider_name)
        stats.fallback_count += 1
        
    def get_health(self, provider_name: str) -> HealthStats:
        return self._get_stats(provider_name)

# Singleton health service
provider_health_service = ProviderHealthService()
