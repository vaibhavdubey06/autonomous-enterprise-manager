"""
Context Builder — Merges all retrieved context into a normalized prompt string.

This is the single place where Memory, Enterprise, and Tool contexts converge.
Neither Response Node nor any other node should duplicate this logic.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def build_merged_context(
    memory_context: str,
    reranked_chunks: List[Dict[str, Any]],
    tool_results: List[Dict[str, Any]],
) -> tuple[str, List[str], List[Dict[str, Any]]]:
    """
    Merges all context sources into a single prompt string.

    Returns:
        merged_context: The full prompt-ready context string.
        context_texts:  Individual text passages (for LLM context param).
        sources:        Citation metadata list.
    """
    context_texts: List[str] = []
    sources: List[Dict[str, Any]] = []

    # ── Reranked enterprise + memory chunks ──
    for chunk in reranked_chunks:
        text = chunk.get("text", "")
        if not text:
            continue
        context_texts.append(text)

        source_data: Dict[str, Any] = {
            "source": chunk.get("source", "unknown"),
            "rerank_score": chunk.get("rerank_score"),
        }

        src = source_data["source"]
        if src == "conversation":
            source_data.update(
                {
                    "conversation_id": chunk.get("conversation_id", ""),
                    "message_id": chunk.get("message_id", ""),
                    "role": chunk.get("role", ""),
                    "timestamp": chunk.get("timestamp", ""),
                }
            )
        elif src == "github":
            source_data.update(
                {
                    "repository": chunk.get("repository", ""),
                    "branch": chunk.get("branch", ""),
                    "path": chunk.get("path", ""),
                    "url": chunk.get("url", ""),
                }
            )
        else:
            source_data.update(
                {
                    "document": chunk.get("document", "Unknown"),
                    "page": chunk.get("page", 1),
                    "chunk": chunk.get("chunk", 0),
                }
            )

        sources.append(source_data)

    # ── Assemble final string ──
    parts: List[str] = []

    if memory_context:
        parts.append(f"--- WORKING MEMORY ---\n{memory_context}")

    if context_texts:
        parts.append(f"--- RETRIEVED CONTEXT ---\n{' '.join(context_texts)}")

    if tool_results:
        tool_texts = []
        for tr in tool_results:
            if tr.get("status") == "executed":
                tool_texts.append(str(tr))
        if tool_texts:
            parts.append(f"--- TOOL RESULTS ---\n{' '.join(tool_texts)}")

    merged_context = "\n\n".join(parts)

    logger.info(
        f"Context built: {len(context_texts)} text passages, "
        f"{len(sources)} sources, {len(tool_results)} tool results."
    )

    return merged_context, context_texts, sources
