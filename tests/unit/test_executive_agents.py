from app.agents.executives.factory import build_default_executive_registry


class _MockLLMGateway:
    pass


def test_default_executive_registry_registers_roles():
    registry = build_default_executive_registry(llm_service=_MockLLMGateway())

    agent_names = [profile.agent_name for profile in registry.list_agents()]

    assert "CEO Agent" in agent_names
    assert "COO Agent" in agent_names
    assert "CFO Agent" in agent_names
    assert "CMO Agent" in agent_names
    assert "CHRO Agent" in agent_names
    assert "CLO Agent" in agent_names
    assert "CISO Agent" in agent_names
    assert "CIO Agent" in agent_names
    assert "CSO Agent" in agent_names
    assert "CPO Agent" in agent_names
    assert "Knowledge Agent" in agent_names
    assert "Research Agent" in agent_names
    assert "Planning Agent" in agent_names
    assert "Analytics Agent" in agent_names


def test_executive_profiles_include_metadata():
    registry = build_default_executive_registry(llm_service=_MockLLMGateway())
    cfo = registry.get_agent("CFO Agent")

    assert cfo is not None
    profile = cfo.get_profile()
    assert profile.responsibilities
    assert profile.decision_boundaries
    assert profile.prompt_strategy
    assert profile.workflow_engine_interaction
