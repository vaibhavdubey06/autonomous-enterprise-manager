import logging
import asyncio
from app.services.a2a.directory import EnterpriseDirectory
from app.services.a2a.client import A2AClient
from app.agents.base.registry import AgentRegistry

logger = logging.getLogger(__name__)


class A2ADiscoveryEngine:
    """
    Engine responsible for discovering remote agents and
    registering them into the native Enterprise AgentRegistry.
    """

    def __init__(
        self,
        directory: EnterpriseDirectory,
        agent_registry: AgentRegistry,
        client: A2AClient,
    ):
        self.directory = directory
        self.agent_registry = agent_registry
        self.client = client

    async def run_discovery(self):
        """
        Interrogates all registered Enterprise organizations and discovers their agents.
        """
        logger.info("Starting A2A Discovery Phase...")
        orgs = self.directory.list_organizations()

        # We can discover from multiple endpoints in parallel
        tasks = []
        for org in orgs:
            for endpoint in org.endpoints:
                tasks.append(self._discover_endpoint(org.org_id, endpoint))

        await asyncio.gather(*tasks)
        logger.info("A2A Discovery Phase completed.")

    async def _discover_endpoint(self, org_id: str, endpoint: str):
        agents = await self.client.discover_agents(endpoint)
        if agents:
            # Update directory
            self.directory.update_organization_agents(org_id, agents)

            # Dynamically wrap and register them in the native AgentRegistry
            from app.agents.executives.external_agent import ExternalAgentWrapper

            for profile in agents:
                wrapper = ExternalAgentWrapper(profile=profile, a2a_client=self.client)
                self.agent_registry.register_agent(wrapper)
                logger.info(
                    f"Registered External Agent '{profile.agent_name}' into AgentRegistry natively."
                )
