"""
tests/test_api_server.py - Basic tests for api_server.py
=======================================================
api_server.py is the HTTP API server.
These tests cover basic import and handler availability.
"""
import os
import sys
from pathlib import Path

TEST_ROOT = Path(__file__).parent
PROJECT_ROOT = TEST_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))
os.environ["QSPECTRUM_LLM"] = "mock"


def test_api_server_import():
    """Test 1: API server can be imported."""
    from api_server import QSpectrumAPIHandler, ThreadingHTTPServer
    assert QSpectrumAPIHandler is not None
    assert ThreadingHTTPServer is not None


def test_api_handler_has_chat_endpoint():
    """Test 2: API handler has _handle_chat method."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_chat')


def test_api_handler_has_status_endpoint():
    """Test 3: API handler has _handle_status method."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_status')


def test_api_handler_has_roles_endpoint():
    """Test 4: API handler has _handle_roles method."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_roles')


def test_api_handler_has_negotiate_endpoint():
    """Test 5: API handler has _handle_negotiate method."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_negotiate')


def test_api_handler_has_reset_endpoint():
    """Test 6: API handler has _handle_reset method."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_reset')


def test_api_handler_has_ghost_channel_endpoints():
    """Test 7: API handler has Ghost Channel endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_gc_status')
    assert hasattr(QSpectrumAPIHandler, '_handle_gc_network')
    assert hasattr(QSpectrumAPIHandler, '_handle_gc_audit')


def test_api_handler_has_deerflow_endpoints():
    """Test 8: API handler has DeerFlow endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_df_status')
    assert hasattr(QSpectrumAPIHandler, '_handle_df_queue')
    assert hasattr(QSpectrumAPIHandler, '_handle_df_skills')


def test_api_handler_has_closed_loop_endpoints():
    """Test 9: API handler has closed-loop endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_cl_status')
    assert hasattr(QSpectrumAPIHandler, '_handle_cl_resources')
    assert hasattr(QSpectrumAPIHandler, '_handle_cl_results')


def test_api_handler_has_knowledge_pipeline_endpoints():
    """Test 10: API handler has knowledge pipeline endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_kp_status')
    assert hasattr(QSpectrumAPIHandler, '_handle_kp_deposits')


def test_api_handler_has_project_endpoints():
    """Test 11: API handler has project endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_projects_list')
    assert hasattr(QSpectrumAPIHandler, '_handle_projects_active')
    assert hasattr(QSpectrumAPIHandler, '_handle_projects_create')
    assert hasattr(QSpectrumAPIHandler, '_handle_projects_switch')


def test_api_handler_has_component_endpoints():
    """Test 12: API handler has component registry endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_components_list')
    assert hasattr(QSpectrumAPIHandler, '_handle_components_history')


def test_api_handler_has_task_endpoints():
    """Test 13: API handler has task manager endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_task_board')
    assert hasattr(QSpectrumAPIHandler, '_handle_task_create')
    assert hasattr(QSpectrumAPIHandler, '_handle_task_update')


def test_api_handler_has_contact_endpoints():
    """Test 14: API handler has contact channel endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_contact_tickets')
    assert hasattr(QSpectrumAPIHandler, '_handle_contact_notifications')


def test_api_handler_has_search_endpoint():
    """Test 15: API handler has global search endpoint."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_global_search')


def test_api_handler_has_memory_endpoints():
    """Test 16: API handler has project memory endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_memory_status')
    assert hasattr(QSpectrumAPIHandler, '_handle_memory_projects')
    assert hasattr(QSpectrumAPIHandler, '_handle_memory_chatrooms')


def test_api_handler_has_scenario_endpoints():
    """Test 17: API handler has scenario engine endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_scenario_start')
    assert hasattr(QSpectrumAPIHandler, '_handle_scenario_advance')


def test_api_handler_has_file_endpoints():
    """Test 18: API handler has file operation endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_file_scan')
    assert hasattr(QSpectrumAPIHandler, '_handle_file_read')
    assert hasattr(QSpectrumAPIHandler, '_handle_file_write')
    assert hasattr(QSpectrumAPIHandler, '_handle_file_tree')


def test_api_handler_has_5layer_endpoints():
    """Test 19: API handler has 5-layer architecture endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_resource_layer_status')
    assert hasattr(QSpectrumAPIHandler, '_handle_result_layer_status')
    assert hasattr(QSpectrumAPIHandler, '_handle_decision_layer_status')
    assert hasattr(QSpectrumAPIHandler, '_handle_full_loop_status')


def test_api_handler_has_skill_endpoints():
    """Test 20: API handler has skill endpoints."""
    from api_server import QSpectrumAPIHandler
    assert hasattr(QSpectrumAPIHandler, '_handle_real_skills_list')
    assert hasattr(QSpectrumAPIHandler, '_handle_real_skills_execute_post')
