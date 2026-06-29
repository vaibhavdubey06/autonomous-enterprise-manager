from typing import Dict, List, Optional
from app.collaboration.teams.agent_roles import AgentCollaborationProfile


class TeamRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentCollaborationProfile] = {}

    def register_agent(self, profile: AgentCollaborationProfile):
        self._agents[profile.agent_id] = profile

    def get_agent(self, agent_id: str) -> Optional[AgentCollaborationProfile]:
        return self._agents.get(agent_id)

    def get_all_agents(self) -> List[AgentCollaborationProfile]:
        return list(self._agents.values())

    def find_agents_by_expertise(
        self, expertise: str
    ) -> List[AgentCollaborationProfile]:
        return [
            a
            for a in self._agents.values()
            if expertise.lower() in [e.lower() for e in a.expertise] and a.availability
        ]
