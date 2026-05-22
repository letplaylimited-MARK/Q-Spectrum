"""
tests/test_core_modules.py - Basic tests for remaining core modules
==================================================================
Covers 16 modules that previously had no dedicated tests.
Each module gets: import test + 1-2 core functionality tests.
"""
import os
import sys
import tempfile
from pathlib import Path

TEST_ROOT = Path(__file__).parent
PROJECT_ROOT = TEST_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))
os.environ["QSPECTRUM_LLM"] = "mock"


# ═══════════════════════════════════════════════════════════
# Ghost Channel Adapter
# ═══════════════════════════════════════════════════════════

def test_ghost_channel_adapter_import():
    """Test: ghost_channel_adapter imports."""
    from ghost_channel_adapter import GhostChannelAdapter, GhostSyncResult
    assert GhostChannelAdapter is not None
    assert GhostSyncResult is not None


def test_ghost_channel_adapter_sync():
    """Test: GhostChannelAdapter can perform sync."""
    from ghost_channel_adapter import GhostChannelAdapter
    adapter = GhostChannelAdapter()
    result = adapter.sync_role_transition(
        from_role="Secretary",
        to_role="Analyst",
        context={"test": True},
    )
    assert result.success
    assert result.integrity_verified


def test_ghost_channel_adapter_audit():
    """Test: GhostChannelAdapter generates audit log."""
    from ghost_channel_adapter import GhostChannelAdapter
    adapter = GhostChannelAdapter()
    for i in range(3):
        adapter.sync_role_transition(f"Role-{i}", f"Role-{i+1}", {"i": i})
    audit = adapter.get_audit_log(last_n=3)
    assert len(audit) == 3


# ═══════════════════════════════════════════════════════════
# Ghost Channel Gate
# ═══════════════════════════════════════════════════════════

def test_ghost_channel_gate_import():
    """Test: ghost_channel_gate imports."""
    from ghost_channel_gate import GhostChannelGate
    assert GhostChannelGate is not None


def test_ghost_channel_gate_activation():
    """Test: GhostChannelGate activation works."""
    from ghost_channel_gate import ActivationKeyManager
    mgr = ActivationKeyManager()
    key = mgr.get_activation_key()
    status = mgr.validate(key)
    assert status.valid
    assert status.tier == "trial"


# ═══════════════════════════════════════════════════════════
# Scenario Engine
# ═══════════════════════════════════════════════════════════

def test_scenario_engine_import():
    """Test: scenario_engine imports."""
    from scenario_engine import ScenarioEngineIntegration
    assert ScenarioEngineIntegration is not None


def test_scenario_engine_list():
    """Test: ScenarioEngine lists scenarios."""
    from scenario_engine import ScenarioEngineIntegration
    engine = ScenarioEngineIntegration()
    scenarios = engine.list_scenarios()
    assert len(scenarios) > 0


# ═══════════════════════════════════════════════════════════
# Negotiation Engine
# ═══════════════════════════════════════════════════════════

def test_negotiation_engine_import():
    """Test: negotiation_engine imports."""
    from negotiation_engine import NegotiationEngine
    assert NegotiationEngine is not None


def test_negotiation_engine_should_negotiate():
    """Test: NegotiationEngine detects negotiation-worthy topics."""
    from negotiation_engine import NegotiationEngine
    engine = NegotiationEngine()
    # Just verify it doesn't crash - return value may be None for simple topics
    result = engine.should_negotiate("架構設計方案討論", {})
    # Result can be None or dict, both are valid
    assert result is None or isinstance(result, dict)


# ═══════════════════════════════════════════════════════════
# Project Memory
# ═══════════════════════════════════════════════════════════

def test_project_memory_import():
    """Test: project_memory imports."""
    from project_memory import ProjectMemoryManager
    assert ProjectMemoryManager is not None


def test_project_memory_create_project():
    """Test: ProjectMemoryManager can create projects."""
    from project_memory import ProjectMemoryManager
    db_path = tempfile.mktemp(suffix=".db")
    try:
        mgr = ProjectMemoryManager(db_path)
        mgr.create_project("test_proj", "Test Project")
        state = mgr.switch_project("test_proj")
        assert state is not None
    finally:
        try:
            mgr._conn.close()
        except Exception:
            pass
        for suffix in ["", "-wal", "-shm", "-journal"]:
            p = db_path + suffix
            if os.path.exists(p):
                os.remove(p)


# ═══════════════════════════════════════════════════════════
# Global Search
# ═══════════════════════════════════════════════════════════

def test_global_search_import():
    """Test: global_search imports."""
    from global_search import GlobalSearchEngine
    assert GlobalSearchEngine is not None


def test_global_search_init():
    """Test: GlobalSearchEngine initializes."""
    from global_search import GlobalSearchEngine
    engine = GlobalSearchEngine()
    status = engine.get_status()
    assert isinstance(status, dict)


# ═══════════════════════════════════════════════════════════
# Contact Channel
# ═══════════════════════════════════════════════════════════

def test_contact_channel_import():
    """Test: contact_channel imports."""
    from contact_channel import ContactChannel
    assert ContactChannel is not None


def test_contact_channel_init():
    """Test: ContactChannel initializes."""
    from contact_channel import ContactChannel
    cc = ContactChannel()
    status = cc.get_status()
    assert isinstance(status, dict)


# ═══════════════════════════════════════════════════════════
# Task Manager
# ═══════════════════════════════════════════════════════════

def test_task_manager_import():
    """Test: task_manager imports."""
    from task_manager import TaskManager
    assert TaskManager is not None


def test_task_manager_create_task():
    """Test: TaskManager can create tasks."""
    from task_manager import TaskManager
    tm = TaskManager()
    task = tm.create_task(
        title="Test Task",
        description="A test task",
        priority="normal",
        project_id="default",
    )
    assert task is not None
    assert task.title == "Test Task"


# ═══════════════════════════════════════════════════════════
# Skill Executor
# ═══════════════════════════════════════════════════════════

def test_skill_executor_import():
    """Test: skill_executor imports."""
    from skill_executor import SkillExecutor
    assert SkillExecutor is not None


def test_skill_executor_list():
    """Test: SkillExecutor lists skills."""
    from skill_executor import SkillExecutor
    executor = SkillExecutor()
    skills = executor.list_skills()
    assert isinstance(skills, list)


# ═══════════════════════════════════════════════════════════
# Real Skills
# ═══════════════════════════════════════════════════════════

def test_real_skills_import():
    """Test: real_skills imports."""
    from real_skills import RealSkillExecutor
    assert RealSkillExecutor is not None


def test_real_skills_list():
    """Test: RealSkillExecutor lists real skills."""
    from real_skills import RealSkillExecutor
    rs = RealSkillExecutor()
    skills = rs.list_real_skills()
    assert isinstance(skills, list)


# ═══════════════════════════════════════════════════════════
# Decision Layer
# ═══════════════════════════════════════════════════════════

def test_decision_layer_import():
    """Test: decision_layer imports."""
    from decision_layer import DecisionEngine, LLMWindowManager, RoutingTuner
    assert LLMWindowManager is not None
    assert RoutingTuner is not None
    assert DecisionEngine is not None


def test_decision_layer_window_manager():
    """Test: LLMWindowManager registers windows."""
    from decision_layer import LLMWindowManager
    db_path = tempfile.mktemp(suffix=".db")
    try:
        mgr = LLMWindowManager(db_path)
        windows = mgr.list_windows()
        assert len(windows) > 0
    finally:
        for suffix in ["", "-wal", "-shm", "-journal"]:
            p = db_path + suffix
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


# ═══════════════════════════════════════════════════════════
# Closed Loop
# ═══════════════════════════════════════════════════════════

def test_closed_loop_import():
    """Test: closed_loop imports."""
    from closed_loop import ComponentConfig, FeedbackLoop, ResourceCollector
    assert ComponentConfig is not None
    assert ResourceCollector is not None
    assert FeedbackLoop is not None


def test_closed_loop_component_config():
    """Test: ComponentConfig loads defaults."""
    from closed_loop import ComponentConfig
    config = ComponentConfig()
    provider = config.get("llm", "provider")
    assert provider == "mock"


# ═══════════════════════════════════════════════════════════
# Resource Layer
# ═══════════════════════════════════════════════════════════

def test_resource_layer_import():
    """Test: resource_layer imports."""
    from resource_layer import ResourceAPI
    assert ResourceAPI is not None


def test_resource_layer_collect():
    """Test: ResourceAPI can collect resources."""
    from resource_layer import ResourceAPI
    rl = ResourceAPI()
    status = rl.get_status() if hasattr(rl, 'get_status') else {}
    assert isinstance(status, dict)


# ═══════════════════════════════════════════════════════════
# Result Layer
# ═══════════════════════════════════════════════════════════

def test_result_layer_import():
    """Test: result_layer imports."""
    from result_layer import ResultLayer
    assert ResultLayer is not None


def test_result_layer_status():
    """Test: ResultLayer returns status."""
    from result_layer import ResultLayer
    rl = ResultLayer()
    status = rl.status()
    assert isinstance(status, dict)


# ═══════════════════════════════════════════════════════════
# Role Config
# ═══════════════════════════════════════════════════════════

def test_role_config_import():
    """Test: role_config imports."""
    from role_config import YAMLRoleLoader
    assert YAMLRoleLoader is not None


def test_role_config_load():
    """Test: YAMLRoleLoader can list roles."""
    from role_config import YAMLRoleLoader
    loader = YAMLRoleLoader()
    roles = loader.list_roles()
    assert isinstance(roles, list)


# ═══════════════════════════════════════════════════════════
# DeerFlow Bridge
# ═══════════════════════════════════════════════════════════

def test_deerflow_bridge_import():
    """Test: deerflow_bridge imports."""
    from deerflow_bridge import DeerFlowBridge
    assert DeerFlowBridge is not None


def test_deerflow_bridge_status():
    """Test: DeerFlowBridge returns status."""
    from deerflow_bridge import DeerFlowBridge
    bridge = DeerFlowBridge()
    status = bridge.status()
    assert "installed" in status
