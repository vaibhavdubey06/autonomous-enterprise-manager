import pytest
from unittest.mock import MagicMock
from app.agents.supervisor.schemas import Task, TaskStatus, ExecutionPlan, SupervisorState
from app.agents.supervisor.task_decomposer import TaskDecomposer
from app.agents.supervisor.router import AgentRouter
from app.agents.supervisor.supervisor_agent import SupervisorGraph

def test_task_decomposer():
    decomposer = TaskDecomposer()
    
    plan = ExecutionPlan(
        goal="Test Goal",
        tasks=[
            Task(goal="T1", description="desc 1"),
            Task(goal="T2", description="desc 2")
        ]
    )
    
    tasks = decomposer.decompose(plan)
    assert len(tasks) == 2
    assert tasks[0].status == TaskStatus.PENDING
    assert tasks[1].status == TaskStatus.PENDING
    assert tasks[0].task_id in tasks[1].dependencies

def test_agent_router_knowledge_fallback():
    mock_knowledge_graph = MagicMock()
    mock_knowledge_graph.run.return_value = {
        "answer": "Mock answer",
        "sources": [],
        "metrics": {"total_time_ms": 100}
    }
    
    router = AgentRouter(knowledge_agent_graph=mock_knowledge_graph)
    
    task = Task(goal="test", description="query", assigned_agent="CTO Agent")
    state = {"session_id": "1", "conversation_id": "1"}
    
    result = router.route_and_execute(task, state)
    
    assert task.status == TaskStatus.COMPLETED
    assert result["agent_used"] == "Knowledge Agent"
    assert result["result"] == "Mock answer"
    mock_knowledge_graph.run.assert_called_once()

def test_supervisor_graph_flow():
    mock_planner = MagicMock()
    mock_planner.plan.return_value = ExecutionPlan(
        goal="Test Goal",
        tasks=[Task(goal="T1", description="desc 1", assigned_agent="Knowledge Agent")]
    )
    
    mock_task_decomposer = MagicMock()
    
    mock_router = MagicMock()
    mock_router.route_and_execute.return_value = {
        "task_id": "123",
        "agent_used": "Knowledge Agent",
        "result": "Final test answer",
        "sources": [],
        "metrics": {}
    }
    
    graph = SupervisorGraph(
        planner=mock_planner,
        task_decomposer=mock_task_decomposer,
        agent_router=mock_router
    )
    
    initial_state = {
        "user_input": "Test goal input",
        "session_id": "123",
        "conversation_id": "456",
        "execution_time_ms": 0.0,
        "selected_agents": [],
        "completed_tasks": [],
        "failed_tasks": [],
        "task_results": []
    }
    
    final_state = graph.run(initial_state)
    
    assert final_state["goal"] == "Test goal input"
    assert final_state["execution_plan"] is not None
    assert "Knowledge Agent" in final_state["selected_agents"]
    assert "Final test answer" in final_state["final_response"]
