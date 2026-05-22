"""
Q-SpecTrum Global Search Engine v1.0
======================================
Implements Point #18: Cross-project/knowledge/skills/roles real-time search.

Search Domains:
  1. Messages  — conversation history across all projects/chatrooms
  2. Knowledge — knowledge deposits from the pipeline
  3. Roles     — role names, capabilities, family attributes
  4. Skills    — DeerFlow skills + Q-SpecTrum skills
  5. Projects  — project names, descriptions, tags
  6. Resources — resource layer entries (if available)

Architecture:
  User Query → Tokenize → Parallel Domain Search → Score & Merge → Ranked Results

Each domain returns typed results that are scored, merged, and ranked
by a composite relevance score (keyword match + recency + frequency).
"""

import logging
import math
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("q-spectrum.global-search")


# ═══════════════════════════════════════════════════════════
# 1. SEARCH RESULT MODEL
# ═══════════════════════════════════════════════════════════

@dataclass
class SearchResult:
    """A single search result from any domain."""
    domain: str          # messages | knowledge | roles | skills | projects | resources
    result_id: str       # unique identifier
    title: str           # display title
    snippet: str         # content preview
    score: float         # relevance score (0-1)
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "id": self.result_id,
            "title": self.title,
            "snippet": self.snippet,
            "score": round(self.score, 4),
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


# ═══════════════════════════════════════════════════════════
# 2. SEARCH SCORING ENGINE
# ═══════════════════════════════════════════════════════════

class SearchScorer:
    """Lightweight keyword-based scoring engine."""

    @staticmethod
    def tokenize(query: str) -> List[str]:
        """Tokenize a query into searchable terms."""
        # Handle both Chinese and English
        terms = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9_]+', query.lower())
        # Also split Chinese into individual characters for partial match
        expanded = []
        for t in terms:
            expanded.append(t)
            if re.match(r'^[\u4e00-\u9fff]+$', t) and len(t) > 1:
                for ch in t:
                    expanded.append(ch)
        return list(set(expanded))

    @staticmethod
    def keyword_score(text: str, tokens: List[str]) -> float:
        """Score text against query tokens."""
        if not text or not tokens:
            return 0.0
        text_lower = text.lower()
        matches = sum(1 for t in tokens if t in text_lower)
        # Exact phrase bonus
        full_query = " ".join(tokens)
        phrase_bonus = 0.3 if full_query in text_lower else 0.0
        return min(1.0, (matches / len(tokens)) * 0.7 + phrase_bonus)

    @staticmethod
    def recency_score(timestamp: float, decay_hours: float = 168) -> float:
        """Time-decay score — more recent = higher score."""
        if timestamp <= 0:
            return 0.1
        age_hours = (time.time() - timestamp) / 3600
        return max(0.05, math.exp(-age_hours / decay_hours))

    @staticmethod
    def composite_score(keyword: float, recency: float = 0.5,
                        domain_boost: float = 0.0) -> float:
        """Combine scores with weights."""
        return min(1.0, keyword * 0.6 + recency * 0.25 + domain_boost * 0.15)


# ═══════════════════════════════════════════════════════════
# 3. DOMAIN SEARCHERS
# ═══════════════════════════════════════════════════════════

class MessageSearcher:
    """Search across project memory messages."""

    def __init__(self, project_memory):
        self._pm = project_memory

    def search(self, tokens: List[str], query: str,
               project_id: str = None, limit: int = 20) -> List[SearchResult]:
        if not self._pm:
            return []
        results_raw = self._pm.search_messages(query, project_id, limit=limit)
        results = []
        scorer = SearchScorer()
        for r in results_raw:
            ks = scorer.keyword_score(r["content"], tokens)
            rs = scorer.recency_score(r["timestamp"])
            score = scorer.composite_score(ks, rs)
            results.append(SearchResult(
                domain="messages",
                result_id=r["id"],
                title=f"[{r['role']}] in {r.get('chatroom_name', 'chatroom')}",
                snippet=r["content"][:200],
                score=score,
                timestamp=r["timestamp"],
                metadata={
                    "project_id": r["project_id"],
                    "chatroom_id": r["chatroom_id"],
                    "role": r["role"],
                },
            ))
        return results


class KnowledgeSearcher:
    """Search across knowledge pipeline deposits."""

    def __init__(self, knowledge_pipeline=None, project_memory=None):
        self._kp = knowledge_pipeline
        self._pm = project_memory

    def search(self, tokens: List[str], query: str,
               project_id: str = None, limit: int = 20) -> List[SearchResult]:
        results = []
        scorer = SearchScorer()

        # Search from project memory knowledge refs
        if self._pm:
            refs = self._pm.get_project_knowledge(project_id, limit=limit) if project_id \
                else self._get_all_knowledge(limit)
            for r in refs:
                ks = scorer.keyword_score(r.get("summary", ""), tokens)
                rs = scorer.recency_score(r.get("timestamp", 0))
                score = scorer.composite_score(ks, rs, domain_boost=0.1)
                results.append(SearchResult(
                    domain="knowledge",
                    result_id=r.get("deposit_id", r.get("ref_id", "")),
                    title=f"Knowledge: {r.get('type', 'unknown')}",
                    snippet=r.get("summary", "")[:200],
                    score=score,
                    timestamp=r.get("timestamp", 0),
                    metadata={"type": r.get("type", ""), "relevance": r.get("relevance", 0)},
                ))

        return results

    def _get_all_knowledge(self, limit: int) -> List[dict]:
        """Get knowledge from all projects."""
        if not self._pm:
            return []
        all_refs = []
        for p in self._pm.list_projects():
            refs = self._pm.get_project_knowledge(p["project_id"], limit=limit)
            all_refs.extend(refs)
        return sorted(all_refs, key=lambda x: x.get("timestamp", 0), reverse=True)[:limit]


class RoleSearcher:
    """Search across roles."""

    def __init__(self, db):
        self._db = db

    def search(self, tokens: List[str], query: str, limit: int = 15) -> List[SearchResult]:
        if not self._db:
            return []
        roles = self._db.get_all_roles()
        results = []
        scorer = SearchScorer()
        for code, role in roles.items():
            search_text = f"{code} {role.get('role_name','')} {role.get('family','')} {' '.join(role.get('capabilities_list',[]))}"
            ks = scorer.keyword_score(search_text, tokens)
            if ks < 0.1:
                continue
            score = scorer.composite_score(ks, 0.5, domain_boost=0.05)
            results.append(SearchResult(
                domain="roles",
                result_id=code,
                title=f"{role.get('role_name',code)} ({role.get('family','').upper()})",
                snippet=f"Capabilities: {', '.join(role.get('capabilities_list',[])[:5])}",
                score=score,
                metadata={"family": role.get("family", ""), "role_code": code},
            ))
        return sorted(results, key=lambda r: r.score, reverse=True)[:limit]


class SkillSearcher:
    """Search across DeerFlow and Q-SpecTrum skills."""

    def __init__(self, deerflow=None, skill_executor=None):
        self._df = deerflow
        self._se = skill_executor

    def search(self, tokens: List[str], query: str, limit: int = 15) -> List[SearchResult]:
        results = []
        scorer = SearchScorer()

        # DeerFlow skills
        if self._df:
            try:
                status = self._df.status()
                skills = status.get("skills", [])
                if isinstance(skills, dict):
                    skills = list(skills.keys())
                for skill_name in skills:
                    ks = scorer.keyword_score(str(skill_name), tokens)
                    if ks < 0.05:
                        continue
                    results.append(SearchResult(
                        domain="skills",
                        result_id=f"df-{skill_name}",
                        title=f"DeerFlow: {skill_name}",
                        snippet=f"DeerFlow skill for {skill_name}",
                        score=scorer.composite_score(ks, 0.5, domain_boost=0.08),
                        metadata={"source": "deerflow", "skill": skill_name},
                    ))
            except Exception:
                pass

        # Q-SpecTrum skill executor
        if self._se:
            try:
                se_skills = self._se.list_skills() if hasattr(self._se, 'list_skills') else []
                for sk in se_skills:
                    name = sk if isinstance(sk, str) else sk.get("name", "")
                    ks = scorer.keyword_score(name, tokens)
                    if ks < 0.05:
                        continue
                    results.append(SearchResult(
                        domain="skills",
                        result_id=f"qs-{name}",
                        title=f"Skill: {name}",
                        snippet=f"Q-SpecTrum skill: {name}",
                        score=scorer.composite_score(ks, 0.5),
                        metadata={"source": "qspectrum", "skill": name},
                    ))
            except Exception:
                pass

        return sorted(results, key=lambda r: r.score, reverse=True)[:limit]


class ProjectSearcher:
    """Search across projects."""

    def __init__(self, project_memory):
        self._pm = project_memory

    def search(self, tokens: List[str], query: str, limit: int = 10) -> List[SearchResult]:
        if not self._pm:
            return []
        results = []
        scorer = SearchScorer()
        for p in self._pm.list_projects():
            search_text = f"{p['project_id']} {p['name']} {' '.join(p.get('tags', []))} {p.get('context_summary', '')}"
            ks = scorer.keyword_score(search_text, tokens)
            if ks < 0.05:
                continue
            score = scorer.composite_score(ks, scorer.recency_score(p.get("created_at", 0)))
            results.append(SearchResult(
                domain="projects",
                result_id=p["project_id"],
                title=p["name"],
                snippet=f"{p.get('total_messages', 0)} messages, {p.get('chatroom_count', 0)} chatrooms. Tags: {', '.join(p.get('tags', []))}",
                score=score,
                timestamp=p.get("created_at", 0),
                metadata={"tags": p.get("tags", [])},
            ))
        return sorted(results, key=lambda r: r.score, reverse=True)[:limit]


class ResourceSearcher:
    """Search across resource layer."""

    def __init__(self, resource_layer):
        self._rl = resource_layer

    def search(self, tokens: List[str], query: str, limit: int = 15) -> List[SearchResult]:
        if not self._rl:
            return []
        results = []
        scorer = SearchScorer()
        try:
            raw = self._rl.search(query, limit=limit) if hasattr(self._rl, 'search') else []
            for r in raw:
                content = r.get("content", "") or r.get("title", "")
                ks = scorer.keyword_score(content, tokens)
                score = scorer.composite_score(ks, scorer.recency_score(r.get("timestamp", 0)))
                results.append(SearchResult(
                    domain="resources",
                    result_id=r.get("resource_id", ""),
                    title=r.get("title", "Resource"),
                    snippet=content[:200],
                    score=score,
                    timestamp=r.get("timestamp", 0),
                    metadata={"type": r.get("type", "")},
                ))
        except Exception:
            pass
        return results


# ═══════════════════════════════════════════════════════════
# 4. GLOBAL SEARCH ENGINE
# ═══════════════════════════════════════════════════════════

class GlobalSearchEngine:
    """
    Unified search across all Q-SpecTrum domains.

    Usage:
        engine = GlobalSearchEngine(
            project_memory=pm,
            knowledge_pipeline=kp,
            db=db,
            deerflow=df,
            resource_layer=rl,
        )
        results = engine.search("API安全架构")
    """

    def __init__(self, project_memory=None, knowledge_pipeline=None,
                 db=None, deerflow=None, skill_executor=None,
                 resource_layer=None):
        self._searchers = {}

        if project_memory:
            self._searchers["messages"] = MessageSearcher(project_memory)
            self._searchers["projects"] = ProjectSearcher(project_memory)

        if knowledge_pipeline or project_memory:
            self._searchers["knowledge"] = KnowledgeSearcher(knowledge_pipeline, project_memory)

        if db:
            self._searchers["roles"] = RoleSearcher(db)

        if deerflow or skill_executor:
            self._searchers["skills"] = SkillSearcher(deerflow, skill_executor)

        if resource_layer:
            self._searchers["resources"] = ResourceSearcher(resource_layer)

        self._search_history: List[dict] = []
        self._total_searches = 0

    def search(self, query: str, domains: List[str] = None,
               project_id: str = None, limit: int = 30) -> dict:
        """
        Perform a global search across specified domains.

        Args:
            query: Search query (Chinese or English)
            domains: List of domains to search (None = all)
            project_id: Limit to specific project (None = cross-project)
            limit: Maximum total results

        Returns:
            {query, tokens, results: [...], domain_counts: {...}, total, elapsed_ms}
        """
        start = time.time()
        self._total_searches += 1

        tokens = SearchScorer.tokenize(query)
        if not tokens:
            return {"query": query, "tokens": [], "results": [], "total": 0, "elapsed_ms": 0}

        target_domains = domains or list(self._searchers.keys())
        all_results: List[SearchResult] = []

        # Per-domain timeout using threads for hard enforcement
        DOMAIN_TIMEOUT = 2.0
        GLOBAL_TIMEOUT = 5.0

        import threading

        for domain in target_domains:
            searcher = self._searchers.get(domain)
            if not searcher:
                continue

            # Hard global cutoff
            if (time.time() - start) > GLOBAL_TIMEOUT:
                logger.warning(f"Global search timeout ({GLOBAL_TIMEOUT}s), skipping remaining domains")
                break

            domain_results_box: List[SearchResult] = []
            domain_error = [None]

            def _run_search(dom=domain, srch=searcher, box=domain_results_box, err=domain_error):
                try:
                    if dom in ("messages", "knowledge"):
                        box.extend(srch.search(tokens, query, project_id, limit=limit))
                    else:
                        box.extend(srch.search(tokens, query, limit=limit))
                except Exception as e:
                    err[0] = e

            t = threading.Thread(target=_run_search, daemon=True)
            t.start()
            t.join(timeout=DOMAIN_TIMEOUT)

            if t.is_alive():
                logger.warning(f"Search domain '{domain}' timed out after {DOMAIN_TIMEOUT}s, skipping")
                # Thread will die on its own as daemon
            elif domain_error[0]:
                logger.warning(f"Search error in domain '{domain}': {domain_error[0]}")
            else:
                all_results.extend(domain_results_box)

        # Sort by score descending
        all_results.sort(key=lambda r: r.score, reverse=True)
        all_results = all_results[:limit]

        # Count per domain
        domain_counts = {}
        for r in all_results:
            domain_counts[r.domain] = domain_counts.get(r.domain, 0) + 1

        elapsed_ms = (time.time() - start) * 1000

        # Track search history
        self._search_history.append({
            "query": query,
            "results": len(all_results),
            "domains": list(domain_counts.keys()),
            "elapsed_ms": round(elapsed_ms, 1),
            "timestamp": time.time(),
        })
        if len(self._search_history) > 100:
            self._search_history = self._search_history[-100:]

        return {
            "query": query,
            "tokens": tokens,
            "results": [r.to_dict() for r in all_results],
            "domain_counts": domain_counts,
            "total": len(all_results),
            "elapsed_ms": round(elapsed_ms, 1),
        }

    def get_status(self) -> dict:
        return {
            "available_domains": list(self._searchers.keys()),
            "total_searches": self._total_searches,
            "recent_searches": self._search_history[-5:],
        }


# ═══════════════════════════════════════════════════════════
# 5. SELF-TEST
# ═══════════════════════════════════════════════════════════

def _self_test():
    """Verify global search works correctly."""
    import shutil
    import tempfile

    print("=" * 60)
    print("Global Search Engine — Self Test")
    print("=" * 60)

    # Create a mock project memory with data
    from project_memory import ProjectMemoryManager
    tmp = tempfile.mkdtemp()
    pm = ProjectMemoryManager(db_path=str(Path(tmp) / "test_search.db"))

    # Set up test data
    pm.create_project("proj-mkt", "Marketing Campaign", tags=["marketing", "ads", "social"])
    pm.create_project("proj-dev", "API Development", tags=["api", "backend", "security"])

    pm.switch_project("proj-mkt")
    pm.add_message("user", "设计一个社交媒体广告投放策略")
    pm.add_message("ROLE-Q05", "Here is the social media ad strategy with budget allocation")
    pm.add_message("user", "What about the marketing budget for Q4?")

    pm.switch_project("proj-dev")
    pm.add_message("user", "Review the API security architecture")
    pm.add_message("ROLE-S01", "The API architecture has several security concerns")

    pm.add_knowledge_ref("KD-001", "strategic", "Ad campaign budget analysis for Q4", project_id="proj-mkt")
    pm.add_knowledge_ref("KD-002", "architectural", "API security design patterns", project_id="proj-dev")

    # Create search engine
    engine = GlobalSearchEngine(project_memory=pm)

    # Test 1: Basic search
    r1 = engine.search("API security")
    assert r1["total"] > 0, "Should find API security results"
    print(f"  [1] Basic search: found {r1['total']} results for 'API security' ✅")

    # Test 2: Chinese search
    r2 = engine.search("广告投放")
    assert r2["total"] > 0, "Should find Chinese results"
    print(f"  [2] Chinese search: found {r2['total']} results for '广告投放' ✅")

    # Test 3: Cross-project search
    r3 = engine.search("budget")
    assert r3["total"] > 0
    print(f"  [3] Cross-project: found {r3['total']} results for 'budget' ✅")

    # Test 4: Domain filtering
    r4 = engine.search("security", domains=["messages"])
    assert all(r["domain"] == "messages" for r in r4["results"])
    print(f"  [4] Domain filter: {r4['total']} results (messages only) ✅")

    # Test 5: Project-scoped search
    r5 = engine.search("strategy", project_id="proj-mkt")
    print(f"  [5] Project-scoped: {r5['total']} results in proj-mkt ✅")

    # Test 6: Token analysis
    tokens = SearchScorer.tokenize("API安全架构设计")
    assert "api" in tokens
    assert "安全" in tokens or "安" in tokens
    print(f"  [6] Tokenization: {tokens} ✅")

    # Test 7: Status
    status = engine.get_status()
    assert status["total_searches"] >= 5
    print(f"  [7] Status: {status['total_searches']} searches, domains={status['available_domains']} ✅")

    shutil.rmtree(tmp, ignore_errors=True)

    print("=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
    return True


if __name__ == "__main__":
    _self_test()
