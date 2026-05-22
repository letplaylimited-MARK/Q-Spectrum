#!/usr/bin/env python3
"""Parameterized tests for QSpectrumEngine.__init__ (379-line God method)."""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QSPECTRUM_LLM", "mock")


class TestEngineInit(unittest.TestCase):

    CORE_ATTRS = ["db", "secretary", "knowledge", "prompt_builder", "protocol_bridge"]
    OPTIONAL_ATTRS = [
        "graph", "vector_store", "deerflow", "ghost_channel", "src_bridge",
        "skill_executor", "real_skills", "deerflow_real_skills", "closed_loop",
        "simulation_flywheel", "negotiation_engine", "ghost_gate",
        "resource_layer", "result_layer", "decision_layer",
        "project_memory", "chatroom_controller", "role_loader",
        "global_search", "contact_channel", "task_manager", "scenario_engine",
    ]

    def _assert_core_not_none(self, engine):
        for attr in self.CORE_ATTRS:
            with self.subTest(core_attr=attr):
                self.assertIsNotNone(
                    getattr(engine, attr, None),
                    f"Core attribute {attr} should not be None",
                )

    def _assert_optional_graceful(self, engine):
        for attr in self.OPTIONAL_ATTRS:
            with self.subTest(optional_attr=attr):
                val = getattr(engine, attr, None)
                self.assertIsNone(
                    val,
                    f"Optional attribute {attr} expected None but got {type(val).__name__}",
                )

    def _assert_session_state(self, engine):
        self.assertEqual(engine.interaction_count, 0)
        self.assertEqual(engine.conversation_history, [])
        self.assertIsNone(engine._last_role)

    def test_default_init(self):
        from qspectrum_engine import QSpectrumEngine
        engine = QSpectrumEngine()
        self._assert_core_not_none(engine)
        self._assert_session_state(engine)

    def test_with_mock_llm_tuple(self):
        from qspectrum_engine import MockLLMProvider, QSpectrumEngine
        mock_llm = MockLLMProvider()
        engine = QSpectrumEngine(llm_provider=(mock_llm, "mock-test"))
        self._assert_core_not_none(engine)
        self.assertEqual(engine.llm_name, "mock-test")

    def test_with_mock_llm_instance(self):
        from qspectrum_engine import MockLLMProvider, QSpectrumEngine
        mock_llm = MockLLMProvider()
        engine = QSpectrumEngine(llm_provider=mock_llm)
        self._assert_core_not_none(engine)
        self.assertIsNotNone(engine.llm)
        self.assertIsNotNone(engine.llm_name)

    def test_llm_fallback_mock(self):
        os.environ["QSPECTRUM_LLM"] = "mock"
        from qspectrum_engine import QSpectrumEngine
        engine = QSpectrumEngine()
        self.assertIsNotNone(engine.llm)
        self.assertIn("Mock", engine.llm_name)

    def test_no_exception_on_init(self):
        from qspectrum_engine import QSpectrumEngine
        try:
            QSpectrumEngine()
        except Exception as e:
            self.fail(f"QSpectrumEngine() raised {type(e).__name__}: {e}")


if __name__ == "__main__":
    unittest.main()
