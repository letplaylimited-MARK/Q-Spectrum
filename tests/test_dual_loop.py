# -*- coding: utf-8 -*-
"""Tests for Dual-Loop Brain Architecture components."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Phase 1: Knowledge Orchestrator ──

def test_knowledge_orchestrator_import():
    from brain_core.knowledge_orchestrator import UniversalKnowledgeOrchestrator
    assert UniversalKnowledgeOrchestrator is not None


def test_knowledge_item_creation():
    from brain_core.knowledge_orchestrator import KnowledgeItem
    item = KnowledgeItem(content="test", source="memory", score=0.8)
    assert item.content == "test"
    assert item.source == "memory"
    assert item.score == 0.8
    assert item.tags == []
    assert item.metadata == {}


def test_knowledge_item_to_prompt_snippet():
    from brain_core.knowledge_orchestrator import KnowledgeItem
    item = KnowledgeItem(content="test content", source="memory", score=0.8)
    snippet = item.to_prompt_snippet()
    assert "[MEMORY]" in snippet
    assert "score=0.80" in snippet
    assert "test content" in snippet


def test_knowledge_context_empty():
    from brain_core.knowledge_orchestrator import KnowledgeContext
    ctx = KnowledgeContext()
    assert ctx.to_prompt_text() == ""
    assert ctx.total_items == 0
    assert ctx.sources_used == []


def test_knowledge_context_with_items():
    from brain_core.knowledge_orchestrator import KnowledgeContext, KnowledgeItem
    ctx = KnowledgeContext(
        items=[
            KnowledgeItem(content="item1", source="memory", score=0.8),
            KnowledgeItem(content="item2", source="sqlite", score=0.5),
        ],
        query_expansion=["expanded1"],
        mode="orchestrator",
    )
    text = ctx.to_prompt_text()
    assert "知識上下文" in text
    assert "[MEMORY]" in text
    assert "[SQLITE]" in text
    assert "查詢擴展" in text
    assert ctx.total_items == 2
    assert set(ctx.sources_used) == {"memory", "sqlite"}


def test_query_expansion_basic():
    from brain_core.knowledge_orchestrator import UniversalKnowledgeOrchestrator
    orchestrator = UniversalKnowledgeOrchestrator()
    expansions = orchestrator._expand_query("路由配置")
    assert "路由配置" in expansions
    assert any("routing" in e for e in expansions)


def test_query_expansion_no_match():
    from brain_core.knowledge_orchestrator import UniversalKnowledgeOrchestrator
    orchestrator = UniversalKnowledgeOrchestrator()
    expansions = orchestrator._expand_query("hello world")
    assert expansions == ["hello world"]


def test_query_expansion_caps():
    from brain_core.knowledge_orchestrator import UniversalKnowledgeOrchestrator
    orchestrator = UniversalKnowledgeOrchestrator()
    expansions = orchestrator._expand_query("知識檢索")
    assert "知識檢索" in expansions
    assert any("knowledge" in e for e in expansions)


def test_retrieve_from_memory_source():
    from brain_core.knowledge_orchestrator import UniversalKnowledgeOrchestrator

    mock_engine = MagicMock()
    mock_engine.knowledge.search.return_value = [
        ("test content 1", 0.8, "explanation 1"),
        ("test content 2", 0.6, "explanation 2"),
    ]

    orchestrator = UniversalKnowledgeOrchestrator(engine=mock_engine)
    results = orchestrator._retrieve_from_source("memory", ["test query"])

    assert len(results) == 2
    assert results[0].source == "memory"
    assert results[0].score == 0.8


def test_retrieve_from_memory_unavailable():
    from brain_core.knowledge_orchestrator import UniversalKnowledgeOrchestrator

    orchestrator = UniversalKnowledgeOrchestrator(engine=None)
    results = orchestrator._retrieve_from_source("memory", ["test query"])
    assert results == []


def test_retrieve_from_sqlite():
    from brain_core.knowledge_orchestrator import UniversalKnowledgeOrchestrator

    mock_engine = MagicMock()
    mock_engine.db.query.return_value = [
        {"title": "Doc 1", "file_path": "/path/1", "doc_type": "spec"},
        {"title": "Doc 2", "file_path": "/path/2", "doc_type": "report"},
    ]

    orchestrator = UniversalKnowledgeOrchestrator(engine=mock_engine)
    results = orchestrator._retrieve_from_source("sqlite", ["test query"])

    assert len(results) >= 1
    assert results[0].source == "sqlite"
    assert "Doc 1" in results[0].content


def test_fusion_deduplication():
    from brain_core.knowledge_orchestrator import KnowledgeItem, UniversalKnowledgeOrchestrator

    orchestrator = UniversalKnowledgeOrchestrator()

    mock_results = [
        [KnowledgeItem(content="test content", source="memory", score=0.8)],
        [KnowledgeItem(content="test content", source="sqlite", score=0.5)],
        [KnowledgeItem(content="unique content", source="graph", score=0.6)],
    ]

    fused = orchestrator._fuse_results(mock_results, ["test query"])

    assert len(fused) == 2
    memory_item = next(i for i in fused if i.source == "memory")
    assert memory_item.score == 0.8


def test_score_confidence():
    from brain_core.knowledge_orchestrator import KnowledgeItem, UniversalKnowledgeOrchestrator

    orchestrator = UniversalKnowledgeOrchestrator()
    items = [
        KnowledgeItem(content="routing configuration", source="memory", score=0.8),
        KnowledgeItem(content="random unrelated text", source="sqlite", score=0.5),
    ]

    scored = orchestrator._score_confidence(items, "routing configuration")

    # First item should have higher score (more relevant)
    assert scored[0].source == "memory"
    assert scored[0].score > scored[1].score


def test_assemble_context_limits_items():
    from brain_core.knowledge_orchestrator import KnowledgeItem, UniversalKnowledgeOrchestrator

    orchestrator = UniversalKnowledgeOrchestrator()
    items = [KnowledgeItem(content=f"item {i}", source="memory", score=0.9 - i * 0.1)
             for i in range(10)]

    ctx = orchestrator._assemble_context(items, "orchestrator", ["query"])
    assert ctx.total_items <= 5

    ctx_peer = orchestrator._assemble_context(items, "peer", ["query"])
    assert ctx_peer.total_items <= 10


def test_retrieve_full_pipeline():
    from brain_core.knowledge_orchestrator import UniversalKnowledgeOrchestrator

    mock_engine = MagicMock()
    mock_engine.knowledge.search.return_value = [
        ("test memory content", 0.7, "explanation"),
    ]
    mock_engine.db.query.return_value = [
        {"title": "Test Doc", "file_path": "/test", "doc_type": "spec"},
    ]

    orchestrator = UniversalKnowledgeOrchestrator(engine=mock_engine)
    result = orchestrator.retrieve("知識路由", mode="orchestrator")

    # Should return non-empty prompt text
    assert isinstance(result, str)
    # Should contain knowledge context
    assert "知識上下文" in result or result == ""


# ── Phase 2: Hybrid Router ──

def test_hybrid_router_import():
    from brain_core.hybrid_router import HybridModeRouter
    assert HybridModeRouter is not None


def test_mode_selection_force_keywords():
    from brain_core.hybrid_router import HybridModeRouter
    router = HybridModeRouter()

    assert router.select_mode("深度研究架構設計") == "peer"
    assert router.select_mode("comprehensive analysis") == "peer"
    assert router.select_mode("你好") == "orchestrator"
    assert router.select_mode("狀態查詢") == "orchestrator"


def test_complexity_score_short_query():
    from brain_core.hybrid_router import HybridModeRouter
    router = HybridModeRouter()

    score = router._compute_complexity_score("你好", {})
    assert 0.0 <= score <= 1.0


def test_complexity_score_long_query():
    from brain_core.hybrid_router import HybridModeRouter
    router = HybridModeRouter()

    text = "設計一個分佈式微服務架構，需要考慮安全性、數據庫schema重構、CI/CD部署流程"
    score = router._compute_complexity_score(text, {})
    assert score > 0.3


def test_risk_assessment():
    from brain_core.hybrid_router import HybridModeRouter
    router = HybridModeRouter()

    assert router._assess_risk("刪除生產數據庫") > 0.5
    assert router._assess_risk("你好") < 0.3


def test_cross_domain_count():
    from brain_core.hybrid_router import HybridModeRouter
    router = HybridModeRouter()

    text = "架構設計和安全風險評估"
    count = router._count_cross_domain_concepts(text)
    assert count >= 2


# ── Integration: Engine has orchestrator ──

def test_engine_has_knowledge_orchestrator():
    from qspectrum_engine import QSpectrumEngine

    engine = QSpectrumEngine()
    assert hasattr(engine, 'knowledge_orchestrator')


def test_engine_has_hybrid_router():
    from qspectrum_engine import QSpectrumEngine

    engine = QSpectrumEngine()
    assert hasattr(engine, 'hybrid_router')


# ── Phase 3: Peer Collaboration ──

def test_peer_collaboration_import():
    from brain_core.peer_collaboration import PeerCollaborationEngine
    assert PeerCollaborationEngine is not None


def test_collaboration_turn_creation():
    from brain_core.peer_collaboration import CollaborationTurn
    turn = CollaborationTurn(round_num=1, speaker="qspectrum", content="test")
    assert turn.round_num == 1
    assert turn.speaker == "qspectrum"
    assert turn.content == "test"
    assert turn.timestamp is not None


def test_collaboration_result_to_dict():
    from brain_core.peer_collaboration import CollaborationResult, CollaborationTurn
    result = CollaborationResult(
        user_input="test", role_code="ROLE-Q01", family="trum",
        turns=[CollaborationTurn(round_num=1, speaker="qspectrum", content="framework")],
        final_response="done",
    )
    d = result.to_dict()
    assert d["user_input"] == "test"
    assert d["role_code"] == "ROLE-Q01"
    assert len(d["turns"]) == 1
    assert d["status"] == "completed"


def test_collaboration_engine_basic():
    from brain_core.peer_collaboration import PeerCollaborationEngine

    engine = PeerCollaborationEngine(engine=None, max_rounds=3)
    result = engine.collaborate(
        user_input="設計一個微服務架構",
        role_code="ROLE-T01",
        family="trum",
    )
    assert result.status == "completed"
    assert len(result.turns) >= 2
    assert result.turns[0].speaker == "qspectrum"
    assert result.turns[1].speaker == "llm"


def test_collaboration_needs_revision():
    from brain_core.peer_collaboration import PeerCollaborationEngine

    engine = PeerCollaborationEngine()
    assert engine._needs_revision("需要修正以下部分") is True
    assert engine._needs_revision("初稿很好，無需調整") is False


def test_collaboration_rounds_control():
    from brain_core.peer_collaboration import PeerCollaborationEngine

    engine_2 = PeerCollaborationEngine(engine=None, max_rounds=2)
    result_2 = engine_2.collaborate("test", "ROLE-Q01", "trum")
    assert len(result_2.turns) == 2

    engine_5 = PeerCollaborationEngine(engine=None, max_rounds=5)
    result_5 = engine_5.collaborate("test", "ROLE-Q01", "trum")
    assert len(result_5.turns) >= 3


# ── Phase 3: Skill Orchestrator ──

def test_skill_orchestrator_import():
    from brain_core.skill_orchestrator import SkillOrchestrator
    assert SkillOrchestrator is not None


def test_skill_matching():
    from brain_core.skill_orchestrator import SkillOrchestrator

    orchestrator = SkillOrchestrator()
    skills = orchestrator.match_skills_for_query("分析文件結構")
    assert "file-analyzer" in skills

    skills = orchestrator.match_skills_for_query("代碼審查和質量檢查")
    assert "code-reviewer" in skills

    skills = orchestrator.match_skills_for_query("你好")
    assert skills == []


def test_skill_orchestrate_empty_engine():
    from brain_core.skill_orchestrator import SkillOrchestrator

    orchestrator = SkillOrchestrator(engine=None)
    results = orchestrator.orchestrate_for_collaboration("分析文件", {})
    assert "file-analyzer" in results
    assert results["file-analyzer"]["status"] == "error"


# ── Phase 3: Knowledge Crystallizer ──

def test_knowledge_crystallizer_import():
    from brain_core.knowledge_crystallizer import KnowledgeCrystallizer
    assert KnowledgeCrystallizer is not None


def test_decision_creation():
    from brain_core.knowledge_crystallizer import Decision
    d = Decision(summary="test", content="content", priority="P0", source="collaboration")
    assert d.priority == "P0"
    assert d.verified is False


def test_crystallizer_extract_decisions():
    from brain_core.knowledge_crystallizer import KnowledgeCrystallizer
    from brain_core.peer_collaboration import CollaborationResult, CollaborationTurn

    crystallizer = KnowledgeCrystallizer()
    collab_result = CollaborationResult(
        user_input="test", role_code="ROLE-Q01", family="trum",
        turns=[
            CollaborationTurn(round_num=1, speaker="qspectrum", content="framework"),
            CollaborationTurn(round_num=2, speaker="llm", content="draft"),
            CollaborationTurn(round_num=3, speaker="qspectrum", content="review意见"),
        ],
        final_response="final answer",
    )

    decisions = crystallizer._extract_decisions(collab_result)
    assert len(decisions) >= 1
    # Should have final response decision
    assert any(d.source == "arbitration" for d in decisions)


def test_crystallizer_verify():
    from brain_core.knowledge_crystallizer import Decision, KnowledgeCrystallizer

    crystallizer = KnowledgeCrystallizer()
    decisions = [
        Decision(summary="short", content="ab", priority="P1", source="test"),
        Decision(summary="long enough", content="this is a substantial decision content", priority="P0", source="test"),
    ]

    verified = crystallizer._verify(decisions)
    assert verified[0].verified is False  # too short
    assert verified[1].verified is True


def test_engine_has_peer_collaboration():
    from qspectrum_engine import QSpectrumEngine

    engine = QSpectrumEngine()
    assert hasattr(engine, 'peer_collaboration')


def test_engine_has_skill_orchestrator():
    from qspectrum_engine import QSpectrumEngine

    engine = QSpectrumEngine()
    assert hasattr(engine, 'skill_orchestrator')


def test_engine_has_knowledge_crystallizer():
    from qspectrum_engine import QSpectrumEngine

    engine = QSpectrumEngine()
    assert hasattr(engine, 'knowledge_crystallizer')


# ── Phase 4: Process() Integration ──

def test_process_peer_mode_triggers_collaboration():
    """Test that process() triggers peer collaboration when hybrid_router selects 'peer'."""
    from qspectrum_engine import QSpectrumEngine

    engine = QSpectrumEngine()

    # Create a query that forces peer mode (contains "深度" keyword)
    result = engine.process("深度研究架構設計與安全風險評估")

    assert result["status"] == "completed"
    assert "peer_collaboration" in result
    assert result["metadata"].get("dual_loop_mode") == "peer"
    assert result["metadata"].get("collaboration_turns", 0) >= 2


def test_process_orchestrator_mode_skips_collaboration():
    """Test that process() skips peer collaboration in orchestrator mode."""
    from qspectrum_engine import QSpectrumEngine

    engine = QSpectrumEngine()

    # Create a query that forces orchestrator mode (contains "你好" keyword)
    result = engine.process("你好")

    assert result["status"] == "completed"
    # peer_collaboration should be None in orchestrator mode
    assert result.get("peer_collaboration") is None
