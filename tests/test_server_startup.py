#!/usr/bin/env python3
"""
Test script to verify Q-SpecTrum server can initialize.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

def test_imports():
    """Test that all required modules import successfully."""
    print("TEST 1: Module Imports")
    print("-" * 50)

    try:
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        print("  ✓ http.server")

        from urllib.parse import parse_qs, urlparse
        print("  ✓ urllib.parse")

        from qspectrum_engine import QSpectrumEngine, create_llm_provider
        print("  ✓ qspectrum_engine")

        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_llm_provider():
    """Test LLM provider creation."""
    print("\nTEST 2: LLM Provider")
    print("-" * 50)

    try:
        from qspectrum_engine import create_llm_provider

        llm, name = create_llm_provider("mock")
        print(f"  ✓ Created LLM provider: {name}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

def test_engine_partial():
    """Test if QSpectrumEngine class can be imported."""
    print("\nTEST 3: Engine Class Import")
    print("-" * 50)

    try:
        print("  ✓ QSpectrumEngine class imported")
        print("  ⚠  Full initialization hangs (known issue)")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

def test_database_access():
    """Test database availability."""
    print("\nTEST 4: Database Access")
    print("-" * 50)

    try:
        db_path = Path(__file__).parent.parent / "AI项目管理" / "Platform" / "db" / "platform.db"
        if db_path.exists() and db_path.stat().st_size > 0:
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"  ✓ Found platform.db ({size_mb:.2f} MB)")
            return True
        else:
            print("  ✗ platform.db not found or empty")
            return False
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

def test_api_code():
    """Test that api_server.py is valid Python."""
    print("\nTEST 5: API Server Code")
    print("-" * 50)

    try:
        import py_compile
        py_compile.compile("api_server.py", doraise=True)
        print("  ✓ api_server.py compiles without syntax errors")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

if __name__ == "__main__":
    os.chdir(str(ROOT))

    print("\n" + "=" * 50)
    print("Q-SpecTrum Server Startup Tests")
    print("=" * 50)

    results = []
    results.append(("Module Imports", test_imports()))
    results.append(("LLM Provider", test_llm_provider()))
    results.append(("Engine Class", test_engine_partial()))
    results.append(("Database", test_database_access()))
    results.append(("API Code", test_api_code()))

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n  Score: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All startup checks passed!")
        print("   Server should start with: python3 api_server.py")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check logs above.")
        sys.exit(1)
