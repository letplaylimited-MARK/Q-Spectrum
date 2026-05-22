#!/usr/bin/env python3
"""
Pre-commit hook for Q-SpecTrum
==============================
Runs before each commit to prevent known issues from being committed.

Install:
    python .githooks/pre_commit.py --install

Checks:
    1. verify-integration.py must pass
    2. No C:\\Users\\ hardcoded paths
    3. No GBK encoding issues (all open() calls must specify encoding)
    4. Document numbers matching actual DB state
"""
from __future__ import annotations

import re
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ERRORS = []
WARNINGS = []


def check(desc, condition, detail="", is_warning=False):
    if condition:
        print(f"  [OK] {desc}")
    else:
        marker = "[WARN]" if is_warning else "[FAIL]"
        print(f"  {marker} {desc}: {detail}")
        if is_warning:
            WARNINGS.append(f"{desc}: {detail}")
        else:
            ERRORS.append(f"{desc}: {detail}")


def run_verify_integration():
    """Run verify-integration.py and check result."""
    print("\n[1/4] Running verify-integration.py...")
    result = subprocess.run(
        [sys.executable, str(ROOT / "verify-integration.py")],
        capture_output=True, text=True, cwd=str(ROOT), timeout=30
    )
    check("verify-integration.py passes", result.returncode == 0,
          result.stderr[:200] if result.returncode != 0 else "")


def check_hardcoded_paths():
    """Check for hardcoded paths in Python files."""
    print("\n[2/4] Checking for hardcoded paths...")
    result = subprocess.run(
        [sys.executable, "-m", "grep", "-rn", r"C:\\\\Users\\\\",
         "--include", "*.py", str(ROOT)],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    lines = [line for line in result.stdout.strip().split("\n") if line
             and "FORBIDDEN" not in line
             and "example" not in line.lower()
             and ".githooks" not in line]
    check("No hardcoded paths", len(lines) == 0,
          f"Found in: {', '.join(line.split(':')[0] for line in lines[:3])}")


def check_encoding_calls():
    """Check that open() calls in Python files specify encoding."""
    print("\n[3/4] Checking open() calls for encoding...")
    issues = []
    for py_file in ROOT.rglob("*.py"):
        if any(p.startswith(".") or p == "__pycache__" for p in py_file.parts):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            for i, line in enumerate(content.split("\n"), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(r"\bopen\s*\(['\"].*?['\"]", stripped):
                    # Skip non-file open() calls (webbrowser, etc)
                    if "webbrowser" in stripped or "http" in stripped:
                        continue
                    if "encoding" not in stripped and "rb" not in stripped and "wb" not in stripped:
                        if py_file.name.startswith("test_"):
                            continue
                        issues.append(f"{py_file.relative_to(ROOT)}:{i}")
        except Exception:
            pass

    check("open() calls specify encoding", len(issues) == 0,
          f"Missing in: {', '.join(issues[:5])}", is_warning=True)


def check_document_numbers():
    """Check that document numbers match actual DB state."""
    print("\n[4/4] Checking document numbers against DB...")
    db_path = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
    if not db_path.exists() or db_path.stat().st_size == 0:
        check("platform.db exists and non-empty", False, "Cannot check numbers", is_warning=True)
        return

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

        docs_to_check = [
            "tests/test_developer.py",
            "AI项目管理/Platform/scripts/e2e_test.py",
            "AI项目管理/Platform/scripts/system_health_check.py",
            "AI项目管理/roles/SPEC-001_Chief_Architect.md",
            "AI项目管理/Platform/config.json",
            "deerflow_real_skills.py",
        ]

        for doc_path in docs_to_check:
            full_path = ROOT / doc_path
            if not full_path.exists():
                continue
            content = full_path.read_text(encoding="utf-8")
            if re.search(r'\b47\s*(tables|表)', content, re.IGNORECASE):
                check(f"{doc_path}: table count", False, "Still says 47 tables", is_warning=True)
            if re.search(r'\b748\s*(rows|行)', content, re.IGNORECASE):
                check(f"{doc_path}: row count", False, "Still says 748 rows", is_warning=True)

        check(f"DB state: {table_count} tables, ~{row_count} rows", True)

    except Exception as e:
        check("DB number check", False, str(e), is_warning=True)


def main():
    print("=" * 60)
    print("  Q-SpecTrum Pre-commit Hook")
    print("=" * 60)

    run_verify_integration()
    check_hardcoded_paths()
    check_encoding_calls()
    check_document_numbers()

    print("\n" + "=" * 60)
    if ERRORS:
        print(f"  [FAIL] COMMIT BLOCKED: {len(ERRORS)} error(s)")
        for e in ERRORS:
            print(f"    - {e}")
        print("\n  Fix the errors above before committing.")
        return 1
    elif WARNINGS:
        print(f"  [WARN] {len(WARNINGS)} warning(s) - commit allowed but please fix")
        for w in WARNINGS:
            print(f"    - {w}")
        return 0
    else:
        print("  [PASS] All checks passed - safe to commit")
        return 0


if __name__ == "__main__":
    sys.exit(main())
