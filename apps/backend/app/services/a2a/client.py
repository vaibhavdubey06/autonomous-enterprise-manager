import time
import logging
from typing import List
from app.services.a2a.transport import A2ATransport, HTTPTransport
from app.services.a2a.models import (
    A2ATaskRequest,
    A2ATaskResponse,
    RemoteAgentProfile,
    A2ANegotiationProposal,
)
from app.operations.tracing.trace_manager import TraceManager

logger = logging.getLogger(__name__)


class A2AClient:
    """
    Client for interacting with remote Enterprise Managers over A2A.
    Handles discovery, delegation, and negotiation safely.
    """

    def __init__(self, transport: A2ATransport = HTTPTransport()):
        self.transport = transport
        self.trace_manager = TraceManager()

    async def discover_agents(self, endpoint: str) -> List[RemoteAgentProfile]:
        with self.trace_manager.span(None, "a2a_discovery_request") as span:
            span.attributes["remote_endpoint"] = endpoint
            start_time = time.time()
            try:
                response = await self.transport.send_request(endpoint, "discover", {})
                agents_data = response.get("agents", [])

                profiles = []
                for data in agents_data:
                    # In a real app we'd validate against RemoteAgentProfile schema fully
                    profile = RemoteAgentProfile(**data)
                    profiles.append(profile)

                span.attributes["discovered_count"] = len(profiles)
                span.status = "SUCCESS"
                return profiles

            except Exception as e:
                span.status = "ERROR"
                span.attributes["error"] = str(e)
                logger.error(f"A2A Discovery failed at {endpoint}: {e}")
                return []
            finally:
                span.attributes["latency_ms"] = (time.time() - start_time) * 1000

    async def execute_task(
        self, endpoint: str, request: A2ATaskRequest
    ) -> A2ATaskResponse:
        with self.trace_manager.span(None, "a2a_delegation_request") as span:
            span.attributes.update(
                {
                    "remote_endpoint": endpoint,
                    "target_agent_id": request.target_agent_id,
                    "task_id": request.task_id,
                    "requester_org": request.requester_org,
                }
            )
            start_time = time.time()
            try:
                response = await self.transport.send_request(
                    endpoint, "execute", request.model_dump()
                )

                result = A2ATaskResponse(**response)
                span.status = result.status
                span.attributes["summary"] = result.summary
                return result

            except Exception as e:
                span.status = "ERROR"
                span.attributes["error"] = str(e)
                logger.error(f"A2A Task Delegation failed at {endpoint}: {e}")
                return A2ATaskResponse(
                    task_id=request.task_id,
                    status="ERROR",
                    summary="Failed to delegate task.",
                    reasoning=str(e),
                    errors=[str(e)],
                )
            finally:
                span.attributes["latency_ms"] = (time.time() - start_time) * 1000

    async def send_proposal(
        self, endpoint: str, proposal: A2ANegotiationProposal
    ) -> dict:
        with self.trace_manager.span(None, "a2a_negotiation_request") as span:
            span.attributes.update(
                {
                    "remote_endpoint": endpoint,
                    "negotiation_id": proposal.negotiation_id,
                    "topic": proposal.topic,
                }
            )
            start_time = time.time()
            try:
                response = await self.transport.send_request(
                    endpoint, "negotiate", proposal.model_dump()
                )
                span.status = "SUCCESS"
                return response
            except Exception as e:
                span.status = "ERROR"
                span.attributes["error"] = str(e)
                logger.error(f"A2A Negotiation failed at {endpoint}: {e}")
                return {"status": "ERROR", "error": str(e)}
            finally:
                span.attributes["latency_ms"] = (time.time() - start_time) * 1000
