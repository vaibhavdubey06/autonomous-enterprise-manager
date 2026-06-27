import pytest
from unittest.mock import MagicMock
from app.agents.base.registry import AgentRegistry
from app.agents.base.profile import AgentProfile
from app.agents.base.capabilities import Capability
from app.agents.base.task import ExecutiveTask
from app.agents.executives.cto.agent import CTOAgent

def test_agent_registry():
    registry = AgentRegistry()
    
    # Create a mock agent
    mock_agent = MagicMock()
    mock_profile = AgentProfile(
        agent_name="Mock Agent",
        title="Mock Title",
        domain="Testing",
        description="A mock agent",
        capabilities=[Capability.CODE_REVIEW]
    )
    mock_agent.get_profile.return_value = mock_profile
    
    registry.register_agent(mock_agent)
    
    assert registry.get_agent("Mock Agent") == mock_agent
    assert len(registry.list_agents()) == 1
    
    # Test capability lookup
    assert len(registry.find_agents_by_capability(Capability.CODE_REVIEW)) == 1
    assert len(registry.find_agents_by_capability(Capability.ARCHITECTURE_ANALYSIS)) == 0

def test_cto_agent_profile():
    mock_llm = MagicMock()
    cto = CTOAgent(llm_service=mock_llm)
    
    profile = cto.get_profile()
    assert profile.agent_name == "CTO Agent"
    assert Capability.ARCHITECTURE_ANALYSIS in profile.capabilities

def test_cto_agent_execution():
    mock_llm = MagicMock()
    mock_knowledge_agent = MagicMock()
    
    cto = CTOAgent(llm_service=mock_llm, knowledge_agent_graph=mock_knowledge_agent)
    
    # Mock Planner
    mock_plan = MagicMock()
    mock_plan.queries = ["architecture context"]
    cto.planner.plan = MagicMock(return_value=mock_plan)
    
    # Mock Architect
    mock_arch_findings = MagicMock()
    mock_arch_findings.scalability_score = 8
    mock_arch_findings.modularity_score = 9
    mock_arch_findings.findings = ["Good scalability"]
    mock_arch_findings.recommendations = ["Add more caching"]
    cto.architect.review = MagicMock(return_value=mock_arch_findings)
    
    # Mock knowledge retrieval
    mock_knowledge_agent.run.return_value = {
        "answer": "system uses microservices",
        "sources": [{"title": "arch.md"}]
    }
    
    task = ExecutiveTask(
        goal="Review architecture",
        description="Check scalability",
        required_capabilities=[Capability.ARCHITECTURE_ANALYSIS]
    )
    
    state = {"session_id": "1"}
    
    result = cto.execute(task, state)
    
    assert result.agent == "CTO Agent"
    assert "caching" in result.recommendations[0]
    assert result.task_id == task.task_id
    mock_knowledge_agent.run.assert_called_once()
