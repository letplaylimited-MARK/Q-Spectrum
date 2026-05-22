"""Pytest fixtures shared across all test modules."""
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path for regression tests
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def r():
    """Results harness for regression tests (test_regression.py)."""
    class Results:
        def __init__(self):
            self.passed = 0
            self.failed = 0
            self.failures = []

        def check(self, name, cond, detail=""):
            if cond:
                self.passed += 1
                print(f"  ✓ {name}")
            else:
                self.failed += 1
                self.failures.append((name, detail))
                print(f"  ✗ {name}  — {detail}")

        def summary(self):
            total = self.passed + self.failed
            rate = 100 * self.passed / max(total, 1)
            print(f"\n  Regression Summary: {self.passed}/{total} passed ({rate:.0f}%)")
            if self.failed:
                print("\n  Failures:")
                for name, detail in self.failures:
                    print(f"    • {name}: {detail}")
            return self.failed == 0

    return Results()


@pytest.fixture
def mock_llm():
    """Mock LLM provider with predictable responses."""
    class MockLLM:
        def generate(self, system_prompt, user_message, **kwargs):
            return f"[Mock Response] 针对：{user_message[:50]}..."

        def get_provider_name(self):
            return "mock"

    return MockLLM()


@pytest.fixture
def test_engine(mock_llm):
    """Create a test engine with all components."""
    from qspectrum_engine import QSpectrumEngine
    engine = QSpectrumEngine(llm_provider=mock_llm)
    try:
        yield engine
    finally:
        engine.close()


@pytest.fixture
def minimal_engine(mock_llm):
    """Create a minimal engine (core only, optional components disabled)."""
    from qspectrum_engine import QSpectrumEngine
    # Create engine but disable optional components for degradation tests
    engine = QSpectrumEngine(llm_provider=mock_llm)
    # Simulate missing components
    assert hasattr(engine, "knowledge_orchestrator"), "Engine API changed"
    engine.knowledge_orchestrator = None
    engine.peer_collaboration = None
    engine.knowledge_crystallizer = None
    try:
        yield engine
    finally:
        engine.close()
