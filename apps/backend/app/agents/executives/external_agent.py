import asyncio
from typing import Dict, Any
from app.agents.base.base_agent import BaseExecutiveAgent
from app.agents.base.task import ExecutiveTask
from app.agents.base.output import ExecutiveResult
from app.agents.base.profile import AgentProfile
from app.services.a2a.models import RemoteAgentProfile, A2ATaskRequest
from app.services.a2a.client import A2AClient


class ExternalAgentWrapper(BaseExecutiveAgent):
    """
    Acts as a proxy/wrapper for a remote agent.
    To the local Planner and Workflow Engine, this looks exactly like a local agent.
    """

    def __init__(
        self,
        profile: RemoteAgentProfile,
        a2a_client: A2AClient,
        llm_service=None,  # Not needed since we delegate
        capability_executor=None,
    ):
        super().__init__(
            llm_service=llm_service, capability_executor=capability_executor
        )
        self.profile = profile
        self.client = a2a_client

    def get_profile(self) -> AgentProfile:
        return self.profile

    def execute(self, task: ExecutiveTask, state: Dict[str, Any]) -> ExecutiveResult:
        """
        Overrides execution to instead delegate the task across the A2A transport.
        Because execute is currently synchronous in BaseExecutiveAgent, we run the asyncio loop.
        In a fully async system, this would just be async def execute.
        """
        request = A2ATaskRequest(
            task_id=task.task_id,
            target_agent_id=self.profile.agent_id,
            task_description=task.description,
            context=state,
            requester_org="Enterprise-Local",
            requester_agent="AgentRouter",
        )

        # Block until remote execution is complete
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio

            nest_asyncio.apply()

        # Execute via Client
        response = loop.run_until_complete(
            self.client.execute_task(self.profile.endpoint_url, request)
        )

        # Parse A2A response back into standard ExecutiveResult
        return self._create_result(
            task=task,
            summary=response.summary,
            reasoning=response.reasoning,
            recommendations=response.recommendations,
            sources=[],
            metrics=response.metrics,
        )
