from app.graph.registry import ToolRegistry, BaseTool
from app.graph.state import GraphState


class MockTool(BaseTool):
    @property
    def name(self) -> str:
        return "test_tool"

    @property
    def description(self) -> str:
        return "A test tool"

    def execute(self, state: GraphState):
        return {"result": "Tested"}


def test_registry():
    registry = ToolRegistry()
    registry.register(MockTool())

    tools = registry.list_tools()
    assert "test_tool" in tools

    tool = registry.get("test_tool")
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"

    state: GraphState = {}
    result = registry.execute("test_tool", state)
    assert result == {"result": "Tested"}

    # Test error
    result = registry.execute("nonexistent", state)
    assert result["status"] == "error"
