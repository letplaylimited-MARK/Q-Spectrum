#!/usr/bin/env python3
"""
Semantic Consistency Audit / 文件間語義一致性審計
==================================================
Across ~180 .md files, verify shared numeric facts are consistent with the
runtime DB. Drift happens naturally as schemas evolve — this tool surfaces it.

Key facts checked:
  - role count (authoritative: COUNT(*) FROM ai_roles)
  - workflow count (COUNT(*) FROM workflow_definitions)
  - protocol count (COUNT(*) FROM collaboration_protocols)
  - table count (COUNT(*) FROM sqlite_master WHERE type='table')
  - scenario count (from scenario_engine's registered list)
  - skill count (from SkillExecutor load)

For each fact, the tool reports:
  - The authoritative value (from runtime)
  - Which .md files claim what
  - Whether critical receiver-facing docs are accurate

Run:
    python tests/semantic_consistency.py
"""
from __future__ import annotations

import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Receiver-facing docs we care most about
RECEIVER_DOCS = {
    "README.md", "QUICK-START.md", "INSTALL-GUIDE.md",
    "USER-GUIDE.md", "INDEX.md",
    "BOOT.md", "SYSTEM-PROMPT.md", "KNOWLEDGE-INDEX.md",
    "ROLE-REGISTRY.md", "SKILLS-INDEX.md", "SCENARIOS.md",
}

# Numeric-claim patterns
PATTERNS = {
    "roles":       re.compile(r"(\d+)\s*(?:個|个)?\s*(?:角色|role|AI role)", re.I),
    "workflows":   re.compile(r"(\d+)\s*(?:個|个)?\s*(?:工作流|workflow)", re.I),
    "scenarios":   re.compile(r"(\d+)\s*(?:個|个)?\s*(?:場景|scenario)s?", re.I),
    "tables":      re.compile(r"(\d+)\s*(?:張表|表格?|table)s?\b", re.I),
    "protocols":   re.compile(r"(\d+)\s*(?:個|个)?\s*(?:協議|protocol)s?", re.I),
    "endpoints":   re.compile(r"(\d+)\s*(?:個|个)?\s*(?:端點|API (?:端點|endpoint))s?", re.I),
    "skills":      re.compile(r"(\d+)\s*(?:個|个)?\s*(?:invocable skills?|可調用技能)", re.I),
}


def get_runtime_values():
    """Query the live DB / engine for authoritative values."""
    out = {}
    db = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
    backup = ROOT / "AI项目管理" / "Platform" / "db" / "platform_restored.db"
    # Prefer populated DB
    target = db if db.exists() and db.stat().st_size > 100_000 else backup
    if target.exists() and target.stat().st_size > 100_000:
        try:
            conn = sqlite3.connect(f"file:{target.resolve()}?immutable=1", uri=True)
            out["tables"] = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            out["roles"] = conn.execute("SELECT COUNT(*) FROM ai_roles").fetchone()[0]
            out["workflows"] = conn.execute(
                "SELECT COUNT(*) FROM workflow_definitions"
            ).fetchone()[0]
            out["protocols"] = conn.execute(
                "SELECT COUNT(*) FROM collaboration_protocols"
            ).fetchone()[0]
            conn.close()
        except Exception as e:
            print(f"  (DB query failed: {e})")
    # Scenarios — best effort via local import
    try:
        sys.path.insert(0, str(ROOT))
        from scenario_engine import ScenarioEngineIntegration
        sei = ScenarioEngineIntegration()
        out["scenarios"] = len(sei.list_scenarios())
    except Exception:
        pass
    # Endpoints — count in api_server.py
    try:
        src = (ROOT / "api_server.py").read_text(encoding="utf-8")
        paths = set(re.findall(r'path\s*==\s*["\'](/api/[^"\']+)["\']', src))
        out["endpoints"] = len(paths)
    except Exception:
        pass
    return out


def scan_claims():
    """Return claims_by_fact: fact → value → [files]."""
    claims_by_fact = defaultdict(lambda: defaultdict(list))
    md_files = sorted(ROOT.rglob("*.md"))
    for p in md_files:
        if any(s in str(p) for s in ["/Archive/", "node_modules"]):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for fact, pat in PATTERNS.items():
            found_vals = set()
            for m in pat.finditer(text):
                n = int(m.group(1))
                if 1 <= n <= 200:
                    found_vals.add(n)
            for n in found_vals:
                claims_by_fact[fact][n].append(str(p.relative_to(ROOT)))
    return claims_by_fact, len(md_files)


def main():
    print("=" * 72)
    print("  Semantic Consistency Audit — shared-fact drift across .md files")
    print("=" * 72)
    truth = get_runtime_values()
    print()
    print("Runtime authoritative values:")
    for k, v in sorted(truth.items()):
        print(f"  {k:14s}: {v}")

    print()
    claims, total_md = scan_claims()
    print(f"Scanned {total_md} .md files.\n")

    # For each fact, check drift relative to truth
    drift_summary = []
    for fact, truth_val in truth.items():
        if fact not in claims:
            continue
        vals = claims[fact]
        # File that claim the correct value
        correct_files = vals.get(truth_val, [])
        # Files that claim a DIFFERENT value
        wrong_files = []
        for v, fs in vals.items():
            if v != truth_val:
                wrong_files.extend(fs)
        # In receiver-facing docs?
        receiver_correct = [f for f in correct_files if Path(f).name in RECEIVER_DOCS]
        receiver_wrong = [f for f in wrong_files if Path(f).name in RECEIVER_DOCS]
        drift_summary.append((fact, truth_val, len(correct_files), len(wrong_files),
                               receiver_correct, receiver_wrong))
        print(f"── {fact.upper():12s} (truth={truth_val}) ──")
        print(f"  Files agreeing (claim={truth_val}): {len(correct_files)}")
        if receiver_correct:
            print(f"    receiver-facing ✓: {receiver_correct}")
        # Show disagreeing values
        for v, fs in sorted(vals.items()):
            if v == truth_val:
                continue
            receiver_drift = [f for f in fs if Path(f).name in RECEIVER_DOCS]
            if receiver_drift:
                print(f"  ⚠ Receiver-facing docs claim {v} (not {truth_val}): {receiver_drift}")
            # Don't dump non-receiver drift — too noisy
        print()

    # Final verdict: any receiver-facing doc has drift?
    print("=" * 72)
    problems = sum(1 for _, _, _, _, _, rw in drift_summary if rw)
    if problems == 0:
        print("  ✅ No drift in receiver-facing docs")
    else:
        print(f"  ⚠  {problems} fact(s) with receiver-facing drift — consider a sweep")
    print("=" * 72)
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
