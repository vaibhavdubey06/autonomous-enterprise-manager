"""
GraphState — Strongly typed state definition for the LangGraph orchestration layer.

Every node reads from and writes to this shared state object.
No business logic lives here — this is purely a data contract.
"""

from typing import TypedDict, List, Dict, Any, Optional


class ExecutionStep(TypedDict):
    """A single step in the execution trace."""

    node: str
    start_time: str
    end_time: str
    duration_ms: float
    status: str  # "success" | "skipped" | "error"


class PlanDecision(TypedDict):
    """Output of the Planner Node — deterministic, no LLM."""

    needs_memory: bool
    needs_retrieval: bool
    needs_tools: List[str]
    workflow_type: str  # "chat" | "research" | "workflow" | "planning"


class GraphMetrics(TypedDict, total=False):
    """Observability metrics collected across nodes."""

    router_ms: float
    planner_ms: float
    memory_ms: float
    retrieval_ms: float
    rerank_ms: float
    tool_ms: float
    context_ms: float
    llm_ms: float
    validation_ms: float
    total_ms: float


class GraphState(TypedDict, total=False):
    """
    Shared state for the entire LangGraph execution.

    Every field is optional (total=False) so nodes only write what they own.
    """

    # ── Input ──────────────────────────────────────────────
    question: str
    session_id: Optional[str]
    conversation_id: Optional[str]

    # ── Router ─────────────────────────────────────────────
    user_intent: str
    workflow_type: str  # "chat" | "research" | "workflow" | "planning"

    # ── Planner ────────────────────────────────────────────
    plan: PlanDecision
    selected_tools: List[str]

    # ── Memory ─────────────────────────────────────────────
    recent_memory: List[Dict[str, Any]]
    semantic_memory: List[Dict[str, Any]]
    memory_context: str

    # ── Retrieval ──────────────────────────────────────────
    enterprise_context: List[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]

    # ── Tools ──────────────────────────────────────────────
    tool_results: List[Dict[str, Any]]

    # ── Context Builder ────────────────────────────────────
    merged_context: str
    context_texts: List[str]
    sources: List[Dict[str, Any]]

    # ── Response ───────────────────────────────────────────
    answer: str
    confidence: float

    # ── Validation ─────────────────────────────────────────
    requires_human: bool

    # ── Observability ──────────────────────────────────────
    execution_trace: List[ExecutionStep]
    metrics: GraphMetrics
    error: Optional[str]
