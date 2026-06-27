from typing import List, Any
import math

def calculate_precision(retrieved: List[Any], relevant: List[Any]) -> float:
    if not retrieved: return 0.0
    hits = sum(1 for r in retrieved if r in relevant)
    return hits / len(retrieved)

def calculate_recall(retrieved: List[Any], relevant: List[Any], k: int = None) -> float:
    if not relevant: return 1.0
    if k is not None:
        retrieved = retrieved[:k]
    hits = sum(1 for r in retrieved if r in relevant)
    return hits / len(relevant)

def calculate_mrr(retrieved: List[Any], relevant: List[Any]) -> float:
    for i, r in enumerate(retrieved):
        if r in relevant:
            return 1.0 / (i + 1)
    return 0.0
