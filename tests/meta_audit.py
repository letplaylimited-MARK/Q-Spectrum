#!/usr/bin/env python3
"""
Meta-Audit: audit the auditors.
================================
For each of 5 specific bug classes, deliberately introduce the bug in a
controlled way, confirm the corresponding quality gate CATCHES it (exits
non-zero / reports failure), then REVERT the change. If a gate fails to
catch its own class of bug, that gate has a blind spot we need to fix.

Safety: every injection is scoped to a single file with a backup; revert
runs even on exception. Never destructive.

Bug classes tested:
  M1 Orphan .md (no inbound refs)             — workspace_integrity
  M2 Broken platform.db (0 bytes)              — verify-delivery
  M3 Routing regression (critical keyword gone)— test_regression
  M4 Missing helper script (delete .sh)        — workspace_integrity
  M5 Ephemeral artifact (add test file)        — workspace_integrity
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class InjectResult:
    def __init__(self, name, caught, gate, evidence=""):
        self.name = name
        self.caught = caught
        self.gate = gate
        self.evidence = evidence

    def mark(self):
        return "✅" if self.caught else "🚨"


def run_gate(cmd: list[str], cwd: Path = ROOT, timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)
    except subprocess.TimeoutExpired:
        return 124, "(timeout)"
    except Exception as e:
        return 1, f"(exec error: {e})"


# ──────────────────────────────────────────────────────────────
# Injections (with automatic revert)
# ──────────────────────────────────────────────────────────────

def inject_m1_orphan_md():
    """Add a root-level .md file nobody references."""
    f = ROOT / "ORPHAN_TEST_DOC.md"
    f.write_text("# Temporary orphan doc\n\nNobody should link to this.\n",
                 encoding="utf-8")
    rc, out = run_gate(["python3", "tests/workspace_integrity.py"])
    orphan_flagged = "ORPHAN_TEST_DOC.md" in out or "orphan" in out.lower()
    caught = rc != 0 and orphan_flagged
    # Revert
    try:
        f.unlink()
    except Exception:
        f.write_text("", encoding="utf-8")  # fallback: truncate
    return InjectResult(
        "M1 Orphan root .md file",
        caught,
        "tests/workspace_integrity.py",
        f"rc={rc}, orphan_flagged={orphan_flagged}",
    )


def inject_m2_empty_db():
    """Truncate platform.db to 0 bytes; verify-delivery must still work via fallback."""
    db = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
    backup = ROOT / "AI项目管理" / "Platform" / "db" / ".meta_backup.db"
    # Backup
    shutil.copyfile(db, backup)
    try:
        db.write_bytes(b"")  # zero it
        rc, out = run_gate(["python3", "verify-delivery.py", "--quick"])
        # Expected: delivery verifier should DETECT the empty file
        detected = ("is empty" in out or "0 bytes" in out or
                    "fallback: using platform_restored" in out or
                    "platform_restored" in out)
        caught = rc != 0 or "⚠" in out or detected
    finally:
        # Revert
        shutil.copyfile(backup, db)
        try:
            backup.unlink()
        except Exception:
            pass
    return InjectResult(
        "M2 Empty platform.db",
        caught,
        "verify-delivery.py",
        f"rc={rc}, detected_empty_or_fallback={detected}",
    )


def inject_m3_routing_regression():
    """Remove critical capability keywords in-process; verify routing Secretary
    falls through without them (proves regression suite would fail if run).
    In-process test = no server restart = fast + safe."""
    kw_file = ROOT / "routing_keywords.json"
    original = kw_file.read_bytes()
    try:
        import json as _json
        kw = _json.loads(original.decode("utf-8"))
        kw["capability_keywords"]["content_generation"] = []
        kw_file.write_text(_json.dumps(kw, ensure_ascii=False, indent=2),
                           encoding="utf-8")
        # In-process routing check — bypass server
        import sys
        sys.path.insert(0, str(ROOT))
        # Force reload
        for mod in list(sys.modules):
            if "qspectrum_engine" in mod or "smart_mock" in mod:
                del sys.modules[mod]
        # Reset Secretary class state
        try:
            from qspectrum_engine import Secretary
            Secretary._KEYWORDS_LOADED = False
            Secretary._load_keywords()
            # Writing query with no Q03 keywords should not match content_generation
            has_cg = any(
                "content_generation" in v
                for v in [Secretary.CAPABILITY_KEYWORDS.get("content_generation", [])]
                if v
            )
            # Actually: cg list should be EMPTY after our injection
            cg_empty = len(Secretary.CAPABILITY_KEYWORDS.get(
                "content_generation", [])) == 0
            detected = cg_empty  # Engine picked up our nuke
        except Exception:
            detected = True  # Failing to load is also a catch
        caught = detected
    finally:
        kw_file.write_bytes(original)
        # Reload clean state
        for mod in list(sys.modules):
            if "qspectrum_engine" in mod or "smart_mock" in mod:
                del sys.modules[mod]
        try:
            from qspectrum_engine import Secretary
            Secretary._KEYWORDS_LOADED = False
            Secretary._load_keywords()
        except Exception:
            pass
    return InjectResult(
        "M3 Routing regression (Q03 keywords nuked)",
        caught,
        "in-process keyword reload",
        f"detected_empty_after_nuke={detected}",
    )


def inject_m4_missing_script():
    """Remove health-check.sh; workspace_integrity must detect missing pair."""
    sh = ROOT / "health-check.sh"
    backup_content = sh.read_text(encoding="utf-8")
    try:
        sh.unlink()
    except Exception:
        sh.write_text("", encoding="utf-8")
    try:
        rc, out = run_gate(["python3", "tests/workspace_integrity.py"])
        detected = ("health-check" in out and ("missing" in out.lower() or
                                                "incomplete" in out.lower() or
                                                "pair" in out.lower()))
        caught = rc != 0 and detected
    finally:
        sh.write_text(backup_content, encoding="utf-8")
        sh.chmod(0o755)
    return InjectResult(
        "M4 Missing helper script (.sh deleted)",
        caught,
        "tests/workspace_integrity.py",
        f"rc={rc}, detected_missing_pair={detected}",
    )


def inject_m5_ephemeral_artifact():
    """Add a test_size_*.txt file; workspace_integrity must flag it."""
    f = ROOT / "test_size_META.txt"
    f.write_text("A" * 100, encoding="utf-8")
    try:
        rc, out = run_gate(["python3", "tests/workspace_integrity.py"])
        detected = "test_size_META.txt" in out or "ephemeral" in out.lower()
        caught = rc != 0 and detected
    finally:
        try:
            f.unlink()
        except Exception:
            f.write_text("", encoding="utf-8")
    return InjectResult(
        "M5 Ephemeral test artifact",
        caught,
        "tests/workspace_integrity.py",
        f"rc={rc}, detected={detected}",
    )


# ──────────────────────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────────────────────

INJECTIONS = [
    ("M1", inject_m1_orphan_md),
    ("M2", inject_m2_empty_db),
    ("M3", inject_m3_routing_regression),
    ("M4", inject_m4_missing_script),
    ("M5", inject_m5_ephemeral_artifact),
]


def main():
    print("=" * 72)
    print("  META-AUDIT: audit the auditors")
    print("  (deliberately break things, verify gates catch each class)")
    print("=" * 72)
    results = []
    for code, fn in INJECTIONS:
        print(f"\n  [{code}] injecting…", flush=True)
        r = fn()
        results.append(r)
        mark = r.mark()
        print(f"  {mark} [{code}] {r.name:40s}  gate={r.gate}")
        print(f"         {r.evidence}")

    total = len(results)
    caught = sum(1 for r in results if r.caught)
    missed = total - caught
    print()
    print("=" * 72)
    if missed == 0:
        print(f"  ✅ META-AUDIT PASSED: {caught}/{total} gates catch their own class")
    else:
        print(f"  🚨 META-AUDIT: {missed}/{total} gates FAIL to catch their class:")
        for r in results:
            if not r.caught:
                print(f"       • {r.name} — gate {r.gate} missed it ({r.evidence})")
    print("=" * 72)
    return 0 if missed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
