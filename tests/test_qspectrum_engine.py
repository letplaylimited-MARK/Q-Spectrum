"""
tests/test_qspectrum_engine.py — 基础测试 for qspectrum_engine.py
================================================================
qspectrum_engine.py 是 4100+ 行的核心引擎。
这些测试覆盖最基本的功能，确保引擎可以加载和运行。
"""
import os
import sys
from pathlib import Path

# Setup paths
TEST_ROOT = Path(__file__).parent
PROJECT_ROOT = TEST_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))
os.environ["QSPECTRUM_LLM"] = "mock"


def test_engine_import():
    """Test 1: Engine can be imported without errors."""
    from qspectrum_engine import QSpectrumDB, QSpectrumEngine, Secretary
    assert QSpectrumEngine is not None
    assert Secretary is not None
    assert QSpectrumDB is not None


def test_db_loads_roles():
    """Test 2: QSpectrumDB loads all 15 roles."""
    from qspectrum_engine import QSpectrumDB
    db = QSpectrumDB()
    try:
        roles = db.get_all_roles()
        assert len(roles) == 15, f"Expected 15 roles, got {len(roles)}"

        # Check key roles exist
        assert "ROLE-T01" in roles
        assert "ROLE-Q01" in roles
        assert "ROLE-S01" in roles
    finally:
        db.close()


def test_db_loads_protocols():
    """Test 3: QSpectrumDB loads all 10 protocols."""
    from qspectrum_engine import QSpectrumDB
    db = QSpectrumDB()
    try:
        protocols = db.get_all_protocols()
        assert len(protocols) == 10, f"Expected 10 protocols, got {len(protocols)}"
    finally:
        db.close()


def test_secretary_routes_to_qcm():
    """Test 4: Secretary routes content creation to QCM."""
    from qspectrum_engine import QSpectrumDB, Secretary
    db = QSpectrumDB()
    try:
        sec = Secretary(db)
        result = sec.route("写一篇关于 AI 的文章")
        assert result["family"] == "qcm", f"Expected qcm, got {result['family']}"
    finally:
        db.close()


def test_secretary_routes_to_trum():
    """Test 5: Secretary routes platform strategy to TRUM."""
    from qspectrum_engine import QSpectrumDB, Secretary
    db = QSpectrumDB()
    try:
        sec = Secretary(db)
        result = sec.route("平台战略规划")
        assert result["family"] == "trum", f"Expected trum, got {result['family']}"
    finally:
        db.close()


def test_secretary_routes_to_spec():
    """Test 6: Secretary routes DB schema to SPEC."""
    from qspectrum_engine import QSpectrumDB, Secretary
    db = QSpectrumDB()
    try:
        sec = Secretary(db)
        result = sec.route("数据库表结构设计")
        assert result["family"] == "spec", f"Expected spec, got {result['family']}"
    finally:
        db.close()


def test_engine_process_single_query():
    """Test 7: Engine can process a single query."""
    from qspectrum_engine import QSpectrumEngine, create_llm_provider
    llm, _ = create_llm_provider("mock")
    engine = QSpectrumEngine(llm_provider=llm)
    try:
        result = engine.process("你好")
        assert "response" in result
        assert "routing" in result
        assert result["routing"]["role_code"] is not None
    finally:
        engine.close()


def test_engine_get_system_status():
    """Test 8: Engine returns system status."""
    from qspectrum_engine import QSpectrumEngine, create_llm_provider
    llm, _ = create_llm_provider("mock")
    engine = QSpectrumEngine(llm_provider=llm)
    try:
        status = engine.get_system_status()
        assert "roles_loaded" in status
        assert status["roles_loaded"] == 15
    finally:
        engine.close()


def test_engine_close():
    """Test 9: Engine can be closed without errors."""
    from qspectrum_engine import QSpectrumEngine, create_llm_provider
    llm, _ = create_llm_provider("mock")
    engine = QSpectrumEngine(llm_provider=llm)
    engine.close()
    # No assertion needed - just verify no exception


def test_dual_loop_components_exist():
    """Test 10: Dual-Loop components are available."""
    from qspectrum_engine import (
        _HAS_HYBRID_ROUTER,
        _HAS_KNOWLEDGE_CRYSTALLIZER,
        _HAS_KNOWLEDGE_ORCHESTRATOR,
        _HAS_PEER_COLLABORATION,
        _HAS_SKILL_ORCHESTRATOR,
    )
    assert _HAS_KNOWLEDGE_ORCHESTRATOR, "Knowledge Orchestrator not loaded"
    assert _HAS_HYBRID_ROUTER, "Hybrid Router not loaded"
    assert _HAS_PEER_COLLABORATION, "Peer Collaboration not loaded"
    assert _HAS_SKILL_ORCHESTRATOR, "Skill Orchestrator not loaded"
    assert _HAS_KNOWLEDGE_CRYSTALLIZER, "Knowledge Crystallizer not loaded"


def test_brain_core_modules_exist():
    """Test 11: brain_core modules are available."""
    from qspectrum_engine import _HAS_BRAIN_CORE
    assert _HAS_BRAIN_CORE, "brain_core not loaded"


def test_engine_metadata_enriched():
    """Test 12: Engine response includes metadata."""
    from qspectrum_engine import QSpectrumEngine, create_llm_provider
    llm, _ = create_llm_provider("mock")
    engine = QSpectrumEngine(llm_provider=llm)
    try:
        result = engine.process("测试查询")
        assert "metadata" in result
        metadata = result["metadata"]
        assert "llm_provider" in metadata
        assert "timestamp" in metadata
    finally:
        engine.close()
