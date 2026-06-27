import pytest
from app.services.memory.scorer import ImportanceScorer
from app.services.memory.models import ExtractedMemory
from app.services.memory.types import MemoryType

def test_importance_scorer_types():
    scorer = ImportanceScorer()
    
    # Decisions should score high
    mem = ExtractedMemory(title="test", content="We decided to use FastAPI", memory_type=MemoryType.DECISION)
    score = scorer.score(mem)
    assert score >= 0.90
    
    # Facts should score high but slightly lower
    mem = ExtractedMemory(title="test", content="The team uses Python for backend", memory_type=MemoryType.FACT)
    score = scorer.score(mem)
    assert score >= 0.80

    # Greetings / Unknown should score low
    mem = ExtractedMemory(title="test", content="Hi", memory_type=MemoryType.UNKNOWN)
    score = scorer.score(mem)
    assert score <= 0.30

def test_importance_scorer_length_adjustment():
    scorer = ImportanceScorer()
    
    short_mem = ExtractedMemory(title="test", content="Yes.", memory_type=MemoryType.FACT)
    long_mem = ExtractedMemory(title="test", content="Yes, this is a very long explanation that goes into detail about the topic.", memory_type=MemoryType.FACT)
    
    assert scorer.score(long_mem) > scorer.score(short_mem)
