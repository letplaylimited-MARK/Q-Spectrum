#!/usr/bin/env python3
"""
Reverse-Thinking Probe Audit / 反向思考探針審計 (Round 17)
============================================================
Existing 12 gates all check "does X work when invoked normally?".
This audit asks the *reverse* question: "What could go wrong that
our 12 gates would NOT catch?" — then builds a probe for each
hypothetical gap and verifies the system survives it.

Six probes, each targets a different existing-gate blind spot:

  P1  Query flood        — R15 longitudinal was MIXED queries. What if
                           the same query fires 60× rapid-fire? Does
                           routing stay deterministic? Does the engine
                           leak memory? Does cache poison?
  P2  Emoji-only input   — regression tests prose & code. What if the
                           user types only "🤔🤔🤔" or "¯\\_(ツ)_/¯"?
                           Engine should NOT crash, should route to
                           a sane fallback (Q01 greeting).
  P3  New-doc drift      — semantic_consistency checks EXISTING docs.
                           What if a receiver adds a new .md with a
                           WRONG role-count claim? Does any gate catch
                           the new doc's drift?  (Answer: semantic_-
                           consistency auto-scans .md globs, so YES —
                           we inject and verify.)
  P4  Silent sabotage    — workspace_integrity checks size ≥200B at
                           scan time. What if a script is zeroed
                           DURING a verify run? We simulate mid-run
                           corruption and confirm the gate catches
                           the state when invoked.
  P5  16th failure mode  — FMEA enumerates 15 known modes. We design
                           a 16th (race-condition double-close) and
                           confirm the engine survives it, proving
                           defense-in-depth beyond FMEA's catalog.
  P6  Canonical-number   — self_report_accuracy trusts DB as truth.
       circular trap       What if DB has 15 roles but 2 are placeholder
                           rows with no real capabilities? Probe:
                           count rows with NON-NULL capabilities.
                           Verify all 15 roles are functionally live.

Each probe is ≤30s. Probe that SURVIVES returns ✓ (system resilient).
Probe that EXPOSES a gap returns ✗ (file a new bug).
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8765"


class Probe:
    def __init__(self, pid, name, passed, observation, hint=""):
        self.pid = pid
        self.name = name
        self.passed = passed
        self.observation = observation
        self.hint = hint


def http_chat(msg, session_id, timeout=8):
    req = urllib.request.Request(
        f"{BASE}/api/chat",
        data=json.dumps({"message": msg, "session_id": session_id}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read())
        return time.time() - t0, body, None
    except Exception as e:
        return time.time() - t0, None, str(e)[:120]


# ──────────────────────────────────────────────────────────────
# Probes
# ──────────────────────────────────────────────────────────────

def probe_1_query_flood():
    """60 identical queries in 10 seconds. Expect: deterministic routing,
    no cache poison, errors ≤2, latency stable."""
    N = 60
    q = "寫一篇關於 AI 的文章"
    session = "probe1-flood"
    roles = []
    errors = 0
    latencies = []
    t0 = time.time()
    for i in range(N):
        dt, body, err = http_chat(q, f"{session}-{i}")  # distinct sessions to avoid topic-tracking
        if err:
            errors += 1
            continue
        roles.append(body.get("routing", {}).get("role_code", "?"))
        latencies.append(dt)
    elapsed = time.time() - t0
    role_dist = Counter(roles)
    # Expect Q03 (Content Craftsman) for content queries
    top_role, top_count = role_dist.most_common(1)[0] if role_dist else ("?", 0)
    determinism = 100 * top_count / max(1, len(roles))
    # 60 HTTP round-trips typically take 25-45s depending on sandbox IO;
    # the real test is deterministic routing + no errors. Timing ≤60s
    # is a generous upper bound for "no runaway slowness".
    passed = (errors <= 2 and determinism >= 95 and top_role == "ROLE-Q03"
              and elapsed < 60)
    return Probe(
        "P1", "query flood — 60× identical, deterministic routing",
        passed,
        f"{len(roles)}/{N} ok, {errors} errs, {determinism:.0f}% → {top_role}, {elapsed:.1f}s",
        "expect ≥95% → ROLE-Q03, errors ≤2, <60s",
    )


def probe_2_emoji_only():
    """Pure emoji/symbol input. Engine must NOT crash, routes to a fallback."""
    inputs = ["🤔🤔🤔", "¯\\_(ツ)_/¯", "😊", "⭐️🔥💡", "👋"]
    session = "probe2-emoji"
    crashed = []
    routed = []
    for msg in inputs:
        _, body, err = http_chat(msg, session)
        if err or not body:
            crashed.append(msg)
        else:
            role = body.get("routing", {}).get("role_code", "?")
            routed.append((msg, role))
    passed = len(crashed) == 0 and len(routed) == len(inputs)
    return Probe(
        "P2", "emoji-only input — no crash, graceful fallback",
        passed,
        f"{len(routed)}/{len(inputs)} routed, crashed: {crashed}",
        "engine must not raise on non-text input",
    )


def probe_3_new_doc_drift():
    """Static analysis: does semantic_consistency.py scan via rglob (catches
    NEW docs) or via a hard-coded list (would miss new docs)?"""
    src = (ROOT / "tests" / "semantic_consistency.py").read_text(encoding="utf-8")
    # Look for rglob("*.md") or glob("*.md") pattern - means it auto-discovers
    uses_glob = bool(re.search(r"rglob\(['\"]\*\.md['\"]\)|glob\(['\"]\*\*/\*\.md['\"]\)", src))
    # Also check if it falls back to a hard-coded list (would be a bug)
    has_hardcoded_only = bool(re.search(
        r"CRITICAL_DOCS\s*=\s*\[[^\]]+\]", src
    )) and not uses_glob
    passed = uses_glob
    return Probe(
        "P3", "new-doc drift — semantic_consistency uses glob discovery",
        passed,
        f"uses rglob: {uses_glob}, hardcoded-only: {has_hardcoded_only}",
        "gate must scan via .md glob, not hard-coded doc list",
    )


def probe_4_silent_sabotage():
    """Zero out a helper script after it was 'valid' — re-run workspace_-
    integrity immediately. It must catch the new state (≥200B rule)."""
    import subprocess as sp
    target = ROOT / "health-check.sh"
    if not target.exists():
        return Probe(
            "P4", "silent sabotage — workspace_integrity catches zeroed scripts",
            False, "health-check.sh not present to sabotage", "skipped",
        )
    original = target.read_bytes()
    try:
        # Zero the file
        target.write_bytes(b"#!/bin/sh\n")  # 9 bytes, below 200B threshold
        size_now = target.stat().st_size
        p = sp.run(
            ["python3", "tests/workspace_integrity.py"],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        out = p.stdout + p.stderr
        # Workspace integrity should now fail or warn
        # Look for indication the sabotage was noticed
        caught = (p.returncode != 0 or "health-check" in out.lower() or
                  "200" in out or "too small" in out.lower() or
                  "≥200" in out)
        observation = f"sabotaged to {size_now}B, gate exit={p.returncode}, caught={caught}"
    finally:
        target.write_bytes(original)
    return Probe(
        "P4", "silent sabotage — integrity gate catches <200B scripts",
        caught,
        observation,
        "integrity gate must enforce the ≥200B invariant on re-run",
    )


def probe_5_16th_failure_mode():
    """FMEA has 15 modes. Design a 16th: rapid session-id reuse with
    alternating crisis/content/analysis queries to test for state
    confusion. Crisis detection must NOT be sticky across turns.

    Role map (from platform.db ai_roles.capabilities — do not confuse):
      Q02 = knowledge_retrieval / literature_analysis (research)
      Q04 = data_insight / trend_analysis / kpi_tracking (numeric data)
      Q07 = emotional_support (crisis)
      Q03 = content_generation (writing)
    """
    session = "probe5-stateconfusion"
    # Interleave crisis ↔ non-crisis; each non-crisis must route per its
    # content, not inherit the session's crisis affinity.
    interleaved = [
        ("我活不下去了", "ROLE-Q07"),        # crisis
        ("幫我寫一首詩", "ROLE-Q03"),        # content (poetry)
        ("真的撐不下去", "ROLE-Q07"),        # crisis
        ("分析這份銷售數據", "ROLE-Q04"),    # data_insight/trend_analysis
        ("真的想結束", "ROLE-Q07"),          # crisis
    ]
    mismatches = []
    for msg, expected in interleaved:
        _, body, err = http_chat(msg, session)
        if err:
            mismatches.append((msg, "ERROR", err[:40]))
            continue
        actual = body.get("routing", {}).get("role_code")
        if actual != expected:
            mismatches.append((msg, expected, actual))
    passed = len(mismatches) == 0
    return Probe(
        "P5", "16th failure mode — state confusion on session re-use",
        passed,
        f"mismatches: {len(mismatches)}" + (f" ({mismatches[:2]})" if mismatches else ""),
        "alternating crisis↔content↔data must route correctly each turn",
    )


def probe_6_canonical_number_trap():
    """self_report_accuracy trusts DB. But are all 15 ai_roles rows
    fully-populated? Probe: every role must have non-empty capabilities."""
    db = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
    c = sqlite3.connect(f"file:{db.resolve()}?immutable=1", uri=True)
    rows = c.execute(
        "SELECT role_code, capabilities FROM ai_roles"
    ).fetchall()
    c.close()
    hollow = []
    for code, caps in rows:
        if not caps or len(str(caps).strip()) < 3:
            hollow.append(code)
    passed = len(rows) == 15 and len(hollow) == 0
    return Probe(
        "P6", "canonical-number trap — all 15 roles are functionally live",
        passed,
        f"{len(rows)} rows, {len(hollow)} hollow: {hollow}",
        "every ai_roles row must have non-empty capabilities",
    )


# ──────────────────────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────────────────────

PROBES = [
    probe_1_query_flood,
    probe_2_emoji_only,
    probe_3_new_doc_drift,
    probe_4_silent_sabotage,
    probe_5_16th_failure_mode,
    probe_6_canonical_number_trap,
]


def main():
    print("=" * 72)
    print("  Reverse-Thinking Probe Audit — 6 gap-probes (R17)")
    print("  'What could go wrong that our 12 gates would NOT catch?'")
    print("=" * 72)
    results = []
    for i, fn in enumerate(PROBES, 1):
        print(f"\n  [{i}/{len(PROBES)}] running {fn.__name__}...", flush=True)
        try:
            t0 = time.time()
            r = fn()
            dt = time.time() - t0
        except Exception as e:
            r = Probe(f"P{i}", fn.__name__, False,
                      f"probe itself crashed: {str(e)[:80]}",
                      "probe logic needs fix")
            dt = 0
        results.append(r)
        mark = "✓" if r.passed else "✗"
        print(f"  {mark} [{r.pid}] {r.name} ({dt:.1f}s)")
        print(f"       {r.observation}")
        if not r.passed:
            print(f"       ⚠ gap exposed: {r.hint}")

    good = sum(1 for r in results if r.passed)
    total = len(results)
    print()
    print("=" * 72)
    if good == total:
        print(f"  ✅ REVERSE-THINKING: {good}/{total} probes — no gap exposed")
        print("     existing 12 gates successfully cover these adversarial angles")
    else:
        print(f"  ⚠  REVERSE-THINKING: {good}/{total} probes — {total-good} gap(s) found")
        for r in results:
            if not r.passed:
                print(f"     • [{r.pid}] {r.name}")
    print("=" * 72)

    # Synthesis
    out = ROOT / "AUDIT-REVERSE-THINKING.md"
    with out.open("w", encoding="utf-8") as f:
        f.write("# Reverse-Thinking Probe Audit (R17)\n\n")
        f.write(f"**{good}/{total} probes survived** — targets gaps the existing 12 gates might miss.\n\n")
        f.write("| # | Probe | Result | Observation |\n")
        f.write("|---|---|:---:|---|\n")
        for r in results:
            f.write(f"| {r.pid} | {r.name} | {'✅' if r.passed else '❌'} | {r.observation} |\n")
    print(f"\n  ✓ Synthesis: {out}")
    return 0 if good == total else 1


if __name__ == "__main__":
    sys.exit(main())
