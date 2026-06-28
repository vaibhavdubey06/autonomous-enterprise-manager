import pytest
from app.collaboration.teams.agent_roles import AgentCollaborationProfile, AgentRole
from app.collaboration.teams.team_registry import TeamRegistry
from app.collaboration.teams.team_builder import TeamBuilder

@pytest.fixture
def registry():
    reg = TeamRegistry()
    reg.register_agent(AgentCollaborationProfile(
        agent_id="CTO", expertise=["Architecture", "Engineering"], capabilities=[], confidence=0.9, workload=1, availability=True
    ))
    reg.register_agent(AgentCollaborationProfile(
        agent_id="CFO", expertise=["Finance", "Cost"], capabilities=[], confidence=0.9, workload=1, availability=True
    ))
    reg.register_agent(AgentCollaborationProfile(
        agent_id="COO", expertise=["Operations"], capabilities=[], confidence=0.9, workload=1, availability=True
    ))
    reg.register_agent(AgentCollaborationProfile(
        agent_id="HR", expertise=["HR"], capabilities=[], confidence=0.9, workload=1, availability=True
    ))
    reg.register_agent(AgentCollaborationProfile(
        agent_id="Security", expertise=["Security"], capabilities=[], confidence=0.9, workload=1, availability=True
    ))
    return reg

def test_team_registry(registry):
    cto = registry.get_agent("CTO")
    assert cto is not None
    assert cto.agent_id == "CTO"
    
    archs = registry.find_agents_by_expertise("Architecture")
    assert len(archs) == 1
    assert archs[0].agent_id == "CTO"
    
def test_team_builder(registry):
    builder = TeamBuilder(registry)
    
    # 1. Repository Review
    team = builder.build_team("Repository Review")
    assert len(team) == 1
    assert team[0].agent_id == "CTO"
    assert team[0].assigned_role == AgentRole.LEADER
    
    # 2. Architecture and Cost
    team = builder.build_team("Architecture and Cost Review")
    assert len(team) == 2
    ids = [a.agent_id for a in team]
    assert "CTO" in ids
    assert "CFO" in ids
    
    # 3. Hiring
    team = builder.build_team("Hiring Strategy")
    assert len(team) == 2
    ids = [a.agent_id for a in team]
    assert "HR" in ids
    assert "CTO" in ids
