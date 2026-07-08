import time
import asyncio
from typing import Dict, Any

from app.services.llm.models import LLMRequest, LLMConfig
from app.services.llm.router.registry import provider_registry
from app.services.llm.router.routing_policy import RoutingPolicy
from app.services.llm.router.routing_engine import RoutingEngine
from app.services.llm.router.provider_health import provider_health_service

class ProviderEvaluator:
    """Evaluates and benchmarks multiple registered LLM providers."""
    
    def __init__(self):
        self.registry = provider_registry
        self.health = provider_health_service
        self.router = RoutingEngine(self.registry, self.health)
        
    def benchmark_providers(self, prompt: str = "Explain the theory of relativity in one sentence.") -> Dict[str, Any]:
        """Runs a benchmark across all registered providers."""
        results = {}
        request = LLMRequest(prompt=prompt, config=LLMConfig(temperature=0.0))
        
        for provider in self.registry.get_all():
            profile = provider.get_profile()
            name = profile.provider_name
            
            try:
                start = time.time()
                # Direct provider call for benchmarking latency natively
                response = provider.generate(request)
                latency = (time.time() - start) * 1000
                
                results[name] = {
                    "status": "success",
                    "latency_ms": latency,
                    "cost_input": profile.cost_input,
                    "cost_output": profile.cost_output,
                    "quality_score": profile.quality_score,
                    "health_score": self.health.get_health(name).health_score
                }
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e)
                }
                
        return results
        
    def evaluate_routing_policy(self, request: LLMRequest, policy: RoutingPolicy) -> str:
        """Evaluate which provider the router selects under a specific policy."""
        try:
            selected = self.router.select_provider(request, policy=policy)
            return selected.get_profile().provider_name
        except ValueError as e:
            return f"ROUTING_FAILED: {e}"
