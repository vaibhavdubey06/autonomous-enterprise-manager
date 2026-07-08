from app.graph.nodes.tool_node import make_tool_node
from app.graph.registry import ToolRegistry, BaseTool
from app.graph.state import GraphState


class MockTool(BaseTool):
    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "A mock tool"

    def execute(self, state: GraphState):
        return {"tool": "mock_tool", "result": "Mocked"}


def test_tool_node():
    registry = ToolRegistry()
    registry.register(MockTool())

    tool_node = make_tool_node(registry)

    state: GraphState = {
        "question": "test",
        "session_id": "test",
        "conversation_id": "test",
        "selected_tools": ["mock_tool"],
        "tool_results": [],
        "execution_trace": [],
        "metrics": {},
    }

    result = tool_node(state)

    assert "tool_results" in result
    assert len(result["tool_results"]) == 1
    assert result["tool_results"][0]["result"] == "Mocked"
    assert "tool_ms" in result["metrics"]
    assert len(result["execution_trace"]) == 1
    assert result["execution_trace"][0]["node"] == "Tool"
