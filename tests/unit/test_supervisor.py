from app.agents.base.registry import AgentRegistry
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.agents.supervisor.schemas import Task, TaskStatus, ExecutionPlan
from app.agents.supervisor.task_decomposer import TaskDecomposer
from app.agents.supervisor.router import AgentRouter
from app.agents.supervisor.supervisor_agent import SupervisorGraph
from app.agents.base.profile import AgentProfile


def test_task_decomposer():
    decomposer = TaskDecomposer()

    plan = ExecutionPlan(
        goal="Test Goal",
        tasks=[
            Task(goal="T1", description="desc 1"),
            Task(goal="T2", description="desc 2"),
        ],
    )

    tasks = decomposer.decompose(plan)
    assert len(tasks) == 2
    assert tasks[0].status == TaskStatus.PENDING
    assert tasks[1].status == TaskStatus.PENDING
    assert len(tasks[0].dependencies) == 0
    assert len(tasks[1].dependencies) == 0


def test_agent_router_knowledge_fallback():
    mock_knowledge_graph = MagicMock()
    mock_knowledge_graph.run.return_value = {
        "answer": "Mock answer",
        "sources": [],
        "metrics": {"total_time_ms": 100},
    }

    registry = AgentRegistry()
    router = AgentRouter(
        agent_registry=registry, knowledge_agent_graph=mock_knowledge_graph
    )

    task = Task(goal="test", description="query", assigned_agent="CTO Agent")
    state = {"session_id": "1", "conversation_id": "1"}

    result = router.route_and_execute(task, state)

    assert task.status == TaskStatus.COMPLETED
    assert result["agent_used"] == "Knowledge Agent"
    assert result["result"] == "Mock answer"
    mock_knowledge_graph.run.assert_called_once()


@pytest.mark.asyncio
async def test_supervisor_graph_flow():
    mock_planner = MagicMock()
    mock_planner.llm_service = MagicMock()
    mock_planner.llm_service.generate.return_value = "Final test answer from LLM"
    mock_planner.plan.return_value = ExecutionPlan(
        goal="Test Goal",
        tasks=[Task(goal="T1", description="desc 1", assigned_agent="Knowledge Agent")],
    )

    mock_task_decomposer = MagicMock()
    mock_memory_service = MagicMock()
    mock_memory_service.build_memory_context.return_value = "memory context"

    mock_router = MagicMock()
    mock_router.route_and_execute.return_value = {
        "task_id": "123",
        "agent_used": "Knowledge Agent",
        "result": "Final test answer",
        "sources": [],
        "metrics": {},
    }

    graph = SupervisorGraph(
        planner=mock_planner,
        task_decomposer=mock_task_decomposer,
        agent_router=mock_router,
        memory_service=mock_memory_service,
    )

    initial_state = {
        "user_input": "Test goal input",
        "session_id": "123",
        "conversation_id": "456",
        "execution_time_ms": 0.0,
        "selected_agents": [],
        "completed_tasks": [],
        "failed_tasks": [],
        "task_results": [],
    }

    final_state = await graph.run(initial_state)

    assert final_state["goal"] == "Test goal input"
    assert final_state["execution_plan"] is not None
    assert "Knowledge Agent" in final_state["selected_agents"]
    assert "Final test answer from LLM" in final_state["final_response"]
    mock_planner.plan.assert_called_once_with(
        goal="Test goal input", context="memory context"
    )


@pytest.mark.asyncio
async def test_supervisor_graph_enables_collaboration_for_multi_task_plan():
    mock_planner = MagicMock()
    mock_planner.plan.return_value = ExecutionPlan(
        goal="Multi-step goal",
        tasks=[
            Task(goal="T1", description="desc 1", assigned_agent="Knowledge Agent"),
            Task(goal="T2", description="desc 2", assigned_agent="CTO Agent"),
        ],
    )

    mock_task_decomposer = MagicMock()
    mock_memory_service = MagicMock()
    mock_memory_service.build_memory_context.return_value = "memory context"

    mock_collaboration_manager = MagicMock()
    mock_session = MagicMock(session_id="session-1")
    mock_collaboration_manager.create_session.return_value = mock_session
    mock_collaboration_manager.form_team.return_value = mock_session
    mock_collaboration_manager.execute.return_value = None
    mock_collaboration_manager.complete_session = AsyncMock(return_value=None)

    mock_router = MagicMock()
    mock_router.route_and_execute.return_value = {
        "task_id": "123",
        "agent_used": "Knowledge Agent",
        "result": "Collaboration result",
        "sources": [],
        "metrics": {},
    }

    graph = SupervisorGraph(
        planner=mock_planner,
        task_decomposer=mock_task_decomposer,
        agent_router=mock_router,
        memory_service=mock_memory_service,
        collaboration_manager=mock_collaboration_manager,
    )

    initial_state = {
        "user_input": "Coordinate a multi-step enterprise rollout",
        "session_id": "123",
        "conversation_id": "456",
        "execution_time_ms": 0.0,
        "selected_agents": [],
        "completed_tasks": [],
        "failed_tasks": [],
        "task_results": [],
    }

    final_state = await graph.run(initial_state)

    assert final_state["use_collaboration"] is True
    assert len(final_state["task_results"]) == 2
    mock_planner.plan.assert_called_once_with(
        goal="Coordinate a multi-step enterprise rollout",
        context="memory context",
    )


def test_agent_router_uses_collaboration_runtime():
    registry = AgentRegistry()
    mock_collaboration_manager = MagicMock()
    mock_collaboration_manager.delegation = MagicMock()
    mock_session = MagicMock(session_id="session-1")
    mock_delegated_task = MagicMock(task_id="delegated-1", description="delegated")
    mock_collaboration_manager.create_session.return_value = mock_session
    mock_collaboration_manager.form_team.return_value = mock_session
    mock_collaboration_manager.execute.return_value = None
    mock_collaboration_manager.delegation.delegate_task.return_value = mock_delegated_task
    mock_collaboration_manager.delegation.complete_task.return_value = mock_delegated_task
    mock_collaboration_manager.complete_session = AsyncMock(return_value=None)

    router = AgentRouter(
        agent_registry=registry,
        collaboration_manager=mock_collaboration_manager,
    )

    task = Task(goal="test", description="collab task", assigned_agent="CTO Agent")
    state = {"session_id": "1", "conversation_id": "1"}

    result = router.route_and_execute(task, state, use_collaboration=True)

    assert task.status == TaskStatus.COMPLETED
    assert result["agent_used"] == "CTO Agent"
    assert "Collaboration Session session-1" in result["result"]
    mock_collaboration_manager.create_session.assert_called_once()


def test_agent_router_routes_by_capability():
    mock_knowledge_graph = MagicMock()
    mock_knowledge_graph.run.return_value = {
        "answer": "Fallback answer",
        "sources": [],
        "metrics": {},
    }

    registry = AgentRegistry()
    mock_ciso_agent = MagicMock()
    mock_ciso_agent.get_profile.return_value = AgentProfile(
        agent_name="CISO Agent",
        title="Chief Information Security Officer",
        domain="Security",
        description="Security posture, threat response, governance.",
        capabilities=["SECURITY_LEADERSHIP"],
    )
    mock_ciso_agent.execute.return_value = MagicMock(
        reasoning="Security review reasoning",
        summary="Security review summary",
        sources=[],
        execution_metrics={},
    )
    registry.register_agent(mock_ciso_agent)
    router = AgentRouter(
        agent_registry=registry,
        knowledge_agent_graph=mock_knowledge_graph,
    )

    task = Task(
        goal="Analyze the security posture",
        description="Review controls and threats",
        assigned_agent="Knowledge Agent",
        required_capabilities=["SECURITY_LEADERSHIP"],
    )
    state = {"session_id": "1", "conversation_id": "1"}

    result = router.route_and_execute(task, state)

    assert result["agent_used"] == "CISO Agent"
    assert task.status == TaskStatus.COMPLETED
