#!/usr/bin/env python3
"""
End-to-end verification of Q-SpecTrum engine + MCP server.
Tests the complete chain: import → DB → MCP protocol → tool execution.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding='utf-8')

errors = []
def check(desc, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {desc}")
    if not ok:
        errors.append(f"{desc}: {detail}")

print("=" * 60)
print("  Q-SpecTrum End-to-End Verification")
print("=" * 60)

# ─── Step 1: Engine Import ────────────────────────────────
print("\n[1/9] Engine Import")
try:
    from qspectrum_engine import MockLLMProvider, QSpectrumDB, QSpectrumEngine
    check("Import qspectrum_engine", True)
except Exception as e:
    check("Import qspectrum_engine", False, str(e))

# ─── Step 2: Knowledge Graph ────────────────────────────
print("\n[2/9] Knowledge Graph Import")
try:
    from knowledge_graph import ALL_OPS, EDGE_LABELS
    check("Import knowledge_graph", True)
    check(f"Operators defined: {len(ALL_OPS)}", len(ALL_OPS) == 21)
    check(f"Edge labels defined: {len(EDGE_LABELS)}", len(EDGE_LABELS) == 19)
except Exception as e:
    check("Import knowledge_graph", False, str(e))

# ─── Step 3: Database Connection ──────────────────────────
print("\n[3/9] Database Connection")
try:
    db_path = ROOT / "AI项目管理/Platform/db/platform.db"
    check(f"platform.db exists ({db_path.stat().st_size} bytes)", db_path.exists() and db_path.stat().st_size > 0)
    db = QSpectrumDB(str(db_path))
    roles = db.get_all_roles()
    check(f"DB connection + roles loaded ({len(roles)})", len(roles) == 15)
except Exception as e:
    check("DB connection", False, str(e))

# ─── Step 4: Engine Initialization ────────────────────────
print("\n[4/9] Engine Initialization")
try:
    llm = MockLLMProvider()
    engine = QSpectrumEngine(llm_provider=llm)
    check(f"Engine init ({type(engine).__name__})", True)
except Exception as e:
    check("Engine init", False, str(e))

# ─── Step 5: System Status ────────────────────────────────
print("\n[5/9] System Status")
try:
    status = engine.get_system_status()
    check(f"Status engine: {status.get('engine', '?')}", True)
    check(f"Roles loaded: {status.get('roles_loaded', 0)}", status.get('roles_loaded', 0) > 0)
except Exception as e:
    check("System status", False, str(e))

# ─── Step 6: Role Queries ─────────────────────────────────
print("\n[6/9] Role Queries")
try:
    trum = engine.db.get_roles_by_family('trum') if hasattr(engine, 'db') and engine.db else []
    spec = engine.db.get_roles_by_family('spec') if hasattr(engine, 'db') and engine.db else []
    qcm = engine.db.get_roles_by_family('qcm') if hasattr(engine, 'db') and engine.db else []
    check(f"TRUM roles: {len(trum) if trum else 0}", len(trum) == 4)
    check(f"SPEC roles: {len(spec) if spec else 0}", len(spec) == 3)
    check(f"QCM roles: {len(qcm) if qcm else 0}", len(qcm) == 8)
except Exception as e:
    check("Role queries", False, str(e))

# ─── Step 7: MCP Server Protocol ──────────────────────────
print("\n[7/9] MCP Server Protocol (stdio simulation)")
try:
    from brain_core.mcp_router import _TOOL_DEFS as TOOLS
    from brain_core.mcp_router import McpRouter
    from qspectrum_engine import MockLLMProvider, QSpectrumEngine
    _test_engine = QSpectrumEngine(llm_provider=MockLLMProvider())
    _test_router = McpRouter(_test_engine, "mock")

    # Test tools/list
    tool_names = [t["name"] for t in TOOLS]
    check(f"MCP tools defined: {len(TOOLS)} ({', '.join(tool_names)})", len(TOOLS) >= 5)

    # Test each tool via McpRouter.call_tool
    default_args = {
        "get_role": {"role_code": "ROLE-T01"},
        "execute_chat": {"message": "hello"},
        "get_history": {"limit": 1},
        "query_knowledge": {"query": "test"},
        "query_database": {"sql": "SELECT count(*) FROM ai_roles"},
        "graph_stats": {},
        "graph_query": {"op_code": "P01"},
        "graph_trace": {"node_id": "op_P01"},
        "graph_path": {"source": "op_P01", "target": "op_E01"},
        "graph_connect": {"source": "op_P01", "target": "op_D01", "label": "SEQ"},
        "vector_search": {"query": "MCP tools"},
        "vector_stats": {},
        "search_all": {"query": "MCP tools"},
        "knowledge_stats": {},
        "get_workflows": {},
    }
    for name in tool_names:
        args = default_args.get(name, {})
        try:
            result = _test_router.call_tool(name, args)
            check(f"MCP tool '{name}' responds", result is not None)
        except Exception as e:
            check(f"MCP tool '{name}' responds", False, str(e))
except Exception as e:
    check("MCP server", False, str(e))

# ─── Step 8: File Infrastructure ──────────────────────────
print("\n[8/9] File Infrastructure")
paths = [
    ("智腦協議", ROOT / "智腦協議-BRAIN-PROTOCOL.md"),
    ("AGENTS.md", ROOT / "AGENTS.md"),
    ("verify脚本", ROOT / "verify-integration.py"),
    ("MCP Server", ROOT / "qspectrum_mcp_server.py"),
    ("AI引擎", ROOT / "qspectrum_engine.py"),
    ("API Server", ROOT / "api_server.py"),
    ("opencode/agents", ROOT / ".opencode/agents"),
    ("opencode/skills", ROOT / ".opencode/skills"),
    ("opencode/tools", ROOT / ".opencode/tools"),
    ("BRAIN-KB", ROOT / "BRAIN-KB"),
    ("Knowledge Graph", ROOT / "knowledge_graph.py"),
    ("KG Test", ROOT / "test_knowledge_graph.py"),
    ("Vector Store", ROOT / "vector_store.py"),
    ("VS Test", ROOT / "test_vector_store.py"),
]
for label, p in paths:
    exists = p.exists()
    check(f"{label}: {'exists' if exists else 'MISSING'}", exists)

# ─── Step 9: Memory System ────────────────────────────────
print("\n[9/9] Memory System")
handoff = ROOT / "_HANDOFF"
for fname in ["STATUS.md", "CRITICAL-REMINDERS.md", "MEMORY-INDEX.md"]:
    f = handoff / fname
    check(f"_HANDOFF/{fname}: {'exists' if f.exists() else 'MISSING'}", f.exists())

# ─── Summary ──────────────────────────────────────────────
print("\n" + "=" * 60)
if errors:
    print(f"  FAILED: {len(errors)} check(s) failed")
    for e in errors:
        print(f"    - {e}")
    sys.exit(1)
else:
    print("  ALL CHECKS PASSED — System is operational")
    print("=" * 60)
