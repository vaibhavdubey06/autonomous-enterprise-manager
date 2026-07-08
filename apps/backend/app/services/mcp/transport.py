import os
from contextlib import asynccontextmanager
from app.services.mcp.models import MCPServerConfig, MCPTransportType

try:
    from mcp.client.stdio import stdio_client, StdioServerParameters
    from mcp.client.sse import sse_client
except ImportError:
    # Handle if mcp is not installed, though it should be.
    stdio_client = None
    sse_client = None

class TransportFactory:
    """
    Factory for creating MCP transport connections based on configuration.
    """
    
    @staticmethod
    @asynccontextmanager
    async def create_transport(config: MCPServerConfig):
        if not stdio_client:
            raise RuntimeError("mcp package is not installed.")
            
        if config.transport == MCPTransportType.STDIO:
            env = os.environ.copy()
            if config.env:
                env.update(config.env)
                
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=env
            )
            async with stdio_client(server_params) as (read_stream, write_stream):
                yield read_stream, write_stream
                
        elif config.transport == MCPTransportType.SSE:
            if not config.url:
                raise ValueError("SSE transport requires a URL.")
            async with sse_client(config.url) as (read_stream, write_stream):
                yield read_stream, write_stream
        else:
            raise ValueError(f"Unsupported transport type: {config.transport}")
