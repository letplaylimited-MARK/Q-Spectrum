"""Universal Knowledge Orchestrator — multi-source knowledge retrieval and fusion.

Dual-Loop Inner Loop: replaces single-source knowledge retrieval with
orchestrated multi-source search, fusion, dedup, and confidence scoring.

Retrieval flow:
  1. Query Expansion: expand user query (synonyms, related concepts)
  2. Source Selection: pick sources based on mode (orchestrator=fast, peer=deep)
  3. Parallel Retrieval: fetch from multiple knowledge sources
  4. Fusion & Dedup: merge results, remove duplicates, keep highest score
  5. Confidence Scoring: adjust scores based on source weight + relevance
  6. Context Assembly: build LLM-ready prompt text
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class KnowledgeItem:
    """A single piece of knowledge from any source."""
    content: str
    source: str  # "memory", "sqlite", "graph", "vector", "skills", "mcp", "web", "files"
    score: float
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def to_prompt_snippet(self) -> str:
        return f"[{self.source.upper()}] (score={self.score:.2f}) {self.content}"


@dataclass
class KnowledgeContext:
    """Assembled knowledge context for LLM prompt injection."""
    items: List[KnowledgeItem] = field(default_factory=list)
    query_expansion: List[str] = field(default_factory=list)
    mode: str = "orchestrator"  # "orchestrator" or "peer"

    def to_prompt_text(self) -> str:
        if not self.items:
            return ""
        lines = ["## 知識上下文 (Knowledge Context)"]
        for item in self.items:
            lines.append(item.to_prompt_snippet())
        if self.query_expansion:
            lines.append(f"\n查詢擴展: {', '.join(self.query_expansion)}")
        return "\n".join(lines)

    @property
    def total_items(self) -> int:
        return len(self.items)

    @property
    def sources_used(self) -> List[str]:
        return list(set(item.source for item in self.items))


class UniversalKnowledgeOrchestrator:
    """
    多源知識編排器 — 統一調度所有知識來源，生成融合上下文。
    """

    SOURCES = {
        "memory": "KnowledgeResonance (R-Formula 內存搜索)",
        "sqlite": "platform.db documents/knowledge_items 表",
        "vector": "VectorStore (TF-IDF 語義搜索)",
        "graph": "KnowledgeGraph (21 算子關聯查詢)",
        "skills": "RealSkills (5 個本地技能)",
        "deerflow": "DeerFlow (deep-research, data-analysis 等)",
        "mcp": "MCP Tools (18 工具元數據)",
        "web": "Web Search (可選，需 API)",
        "files": "專案文件系統 (markdown/python 等)",
    }

    SYNONYM_MAP = {
        "路由": ["routing", "route", "秘書", "secretary", "5D雷達"],
        "知識": ["knowledge", "記憶", "memory", "檢索", "retrieval"],
        "角色": ["role", "agent", "AI角色", "family", "家族"],
        "技能": ["skill", "capability", "能力", "executor"],
        "圖譜": ["graph", "knowledge graph", "knowledge_graph", "算子", "operator"],
        "向量": ["vector", "embedding", "語義", "semantic", "TF-IDF"],
        "架構": ["architecture", "system design", "系統設計", "distributed", "分佈式"],
        "安全": ["security", "risk", "風險", "threat", "威脅", "vulnerability"],
    }

    def __init__(self, engine=None):
        """
        Args:
            engine: QSpectrumEngine instance (for accessing knowledge, db, graph, etc.)
        """
        self.engine = engine
        self._source_cache = {}

    def _expand_query(self, query: str) -> List[str]:
        """Step 1: Query Expansion — expand user query with synonyms."""
        expansions = [query]
        query_lower = query.lower()

        for keyword, synonyms in self.SYNONYM_MAP.items():
            if keyword in query_lower:
                for syn in synonyms[:2]:
                    expanded = query_lower.replace(keyword, syn)
                    if expanded not in expansions:
                        expansions.append(expanded)

        return expansions[:5]

    def _select_sources(self, query: str, mode: str, max_sources: int = 5) -> List[str]:
        """Select which sources to query based on mode and query type."""
        if mode == "peer":
            default_sources = ["memory", "sqlite", "graph", "vector", "skills", "mcp"]
        else:
            default_sources = ["memory", "sqlite", "graph"]

        return default_sources[:max_sources]

    def _retrieve_from_source(self, source_name: str, expanded_queries: List[str]) -> List[KnowledgeItem]:
        """Retrieve knowledge from a specific source."""
        if source_name == "memory":
            return self._retrieve_from_memory(expanded_queries)
        elif source_name == "sqlite":
            return self._retrieve_from_sqlite(expanded_queries)
        elif source_name == "graph":
            return self._retrieve_from_graph(expanded_queries)
        elif source_name == "vector":
            return self._retrieve_from_vector(expanded_queries)
        elif source_name == "skills":
            return self._retrieve_from_skills(expanded_queries)
        elif source_name == "mcp":
            return self._retrieve_from_mcp(expanded_queries)
        else:
            return []

    def _retrieve_from_memory(self, queries: List[str]) -> List[KnowledgeItem]:
        """Retrieve from KnowledgeResonance (R-Formula search)."""
        if not self.engine or not hasattr(self.engine, 'knowledge'):
            return []

        results = []
        for query in queries[:3]:
            try:
                search_results = self.engine.knowledge.search(query, top_k=3)
                for content, score, explanation in search_results:
                    results.append(KnowledgeItem(
                        content=content,
                        source="memory",
                        score=score,
                        tags=["memory", "resonance"],
                        metadata={"explanation": explanation},
                    ))
            except Exception:
                pass
        return results

    def _retrieve_from_sqlite(self, queries: List[str]) -> List[KnowledgeItem]:
        """Retrieve from platform.db documents table."""
        if not self.engine or not hasattr(self.engine, 'db'):
            return []

        results = []
        for query in queries[:2]:
            try:
                keywords = [w for w in query.split() if len(w) > 1][:3]
                for kw in keywords:
                    rows = self.engine.db.query(
                        "SELECT title, file_path, doc_type FROM documents WHERE title LIKE ? LIMIT 3",
                        (f"%{kw}%",)
                    )
                    for row in rows:
                        r = dict(row)
                        results.append(KnowledgeItem(
                            content=f"{r['title']} ({r.get('file_path', 'N/A')})",
                            source="sqlite",
                            score=0.5,
                            tags=["sqlite", "document", r.get('doc_type', 'unknown')],
                        ))
            except Exception:
                pass
        return results

    def _retrieve_from_graph(self, queries: List[str]) -> List[KnowledgeItem]:
        """Retrieve from KnowledgeGraph (21 operators)."""
        if not self.engine or not hasattr(self.engine, 'graph'):
            return []

        results = []
        for query in queries[:2]:
            try:
                nodes = self.engine.graph.query(label=query)
                for node in nodes[:5]:
                    results.append(KnowledgeItem(
                        content=f"Graph node: {node.get('label', 'unknown')} ({node.get('node_type', 'unknown')})",
                        source="graph",
                        score=0.6,
                        tags=["graph", "operator", node.get('op_code', '')],
                        metadata={"node": node},
                    ))
            except Exception:
                pass
        return results

    def _retrieve_from_vector(self, queries: List[str]) -> List[KnowledgeItem]:
        """Retrieve from VectorStore (TF-IDF semantic search)."""
        if not self.engine or not hasattr(self.engine, 'vector_store'):
            return []

        results = []
        for query in queries[:2]:
            try:
                vs_results = self.engine.vector_store.search(query, top_k=3)
                for item in vs_results:
                    results.append(KnowledgeItem(
                        content=item.get('content', str(item)),
                        source="vector",
                        score=item.get('score', 0.5),
                        tags=["vector", "semantic"],
                    ))
            except Exception:
                pass
        return results

    def _retrieve_from_skills(self, queries: List[str]) -> List[KnowledgeItem]:
        """Retrieve metadata from RealSkills."""
        if not self.engine or not hasattr(self.engine, 'real_skills'):
            return []

        results = []
        skill_names = ["file-analyzer", "code-reviewer", "data-processor", "project-planner", "system-reporter"]
        for skill_name in skill_names:
            results.append(KnowledgeItem(
                content=f"可用技能: {skill_name}",
                source="skills",
                score=0.3,
                tags=["skill", skill_name],
            ))
        return results

    def _retrieve_from_mcp(self, queries: List[str]) -> List[KnowledgeItem]:
        """Retrieve metadata from MCP Tools."""
        if not self.engine or not hasattr(self.engine, 'protocol_bridge'):
            return []

        results = []
        try:
            tools = self.engine.protocol_bridge.list_tools() if hasattr(self.engine.protocol_bridge, 'list_tools') else []
            for tool in tools[:5]:
                results.append(KnowledgeItem(
                    content=f"MCP Tool: {tool.get('name', 'unknown')} — {tool.get('description', '')[:100]}",
                    source="mcp",
                    score=0.3,
                    tags=["mcp", "tool"],
                ))
        except Exception:
            pass
        return results

    def _fuse_results(self, all_results: List[List[KnowledgeItem]],
                      expanded_queries: List[str]) -> List[KnowledgeItem]:
        """Step 3: Fusion & Dedup — merge results, remove duplicates, keep highest score."""
        seen_content = {}

        for results in all_results:
            for item in results:
                normalized = self._normalize_content(item.content)
                if normalized in seen_content:
                    if item.score > seen_content[normalized].score:
                        seen_content[normalized] = item
                else:
                    seen_content[normalized] = item

        return list(seen_content.values())

    def _normalize_content(self, content: str) -> str:
        """Normalize content for deduplication."""
        normalized = re.sub(r'[^\w\s]', '', content.lower().strip())
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized[:100]

    def _score_confidence(self, items: List[KnowledgeItem], query: str) -> List[KnowledgeItem]:
        """Step 4: Confidence Scoring — adjust scores based on multiple factors."""
        query_lower = query.lower()
        for item in items:
            source_weights = {
                "memory": 1.0, "sqlite": 0.9, "graph": 0.8,
                "vector": 0.85, "skills": 0.7, "mcp": 0.6,
                "web": 0.75, "files": 0.65, "deerflow": 0.8,
            }
            source_weight = source_weights.get(item.source, 0.5)

            query_tokens = set(query_lower.split())
            content_tokens = set(item.content.lower().split())
            relevance = len(query_tokens & content_tokens) / max(len(query_tokens), 1)

            recency = item.metadata.get('recency', 1.0)

            item.score = item.score * source_weight * (0.5 + 0.5 * relevance) * recency
            item.score = min(1.0, max(0.0, item.score))

        items.sort(key=lambda x: x.score, reverse=True)
        return items

    def _assemble_context(self, items: List[KnowledgeItem], mode: str,
                          expanded_queries: List[str]) -> KnowledgeContext:
        """Step 5: Context Assembly — build final KnowledgeContext."""
        max_items = 10 if mode == "peer" else 5
        limited_items = items[:max_items]

        return KnowledgeContext(
            items=limited_items,
            query_expansion=expanded_queries[1:],
            mode=mode,
        )

    def retrieve(self, query: str, context: dict = None, mode: str = "orchestrator",
                 max_sources: int = 5) -> str:
        """
        Main retrieval entry point (sync, returns prompt text for fallback chain).

        Args:
            query: User query
            context: Optional context dict (unused for now, reserved for hybrid_router)
            mode: "orchestrator" (fast) or "peer" (deep)
            max_sources: Maximum number of sources to query

        Returns:
            Prompt text string (empty string if no knowledge found)
        """
        # Step 1: Query Expansion
        expanded = self._expand_query(query)

        # Step 2: Select sources
        sources = self._select_sources(query, mode, max_sources)

        # Step 3: Retrieval
        all_results = []
        for source_name in sources:
            results = self._retrieve_from_source(source_name, expanded)
            all_results.append(results)

        # Step 4: Fusion & Dedup
        fused = self._fuse_results(all_results, expanded)

        # Step 5: Confidence Scoring
        scored = self._score_confidence(fused, query)

        # Step 6: Context Assembly
        ctx = self._assemble_context(scored, mode, expanded)

        return ctx.to_prompt_text()
