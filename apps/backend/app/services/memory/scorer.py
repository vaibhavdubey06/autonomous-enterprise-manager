from app.services.memory.models import ExtractedMemory
from app.services.memory.types import MemoryType

class ImportanceScorer:
    """
    Scores memory importance based on type, novelty, and specificity.
    Returns a score between 0.0 and 1.0.
    """
    def score(self, memory: ExtractedMemory) -> float:
        # Base score based on memory type
        type_scores = {
            MemoryType.DECISION: 0.95,
            MemoryType.GOAL: 0.90,
            MemoryType.FACT: 0.85,
            MemoryType.PREFERENCE: 0.80,
            MemoryType.PERSON: 0.75,
            MemoryType.PROJECT: 0.70,
            MemoryType.TASK: 0.70,
            MemoryType.EVENT: 0.65,
            MemoryType.RELATIONSHIP: 0.60,
            MemoryType.SKILL: 0.75,
            MemoryType.QUESTION: 0.50,
            MemoryType.UNKNOWN: 0.30,
        }
        
        base_score = type_scores.get(memory.memory_type, 0.30)
        
        # Adjust based on content length/specificity (heuristic)
        # e.g., longer descriptions might be slightly more specific up to a point
        length = len(memory.content)
        if length > 50:
            base_score = min(base_score + 0.05, 1.0)
        elif length < 10:
            base_score = max(base_score - 0.1, 0.0)
            
        return round(base_score, 2)
