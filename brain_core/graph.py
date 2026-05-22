"""Graph module — KnowledgeGraph + VectorStore lazy init."""

from typing import Any


def init_knowledge_graph() -> Any:
    """Lazy-init KnowledgeGraph. Returns None on failure."""
    try:
        from knowledge_graph import KnowledgeGraph as _KG
        return _KG()
    except Exception:
        return None


def init_vector_store() -> Any:
    """Lazy-init VectorStore (ChromaDB). Returns None on failure."""
    try:
        from vector_store import VectorStore as _VS
        return _VS()
    except Exception:
        return None


class GraphEngine:
    """Wraps KnowledgeGraph + VectorStore as a single unit."""

    def __init__(self):
        self.graph = None
        self.vector_store = None
        self._init_all()

    def _init_all(self):
        self.graph = init_knowledge_graph()
        self.vector_store = init_vector_store()

    @property
    def has_graph(self) -> bool:
        return self.graph is not None

    @property
    def has_vector_store(self) -> bool:
        return self.vector_store is not None
