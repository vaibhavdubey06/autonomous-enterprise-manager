from app.services.memory.normalizer import MemoryNormalizer
from app.services.memory.models import ExtractedMemory
from app.services.memory.memory_types import MemoryType


def test_memory_normalizer():
    normalizer = MemoryNormalizer()

    mem = ExtractedMemory(
        title="  test title  ",
        content="  this is some content. ",
        memory_type=MemoryType.FACT,
    )

    normalized = normalizer.normalize(mem)

    assert normalized.title == "Test Title"
    assert normalized.content == "This is some content."
