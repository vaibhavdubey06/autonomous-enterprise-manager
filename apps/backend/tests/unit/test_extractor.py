from unittest.mock import MagicMock
from app.services.memory.extractor import MemoryExtractor
from app.services.memory.models import ExtractedMemory
from app.services.memory.memory_types import MemoryType


def test_memory_extractor_pipeline():
    mock_strategy = MagicMock()
    mock_strategy.strategy_name = "MockStrategy"
    mock_strategy.version = "1.0"

    mock_normalizer = MagicMock()
    mock_scorer = MagicMock()
    mock_deduplicator = MagicMock()
    mock_repo = MagicMock()
    mock_qdrant_search = MagicMock()
    mock_qdrant_store = MagicMock()

    extractor = MemoryExtractor(
        strategy=mock_strategy,
        normalizer=mock_normalizer,
        scorer=mock_scorer,
        deduplicator=mock_deduplicator,
        repository=mock_repo,
        qdrant_search_callback=mock_qdrant_search,
        qdrant_store_callback=mock_qdrant_store,
        importance_threshold=0.5,
    )

    mem1 = ExtractedMemory(title="t1", content="c1", memory_type=MemoryType.FACT)
    mem2 = ExtractedMemory(
        title="t2", content="c2", memory_type=MemoryType.UNKNOWN
    )  # will score low

    mock_strategy.extract.return_value = [mem1, mem2]
    mock_normalizer.normalize.side_effect = lambda m: m

    # Scorer assigns 0.9 to mem1, 0.2 to mem2
    def mock_score(m):
        return 0.9 if m.title == "t1" else 0.2

    mock_scorer.score.side_effect = mock_score

    # deduplicator says None (new)
    mock_deduplicator.deduplicate.return_value = None

    mock_repo.add_memory.return_value = MagicMock(
        id="123",
        memory_type=MemoryType.FACT,
        importance=0.9,
        confidence=0.8,
        memory_status="NEW",
        conversation_id="conv",
        user_id="user",
        tags=[],
    )

    extractor.process(
        "history",
        "user",
        "assistant",
        context_kwargs={"conversation_id": "conv", "user_id": "user"},
    )

    # Verification
    mock_strategy.extract.assert_called_once()
    assert mock_normalizer.normalize.call_count == 2
    assert mock_scorer.score.call_count == 2

    # Deduplicator should only be called for mem1 since mem2 scored below 0.5
    mock_deduplicator.deduplicate.assert_called_once()

    # Store should only be called for mem1
    mock_repo.add_memory.assert_called_once()
    mock_qdrant_store.assert_called_once()
