"""
Tool Registry — Generic tool abstraction for the Tool Node.

Every external tool (GitHub, Slack, Notion, Calendar, etc.) implements
BaseTool and registers itself with the ToolRegistry.  The Tool Node
calls the registry; it never touches connectors directly.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from app.graph.state import GraphState

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Interface that every tool must implement.

    Subclasses wrap an existing service/connector and expose a
    single `execute(state) -> result` contract.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this tool (e.g. 'github')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description shown to the Planner."""
        ...

    @abstractmethod
    def execute(self, state: GraphState) -> Dict[str, Any]:
        """
        Run the tool using data from the current GraphState.

        Returns a dict of results that the Tool Node will merge
        into `state["tool_results"]`.
        """
        ...


class GitHubTool(BaseTool):
    """Wraps GitHubConnector for use inside the graph."""

    @property
    def name(self) -> str:
        return "github"

    @property
    def description(self) -> str:
        return "Search GitHub repositories for code, issues, and pull requests."

    def execute(self, state: GraphState) -> Dict[str, Any]:
        """
        Execute a GitHub search based on the current question.

        Note: Full GitHub search integration requires the connector
        to support query-based searching. For now, this returns
        a structured result indicating the tool was invoked.
        """
        question = state.get("question", "")
        logger.info(f"GitHubTool executing for question: {question[:80]}")

        # The GitHubConnector currently supports repo indexing,
        # not live query search. Return a placeholder that future
        # iterations will expand into full search.
        return {
            "tool": self.name,
            "status": "executed",
            "note": "GitHub search indexed via existing connector. "
            "Live query search will be available in a future iteration.",
            "query": question,
        }


class ToolRegistry:
    """
    Central registry for all available tools.

    The Tool Node asks the registry to execute tools by name.
    New tools are added here — no graph changes required.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' is already registered — overwriting.")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def execute(self, name: str, state: GraphState) -> Dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            logger.error(f"Tool '{name}' not found in registry.")
            return {
                "tool": name,
                "status": "error",
                "detail": f"Tool '{name}' is not registered.",
            }
        try:
            return tool.execute(state)
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}")
            return {"tool": name, "status": "error", "detail": str(e)}


def build_default_registry() -> ToolRegistry:
    """Create a registry pre-loaded with all available tools."""
    registry = ToolRegistry()
    registry.register(GitHubTool())
    # Future: registry.register(SlackTool())
    # Future: registry.register(NotionTool())
    # Future: registry.register(CalendarTool())
    # Future: registry.register(EmailTool())
    # Future: registry.register(GoogleDriveTool())
    # Future: registry.register(CodeExecutionTool())
    return registry
