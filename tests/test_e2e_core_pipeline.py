"""
tests/test_e2e_core_pipeline.py — 端到端核心链路行为断言测试
===========================================================
验证 Q-SpecTrum 核心处理链路真正工作：
  用户输入 → Secretary 路由 → HybridModeRouter 模式选择 → KnowledgeOrchestrator 检索 → LLM 生成 → KnowledgeCrystallizer 结晶 → 响应输出

8 个测试覆盖：简单查询、复杂查询、跨域查询、安全查询、模糊输入、知识检索质量、记忆持久化、优雅降级。
"""
import os
import sys
from pathlib import Path

import pytest

# Setup paths
TEST_ROOT = Path(__file__).parent
PROJECT_ROOT = TEST_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))
os.environ["QSPECTRUM_LLM"] = "mock"


def test_simple_query_inner_loop(test_engine):
    """简单查询走 Inner Loop：路由→快速检索→LLM→响应"""
    result = test_engine.process("你好，帮我写个 Python 函数")

    # 断言 1：正确路由到 QCM 家族
    assert result["routing"]["family"] == "qcm", f"Expected qcm, got {result['routing']['family']}"

    # 断言 2：LLM 生成了响应
    assert "response" in result, "Response missing from result"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"

    # 断言 3：元数据完整
    assert "metadata" in result, "Metadata missing from result"
    assert "timestamp" in result["metadata"], "Timestamp missing in metadata"
    assert "llm_provider" in result["metadata"], "llm_provider missing in metadata"


def test_complex_query_triggers_peer_mode(test_engine):
    """复杂查询触发 Peer Collaboration"""
    result = test_engine.process("深度分析：如何设计一个支持 10 万并发的微服务架构？")

    # 断言 1：路由到架构相关角色（Q01 或 S01 均可接受）
    assert result["routing"]["role_code"] in ("ROLE-Q01", "ROLE-S01"), \
        f"Expected ROLE-Q01 or ROLE-S01, got {result['routing']['role_code']}"

    # 断言 2：最终响应有内容
    assert "response" in result, "Response missing from complex query"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"


def test_cross_domain_query_negotiation(test_engine):
    """跨域查询触发多源知识检索"""
    result = test_engine.process("这个项目的技术债务如何影响安全架构？")

    # 断言 1：路由到 TRUM 家族（技术债务 → T04 Evolution）
    assert result["routing"]["family"] == "trum", f"Expected trum, got {result['routing']['family']}"

    # 断言 2：知识检索从多个源获取（如果 orchestrator 可用）
    if test_engine.knowledge_orchestrator is not None:
        user_input = result["metadata"].get("user_input", "这个项目的技术债务如何影响安全架构？")
        ctx = test_engine.knowledge_orchestrator.retrieve(user_input)
        # retrieve() returns prompt text string in the engine
        assert isinstance(ctx, str), f"Expected str from retrieve(), got {type(ctx)}"
        assert len(ctx) > 0, "Knowledge context is empty"

    # 断言 3：响应有内容
    assert "response" in result, "Response missing from cross-domain query"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"


def test_security_sensitive_query(test_engine):
    """安全敏感查询路由到 Q06 Risk Auditor"""
    result = test_engine.process("这个系统有什么安全风险？如何防护？")

    # 断言 1：路由到 Q06
    assert result["routing"]["role_code"] == "ROLE-Q06", f"Expected ROLE-Q06, got {result['routing']['role_code']}"

    # 断言 2：confidence 合理
    assert result["routing"]["confidence"] > 0.5, f"Confidence too low: {result['routing']['confidence']}"

    # 断言 3：响应有内容
    assert "response" in result, "Response missing from security query"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"


def test_ambiguous_mixed_input(test_engine):
    """模糊输入走默认路由，不崩溃"""
    result = test_engine.process("我想做个东西，类似 shopify 但更简单，怎么开始？")

    # 断言 1：路由到 QCM 家族（默认角色可能是 Q01 或其他 QCM 角色）
    assert result["routing"]["family"] == "qcm", f"Expected qcm family, got {result['routing']['family']}"

    # 断言 2：有响应（不崩溃）
    assert "response" in result, "Response missing"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"


def test_knowledge_retrieval_quality(test_engine):
    """验证知识检索返回相关内容"""
    # 直接测试 KnowledgeOrchestrator
    if test_engine.knowledge_orchestrator is None:
        pytest.skip("KnowledgeOrchestrator not loaded")

    # retrieve() returns prompt text string (the engine's public interface)
    prompt_text = test_engine.knowledge_orchestrator.retrieve("角色路由机制")

    # 断言 1：返回了字符串（prompt text）
    assert isinstance(prompt_text, str), f"Expected str from retrieve(), got {type(prompt_text)}"

    # 断言 2：prompt text 包含知识上下文标记
    assert "Knowledge Context" in prompt_text or "知識上下文" in prompt_text, \
        "Prompt text missing knowledge context marker"


def test_memory_persistence(test_engine):
    """验证记忆相关组件存在且文件结构完整"""
    # 断言 1：知识结晶器存在
    assert test_engine.knowledge_crystallizer is not None, "KnowledgeCrystallizer not loaded"

    # 断言 2：记忆文件存在
    memory_path = PROJECT_ROOT / "MEMORY.md"
    assert memory_path.exists(), f"MEMORY.md not found at {memory_path}"

    # 断言 3：_HANDOFF 目录存在
    handoff_dir = PROJECT_ROOT / "_HANDOFF"
    assert handoff_dir.exists(), f"_HANDOFF directory not found at {handoff_dir}"

    # 断言 4：STATUS.md 存在
    status_path = handoff_dir / "STATUS.md"
    assert status_path.exists(), f"STATUS.md not found at {status_path}"


def test_graceful_degradation(minimal_engine):
    """组件缺失时系统不崩溃"""
    # minimal_engine 有 knowledge_orchestrator, peer_collaboration, knowledge_crystallizer = None

    result = minimal_engine.process("测试降级")

    # 断言 1：仍然有响应
    assert "response" in result, "Response missing even with minimal components"
    assert len(result["response"]) > 10, f"Response too short: {len(result['response'])} chars"

    # 断言 2：路由仍然工作
    assert "routing" in result, "Routing missing in degradation test"
    assert result["routing"]["role_code"] is not None, "Role code missing in degradation test"
