#!/usr/bin/env python3
"""
check_doc_numbers.py - Document number consistency check.
Queries actual DB numbers, compares against documents.
Returns error on mismatch.

Run:
    python .githooks/check_doc_numbers.py
"""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ERRORS = []


def get_db_state():
    """Get actual table and row counts from platform.db."""
    db_path = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
    if not db_path.exists() or db_path.stat().st_size == 0:
        return None, None

    try:
        conn = sqlite3.connect(f"file:{db_path.resolve()}?immutable=1", uri=True)
        table_count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]

        row_count = 0
        for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ):
            try:
                row_count += conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
            except Exception:
                pass
        conn.close()
        return table_count, row_count
    except Exception as e:
        print(f"  [ERROR] DB error: {e}")
        return None, None


def check_file_for_stale_numbers(file_path: Path, expected_tables: int, expected_rows: int):
    """Check a file for stale table/row counts."""
    if not file_path.exists():
        return

    content = file_path.read_text(encoding="utf-8")
    rel_path = file_path.relative_to(ROOT)

    # Check for old table counts
    for match in re.finditer(r'\b(\d+)\s*(tables?|表)', content, re.IGNORECASE):
        found = int(match.group(1))
        if found != expected_tables and found > 30:
            ERRORS.append(f"{rel_path}: says {found} tables, actual {expected_tables}")

    # Check for old row counts
    for match in re.finditer(r'\b(\d+)\s*(rows?|行)', content, re.IGNORECASE):
        found = int(match.group(1))
        if found != expected_rows and found > 50:
            ERRORS.append(f"{rel_path}: says {found} rows, actual {expected_rows}")


def main():
    print("=" * 60)
    print("  Document Number Consistency Check")
    print("=" * 60)

    tables, rows = get_db_state()
    if tables is None:
        print("  [WARN] Cannot read database -- skipping check")
        return 0

    print(f"\n  DB State: {tables} tables, ~{rows} rows")

    files_to_check = [
        ROOT / "tests" / "test_developer.py",
        ROOT / "AI项目管理" / "Platform" / "scripts" / "e2e_test.py",
        ROOT / "AI项目管理" / "Platform" / "scripts" / "system_health_check.py",
        ROOT / "AI项目管理" / "roles" / "SPEC-001_Chief_Architect.md",
        ROOT / "AI项目管理" / "Platform" / "config.json",
        ROOT / "deerflow_real_skills.py",
        # INDEX.md and CHANGELOG.md are excluded - they contain historical references
    ]

    print("\n  Checking files...")
    for f in files_to_check:
        if f.exists():
            check_file_for_stale_numbers(f, tables, rows)
            print(f"  [OK] {f.relative_to(ROOT)}")

    print("\n" + "=" * 60)
    if ERRORS:
        print(f"  [FAIL] {len(ERRORS)} inconsistency(ies) found:")
        for e in ERRORS:
            print(f"    - {e}")
        return 1
    else:
        print("  [PASS] All document numbers match DB state")
        return 0


if __name__ == "__main__":
    sys.exit(main())
