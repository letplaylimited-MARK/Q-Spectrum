"""
Q-SpecTrum End-to-End Test Suite v1.0
=====================================
Validates DB integrity, Schema SQL, Workflow Engine,
Protocol Executor, and PathGuard in one run.

Usage:
    python e2e_test.py                    # Run all tests
    python e2e_test.py --db path/to/db    # Use custom DB path
"""

import sqlite3
import sys
from pathlib import Path

# ─── Setup ───
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# Resolve DB path: CLI flag > PathGuard > hardcoded fallback
if "--db" in sys.argv:
    idx = sys.argv.index("--db")
    if idx + 1 < len(sys.argv):
        DB_PATH = Path(sys.argv[idx + 1])
else:
    try:
        from path_utils import get_db_path
        DB_PATH = Path(get_db_path())
    except Exception:
        DB_PATH = SCRIPT_DIR.parent / "db" / "platform.db"

passed = 0
failed = 0
results = []


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        results.append(f"  PASS  {name}")
    else:
        failed += 1
        results.append(f"  FAIL  {name} -- {detail}")


def run_tests():
    global passed, failed

    print("=" * 60)
    print("Q-SpecTrum E2E Test Suite v1.0")
    print(f"DB: {DB_PATH}")
    print("=" * 60)

    # Use immutable mode to avoid virtiofs journal file issues
    db_uri = f"file:{DB_PATH.resolve()}?immutable=1"
    conn = sqlite3.connect(db_uri, uri=True)
    conn.row_factory = sqlite3.Row

    # ─── 1. DB Integrity ───
    print("\n[1] Database Integrity")
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    test("40 tables exist", len(tables) == 40, f"found {len(tables)}")

    total_rows = sum(
        conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        for t in tables
    )
    test("500+ rows total", total_rows >= 500, f"found {total_rows}")

    empty = [t for t in tables
             if conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0] == 0]
    test("0 empty tables", len(empty) == 0, f"empty: {empty}")

    # Old path check
    old_paths = 0
    for t in tables:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info([{t}])").fetchall()]
        for col in cols:
            try:
                c = conn.execute(
                    f"SELECT COUNT(*) FROM [{t}] WHERE [{col}] LIKE '%Users%z%Desktop%'"
                ).fetchone()[0]
                old_paths += c
            except Exception:
                pass
    test("0 old paths", old_paths == 0, f"found {old_paths}")

    # ─── 2. Key Data ───
    print("\n[2] Key Data Verification")
    checks = [
        ("ai_roles", 15, "AI roles"),
        ("collaboration_protocols", 10, "protocols"),
        ("workflow_definitions", 4, "workflows"),
        ("workflow_phases", 20, "phases"),
        ("workflow_tasks", 40, "tasks"),
        ("workflow_steps", 84, "steps"),
        ("agents", 7, "agents"),
    ]
    for table, expected, label in checks:
        actual = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
        test(f"{expected} {label}", actual == expected, f"found {actual}")

    # ─── 3. Schema SQL ───
    print("\n[3] Schema SQL Validation")
    schema_dir = SCRIPT_DIR.parent / "db" / "schema"
    if schema_dir.exists():
        bad_syntax = ['ENGINE=InnoDB', 'utf8mb4', 'ON UPDATE CURRENT_TIMESTAMP', 'UUID()']
        schema_clean = True
        for sf in sorted(schema_dir.glob("*.sql")):
            content = sf.read_text()
            for bad in bad_syntax:
                if bad in content:
                    test(f"{sf.name} no MySQL syntax", False, f"contains {bad}")
                    schema_clean = False
                    break
        if schema_clean:
            test("All schema files use SQLite syntax", True)
    else:
        test("Schema directory exists", False, str(schema_dir))

    # ─── 4. Workflow Engine ───
    print("\n[4] Workflow Engine")
    try:
        from workflow_engine import WorkflowEngine
        engine = WorkflowEngine(str(DB_PATH))
        wfs = engine.list_workflows()
        test("list_workflows returns 4", len(wfs) == 4, f"got {len(wfs)}")

        for wf_code in ['WF-0001', 'WF-0002', 'WF-0003', 'WF-0004']:
            pts = engine.get_full_pts(wf_code)
            step_count = sum(
                len(s.get("steps", []))
                for p in pts["phases"]
                for s in p["tasks"]
            ) if pts else 0
            test(f"{wf_code} loads ({step_count} steps)", step_count > 0)

        result = engine.run_workflow('WF-0001', dry_run=True)
        test("WF-0001 dry-run", result.get("status") == "preview")
        engine.close()
    except Exception as e:
        test("Workflow Engine import", False, str(e))

    # ─── 5. Protocol Executor ───
    print("\n[5] Protocol Executor")
    try:
        from protocol_executor import ProtocolExecutor
        executor = ProtocolExecutor(str(DB_PATH))
        protos = executor.list_protocols()
        test("list_protocols returns 10", len(protos) == 10, f"got {len(protos)}")

        result = executor.trigger_protocol('PROTO-001')
        test("PROTO-001 triggers", result.get("status") == "completed")

        comm_map = executor.get_role_communication_map()
        test("Communication map populated", len(comm_map) > 0)
        executor.close()
    except Exception as e:
        test("Protocol Executor import", False, str(e))

    # ─── 6. PathGuard ───
    print("\n[6] PathGuard v3.0")
    try:
        from path_utils import is_forbidden_path
        # Test with portable path strings (platform-agnostic)
        old_test_path = str(Path("/Users/z/Desktop/Q-SpecTrum/test.txt"))
        new_test_path = str(SCRIPT_DIR.parent.parent / "test.txt")
        test("Blocks old path", is_forbidden_path(old_test_path))
        test("Allows new path", not is_forbidden_path(new_test_path))
    except Exception as e:
        test("PathGuard import", False, str(e))

    conn.close()

    # ─── Summary ───
    print("\n" + "=" * 60)
    for r in results:
        print(r)
    print("=" * 60)
    status = "ALL PASSED" if failed == 0 else f"{failed} FAILED"
    print(f"\n{status}: {passed} passed, {failed} failed, {passed + failed} total")
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(run_tests())
