"""Enterprise Plugin & Extension SDK."""

import logging
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    DISCOVERED = "discovered"
    LOADED = "loaded"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


class PluginType(Enum):
    AGENT = "agent"
    CONNECTOR = "connector"
    CAPABILITY = "capability"
    WORKFLOW = "workflow"
    POLICY = "policy"
    LLM_PROVIDER = "llm_provider"


class PluginManifest:
    """Describes a plugin's metadata and requirements."""

    def __init__(
        self,
        name: str,
        version: str,
        plugin_type: PluginType,
        description: str = "",
        author: str = "",
        dependencies: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        entry_point: Optional[str] = None,
    ):
        self.plugin_id = str(uuid.uuid4())
        self.name = name
        self.version = version
        self.plugin_type = plugin_type
        self.description = description
        self.author = author
        self.dependencies = dependencies or []
        self.permissions = permissions or []
        self.entry_point = entry_point

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "type": self.plugin_type.value,
            "description": self.description,
            "author": self.author,
        }


class PluginContext:
    """Runtime context provided to plugins during execution."""

    def __init__(self, config: Dict[str, Any], services: Dict[str, Any]):
        self.config = config
        self.services = services


class PluginHook(ABC):
    """Abstract hook that plugins implement to extend platform behavior."""

    @abstractmethod
    def on_load(self, context: PluginContext) -> None: ...

    @abstractmethod
    def on_unload(self) -> None: ...


class PluginRegistry:
    """Central registry for all installed plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginManifest] = {}
        self._hooks: Dict[str, PluginHook] = {}
        self._statuses: Dict[str, PluginStatus] = {}

    def register(
        self, manifest: PluginManifest, hook: Optional[PluginHook] = None
    ) -> str:
        self._plugins[manifest.plugin_id] = manifest
        self._statuses[manifest.plugin_id] = PluginStatus.DISCOVERED
        if hook:
            self._hooks[manifest.plugin_id] = hook
        logger.info(f"Plugin registered: {manifest.name} v{manifest.version}")
        return manifest.plugin_id

    def activate(self, plugin_id: str, context: PluginContext) -> bool:
        if plugin_id not in self._plugins:
            return False
        hook = self._hooks.get(plugin_id)
        if hook:
            try:
                hook.on_load(context)
                self._statuses[plugin_id] = PluginStatus.ACTIVE
                return True
            except Exception as e:
                logger.error(f"Plugin activation failed: {e}")
                self._statuses[plugin_id] = PluginStatus.ERROR
                return False
        self._statuses[plugin_id] = PluginStatus.ACTIVE
        return True

    def deactivate(self, plugin_id: str) -> bool:
        hook = self._hooks.get(plugin_id)
        if hook:
            hook.on_unload()
        self._statuses[plugin_id] = PluginStatus.DISABLED
        return True

    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        manifest = self._plugins.get(plugin_id)
        if manifest:
            info = manifest.to_dict()
            info["status"] = self._statuses.get(
                plugin_id, PluginStatus.DISCOVERED
            ).value
            return info
        return None

    def list_plugins(
        self, plugin_type: Optional[PluginType] = None
    ) -> List[Dict[str, Any]]:
        plugins = list(self._plugins.values())
        if plugin_type:
            plugins = [p for p in plugins if p.plugin_type == plugin_type]
        result = []
        for p in plugins:
            info = p.to_dict()
            info["status"] = self._statuses.get(
                p.plugin_id, PluginStatus.DISCOVERED
            ).value
            result.append(info)
        return result
