import logging
import asyncio
from typing import List, Dict, Any
from app.capabilities.mcp.client import EnterpriseMCPClient
from app.capabilities.base.base_capability import BaseCapability
from app.capabilities.base.schemas import Capability, CapabilityType
from app.capabilities.base.capability_registry import CapabilityRegistry
from app.services.decisions.engine import DecisionEngine
from app.services.decisions.models import DecisionType

logger = logging.getLogger(__name__)

class MCPCapabilityTranslator(BaseCapability):
    """
    Translates an external MCP tool into an Enterprise BaseCapability.
    """
    def __init__(self, client: EnterpriseMCPClient, mcp_tool: Any):
        self.client = client
        self.mcp_tool = mcp_tool
        
    def get_metadata(self) -> Capability:
        return Capability(
            capability_id=f"mcp_{self.client.config.server_id}_{self.mcp_tool.name}",
            name=self.mcp_tool.name,
            description=getattr(self.mcp_tool, "description", ""),
            type=CapabilityType.MCP_SERVER,
            supported_actions=[self.mcp_tool.name],
            required_permissions=[],
            supported_agents=["*"], # Available to all agents by default
            input_schema=getattr(self.mcp_tool, "inputSchema", {}),
            output_schema={}
        )

    def _execute_internal(self, action: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        # Support running async client call inside sync _execute_internal
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            
        try:
            # We assume self.client.call_tool handles tracing and telemetry
            result = loop.run_until_complete(self.client.call_tool(self.mcp_tool.name, kwargs))
            # Format the output if it has 'content' or similar attributes
            if hasattr(result, "content"):
                data = [{"type": c.type, "text": getattr(c, "text", "")} for c in result.content]
            else:
                data = result
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class MCPDiscoveryEngine:
    """
    Discovers tools from an MCP Client and registers them in the Capability Registry.
    """
    def __init__(self, registry: CapabilityRegistry, decision_engine: DecisionEngine = None):
        self.registry = registry
        self.decision_engine = decision_engine or DecisionEngine()
        
    async def discover_and_register(self, client: EnterpriseMCPClient) -> int:
        tools = await client.list_tools()
        count = 0
        for t in tools:
            cap = MCPCapabilityTranslator(client, t)
            self.registry.register(cap)
            count += 1
            
            # Record decision about capability discovery
            self.decision_engine.record_decision(
                decision_type=DecisionType.CAPABILITY,
                component="MCPDiscoveryEngine",
                selected_option=cap.get_metadata().capability_id,
                context={"mcp_server": client.config.server_id, "tool_name": t.name}
            )
            
        logger.info(f"Discovered and registered {count} tools from MCP server {client.config.server_id}")
        return count
