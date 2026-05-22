"""
tests/test_e2e_scenarios.py — 端到端场景集成测试
================================================
验证真实用户场景下核心链路的行为质量。

6 个场景覆盖：架构设计、内容创作、数据分析、安全审计、平台战略、模糊请求。
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


def test_scenario_architecture_design(test_engine):
    """场景：架构设计查询"""
    result = test_engine.process("如何设计微服务架构？")

    # 验证路由到架构相关角色（Q01 或 S01 均可接受）
    assert result["routing"]["role_code"] in ("ROLE-Q01", "ROLE-S01"), \
        f"Expected ROLE-Q01 or ROLE-S01, got {result['routing']['role_code']}"

    # 验证有响应
    assert "response" in result, "Response missing from architecture design scenario"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"


def test_scenario_content_creation(test_engine):
    """场景：内容创作查询"""
    result = test_engine.process("写一篇关于 AI 的文章")

    # 验证路由到 Q03 Creator
    assert result["routing"]["role_code"] == "ROLE-Q03", f"Expected ROLE-Q03, got {result['routing']['role_code']}"

    # 验证有响应
    assert "response" in result, "Response missing from content creation scenario"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"


def test_scenario_data_analysis(test_engine):
    """场景：数据分析查询"""
    result = test_engine.process("分析这个项目的技术趋势")

    # 验证路由到 Q04 Analyst
    assert result["routing"]["role_code"] == "ROLE-Q04", f"Expected ROLE-Q04, got {result['routing']['role_code']}"

    # 验证有响应
    assert "response" in result, "Response missing from data analysis scenario"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"


def test_scenario_security_audit(test_engine):
    """场景：安全审计查询"""
    result = test_engine.process("系统有什么安全风险？")

    # 验证路由到 Q06 Risk Auditor
    assert result["routing"]["role_code"] == "ROLE-Q06", f"Expected ROLE-Q06, got {result['routing']['role_code']}"

    # 验证有响应
    assert "response" in result, "Response missing from security audit scenario"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"


def test_scenario_platform_strategy(test_engine):
    """场景：平台战略查询"""
    result = test_engine.process("平台未来三年发展方向")

    # 验证路由到 TRUM 家族
    assert result["routing"]["family"] == "trum", f"Expected trum, got {result['routing']['family']}"

    # 验证有响应
    assert "response" in result, "Response missing from platform strategy scenario"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"


def test_scenario_ambiguous_request(test_engine):
    """场景：模糊请求"""
    result = test_engine.process("帮我做点什么有用的")

    # 验证路由到 QCM 家族（默认角色）
    assert result["routing"]["family"] == "qcm", f"Expected qcm family, got {result['routing']['family']}"

    # 验证不崩溃
    assert "response" in result, "Response missing from ambiguous request scenario"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"
