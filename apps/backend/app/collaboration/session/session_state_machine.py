import logging
from typing import Dict, List, Tuple
from app.collaboration.session.collaboration_session import SessionPhase

logger = logging.getLogger(__name__)

class SessionStateMachine:
    """
    Manages the lifecycle of a Collaboration Session.
    """
    
    # Define valid transitions
    TRANSITIONS: Dict[SessionPhase, List[SessionPhase]] = {
        SessionPhase.CREATED: [SessionPhase.PLANNING, SessionPhase.CANCELLED],
        SessionPhase.PLANNING: [SessionPhase.TEAM_FORMATION, SessionPhase.CANCELLED],
        SessionPhase.TEAM_FORMATION: [SessionPhase.DELEGATION, SessionPhase.CANCELLED],
        SessionPhase.DELEGATION: [SessionPhase.EXECUTION, SessionPhase.CANCELLED],
        SessionPhase.EXECUTION: [SessionPhase.NEGOTIATION, SessionPhase.CONSENSUS, SessionPhase.VERIFICATION, SessionPhase.FAILED],
        SessionPhase.NEGOTIATION: [SessionPhase.CONSENSUS, SessionPhase.EXECUTION, SessionPhase.FAILED],
        SessionPhase.CONSENSUS: [SessionPhase.VERIFICATION, SessionPhase.NEGOTIATION, SessionPhase.FAILED],
        SessionPhase.VERIFICATION: [SessionPhase.COMPLETED, SessionPhase.EXECUTION, SessionPhase.FAILED],
        SessionPhase.COMPLETED: [],
        SessionPhase.CANCELLED: [],
        SessionPhase.FAILED: []
    }

    @staticmethod
    def can_transition(current_phase: SessionPhase, target_phase: SessionPhase) -> bool:
        if target_phase in SessionStateMachine.TRANSITIONS.get(current_phase, []):
            return True
        return False

    @staticmethod
    def validate_transition(current_phase: SessionPhase, target_phase: SessionPhase) -> None:
        if not SessionStateMachine.can_transition(current_phase, target_phase):
            raise ValueError(f"Invalid state transition from {current_phase} to {target_phase}")
