import pytest
from app.collaboration.coordinator.collaboration_manager import CollaborationManager
from app.collaboration.teams.team_registry import TeamRegistry
from app.collaboration.teams.agent_roles import AgentCollaborationProfile
from app.collaboration.session.collaboration_session import SessionPhase


@pytest.fixture
def manager(db_session):
    registry = TeamRegistry()
    registry.register_agent(
        AgentCollaborationProfile(
            agent_id="CTO",
            expertise=["Architecture", "Engineering"],
            capabilities=[],
            confidence=0.9,
            workload=1,
            availability=True,
        )
    )
    registry.register_agent(
        AgentCollaborationProfile(
            agent_id="CFO",
            expertise=["Finance", "Cost"],
            capabilities=[],
            confidence=0.9,
            workload=1,
            availability=True,
        )
    )
    registry.register_agent(
        AgentCollaborationProfile(
            agent_id="CEO",
            expertise=["Leadership", "Strategy"],
            capabilities=[],
            confidence=0.9,
            workload=1,
            availability=True,
        )
    )
    return CollaborationManager(db_session, registry)


@pytest.mark.asyncio
async def test_scenario_1_end_to_end_lifecycle(manager):
    # Create Session
    session = manager.create_session("Architecture and Cost Review")
    assert session.current_phase == SessionPhase.CREATED

    # Form Team
    session = manager.form_team(session.session_id)
    assert session.current_phase == SessionPhase.PLANNING
    assert "CTO" in session.participants
    assert "CFO" in session.participants

    # Execute
    manager.execute(session.session_id)

    # Complete
    await manager.complete_session(session.session_id)
    session = manager.session_repo.get_session(session.session_id)
    assert session.current_phase == SessionPhase.COMPLETED


def test_scenario_2_delegation_and_resolution(manager):
    session = manager.create_session("Refactor Service")
    manager.form_team(session.session_id)
    manager.execute(session.session_id)

    # Delegate
    task = manager.delegation.delegate_task("Analyze code", "CTO")
    assert task.assignee == "CTO"

    # Complete
    manager.delegation.complete_task(task.task_id)
    assert task.status == "Completed"


def test_scenario_3_negotiation_and_consensus(manager):
    session = manager.create_session("Budget Planning")
    manager.form_team(session.session_id)
    manager.execute(session.session_id)

    # Negotiate
    nid = manager.negotiation.start_negotiation("Q3 Budget")
    manager.negotiation.add_proposal(nid, "CTO", "Increase engineering by 20%")
    p2 = manager.negotiation.add_proposal(nid, "CFO", "Increase engineering by 10%")

    manager.negotiation.accept_proposal(nid, p2.proposal_id)

    # Consensus
    manager.consensus.start_consensus("Q3 Budget Final", ["10%", "20%"])
    manager.consensus.cast_vote("Q3 Budget Final", "CTO", "10%")
    manager.consensus.cast_vote("Q3 Budget Final", "CFO", "10%")
    manager.consensus.cast_vote("Q3 Budget Final", "CEO", "10%")

    decision = manager.consensus.finalize_consensus(
        "Q3 Budget Final", ["CTO", "CFO", "CEO"]
    )
    assert decision.selected_option == "10%"
