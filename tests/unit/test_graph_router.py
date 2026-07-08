from unittest.mock import MagicMock

from app.graph.dependencies import ServiceContainer
from app.graph.registry import ToolRegistry
from app.graph.router import GraphRouter


class _FakeGraph:
    def __init__(self, name: str):
        self.name = name
        self.invocations: list[dict[str, object]] = []

    def invoke(self, state):
        self.invocations.append(state)
        return {**state, "graph_used": self.name}


def _make_services():
    return ServiceContainer(
        memory_service=MagicMock(),
        llm_service=MagicMock(),
        cross_encoder_service=MagicMock(),
    )


def test_graph_router_defaults_to_chat(monkeypatch):
    chat_graph = _FakeGraph("chat")
    research_graph = _FakeGraph("research")
    planning_graph = _FakeGraph("planning")
    workflow_graph = _FakeGraph("workflow")
    analytics_graph = _FakeGraph("analytics")
    executive_graph = _FakeGraph("executive_decision")
    incident_graph = _FakeGraph("incident_response")

    monkeypatch.setattr(
        "app.graph.router.build_chat_graph",
        lambda *args, **kwargs: chat_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_research_graph",
        lambda *args, **kwargs: research_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_planning_graph",
        lambda *args, **kwargs: planning_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_workflow_graph",
        lambda *args, **kwargs: workflow_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_analytics_graph",
        lambda *args, **kwargs: analytics_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_executive_decision_graph",
        lambda *args, **kwargs: executive_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_incident_response_graph",
        lambda *args, **kwargs: incident_graph,
    )

    router = GraphRouter(
        services=_make_services(), tool_registry=ToolRegistry()
    )

    result = router.run({"question": "hello"})

    assert result["graph_used"] == "chat"
    assert chat_graph.invocations[0]["question"] == "hello"


def test_graph_router_routes_by_workflow_type(monkeypatch):
    chat_graph = _FakeGraph("chat")
    research_graph = _FakeGraph("research")
    planning_graph = _FakeGraph("planning")
    workflow_graph = _FakeGraph("workflow")
    analytics_graph = _FakeGraph("analytics")
    executive_graph = _FakeGraph("executive_decision")
    incident_graph = _FakeGraph("incident_response")

    monkeypatch.setattr(
        "app.graph.router.build_chat_graph",
        lambda *args, **kwargs: chat_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_research_graph",
        lambda *args, **kwargs: research_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_planning_graph",
        lambda *args, **kwargs: planning_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_workflow_graph",
        lambda *args, **kwargs: workflow_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_analytics_graph",
        lambda *args, **kwargs: analytics_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_executive_decision_graph",
        lambda *args, **kwargs: executive_graph,
    )
    monkeypatch.setattr(
        "app.graph.router.build_incident_response_graph",
        lambda *args, **kwargs: incident_graph,
    )

    router = GraphRouter(
        services=_make_services(), tool_registry=ToolRegistry()
    )

    result = router.run(
        {"question": "need research", "workflow_type": "research"}
    )

    assert result["graph_used"] == "research"
    assert research_graph.invocations[0]["workflow_type"] == "research"
