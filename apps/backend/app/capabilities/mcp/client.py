import logging
from typing import Dict, Any, List
from app.services.mcp.models import MCPServerConfig
from app.services.mcp.transport import TransportFactory
from app.operations.tracing.trace_manager import TraceManager

try:
    from mcp import ClientSession
except ImportError:
    ClientSession = None

logger = logging.getLogger(__name__)


class EnterpriseMCPClient:
    """
    Connects to external MCP servers and provides methods to call tools.
    Integrates with TraceManager to emit telemetry for MCP client requests.
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.session = None
        self._exit_stack = None
        self.trace_manager = TraceManager()

    async def connect(self):
        if not ClientSession:
            logger.error("mcp package is not installed.")
            return False

        try:
            from contextlib import AsyncExitStack

            self._exit_stack = AsyncExitStack()

            read_stream, write_stream = await self._exit_stack.enter_async_context(
                TransportFactory.create_transport(self.config)
            )

            self.session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            await self.session.initialize()
            logger.info(f"Connected to MCP Server: {self.config.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MCP Server {self.config.name}: {e}")
            if self._exit_stack:
                await self._exit_stack.aclose()
            return False

    async def disconnect(self):
        if self._exit_stack:
            await self._exit_stack.aclose()
            self.session = None
            self._exit_stack = None

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if not self.session:
            raise RuntimeError("Client is not connected.")

        with self.trace_manager.span(None, "mcp_client_request") as span:
            span.attributes.update(
                {"mcp_server": self.config.name, "tool_name": tool_name}
            )

            try:
                result = await self.session.call_tool(tool_name, arguments)
                return result
            except Exception as e:
                span.attributes["error"] = str(e)
                raise

    async def list_tools(self) -> List[Any]:
        if not self.session:
            raise RuntimeError("Client is not connected.")

        with self.trace_manager.span(None, "mcp_list_tools") as span:
            span.attributes.update({"mcp_server": self.config.name})
            try:
                response = await self.session.list_tools()
                # Depending on mcp version, it might be response.tools or response itself
                return getattr(response, "tools", response)
            except Exception as e:
                span.attributes["error"] = str(e)
                raise
