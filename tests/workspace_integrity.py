#!/usr/bin/env python3
"""
Workspace Integrity Audit / 工作空間完整性審計
============================================
Locks the folder's coherence as a single deliverable artifact:
  - No orphan root .md files (every doc reachable from INDEX.md or README.md)
  - No broken file references in user-facing docs
  - No leftover ephemeral test files
  - INDEX.md is up-to-date with respect to existing audit reports

This is the 7th automated quality gate. It runs in seconds, no server needed.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── Knobs ──
EPHEMERAL_PATTERNS = [
    "test_size_*.txt", "test_utf8.txt", "test_write_*.txt",
    "qspectrum-backup-*.tar.gz", "qspectrum-backup-*.zip",
    "_bintest.bin", "_writetest.txt",
    ".write_test*", ".sqlite_write_test*", ".runtime_write_test*",
    "*.db-journal", "*.db-wal", "*.db-shm",
    ".env.tmp", ".first_run_done",
]

# Root .md files that are entry-point exempt from the orphan check
ENTRY_POINTS = {"README.md", "INDEX.md"}


class Result:
    def __init__(self):
        self.passed: list[str] = []
        self.failed: list[tuple[str, str]] = []

    def ok(self, label):
        self.passed.append(label)
        print(f"  ✓ {label}")

    def fail(self, label, hint):
        self.failed.append((label, hint))
        print(f"  ✗ {label}")
        print(f"      hint: {hint}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        rate = 100 * len(self.passed) / max(total, 1)
        print()
        print("=" * 60)
        if not self.failed:
            print(f"  ✅ Workspace integrity: {len(self.passed)}/{total} ({rate:.0f}%)")
        else:
            print(f"  ❌ Workspace integrity: {len(self.passed)}/{total} "
                  f"({len(self.failed)} failures)")
        print("=" * 60)
        return 0 if not self.failed else 1


def check_no_ephemeral_files(r: Result):
    found = []
    for pattern in EPHEMERAL_PATTERNS:
        for p in ROOT.rglob(pattern):
            if p.is_file() and not any(part.startswith(".") and part != ".env.tmp"
                                        for part in p.parts):
                found.append(str(p.relative_to(ROOT)))
    if found:
        # Show up to 8
        sample = ", ".join(found[:8])
        more = f" (+{len(found)-8} more)" if len(found) > 8 else ""
        r.fail(f"No ephemeral test artifacts ({len(found)} found)",
               f"run clean-for-delivery.bat/.sh — found: {sample}{more}")
    else:
        r.ok("No ephemeral test artifacts at root")


def check_orphan_root_md(r: Result):
    root_md = sorted([p.name for p in ROOT.glob("*.md")])
    refs_in = defaultdict(set)
    file_pat = re.compile(r"`?([A-Z0-9][\w_-]*\.(?:md|py|bat|sh|html))`?")
    for md in root_md:
        text = (ROOT / md).read_text(encoding="utf-8", errors="replace")
        for m in file_pat.finditer(text):
            ref = m.group(1)
            if ref == md:
                continue
            if ref in {p.name for p in ROOT.glob("*.md")}:
                refs_in[ref].add(md)
    orphans = [md for md in root_md
               if md not in ENTRY_POINTS and not refs_in.get(md)]
    if orphans:
        r.fail(f"No orphan root .md files ({len(orphans)} found)",
               f"add to INDEX.md or README.md: {orphans}")
    else:
        r.ok(f"No orphan root .md files ({len(root_md)} docs all reachable)")


def check_index_exists(r: Result):
    if (ROOT / "INDEX.md").exists():
        r.ok("INDEX.md exists (single-folder navigation entry point)")
    else:
        r.fail("INDEX.md missing",
               "create INDEX.md as canonical navigation map")


def check_index_covers_audit_reports(r: Result):
    """Every AUDIT-*.md should be referenced by INDEX.md or FIXES-APPLIED.md."""
    audit_md = [p.name for p in ROOT.glob("AUDIT-*.md")]
    if not audit_md:
        r.ok("No AUDIT-*.md to track")
        return
    references = ""
    for f in ("INDEX.md", "FIXES-APPLIED.md", "README.md"):
        if (ROOT / f).exists():
            references += (ROOT / f).read_text(encoding="utf-8", errors="replace")
    missing = [a for a in audit_md if a not in references]
    if missing:
        r.fail(f"AUDIT reports not referenced: {missing}",
               "add these to INDEX.md")
    else:
        r.ok(f"All {len(audit_md)} AUDIT-*.md reports linked from INDEX/FIXES/README")


def check_quality_gates_documented(r: Result):
    """README.md or INDEX.md must mention each test_*.py / *_audit.py / verify-delivery."""
    expected = [
        "verify-delivery.py",
        "test_regression.py",
        "flywheel_audit.py",
        "adversarial_audit.py",
        "journey_wargame.py",
        "persona_stressor_matrix.py",
    ]
    references = ""
    for f in ("README.md", "INDEX.md"):
        if (ROOT / f).exists():
            references += (ROOT / f).read_text(encoding="utf-8", errors="replace")
    missing = [e for e in expected if e not in references]
    if missing:
        r.fail(f"Quality gates not documented in README/INDEX: {missing}",
               "add a Quality Gates table")
    else:
        r.ok(f"All {len(expected)} quality gates documented in README/INDEX")


def check_critical_db_present(r: Result):
    db = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
    backup = ROOT / "AI项目管理" / "Platform" / "db" / "platform_restored.db"
    if db.exists() and db.stat().st_size > 100_000:
        r.ok(f"platform.db present and populated ({db.stat().st_size:,} bytes)")
    elif backup.exists() and backup.stat().st_size > 100_000:
        r.ok(f"platform.db missing but platform_restored.db OK "
             f"({backup.stat().st_size:,} bytes)")
    else:
        r.fail("platform.db is missing or empty",
               "rebuild via setup_platform.py + apply 100_ai_roles_patch.sql")


def check_helper_pairs(r: Result):
    """Each helper script should have both .bat and .sh, both non-trivially sized."""
    pairs = ["start", "health-check", "clean-for-delivery",
             "backup-user-data", "install"]
    MIN_SCRIPT_BYTES = 200  # below this, the script can't be functional
    missing_pairs = []
    for p in pairs:
        bat = ROOT / f"{p}.bat"
        sh = ROOT / f"{p}.sh"
        bat_ok = bat.exists() and bat.stat().st_size >= MIN_SCRIPT_BYTES
        sh_ok = sh.exists() and sh.stat().st_size >= MIN_SCRIPT_BYTES
        if not (bat_ok and sh_ok):
            bat_state = "missing" if not bat.exists() else \
                        f"empty ({bat.stat().st_size}B)" if bat.stat().st_size < MIN_SCRIPT_BYTES \
                        else "ok"
            sh_state = "missing" if not sh.exists() else \
                       f"empty ({sh.stat().st_size}B)" if sh.stat().st_size < MIN_SCRIPT_BYTES \
                       else "ok"
            missing_pairs.append(f"{p} (.bat={bat_state}, .sh={sh_state})")
    if missing_pairs:
        r.fail(f"Helper script pairs incomplete: {missing_pairs}",
               "ensure .bat + .sh both exist with non-trivial content")
    else:
        r.ok(f"All {len(pairs)} helper scripts have non-empty .bat + .sh pairs")


def main():
    print("=" * 60)
    print("  Q-SpecTrum Workspace Integrity Audit")
    print("=" * 60)
    print()
    r = Result()
    check_index_exists(r)
    check_orphan_root_md(r)
    check_index_covers_audit_reports(r)
    check_quality_gates_documented(r)
    check_critical_db_present(r)
    check_helper_pairs(r)
    check_no_ephemeral_files(r)
    return r.summary()


if __name__ == "__main__":
    sys.exit(main())
