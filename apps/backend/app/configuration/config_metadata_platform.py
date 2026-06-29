"""Enterprise Configuration & Metadata Platform."""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FeatureFlag:
    """Represents a runtime feature flag."""

    def __init__(self, name: str, enabled: bool = False, description: str = ""):
        self.name = name
        self.enabled = enabled
        self.description = description
        self.updated_at = time.time()


class ConfigurationRegistry:
    """Central registry for all runtime configuration, feature flags, and versioned assets."""

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._feature_flags: Dict[str, FeatureFlag] = {}
        self._versions: Dict[str, Dict[str, str]] = {}  # asset_type -> {name: version}

    # --- Configuration ---
    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        return dict(self._config)

    # --- Feature Flags ---
    def register_flag(
        self, name: str, enabled: bool = False, description: str = ""
    ) -> None:
        self._feature_flags[name] = FeatureFlag(name, enabled, description)

    def is_enabled(self, flag_name: str) -> bool:
        flag = self._feature_flags.get(flag_name)
        return flag.enabled if flag else False

    def toggle_flag(self, flag_name: str) -> bool:
        flag = self._feature_flags.get(flag_name)
        if flag:
            flag.enabled = not flag.enabled
            flag.updated_at = time.time()
            return flag.enabled
        return False

    def list_flags(self) -> List[Dict[str, Any]]:
        return [
            {"name": f.name, "enabled": f.enabled, "description": f.description}
            for f in self._feature_flags.values()
        ]

    # --- Version Registry ---
    def register_version(self, asset_type: str, name: str, version: str) -> None:
        if asset_type not in self._versions:
            self._versions[asset_type] = {}
        self._versions[asset_type][name] = version

    def get_version(self, asset_type: str, name: str) -> Optional[str]:
        return self._versions.get(asset_type, {}).get(name)

    def list_versions(self, asset_type: Optional[str] = None) -> Dict[str, Any]:
        if asset_type:
            return self._versions.get(asset_type, {})
        return dict(self._versions)


class MetadataEntry:
    """Metadata entry for an enterprise asset."""

    def __init__(
        self,
        asset_type: str,
        asset_id: str,
        name: str,
        owner: str = "",
        tags: Optional[List[str]] = None,
        domain: str = "",
        classification: str = "internal",
        relationships: Optional[List[str]] = None,
    ):
        self.entry_id = str(uuid.uuid4())
        self.asset_type = asset_type
        self.asset_id = asset_id
        self.name = name
        self.owner = owner
        self.tags = tags or []
        self.domain = domain
        self.classification = classification
        self.relationships = relationships or []
        self.registered_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "asset_type": self.asset_type,
            "asset_id": self.asset_id,
            "name": self.name,
            "owner": self.owner,
            "tags": self.tags,
            "domain": self.domain,
            "classification": self.classification,
            "relationships": self.relationships,
        }


class MetadataRegistry:
    """Central registry for enterprise asset metadata, ownership, and lineage."""

    def __init__(self) -> None:
        self._entries: Dict[str, MetadataEntry] = {}

    def register(self, entry: MetadataEntry) -> str:
        self._entries[entry.entry_id] = entry
        logger.info(f"Metadata registered: {entry.asset_type}/{entry.name}")
        return entry.entry_id

    def get_by_asset(self, asset_type: str, asset_id: str) -> Optional[Dict[str, Any]]:
        for entry in self._entries.values():
            if entry.asset_type == asset_type and entry.asset_id == asset_id:
                return entry.to_dict()
        return None

    def search(
        self,
        asset_type: Optional[str] = None,
        tag: Optional[str] = None,
        domain: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = list(self._entries.values())
        if asset_type:
            results = [e for e in results if e.asset_type == asset_type]
        if tag:
            results = [e for e in results if tag in e.tags]
        if domain:
            results = [e for e in results if e.domain == domain]
        if owner:
            results = [e for e in results if e.owner == owner]
        return [e.to_dict() for e in results]

    def list_all(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._entries.values()]
