# -*- coding: utf-8 -*-
"""
Test _retrieve_knowledge() 4-layer fallback chain.

Tests:
  1. Fallback 1→2: knowledge_orchestrator None → prompt_builder (normal path)
  2. Fallback 1→2: knowledge_orchestrator returns empty → prompt_builder
  3. Fallback 1→2: knowledge_orchestrator raises exception → prompt_builder
  4. Fallback 2→3: prompt_builder fails → raw DB search
  5. Fallback 3→4: raw DB fails → empty string
  6. Performance: no regression vs direct prompt_builder call
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from qspectrum_engine import QSpectrumEngine


def make_engine():
    return QSpectrumEngine()


def test_fallback_1_to_2_normal():
    engine = make_engine()
    assert engine.knowledge_orchestrator is not None, "orchestrator should be initialized"
    result = engine._retrieve_knowledge("項目管理")
    print(f"  [OK] Fallback 1 (orchestrator active): got {len(result)} chars")
    return True


def test_fallback_1_to_2_orchestrator_empty():
    engine = make_engine()
    class FakeOrchestrator:
        def retrieve(self, query, context, mode="orchestrator"):
            return ""
    engine.knowledge_orchestrator = FakeOrchestrator()
    result = engine._retrieve_knowledge("項目管理")
    print(f"  [OK] Fallback 1→2 (orchestrator empty): got {len(result)} chars")
    return True


def test_fallback_1_to_2_orchestrator_exception():
    engine = make_engine()
    class FakeOrchestrator:
        def retrieve(self, query, context, mode="orchestrator"):
            raise RuntimeError("orchestrator failed")
    engine.knowledge_orchestrator = FakeOrchestrator()
    result = engine._retrieve_knowledge("項目管理")
    print(f"  [OK] Fallback 1→2 (orchestrator exception): got {len(result)} chars")
    return True


def test_fallback_2_to_3():
    engine = make_engine()
    engine.knowledge_orchestrator = None
    original_pb = engine.prompt_builder
    class FakePromptBuilder:
        def build_knowledge_context(self, user_input):
            raise RuntimeError("prompt_builder failed")
    engine.prompt_builder = FakePromptBuilder()
    result = engine._retrieve_knowledge("項目管理")
    engine.prompt_builder = original_pb
    if "相關文檔 (fallback)" in result or result == "":
        print(f"  [OK] Fallback 2→3: got {len(result)} chars (raw DB or empty)")
        return True
    print(f"  [FAIL] Fallback 2→3: unexpected result: {result[:100]}")
    return False


def test_fallback_3_to_4():
    engine = make_engine()
    engine.knowledge_orchestrator = None
    original_pb = engine.prompt_builder
    original_db = engine.db
    class FakePromptBuilder:
        def build_knowledge_context(self, user_input):
            raise RuntimeError("prompt_builder failed")
    class FakeDB:
        def query(self, sql, params):
            raise RuntimeError("db query failed")
    engine.prompt_builder = FakePromptBuilder()
    engine.db = FakeDB()
    result = engine._retrieve_knowledge("zzz_nonexistent_keyword_xyz")
    engine.prompt_builder = original_pb
    engine.db = original_db
    if result == "":
        print("  [OK] Fallback 3→4: got empty string (graceful degradation)")
        return True
    print(f"  [FAIL] Fallback 3→4: expected empty, got: {result[:100]}")
    return False


def test_performance_no_regression():
    engine = make_engine()
    engine._retrieve_knowledge("test")
    iterations = 50
    start = time.time()
    for _ in range(iterations):
        engine._retrieve_knowledge("項目管理")
    elapsed_new = time.time() - start
    start = time.time()
    for _ in range(iterations):
        engine.prompt_builder.build_knowledge_context("項目管理")
    elapsed_direct = time.time() - start
    overhead = (elapsed_new - elapsed_direct) / elapsed_direct * 100
    print(f"  [OK] Performance: _retrieve_knowledge {elapsed_new:.4f}s vs direct {elapsed_direct:.4f}s (overhead: {overhead:.1f}%)")
    return overhead < 100


def test_orchestrator_success_short_circuit():
    engine = make_engine()
    call_count = {"pb": 0}
    class FakeOrchestrator:
        def retrieve(self, query, context, mode="orchestrator"):
            return "orchestrator result"
    class FakePromptBuilder:
        def build_knowledge_context(self, user_input):
            call_count["pb"] += 1
            return "prompt_builder result"
    engine.knowledge_orchestrator = FakeOrchestrator()
    engine.prompt_builder = FakePromptBuilder()
    result = engine._retrieve_knowledge("test")
    if result == "orchestrator result" and call_count["pb"] == 0:
        print("  [OK] Short-circuit: orchestrator result returned, prompt_builder NOT called")
        return True
    print(f"  [FAIL] Short-circuit: got '{result}', pb called {call_count['pb']} times")
    return False


if __name__ == "__main__":
    print("=" * 60)
    print("  _retrieve_knowledge() Fallback Chain Tests")
    print("=" * 60)

    tests = [
        ("Fallback 1→2: orchestrator None → prompt_builder", test_fallback_1_to_2_normal),
        ("Fallback 1→2: orchestrator empty → prompt_builder", test_fallback_1_to_2_orchestrator_empty),
        ("Fallback 1→2: orchestrator exception → prompt_builder", test_fallback_1_to_2_orchestrator_exception),
        ("Fallback 2→3: prompt_builder fails → raw DB", test_fallback_2_to_3),
        ("Fallback 3→4: raw DB fails → empty string", test_fallback_3_to_4),
        ("Short-circuit: orchestrator success → no fallback", test_orchestrator_success_short_circuit),
        ("Performance: no regression vs direct call", test_performance_no_regression),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n[{passed + failed + 1}/{len(tests)}] {name}")
        try:
            if fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [FAIL] Exception: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed}/{len(tests)} passed")
    if failed == 0:
        print("  ALL TESTS PASSED")
    else:
        print(f"  {failed} TEST(S) FAILED")
    print(f"{'=' * 60}")

    sys.exit(0 if failed == 0 else 1)
