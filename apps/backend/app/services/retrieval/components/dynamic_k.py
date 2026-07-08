def compute_dynamic_k(intent: str, is_complex: bool, confidence: float) -> int:
    """
    Dynamically select top_k based on query complexity, workflow type (intent),
    and capability confidence.
    """
    base_k = 5
    
    # Adjust based on intent
    if intent == "architecture":
        base_k += 7  # Architecture needs broad context
    elif intent == "troubleshooting":
        base_k += 5  # Needs logs and multiple potential solutions
    elif intent == "how_to":
        base_k += 3  # Tutorials need sequential steps
    elif intent == "code_search":
        base_k = 4   # Exact code matches need fewer, highly precise chunks
        
    # Adjust based on complexity
    if is_complex:
        base_k += 5
        
    # Adjust based on capability confidence (if we are unsure, retrieve more broadly)
    if confidence < 0.6:
        base_k += 4
        
    # Cap at a reasonable token budget max
    return min(base_k, 25)
