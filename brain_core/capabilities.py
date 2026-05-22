"""Capabilities module — ComponentRegistry + capability registration."""

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("q-spectrum.capabilities")


class ComponentRegistry:
    """Pluggable component registry for hot-swapping system parts."""

    def __init__(self):
        self._components: Dict[str, Dict] = {}
        self._hooks: Dict[str, List[Callable]] = {}

    def register(self, component_type: str, name: str, instance: Any,
                 version: str = "1.0", metadata: dict = None) -> bool:
        key = f"{component_type}:{name}"
        old = self._components.get(key)
        self._components[key] = {
            "type": component_type,
            "name": name,
            "instance": instance,
            "version": version,
            "metadata": metadata or {},
        }
        for callback in self._hooks.get(f"on_register:{component_type}", []):
            try:
                callback(name, instance)
            except Exception as e:
                logger.warning(f"Component callback error for {component_type}/{name}: {e}")
        return True

    def get(self, component_type: str, name: Optional[str] = None) -> Any:
        if name:
            entry = self._components.get(f"{component_type}:{name}")
            return entry["instance"] if entry else None
        for key, entry in self._components.items():
            if entry["type"] == component_type:
                return entry["instance"]
        return None

    def all_of_type(self, component_type: str) -> List[Dict]:
        return [v for v in self._components.values() if v["type"] == component_type]

    def on_register(self, component_type: str, callback: Callable):
        self._hooks.setdefault(f"on_register:{component_type}", []).append(callback)


class CapabilityRegistry:
    """Decorator-based capability registration for MCP Auto-Bridge."""

    def __init__(self):
        self._capabilities: Dict[str, Dict] = {}

    def register(self, name: str, description: str, handler: Callable,
                 params: dict = None) -> None:
        self._capabilities[name] = {
            "name": name,
            "description": description,
            "handler": handler,
            "params": params or {},
        }

    def get_handler(self, name: str) -> Optional[Callable]:
        entry = self._capabilities.get(name)
        return entry["handler"] if entry else None

    def list_capabilities(self) -> List[Dict]:
        return list(self._capabilities.values())

    def as_mcp_tools(self) -> List[Dict]:
        return [
            {
                "name": name,
                "description": info["description"],
                "input_schema": {
                    "type": "object",
                    "properties": info["params"],
                },
            }
            for name, info in self._capabilities.items()
        ]
