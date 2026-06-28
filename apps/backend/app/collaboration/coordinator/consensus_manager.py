from typing import List, Dict, Callable
from app.collaboration.workspace.shared_workspace import DecisionRecord
from app.collaboration.coordinator.conflict_manager import ConflictRecord
import uuid
import datetime

class ConsensusStrategy:
    def evaluate(self, topic: str, votes: Dict[str, str], options: List[str]) -> str:
        raise NotImplementedError

class MajorityVote(ConsensusStrategy):
    def evaluate(self, topic: str, votes: Dict[str, str], options: List[str]) -> str:
        counts = {}
        for vote in votes.values():
            counts[vote] = counts.get(vote, 0) + 1
        
        best_option = max(counts.items(), key=lambda x: x[1])[0]
        return best_option

class ConsensusManager:
    def __init__(self, strategy: ConsensusStrategy = MajorityVote()):
        self.strategy = strategy
        self.pending_votes: Dict[str, Dict[str, str]] = {}
        self.topics: Dict[str, List[str]] = {}
        
    def start_consensus(self, topic_id: str, options: List[str]):
        self.pending_votes[topic_id] = {}
        self.topics[topic_id] = options
        
    def cast_vote(self, topic_id: str, agent_id: str, option: str):
        if topic_id not in self.pending_votes:
            raise ValueError("Consensus topic not active")
        if option not in self.topics[topic_id]:
            raise ValueError("Invalid option")
        self.pending_votes[topic_id][agent_id] = option
        
    def finalize_consensus(self, topic_id: str, required_voters: List[str]) -> DecisionRecord:
        votes = self.pending_votes.get(topic_id, {})
        for voter in required_voters:
            if voter not in votes:
                raise ValueError(f"Waiting for vote from {voter}")
                
        selected_option = self.strategy.evaluate(topic_id, votes, self.topics[topic_id])
        
        return DecisionRecord(
            decision_id=str(uuid.uuid4()),
            topic=topic_id,
            alternatives=self.topics[topic_id],
            selected_option=selected_option,
            reasoning=f"Resolved via {self.strategy.__class__.__name__}",
            confidence=1.0,
            participants=list(votes.keys()),
            timestamp=datetime.datetime.utcnow().isoformat()
        )
