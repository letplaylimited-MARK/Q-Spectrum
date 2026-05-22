"""MCP Bridge — wraps ProtocolBridge + MCP tool auto-discovery."""

import sys
from pathlib import Path
from typing import Optional


def get_scripts_dir() -> Optional[Path]:
    target = Path(__file__).resolve().parent.parent / "AI项目管理" / "Platform" / "scripts"
    return target if target.exists() else None


class ProtocolBridge:
    """Bridge to Platform/scripts/ engines (when available)."""

    def __init__(self):
        self._workflow_engine = None
        self._protocol_executor = None
        self._agent_runtime = None
        self._load_engines()

    def _load_engines(self):
        scripts_dir = get_scripts_dir()
        if not scripts_dir:
            return
        sys.path.insert(0, str(scripts_dir))
        try:
            from workflow_engine import WorkflowEngine
            self._workflow_engine = WorkflowEngine()
        except Exception:
            pass
        try:
            from protocol_executor import ProtocolExecutor
            db_path = str(scripts_dir.parent / "db" / "platform.db")
            self._protocol_executor = ProtocolExecutor(db_path)
        except Exception:
            pass

    def list_workflows(self):
        if self._workflow_engine:
            try:
                return self._workflow_engine.list_workflows()
            except Exception:
                pass
        return []

    def run_workflow(self, wf_code):
        if self._workflow_engine:
            return self._workflow_engine.run_workflow(wf_code)
        return {"error": "Workflow engine not available"}

    def trigger_protocol(self, proto_code):
        if self._protocol_executor:
            return self._protocol_executor.trigger_protocol(proto_code)
        return {"error": "Protocol executor not available"}

    def list_protocols(self):
        if self._protocol_executor:
            try:
                return self._protocol_executor.list_protocols()
            except Exception:
                pass
        return []


class McpAutoBridge:
    """Auto-discover capabilities and generate MCP tool schemas."""

    def __init__(self):
        self._tools = {}

    def discover_from(self, registry, prefix: str = "brain") -> dict:
        """Discover tools from a ComponentRegistry and return MCP tool schemas."""
        tools = {}
        for key, entry in registry._components.items():
            tool_name = f"{prefix}_{entry['type']}_{entry['name']}"
            tools[tool_name] = {
                "name": tool_name,
                "type": entry["type"],
                "version": entry["version"],
                "description": f"{entry['type']}: {entry['name']} v{entry['version']}",
            }
        self._tools.update(tools)
        return self._tools

    @property
    def tool_list(self) -> list:
        return list(self._tools.values())
