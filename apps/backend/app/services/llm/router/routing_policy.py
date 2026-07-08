from enum import Enum
from typing import Dict, Any

class RoutingPolicy(str, Enum):
    FASTEST = "fastest"
    CHEAPEST = "cheapest"
    HIGHEST_QUALITY = "highest_quality"
    BALANCED = "balanced"
    # Domain specific
    CODING = "coding"
    REASONING = "reasoning"
    LONG_CONTEXT = "long_context"

def get_policy_weights(policy: RoutingPolicy) -> Dict[str, float]:
    """Returns scoring weights (cost, latency, quality, health) for a given policy."""
    if policy == RoutingPolicy.FASTEST:
        return {"cost": 0.1, "latency": 0.6, "quality": 0.1, "health": 0.2}
    elif policy == RoutingPolicy.CHEAPEST:
        return {"cost": 0.6, "latency": 0.1, "quality": 0.1, "health": 0.2}
    elif policy == RoutingPolicy.HIGHEST_QUALITY:
        return {"cost": 0.1, "latency": 0.1, "quality": 0.6, "health": 0.2}
    elif policy == RoutingPolicy.BALANCED:
        return {"cost": 0.25, "latency": 0.25, "quality": 0.25, "health": 0.25}
    elif policy == RoutingPolicy.CODING or policy == RoutingPolicy.REASONING:
        # Heavily favors quality and reasoning capability
        return {"cost": 0.1, "latency": 0.1, "quality": 0.6, "health": 0.2}
    elif policy == RoutingPolicy.LONG_CONTEXT:
        # Quality and Health mostly, context window is an absolute filter though
        return {"cost": 0.2, "latency": 0.2, "quality": 0.4, "health": 0.2}
    
    # Default balanced
    return {"cost": 0.25, "latency": 0.25, "quality": 0.25, "health": 0.25}
