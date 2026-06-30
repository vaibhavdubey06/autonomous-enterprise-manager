"""
Planner Node — Deterministic rule-based planner.

NO LLM calls.  NO retrieval.  NO embedding.
Analyses the question with simple heuristics and produces a PlanDecision.
"""

import logging
import time
from datetime import datetime, timezone
from typing import List

from app.graph.state import GraphState, PlanDecision

logger = logging.getLogger(__name__)

# ── Keyword banks for deterministic classification ──
_MEMORY_KEYWORDS = [
    "yesterday",
    "last time",
    "earlier",
    "before",
    "previous",
    "we discussed",
    "we decided",
    "remember",
    "you said",
    "i said",
    "our conversation",
    "last conversation",
    "previously",
]

_GITHUB_KEYWORDS = [
    "github",
    "pull request",
    "pr",
    "issue",
    "commit",
    "merge",
    "branch",
    "repository",
    "repo",
    "code review",
]

_RETRIEVAL_SKIP_KEYWORDS = [
    "hello",
    "hi",
    "hey",
    "thanks",
    "thank you",
    "bye",
    "goodbye",
]


def _needs_memory(question_lower: str) -> bool:
    return any(kw in question_lower for kw in _MEMORY_KEYWORDS)


def _needs_retrieval(question_lower: str) -> bool:
    # Skip retrieval for pure greetings / pleasantries
    if any(question_lower.strip() == kw for kw in _RETRIEVAL_SKIP_KEYWORDS):
        return False
    return True


def _detect_tools(question_lower: str) -> List[str]:
    tools: List[str] = []
    if any(kw in question_lower for kw in _GITHUB_KEYWORDS):
        tools.append("github")
    # Future: if any(kw in question_lower for kw in _SLACK_KEYWORDS): tools.append("slack")
    return tools


def planner_node(state: GraphState) -> GraphState:
    """
    Produce a structured PlanDecision using deterministic heuristics.
    """
    start = time.perf_counter()
    start_ts = datetime.now(timezone.utc).isoformat()
    logger.info("PlannerNode — start")

    question = state.get("question", "")
    q_lower = question.lower()

    needs_mem = _needs_memory(q_lower)
    needs_ret = _needs_retrieval(q_lower)
    tools = _detect_tools(q_lower)

    plan: PlanDecision = {
        "needs_memory": needs_mem,
        "needs_retrieval": needs_ret,
        "needs_tools": tools,
        "workflow_type": state.get("workflow_type", "chat"),
    }

    duration_ms = (time.perf_counter() - start) * 1000
    end_ts = datetime.now(timezone.utc).isoformat()
    logger.info(
        f"PlannerNode — finish ({duration_ms:.1f}ms) → "
        f"memory={needs_mem}, retrieval={needs_ret}, tools={tools}"
    )

    trace = list(state.get("execution_trace", []))
    trace.append(
        {
            "node": "Planner",
            "start_time": start_ts,
            "end_time": end_ts,
            "duration_ms": round(duration_ms, 2),
            "status": "success",
        }
    )

    metrics = state.get("metrics", {})
    metrics["planner_ms"] = round(duration_ms, 2)

    return {
        **state,
        "plan": plan,
        "selected_tools": tools,
        "execution_trace": trace,
        "metrics": metrics,
    }
