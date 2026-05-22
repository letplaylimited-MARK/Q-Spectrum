"""Brain orchestrator — demo/bootstrap wrapper for brain_core modules.

NOTE: This class is used by start.py for demo/status/bootstrap purposes only.
The production engine is QSpectrumEngine (qspectrum_engine.py), which creates
its own independent component instances. This is by design — Brain is a
lightweight orchestrator for quick status checks, while QSpectrumEngine is
the full production engine with all features (Secretary, KnowledgeResonance,
GhostChannel, DeerFlow, Skills, Closed-Loop, etc.).

When adding Dual-Loop Brain components (KnowledgeOrchestrator, HybridRouter,
PeerCollaboration, etc.), add them to QSpectrumEngine, NOT to this class.
"""

import logging
import sys

logger = logging.getLogger("q-spectrum.brain")

from brain_core.capabilities import CapabilityRegistry, ComponentRegistry
from brain_core.config import (
    detect_modules,
    detect_writable_dir,
    find_db_path,
    get_project_root,
)
from brain_core.graph import GraphEngine
from brain_core.mcp_bridge import McpAutoBridge, ProtocolBridge


def _load_brain_config():
    """Load project brain_config.py if available, else return defaults."""
    root = get_project_root()
    config_path = str(root)
    if config_path not in sys.path:
        sys.path.insert(0, config_path)
    try:
        import brain_config
        return getattr(brain_config, "BRAIN", {})
    except ImportError:
        logger.debug("brain_config not found, using empty config")
        return {}


def _resolve_module(name: str, cfg: dict, profile: str) -> bool:
    """Determine if module should be active: config override > profile default.

    This is the canonical source of profile defaults. The profile defaults dict
    here mirrors the profile definitions in brain_config.py (BRAIN["profile"]).
    brain_config.py is the user-editable config; this function provides fallback
    defaults if brain_config.py is not found.
    """
    overrides = cfg.get("modules", {})
    if name in overrides and overrides[name] is not None:
        return overrides[name]
    profile_defaults = {
        "minimal": {"graph": True, "protocol_bridge": False},
        "standard": {"graph": True, "protocol_bridge": True},
        "full": {"graph": True, "vector_store": True, "protocol_bridge": True},
    }
    return profile_defaults.get(profile, {}).get(name, True)




class Brain:
    """Central orchestrator for all brain_core modules."""

    def __init__(self, profile: str = None):
        cfg = _load_brain_config()
        self.profile = profile or cfg.get("profile", "standard")
        self.cfg = cfg
        self.root = get_project_root()
        self.writable_dir = detect_writable_dir()
        self.db_path = find_db_path()
        self.module_avail = detect_modules()

        self.graph_engine = GraphEngine()
        self.protocol_bridge = ProtocolBridge() if self._active("protocol_bridge") else None
        self.component_registry = ComponentRegistry()
        self.capability_registry = CapabilityRegistry()
        self.mcp_bridge = McpAutoBridge()

    def _active(self, name: str) -> bool:
        return _resolve_module(name, self.cfg, self.profile)

    @property
    def has_graph(self) -> bool:
        return self.graph_engine.has_graph

    @property
    def has_vector_store(self) -> bool:
        return self.graph_engine.has_vector_store

    def get_db_path_str(self) -> str:
        return str(self.db_path) if self.db_path else ""

    def status(self) -> dict:
        return {
            "profile": self.profile,
            "root": str(self.root),
            "writable_dir": str(self.writable_dir),
            "db_path": self.get_db_path_str(),
            "has_graph": self.has_graph,
            "has_vector_store": self.has_vector_store,
            "modules": dict(self.module_avail),
            "protocol_bridge_loaded": self.protocol_bridge is not None,
        }
