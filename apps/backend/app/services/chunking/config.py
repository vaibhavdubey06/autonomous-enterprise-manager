from typing import Dict, Any, Tuple

# Target tokens depending on document type/density (soft min, hard max, overlap tokens)
TARGET_TOKENS: Dict[str, Tuple[int, int, int]] = {
    "default": (300, 500, 50),
    "markdown": (300, 800, 50),
    "code": (100, 1000, 0),  # Code prefers logical boundaries, no token overlaps inside bodies
    "pdf": (400, 1000, 50),
    "json": (100, 500, 0),
}

# Tiers mapping file extensions/types to strategies
# Tier 1 (Fast <10ms/MB): txt, log, email -> Fixed, Sentence, Paragraph
# Tier 2 (Balanced <50ms/MB): md, html, pdf -> Recursive, Markdown, HTML
# Tier 3 (Deep): research, legal -> Semantic (only if explicitly triggered)

CHUNK_STRATEGY_MAP: Dict[str, str] = {
    "txt": "ParagraphChunker",
    "log": "FixedChunker",
    "md": "MarkdownChunker",
    "py": "CodeChunker",
    "js": "CodeChunker",
    "ts": "CodeChunker",
    "java": "CodeChunker",
    "go": "CodeChunker",
    "html": "HTMLChunker",
    "json": "JSONChunker",
    "ipynb": "NotebookChunker",
    "pdf": "RecursiveChunker",
    "default": "FixedChunker",
}

# Enable expensive semantic chunking only for highly dense text if config permits
ENABLE_SEMANTIC_CHUNKING = False
