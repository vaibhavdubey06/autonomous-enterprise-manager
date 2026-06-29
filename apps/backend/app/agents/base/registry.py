import logging
from typing import Dict, List, Optional
from app.agents.base.profile import AgentProfile
from app.agents.base.capabilities import Capability

logger = logging.getLogger(__name__)


# Note: We will use Any for the agent instance type to avoid circular imports
# since BaseExecutiveAgent will likely import from profile/capabilities.
class AgentRegistry:
    """
    Registry for discovering and retrieving Executive Agents.
    The Supervisor queries this registry to find agents capable of handling specific tasks.
    """

    def __init__(self):
        self._agents: Dict[str, "BaseExecutiveAgent"] = {}  # type: ignore

    def register_agent(self, agent: "BaseExecutiveAgent"):  # type: ignore
        """
        Registers an instantiated Executive Agent.
        """
        profile = agent.get_profile()
        self._agents[profile.agent_name] = agent
        logger.info(f"Registered Executive Agent: {profile.agent_name}")

    def get_agent(self, agent_name: str) -> Optional["BaseExecutiveAgent"]:  # type: ignore
        """
        Retrieves a registered agent by name.
        """
        return self._agents.get(agent_name)

    def list_agents(self) -> List[AgentProfile]:
        """
        Returns the profiles of all registered agents.
        """
        return [agent.get_profile() for agent in self._agents.values()]

    def find_agents_by_capability(self, capability: Capability) -> List["BaseExecutiveAgent"]:  # type: ignore
        """
        Finds all agents that possess a specific capability.
        """
        matching_agents = []
        for agent in self._agents.values():
            if capability in agent.get_profile().capabilities:
                matching_agents.append(agent)
        return matching_agents
