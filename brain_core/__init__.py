"""brain_core — Q-SpecTrum Brain Template.

Extracted from qspectrum_engine.py into modular components.
"""

from brain_core.brain import Brain
from brain_core.capabilities import CapabilityRegistry, ComponentRegistry
from brain_core.config import (
    detect_modules,
    detect_writable_dir,
    find_db_path,
    get_llm_env,
    get_project_root,
)
from brain_core.graph import GraphEngine, init_knowledge_graph, init_vector_store
from brain_core.hybrid_router import HybridModeRouter
from brain_core.knowledge_crystallizer import Decision, KnowledgeCrystallizer
from brain_core.knowledge_orchestrator import KnowledgeContext, KnowledgeItem, UniversalKnowledgeOrchestrator
from brain_core.mcp_bridge import McpAutoBridge, ProtocolBridge
from brain_core.peer_collaboration import CollaborationResult, CollaborationTurn, PeerCollaborationEngine
from brain_core.skill_orchestrator import SkillOrchestrator

__all__ = [
    "get_project_root", "find_db_path", "detect_writable_dir", "detect_modules", "get_llm_env",
    "GraphEngine", "init_knowledge_graph", "init_vector_store",
    "ProtocolBridge", "McpAutoBridge",
    "ComponentRegistry", "CapabilityRegistry",
    "Brain",
    "UniversalKnowledgeOrchestrator", "KnowledgeItem", "KnowledgeContext",
    "HybridModeRouter",
    "PeerCollaborationEngine", "CollaborationTurn", "CollaborationResult",
    "SkillOrchestrator",
    "KnowledgeCrystallizer", "Decision",
]
