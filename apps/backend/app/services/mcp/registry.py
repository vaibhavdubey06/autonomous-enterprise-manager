import yaml
import logging
from typing import Dict, List, Optional
from app.services.mcp.models import MCPServerConfig, MCPTransportType

logger = logging.getLogger(__name__)


class MCPServerRegistry:
    """
    Registry for configuration-driven external MCP server discovery.
    Allows dynamic configuration of external servers (github, slack, sqlite, etc).
    """

    def __init__(self, config_path: str = None):
        self.servers: Dict[str, MCPServerConfig] = {}
        if config_path:
            self.load_from_yaml(config_path)

    def load_from_yaml(self, path: str):
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)

            servers_data = data.get("mcp_servers", {})
            for sid, sdata in servers_data.items():
                transport = MCPTransportType(sdata.get("transport", "stdio"))
                config = MCPServerConfig(
                    server_id=sid,
                    name=sdata.get("name", sid),
                    transport=transport,
                    command=sdata.get("command"),
                    args=sdata.get("args", []),
                    env=sdata.get("env", {}),
                    url=sdata.get("url"),
                )
                self.register(config)
        except Exception as e:
            logger.error(f"Failed to load MCP servers from {path}: {e}")

    def register(self, config: MCPServerConfig):
        self.servers[config.server_id] = config
        logger.info(f"Registered external MCP server config: {config.name}")

    def get_server(self, server_id: str) -> Optional[MCPServerConfig]:
        return self.servers.get(server_id)

    def list_servers(self) -> List[MCPServerConfig]:
        return list(self.servers.values())
