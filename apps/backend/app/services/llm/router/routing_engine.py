import logging
from typing import List, Optional, Set

from app.services.llm.providers.base import AbstractLLMProvider
from app.services.llm.router.registry import ProviderRegistry
from app.services.llm.router.provider_health import ProviderHealthService
from app.services.llm.router.routing_policy import RoutingPolicy, get_policy_weights
from app.services.llm.models import LLMRequest

logger = logging.getLogger(__name__)

class RoutingEngine:
    """Engine that selects the best LLM provider dynamically based on capabilities and scores."""
    
    def __init__(self, registry: ProviderRegistry, health_service: ProviderHealthService, decision_engine=None):
        self.registry = registry
        self.health_service = health_service
        from app.services.decisions.engine import DecisionEngine
        self.decision_engine = decision_engine or DecisionEngine()

    def _normalize_cost(self, cost: float) -> float:
        """Invert cost so lower cost is a higher score."""
        if cost == 0: return 1.0
        return max(0.0, 1.0 - (cost / 10.0))  # arbitrary normalization

    def _normalize_latency(self, latency_class: str) -> float:
        if latency_class == "fast": return 1.0
        if latency_class == "medium": return 0.5
        return 0.1

    def select_provider(self, request: LLMRequest, policy: RoutingPolicy = RoutingPolicy.BALANCED, exclude_providers: Optional[Set[str]] = None) -> AbstractLLMProvider:
        """Selects the best provider, ignoring those in exclude_providers."""
        if exclude_providers is None:
            exclude_providers = set()
            
        candidates = self.registry.get_all()
        if not candidates:
            raise ValueError("No LLM Providers registered.")

        # Capability filtering based on the request requirements
        filtered_candidates = []
        for p in candidates:
            profile = p.get_profile()
            
            if profile.provider_name in exclude_providers:
                continue
                
            if profile.health_status == "offline":
                continue
                
            # Capability filters
            if request.schema and not profile.supports_json:
                continue
            
            # Simple context window check based on prompt length heuristic
            if len(request.prompt) > profile.context_window:
                continue
                
            filtered_candidates.append(p)
            
        if not filtered_candidates:
            raise ValueError("No providers available that meet the request capabilities.")
            
        weights = get_policy_weights(policy)
        best_provider = None
        best_score = -1.0
        
        for p in filtered_candidates:
            profile = p.get_profile()
            health = self.health_service.get_health(profile.provider_name)
            
            cost_score = self._normalize_cost(profile.cost_input + profile.cost_output)
            latency_score = self._normalize_latency(profile.latency_class)
            quality_score = profile.quality_score
            health_score = health.health_score
            
            total_score = (
                (cost_score * weights["cost"]) +
                (latency_score * weights["latency"]) +
                (quality_score * weights["quality"]) +
                (health_score * weights["health"])
            )
            
            logger.debug(f"Provider {profile.provider_name} score: {total_score}")
            if total_score > best_score:
                best_score = total_score
                best_provider = p
                
        if not best_provider:
            raise ValueError("Routing Engine failed to find a suitable provider.")
            
        provider_name = best_provider.get_profile().provider_name
        logger.info(f"Routing request to {provider_name} (Score: {best_score:.2f})")
        
        from app.services.decisions.models import DecisionType
        self.decision_engine.record_decision(
            decision_type=DecisionType.ROUTING,
            component="RoutingEngine",
            selected_option=provider_name,
            alternative_options=[p.get_profile().provider_name for p in candidates if p != best_provider],
            context={
                "health_score": self.health_service.get_health(provider_name).health_score,
                "latency_class": best_provider.get_profile().latency_class,
                "historical_success": 0.9  # simulated for now
            },
            trace_id=getattr(request, 'trace_id', None)
        )
        
        return best_provider
