from app.collaboration.coordinator.conflict_manager import (
    ConflictManager,
    ConflictSeverity,
    ConflictStatus,
)
from app.collaboration.coordinator.consensus_manager import (
    ConsensusManager,
    MajorityVote,
)
from app.collaboration.coordinator.negotiation_manager import (
    NegotiationManager,
    NegotiationStatus,
)
from app.collaboration.coordinator.delegation_manager import (
    DelegationManager,
    TaskStatus,
)


def test_conflict_manager():
    mgr = ConflictManager()

    # Raise conflict
    conflict = mgr.raise_conflict(
        "c1", "Cloud Provider", ["CTO", "CFO"], ConflictSeverity.HIGH
    )
    assert conflict.conflict_id == "c1"
    assert conflict.status == ConflictStatus.OPEN

    # Get open
    open_conflicts = mgr.get_open_conflicts()
    assert len(open_conflicts) == 1

    # Resolve
    resolved = mgr.resolve_conflict("c1", "Agreed on AWS")
    assert resolved.status == ConflictStatus.RESOLVED
    assert len(mgr.get_open_conflicts()) == 0


def test_consensus_manager():
    mgr = ConsensusManager(MajorityVote())

    mgr.start_consensus("topic1", ["AWS", "GCP", "Azure"])
    mgr.cast_vote("topic1", "CTO", "AWS")
    mgr.cast_vote("topic1", "CFO", "AWS")
    mgr.cast_vote("topic1", "CEO", "GCP")

    decision = mgr.finalize_consensus("topic1", ["CTO", "CFO", "CEO"])
    assert decision.selected_option == "AWS"
    assert decision.topic == "topic1"
    assert "CTO" in decision.participants


def test_negotiation_manager():
    mgr = NegotiationManager()

    nid = mgr.start_negotiation("Budget")
    mgr.add_proposal(nid, "CTO", "Increase by 10%")
    p2 = mgr.add_proposal(nid, "CFO", "Increase by 5%")

    assert len(mgr.negotiations[nid].proposals) == 2

    neg = mgr.accept_proposal(nid, p2.proposal_id)
    assert neg.status == NegotiationStatus.ACCEPTED
    assert neg.final_proposal_id == p2.proposal_id


def test_delegation_manager():
    mgr = DelegationManager()

    task = mgr.delegate_task("Analyze metrics", "CTO")
    assert task.status == TaskStatus.ASSIGNED
    assert task.assignee == "CTO"

    reassigned = mgr.reassign_task(task.task_id, "DataScientist")
    assert reassigned.assignee == "DataScientist"

    escalated = mgr.escalate_task(task.task_id)
    assert escalated.status == TaskStatus.ESCALATED

    completed = mgr.complete_task(task.task_id)
    assert completed.status == TaskStatus.COMPLETED
