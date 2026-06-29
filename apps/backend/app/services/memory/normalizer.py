from app.services.memory.models import ExtractedMemory


class MemoryNormalizer:
    """
    Normalizes memory content by adjusting casing, removing whitespace, and standardizing metadata.
    """

    def normalize(self, memory: ExtractedMemory) -> ExtractedMemory:
        # Standardize casing (example: title casing for titles, stripping whitespace)
        memory.title = memory.title.strip().title()
        memory.content = memory.content.strip()

        # We could add more complex rules here, e.g., 'PYTHON' -> 'Python'
        # For now, capitalizing first letter of content if needed, though raw content is often fine
        if memory.content and memory.content[0].islower():
            memory.content = memory.content[0].upper() + memory.content[1:]

        return memory
