#!/usr/bin/env python3
"""
Self-Report Accuracy Audit / 測試報告自我表述準確性審計
=========================================================
The class of bug the user caught in R15: a gate ran fine, but its OUTPUT
SUMMARY used misleading framing ("13 active roles" when truth was 15 out
of which only 13 were exercised by the test pool). The gate didn't lie,
but the wording obscured a real coverage gap.

This audit re-runs each gate and cross-checks its stated numbers against
the runtime authoritative values. Flags any framing slippage.

For each gate:
  claimed_value — what the report text says
  actual_value  — what runtime queries return
  aligned       — do they agree AND do they measure the right thing?
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8765"


class Check:
    def __init__(self, name, claimed, actual, aligned, hint=""):
        self.name = name
        self.claimed = claimed
        self.actual = actual
        self.aligned = aligned
        self.hint = hint

    def mark(self):
        return "✓" if self.aligned else "✗"


def truth_role_count():
    db = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
    c = sqlite3.connect(f"file:{db.resolve()}?immutable=1", uri=True)
    n = c.execute("SELECT COUNT(*) FROM ai_roles").fetchone()[0]
    c.close()
    return n


def truth_scenario_count():
    with urllib.request.urlopen(f"{BASE}/api/scenarios/list", timeout=5) as r:
        return len(json.loads(r.read()).get("scenarios", []))


def truth_endpoint_count():
    src = (ROOT / "api_server.py").read_text(encoding="utf-8")
    return len(set(re.findall(r'path\s*==\s*["\'](/api/[^"\']+)["\']', src)))


def truth_doc_count_md():
    return len(list(ROOT.rglob("*.md")))


def run_gate_capture_output(cmd, timeout=120):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


# ──────────────────────────────────────────────────────────────
# Accuracy checks
# ──────────────────────────────────────────────────────────────

def check_longitudinal_claims():
    """R15 longitudinal should check 15-role coverage (not 13 "essential")."""
    # Static check: read the source of longitudinal_drift.py
    src = (ROOT / "tests" / "longitudinal_drift.py").read_text(encoding="utf-8")
    # Count roles in expected_roles set literal
    m = re.search(r"expected_roles\s*=\s*\{([^}]+)\}", src, re.DOTALL)
    if not m:
        return Check(
            "longitudinal expected_roles covers all 15",
            claimed="unparsed", actual="unparsed",
            aligned=False,
            hint="expected_roles set literal not found",
        )
    roles_in_set = len(re.findall(r'"ROLE-[A-Z]\d+"', m.group(1)))
    db_truth = truth_role_count()
    # Also look for invariant "all 15 roles reached" vs "essential role silenced"
    all_15_check = "All 15 roles reached" in src
    aligned = roles_in_set == 15 and db_truth == 15 and all_15_check
    return Check(
        "longitudinal expected_roles covers all 15",
        claimed=f"{roles_in_set} in expected set",
        actual=f"DB has {db_truth}",
        aligned=aligned,
        hint="expected_roles must be all 15 (not '10 essential')",
    )


def check_workspace_role_count_in_reports():
    """Verify reports saying 'X roles' use X=15 consistently."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "INDEX.md").read_text(encoding="utf-8")
    # Count claims of "N roles" in receiver-facing docs
    matches = []
    # Tighter regex: numeric + optional qualifiers + 'roles' (NOT 'role-XXX' compounds
    # like 'role-driven', 'role-scoped'). Require word-boundary 's' or plain 'roles'.
    role_re = re.compile(
        r"(\d+)\s*(?:specialized\s+|AI\s+|個|个)*roles(?![a-z-])",
        re.I,
    )
    for doc, text in [("README.md", readme), ("INDEX.md", index)]:
        for m in role_re.finditer(text):
            n = int(m.group(1))
            if 8 <= n <= 30:  # plausible total-role range
                matches.append((doc, n, m.group(0)))
    db_truth = truth_role_count()
    # All claims in receiver-facing docs should be 15 (or compound like "8 QCM")
    misaligned = [(d, n, ctx) for d, n, ctx in matches if n != db_truth]
    return Check(
        "README/INDEX role-count claims",
        claimed=f"mentions: {[n for _,n,_ in matches]}",
        actual=f"DB: {db_truth}",
        aligned=len(misaligned) == 0,
        hint="any '13 roles' or inflated role claims should be 15",
    )


def check_scenario_count_consistency():
    """SCENARIOS.md + /api/scenarios/list should both report 12."""
    api_scn = truth_scenario_count()
    scenarios_md = (ROOT / "SCENARIOS.md").read_text(encoding="utf-8")
    md_claim = 0
    m = re.search(r"(\d+)\s*scenarios", scenarios_md, re.I)
    if m:
        md_claim = int(m.group(1))
    aligned = api_scn == 12 and md_claim in (12, 0)
    return Check(
        "scenario count: /api/scenarios vs SCENARIOS.md",
        claimed=f"SCENARIOS.md: {md_claim}",
        actual=f"/api/scenarios/list: {api_scn}",
        aligned=aligned,
        hint="both should be 12; 0 means regex missed",
    )


def check_regression_pass_count():
    """Regression suite: docs' claimed count must match runtime-reported count."""
    # Runtime truth: run the suite and parse its own summary line.
    rc, out = run_gate_capture_output(
        ["python3", "tests/test_regression.py"], timeout=60)
    m = re.search(r"Regression Summary:\s*(\d+)/(\d+)\s*passed", out)
    if not m:
        return Check(
            "regression suite: docs match runtime",
            claimed="?", actual="could not parse suite output",
            aligned=False,
            hint="regression summary line not found in output",
        )
    runtime_passed = int(m.group(1))
    runtime_total = int(m.group(2))
    runtime_ok = runtime_passed == runtime_total
    # Scan receiver-facing CURRENT-state docs for claims about the count.
    claim_pattern = re.compile(
        r"(\d+)\s*(?:/\s*\d+\s+)?(?:regression|automated)\s+assertions?",
        re.I,
    )
    doc_claims = []
    for doc in ("README.md", "INDEX.md"):
        p = ROOT / doc
        if not p.exists():
            continue
        for m2 in claim_pattern.finditer(p.read_text(encoding="utf-8")):
            doc_claims.append((doc, int(m2.group(1))))
    bad = [(d, n) for d, n in doc_claims if n != runtime_total]
    aligned = runtime_ok and not bad
    return Check(
        "regression suite: docs match runtime",
        claimed=f"docs say: {[n for _, n in doc_claims]}",
        actual=f"runtime: {runtime_passed}/{runtime_total}",
        aligned=aligned,
        hint=(f"stale doc claims: {bad}" if bad else
              ("some assertions failed" if not runtime_ok else "ok")),
    )


def check_all_gates_still_runnable():
    """Verify every gate file exists AND is executable (not empty)."""
    gates = [
        "tests/test_regression.py",
        "tests/flywheel_audit.py",
        "tests/adversarial_audit.py",
        "tests/journey_wargame.py",
        "tests/persona_stressor_matrix.py",
        "tests/workspace_integrity.py",
        "tests/meta_audit.py",
        "tests/semantic_consistency.py",
        "tests/fmea_audit.py",
        "tests/longitudinal_drift.py",
        "tests/generational_chain.py",
        "tests/self_report_accuracy.py",
        "tests/reverse_thinking_probes.py",
        "tests/industry_scenario_wargame.py",
        "verify-delivery.py",
    ]
    missing = []
    too_small = []
    for g in gates:
        p = ROOT / g
        if not p.exists():
            missing.append(g)
        elif p.stat().st_size < 1000:
            too_small.append(f"{g} ({p.stat().st_size}B)")
    aligned = not missing and not too_small
    return Check(
        f"all {len(gates)} quality-gate files present + non-trivial",
        claimed=f"{len(gates)} gates",
        actual=f"{len(gates) - len(missing) - len(too_small)} valid",
        aligned=aligned,
        hint=f"missing: {missing}; too small: {too_small}",
    )


def check_fmea_test_count():
    """R14 FMEA should enumerate 15 failure modes."""
    src = (ROOT / "tests" / "fmea_audit.py").read_text(encoding="utf-8")
    # Count test entries in TESTS = [...]
    m = re.search(r"TESTS\s*=\s*\[(.+?)^\]", src, re.MULTILINE | re.DOTALL)
    tests_count = 0
    if m:
        tests_count = len(re.findall(r'"F\d+', m.group(1)))
    aligned = tests_count == 15
    return Check(
        "FMEA enumerates 15 failure modes",
        claimed=f"{tests_count} F* entries in TESTS list",
        actual="15 expected",
        aligned=aligned,
        hint="FMEA should have 15 distinct failure-mode tests",
    )


def check_api_endpoint_count():
    """INSTALL-GUIDE says '~85 endpoints' — what's truth?"""
    install_guide = (ROOT / "INSTALL-GUIDE.md").read_text(encoding="utf-8")
    # Find endpoint count claim
    m = re.search(r"~?(\d+)\s*(?:個|个)?\s*(?:REST API\s+)?endpoints?", install_guide)
    claimed = int(m.group(1)) if m else None
    actual = truth_endpoint_count()
    aligned = claimed is not None and abs(actual - claimed) <= 5
    return Check(
        "INSTALL-GUIDE endpoint count",
        claimed=str(claimed),
        actual=str(actual),
        aligned=aligned,
        hint="±5 tolerance for 'approximately' phrasing",
    )


def check_delivery_healthy_really_means_healthy():
    """If verify-delivery says 'HEALTHY', does it check >=10 items?"""
    rc, out = run_gate_capture_output(
        ["python3", "verify-delivery.py", "--quick"], timeout=30)
    healthy = "DELIVERY HEALTHY" in out
    m = re.search(r"(\d+)/(\d+)\s*checks\s*passed", out)
    if m:
        passed = int(m.group(1))
        total = int(m.group(2))
        aligned = healthy and passed == total and passed >= 6  # quick has 6
        detail = f"{passed}/{total}"
    else:
        aligned = False
        detail = "unparsed"
    return Check(
        "'DELIVERY HEALTHY' = all checks pass (quick mode)",
        claimed="HEALTHY" if healthy else "not HEALTHY",
        actual=detail,
        aligned=aligned,
        hint="quick mode checks ≥6 static items",
    )


# ──────────────────────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────────────────────

CHECKS = [
    check_longitudinal_claims,
    check_workspace_role_count_in_reports,
    check_scenario_count_consistency,
    check_regression_pass_count,
    check_all_gates_still_runnable,
    check_fmea_test_count,
    check_api_endpoint_count,
    check_delivery_healthy_really_means_healthy,
]


def main():
    print("=" * 72)
    print("  Self-Report Accuracy Audit — truth vs framing")
    print("  (does 'PASS' really mean pass? does '15/15' really mean 15?)")
    print("=" * 72)
    results = []
    for fn in CHECKS:
        print(f"\n  running {fn.__name__}...", flush=True)
        try:
            r = fn()
        except Exception as e:
            r = Check(fn.__name__, "error", str(e)[:60], False,
                     f"check itself crashed: {e}")
        results.append(r)
        print(f"  {r.mark()} {r.name:50s}")
        print(f"     claimed: {r.claimed}")
        print(f"     actual:  {r.actual}")
        if not r.aligned:
            print(f"     ⚠ misaligned: {r.hint}")

    good = sum(1 for r in results if r.aligned)
    total = len(results)
    print()
    print("=" * 72)
    if good == total:
        print(f"  ✅ Self-report accuracy: {good}/{total} — all claims truthful")
    else:
        print(f"  ⚠  Self-report accuracy: {good}/{total} — {total-good} framing issues")
        for r in results:
            if not r.aligned:
                print(f"     • {r.name} — {r.hint}")
    print("=" * 72)
    return 0 if good == total else 1


if __name__ == "__main__":
    sys.exit(main())
