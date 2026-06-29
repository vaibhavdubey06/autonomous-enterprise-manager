from pydantic import BaseModel


class CollaborationPolicy(BaseModel):
    max_participants: int = 5
    approval_quorum: float = 0.51
    consensus_strategy: str = "MajorityVote"
    negotiation_timeout_seconds: int = 3600
    escalation_rules: dict = {}

    @classmethod
    def default(cls):
        return cls()
