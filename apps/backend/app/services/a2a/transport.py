import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

class A2ATransport(ABC):
    @abstractmethod
    async def send_request(self, endpoint: str, path: str, payload: dict) -> dict:
        pass

class HTTPTransport(A2ATransport):
    async def send_request(self, endpoint: str, path: str, payload: dict) -> dict:
        # In a real enterprise system this would include mTLS or JWT tokens
        url = f"{endpoint.rstrip('/')}/{path.lstrip('/')}"
        logger.info(f"A2A HTTP Transport sending request to {url}")
        
        # We simulate the HTTP call since this is a local evaluation framework
        # If the endpoint is local, we could route it directly.
        # For evaluation purposes, we will return a simulated success response
        # or fail if it's an explicitly bad endpoint.
        
        if "mock" in endpoint or "partner" in endpoint:
            # Simulated response for A2A evaluations
            if "discover" in path:
                return {
                    "agents": [
                        {
                            "agent_id": f"remote-agent-{endpoint[-3:]}",
                            "agent_name": f"RemoteAgent-{endpoint[-3:]}",
                            "title": "External Specialist",
                            "domain": "Logistics",
                            "description": "Handles remote execution tasks.",
                            "organization": "Partner ABC Logistics",
                            "endpoint_url": endpoint
                        }
                    ]
                }
            elif "execute" in path:
                return {
                    "task_id": payload.get("task_id"),
                    "status": "SUCCESS",
                    "summary": f"Remotely executed {payload.get('task_description')}",
                    "reasoning": "Delegated to partner systems successfully.",
                    "recommendations": ["Proceed with local planner."],
                    "metrics": {"latency_ms": 150}
                }
            elif "negotiate" in path:
                return {
                    "status": "ACCEPTED",
                    "message": "Proposal received and accepted."
                }
                
        raise ConnectionError(f"Failed to connect to A2A endpoint: {url}")
