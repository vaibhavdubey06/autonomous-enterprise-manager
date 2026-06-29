import pytest
from unittest.mock import MagicMock
from app.services.memory.deduplicator import MemoryDeduplicator
from app.services.memory.models import ExtractedMemory
from app.services.memory.memory_types import MemoryType
from app.models.memory import MemoryObject
import uuid


def test_deduplicator_new_memory():
    mock_repo = MagicMock()
    deduplicator = MemoryDeduplicator(memory_repository=mock_repo)

    mem = ExtractedMemory(title="test", content="content", memory_type=MemoryType.FACT)
    mem.importance = 0.8
    mem.confidence = 0.8

    # Empty similar memories
    result = deduplicator.deduplicate(mem, [])
    assert result is None
    mock_repo.update_memory.assert_not_called()


def test_deduplicator_update_existing_better_quality():
    mock_repo = MagicMock()
    existing_id = str(uuid.uuid4())

    # Mock the DB returning an existing memory with lower importance
    existing_mem = MemoryObject(id=existing_id, importance=0.5, confidence=0.5)
    mock_repo.get_memory.return_value = existing_mem

    deduplicator = MemoryDeduplicator(memory_repository=mock_repo)

    # Incoming is better
    mem = ExtractedMemory(
        title="test", content="better content", memory_type=MemoryType.FACT
    )
    mem.importance = 0.9
    mem.confidence = 0.9

    similar = [{"score": 0.95, "memory_id": existing_id}]

    result = deduplicator.deduplicate(mem, similar)
    assert result == existing_id

    mock_repo.update_memory.assert_called_once()
    args, kwargs = mock_repo.update_memory.call_args
    assert args[0] == existing_id
    assert args[1]["content"] == "better content"
    assert args[1]["importance"] == 0.9
    assert args[1]["confidence"] == 0.6  # 0.5 + 0.1


def test_deduplicator_update_existing_lower_quality():
    mock_repo = MagicMock()
    existing_id = str(uuid.uuid4())

    # Mock the DB returning an existing memory with higher importance
    existing_mem = MemoryObject(id=existing_id, importance=0.9, confidence=0.9)
    mock_repo.get_memory.return_value = existing_mem

    deduplicator = MemoryDeduplicator(memory_repository=mock_repo)

    # Incoming is worse
    mem = ExtractedMemory(
        title="test", content="worse content", memory_type=MemoryType.FACT
    )
    mem.importance = 0.5
    mem.confidence = 0.5

    similar = [{"score": 0.95, "memory_id": existing_id}]

    result = deduplicator.deduplicate(mem, similar)
    assert result == existing_id

    mock_repo.update_memory.assert_called_once()
    args, kwargs = mock_repo.update_memory.call_args
    assert args[0] == existing_id
    assert "content" not in args[1]
    assert args[1]["confidence"] == pytest.approx(0.95)  # 0.9 + 0.05
