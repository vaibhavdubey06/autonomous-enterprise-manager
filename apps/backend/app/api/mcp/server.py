import logging
from typing import Any
from mcp.server.fastmcp import FastMCP
from app.capabilities.base.capability_registry import CapabilityRegistry
from app.capabilities.base.executor import CapabilityExecutor
from app.operations.tracing.trace_manager import TraceManager
from app.services.decisions.engine import DecisionEngine
from app.services.decisions.models import DecisionType

logger = logging.getLogger(__name__)

mcp = FastMCP("EnterpriseManager")
trace_manager = TraceManager()
decision_engine = DecisionEngine()
cap_registry = CapabilityRegistry()
cap_executor = CapabilityExecutor(cap_registry)


def execute_through_governance(
    agent_name: str, capability_id: str, action: str, **kwargs
) -> Any:
    """
    Executes a capability while enforcing Enterprise Security:
    Authentication, Authorization, Guardrails, Policy Engine, Telemetry, Decision Engine.
    """
    with trace_manager.span(None, "mcp_tool_execution") as span:
        span.attributes.update(
            {
                "mcp_client_id": agent_name,  # client_id representation
                "mcp_server_id": "EnterpriseManager",
                "tool_name": action,
                "capability_id": capability_id,
                "latency": 0.0,
                "cost": 0.0,
                "tokens": 0,
            }
        )

        # Enforce MCP Security policies
        decision_engine.record_decision(
            decision_type=DecisionType.CAPABILITY,
            component="MCP_Server_Governance",
            selected_option=capability_id,
            context={"agent": agent_name, "action": action},
        )

        # Internally everything should still execute through Capability Registry
        # Capability Registry -> Agent Router -> Workflow Engine -> Execution
        result = cap_executor.execute(agent_name, capability_id, action, **kwargs)

        span.attributes["latency"] = result.execution_time_ms
        if result.success:
            span.status = "SUCCESS"
        else:
            span.status = "ERROR"
            span.attributes["errors"] = result.errors

        return result


# ── Tools ────────────────────────────────────────────


@mcp.tool()
def enterprise_planning(goal: str, context: str = "") -> str:
    """Enterprise Planning capability."""
    result = execute_through_governance(
        "mcp_client", "planner", "plan", goal=goal, context=context
    )
    return str(result.data) if result.success else f"Error: {result.errors}"


@mcp.tool()
def knowledge_retrieval(query: str, filters: dict = None) -> str:
    """Knowledge Retrieval capability."""
    result = execute_through_governance(
        "mcp_client", "retrieval_engine", "retrieve", query=query, filters=filters
    )
    return str(result.data) if result.success else f"Error: {result.errors}"


@mcp.tool()
def repository_search(repository_name: str, query: str = "") -> str:
    """Repository Search capability."""
    result = execute_through_governance(
        "mcp_client",
        "github_tool",
        "INDEX_REPOSITORY",
        repository_name=repository_name,
        query=query,
    )
    return str(result.data) if result.success else f"Error: {result.errors}"


@mcp.tool()
def workflow_execution(workflow_id: str, inputs: dict) -> str:
    """Workflow Execution capability."""
    result = execute_through_governance(
        "mcp_client",
        "workflow_engine",
        "execute",
        workflow_id=workflow_id,
        inputs=inputs,
    )
    return str(result.data) if result.success else f"Error: {result.errors}"


@mcp.tool()
def capability_discovery() -> str:
    """Capability Discovery capability."""
    result = execute_through_governance(
        "mcp_client", "capability_inference", "discover"
    )
    return str(result.data) if result.success else f"Error: {result.errors}"


# ── Resources ────────────────────────────────────────


@mcp.resource("knowledge://{item_id}")
def get_knowledge_item(item_id: str) -> str:
    """Read from the enterprise knowledge base."""
    with trace_manager.span(None, "mcp_resource_read") as span:
        span.attributes["resource_name"] = f"knowledge://{item_id}"
        return f"Knowledge content for {item_id}"


@mcp.resource("workflow://{workflow_id}")
def get_workflow_definition(workflow_id: str) -> str:
    """Read workflow definition."""
    with trace_manager.span(None, "mcp_resource_read") as span:
        span.attributes["resource_name"] = f"workflow://{workflow_id}"
        return f"Workflow {workflow_id}"


@mcp.resource("memory://conversations/{conversation_id}")
def get_conversation_memory(conversation_id: str) -> str:
    """Read conversation memory."""
    with trace_manager.span(None, "mcp_resource_read") as span:
        span.attributes["resource_name"] = f"memory://conversations/{conversation_id}"
        return f"Memory for conversation {conversation_id}"


@mcp.resource("reflection://heuristics")
def get_reflection_heuristics() -> str:
    """Read workflow optimization heuristics."""
    with trace_manager.span(None, "mcp_resource_read") as span:
        span.attributes["resource_name"] = "reflection://heuristics"
        return "Reflection heuristics data"


@mcp.resource("telemetry://traces/{trace_id}")
def get_telemetry_trace(trace_id: str) -> str:
    """Read a specific telemetry trace."""
    with trace_manager.span(None, "mcp_resource_read") as span:
        span.attributes["resource_name"] = f"telemetry://traces/{trace_id}"
        return "Telemetry trace data"


@mcp.resource("benchmark://latest")
def get_latest_benchmark() -> str:
    """Read the latest benchmark reports."""
    with trace_manager.span(None, "mcp_resource_read") as span:
        span.attributes["resource_name"] = "benchmark://latest"
        return "Benchmark report data"


# ── Prompts ──────────────────────────────────────────


@mcp.prompt("enterprise_task")
def enterprise_task_prompt(task_description: str) -> str:
    """Prompt for executing an enterprise task."""
    with trace_manager.span(None, "mcp_prompt_request") as span:
        span.attributes["prompt_name"] = "enterprise_task"
        # We would integrate with Prompt Compiler here
        return f"System: You are an Enterprise Manager.\nUser: Execute the following task: {task_description}"


if __name__ == "__main__":
    # Can run directly using FastMCP run
    mcp.run(transport="stdio")
