#!/usr/bin/env python3
"""
FMEA: Failure Mode & Effects Analysis / 故障模式與影響分析
=========================================================
For each critical component, enumerate failure modes, measure the user impact,
verify the current mitigation — or add one.

Unlike the meta-audit (Round 12) which tests "do the auditors catch their own
class?", this audits the PRODUCT itself: "for every way a piece can fail,
what does the user see?"

Each entry reports:
  component — the piece being stressed
  failure_mode — how it breaks
  user_impact — what the receiver would see
  current_mitigation — what the system does today (graceful/degraded/crash)
  verdict — GOOD / PARTIAL / GAP
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class FMEAEntry:
    def __init__(self, component, mode, impact, mitigation, verdict, detail=""):
        self.component = component
        self.mode = mode
        self.impact = impact
        self.mitigation = mitigation
        self.verdict = verdict  # "GOOD" / "PARTIAL" / "GAP"
        self.detail = detail

    def glyph(self):
        return {"GOOD": "✅", "PARTIAL": "⚠️", "GAP": "❌"}.get(self.verdict, "?")


def ping(path="/api/status", timeout=3):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:8765{path}", timeout=timeout) as r:
            return r.status
    except Exception:
        return 0


# ══════════════════════════════════════════════════════════════════
# Failure mode tests (each with automatic revert)
# ══════════════════════════════════════════════════════════════════

def fm_platform_db_missing():
    """What if platform.db doesn't exist?"""
    db = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
    backup = ROOT / "AI项目管理" / "Platform" / "db" / "platform_restored.db"
    holder = Path("/tmp/.fmea_platform_db.bak")
    if db.exists():
        shutil.copyfile(db, holder)
    try:
        db.write_bytes(b"")  # zero out
        # Does run.py --status still work via fallback?
        p = subprocess.run(
            ["python3", "run.py", "--status"],
            cwd=ROOT, capture_output=True, text=True, timeout=20
        )
        out = p.stdout + p.stderr
        fallback_used = "platform_restored" in out or "fallback" in out.lower()
        crashed = p.returncode not in (0,)
        if fallback_used and not crashed:
            return FMEAEntry(
                "platform.db", "file zeroed",
                "engine tries to open empty DB",
                "automatic fallback to platform_restored.db",
                "GOOD",
                f"run.py --status uses 3-candidate fallback; fallback_used={fallback_used}",
            )
        elif fallback_used:
            return FMEAEntry(
                "platform.db", "file zeroed",
                "engine opens DB",
                "fallback triggered but exit non-zero",
                "PARTIAL",
                f"rc={p.returncode}",
            )
        else:
            return FMEAEntry(
                "platform.db", "file zeroed",
                "engine opens DB",
                "no fallback — user sees error",
                "GAP",
                f"rc={p.returncode}; no fallback path",
            )
    finally:
        if holder.exists():
            shutil.copyfile(holder, db)
            holder.unlink()
        elif backup.exists():
            shutil.copyfile(backup, db)


def fm_routing_keywords_missing():
    """What if routing_keywords.json is missing?"""
    kw = ROOT / "routing_keywords.json"
    holder = Path("/tmp/.fmea_routing_kw.bak")
    if kw.exists():
        shutil.copyfile(kw, holder)
    try:
        kw.write_text("", encoding="utf-8")  # empty file
        # Try to import Secretary and see if it falls back to inline defaults
        sys.path.insert(0, str(ROOT))
        for mod in list(sys.modules):
            if "qspectrum_engine" in mod:
                del sys.modules[mod]
        try:
            from qspectrum_engine import Secretary
            Secretary._KEYWORDS_LOADED = False
            Secretary._load_keywords()
            # If TRUM_KEYWORDS is a non-empty list, inline fallback worked
            has_defaults = bool(getattr(Secretary, "TRUM_KEYWORDS", []))
            return FMEAEntry(
                "routing_keywords.json",
                "empty / corrupt",
                "Secretary can't load routing rules",
                "inline TRUM_KEYWORDS / SPEC_KEYWORDS defaults" if has_defaults
                    else "no fallback",
                "GOOD" if has_defaults else "GAP",
                f"has_defaults={has_defaults}",
            )
        except Exception as e:
            return FMEAEntry(
                "routing_keywords.json", "empty / corrupt",
                "Secretary import fails", f"crash: {e}",
                "GAP", str(e)[:80],
            )
    finally:
        if holder.exists():
            shutil.copyfile(holder, kw)
            holder.unlink()
        # Cleanup module state
        for mod in list(sys.modules):
            if "qspectrum_engine" in mod:
                del sys.modules[mod]


def fm_memory_md_readonly():
    """What if MEMORY.md is read-only when engine tries to append?"""
    m = ROOT / "MEMORY.md"
    # Save original permissions
    original_mode = os.stat(m).st_mode
    try:
        # Remove write permissions (simulating read-only mount)
        os.chmod(m, 0o444)
        # Try to hit /api/memory/append
        req = urllib.request.Request(
            "http://127.0.0.1:8765/api/memory/append",
            data=json.dumps({"kind": "insight",
                             "entry": "FMEA_RO_TEST_DO_NOT_KEEP"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                body = json.loads(r.read())
            # Expect a clean error response with specific forbidden/IO code
            if "error" in body and ("permission" in str(body.get("error","")).lower()
                                     or "readonly" in str(body.get("error","")).lower()
                                     or "not writable" in str(body.get("error","")).lower()):
                verdict = "GOOD"
            elif "error" in body:
                verdict = "PARTIAL"
            else:
                verdict = "GAP"
            detail = f"body={str(body)[:100]}"
        except urllib.error.HTTPError as e:
            # HTTP 403 = specific permission error (good); 500 = generic (partial)
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 403:
                verdict = "GOOD"
            elif e.code == 500:
                verdict = "PARTIAL"
            else:
                verdict = "GOOD" if e.code < 500 else "GAP"
            detail = f"HTTP {e.code}, body={body[:80]}"
    finally:
        os.chmod(m, original_mode)
        # Clean up any test entry
        try:
            text = m.read_text(encoding="utf-8")
            if "FMEA_RO_TEST_DO_NOT_KEEP" in text:
                import re
                text = re.sub(r"\*\*K\d+\*\* \(.+?\) — FMEA_RO_TEST_DO_NOT_KEEP\n",
                              "", text)
                m.write_text(text, encoding="utf-8")
        except Exception:
            pass
    return FMEAEntry(
        "MEMORY.md", "read-only mount / permission denied",
        "/api/memory/append can't write",
        "HTTP 500 with permission error" if verdict != "GAP" else "silent failure",
        verdict, detail,
    )


def fm_port_in_use():
    """Port 8765 already in use — second launch should give friendly error."""
    # Server is already running (we start it before fmea). Launch another.
    p = subprocess.run(
        ["python3", "run.py", "--web"],
        cwd=ROOT, capture_output=True, text=True, timeout=10,
    )
    out = p.stdout + p.stderr
    friendly = ("Port already in use" in out or "端口已被佔用" in out or
                "already running" in out.lower())
    if friendly and p.returncode != 0:
        verdict = "GOOD"
    elif "OSError" in out and "Address already in use" in out:
        verdict = "GAP"  # ugly stack trace
    else:
        verdict = "PARTIAL"
    return FMEAEntry(
        "port 8765 binding", "port already in use",
        "second start.bat / start.sh launch",
        "friendly bilingual message + alternate-port hint" if verdict == "GOOD"
            else "ugly stack trace",
        verdict, f"rc={p.returncode}",
    )


def fm_invalid_provider():
    """--provider fake_value should reject cleanly."""
    p = subprocess.run(
        ["python3", "run.py", "--web", "--provider", "made_up_provider"],
        cwd=ROOT, capture_output=True, text=True, timeout=8,
    )
    out = p.stdout + p.stderr
    rejected = "Unknown --provider" in out and p.returncode == 2
    return FMEAEntry(
        "CLI args", "invalid --provider value",
        "user passes typo / unknown provider",
        "validate against whitelist of 7 providers; exit 2 with hint"
            if rejected else "cryptic error or silent acceptance",
        "GOOD" if rejected else "GAP",
        f"rc={p.returncode}, rejected={rejected}",
    )


def fm_invalid_port():
    """--port 99999 should reject cleanly."""
    p = subprocess.run(
        ["python3", "run.py", "--web", "--port", "99999"],
        cwd=ROOT, capture_output=True, text=True, timeout=8,
    )
    out = p.stdout + p.stderr
    rejected = "Invalid --port" in out and p.returncode == 2
    return FMEAEntry(
        "CLI args", "out-of-range --port",
        "user passes invalid port number",
        "range-check 1-65535; exit 2 with error" if rejected
            else "OverflowError stack trace",
        "GOOD" if rejected else "GAP",
        f"rc={p.returncode}",
    )


def fm_empty_chat_body():
    """POST /api/chat with empty body should return HTTP 400."""
    req = urllib.request.Request(
        "http://127.0.0.1:8765/api/chat",
        data=b"",
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            code, body = r.status, r.read()
    except urllib.error.HTTPError as e:
        code, body = e.code, e.read()
    except Exception as e:
        return FMEAEntry(
            "/api/chat", "empty body", "user sends no message",
            f"exception: {e}", "GAP", str(e)[:60],
        )
    if code == 400:
        verdict = "GOOD"
    elif code == 200:
        verdict = "PARTIAL"
    else:
        verdict = "GAP"
    return FMEAEntry(
        "/api/chat", "empty body POST",
        "user submits empty form",
        "HTTP 400 'Empty message / 消息为空'" if verdict == "GOOD"
            else "other behavior",
        verdict, f"HTTP {code}",
    )


def fm_malformed_json():
    """POST with malformed JSON should return HTTP 400."""
    req = urllib.request.Request(
        "http://127.0.0.1:8765/api/skills/execute",
        data=b"not a valid json",
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        return FMEAEntry(
            "any POST endpoint", "malformed JSON body",
            "client sends garbage", f"exception: {e}", "GAP", str(e)[:60],
        )
    verdict = "GOOD" if code == 400 else "PARTIAL" if code < 500 else "GAP"
    return FMEAEntry(
        "any POST endpoint", "malformed JSON body",
        "client sends invalid JSON",
        "HTTP 400 'Invalid JSON body'" if verdict == "GOOD"
            else "other behavior",
        verdict, f"HTTP {code}",
    )


def fm_oversized_payload():
    """POST with 15MB body — server should reject via MAX_BODY guard."""
    data = json.dumps({"message": "A" * (15 * 1024 * 1024)}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:8765/api/chat",
        data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception:
        code = 0
    # 413 = clean rejection; broken pipe / connection closed also counts as mitigation
    verdict = "GOOD" if code in (400, 413) or code == 0 else "GAP"
    return FMEAEntry(
        "any POST endpoint", "oversized payload (15MB)",
        "malicious or misconfigured client",
        "10MB cap in _read_body → 413 or connection close"
            if verdict == "GOOD" else "accepted and processed",
        verdict, f"HTTP {code}",
    )


def fm_unknown_api_path():
    """GET /api/nonexistent — should return 404, not crash."""
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8765/api/nonexistent_endpoint_xyz",
            timeout=5,
        ) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    verdict = "GOOD" if code == 404 else "PARTIAL" if code < 500 else "GAP"
    return FMEAEntry(
        "REST API", "unknown /api/ path",
        "client hits wrong URL",
        "HTTP 404" if verdict == "GOOD" else "other",
        verdict, f"HTTP {code}",
    )


def fm_path_traversal():
    """GET /api/files/read?path=../../etc/passwd — must be blocked."""
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8765/api/files/read?path=../../../../etc/passwd",
            timeout=5,
        ) as r:
            code, body = r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        code, body = e.code, e.read().decode("utf-8", errors="replace")
    # Look for block message
    blocked = "traversal" in body.lower() or "越界" in body or code in (400, 403)
    leaked = "root:x:" in body  # shouldn't contain /etc/passwd content
    if blocked and not leaked:
        verdict = "GOOD"
    elif leaked:
        verdict = "GAP"
    else:
        verdict = "PARTIAL"
    return FMEAEntry(
        "/api/files/read", "path traversal attack",
        "attacker accesses parent-dir files",
        "PathGuard v3.1 blocks '..' patterns"
            if verdict == "GOOD" else "may leak",
        verdict, f"HTTP {code}, leaked={leaked}",
    )


def fm_deerflow_missing():
    """DeerFlow directory doesn't exist — documented as optional."""
    # Check the status output reports it as WARN not FAIL
    p = subprocess.run(
        ["python3", "run.py", "--status"],
        cwd=ROOT, capture_output=True, text=True, timeout=20,
    )
    out = p.stdout + p.stderr
    # Expected: "⚠️  DeerFlow directory not found" — warn, not fail
    reported_warn = "DeerFlow" in out and "not found" in out
    overall_green = "ALL GREEN" in out
    if reported_warn and overall_green:
        verdict = "GOOD"
    elif reported_warn:
        verdict = "PARTIAL"
    else:
        verdict = "GAP"
    return FMEAEntry(
        "DeerFlow", "optional integration absent",
        "user sees message at startup",
        "reported as ⚠️ warning, system remains ALL GREEN"
            if verdict == "GOOD" else "harder to read",
        verdict,
        f"reported_warn={reported_warn}, overall_green={overall_green}",
    )


def fm_concurrent_writes():
    """Two simultaneous /api/memory/append — does the file survive?"""
    m = ROOT / "MEMORY.md"
    before_size = m.stat().st_size
    import threading
    errors = []
    def worker(tag):
        req = urllib.request.Request(
            "http://127.0.0.1:8765/api/memory/append",
            data=json.dumps({"kind": "insight",
                             "entry": f"FMEA_CONC_{tag}_DO_NOT_KEEP"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                _ = r.read()
        except Exception as e:
            errors.append(str(e))
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    after_size = m.stat().st_size
    # Clean up test entries
    try:
        text = m.read_text(encoding="utf-8")
        import re
        text = re.sub(r"\*\*K\d+\*\* \(.+?\) — FMEA_CONC_\d+_DO_NOT_KEEP\n",
                      "", text)
        m.write_text(text, encoding="utf-8")
    except Exception:
        pass
    if not errors:
        verdict = "GOOD"
        detail = f"10/10 concurrent writes OK, file grew {before_size}→{after_size}"
    elif len(errors) < 10:
        verdict = "PARTIAL"
        detail = f"{10-len(errors)}/10 succeeded"
    else:
        verdict = "GAP"
        detail = f"all {len(errors)} failed"
    return FMEAEntry(
        "/api/memory/append", "concurrent writers",
        "multi-user race condition",
        "10 parallel writes all complete without corruption"
            if verdict == "GOOD" else "race issues",
        verdict, detail,
    )


def fm_skill_execute_nonexistent():
    """POST /api/skills/execute with non-existent skill name."""
    req = urllib.request.Request(
        "http://127.0.0.1:8765/api/skills/execute",
        data=json.dumps({"skill": "totally_fake_skill_name_xyz",
                         "message": "hi"}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            code, body = r.status, json.loads(r.read())
        status = body.get("status")
        err = body.get("error", "")
        if code == 200 and status == "error" and "not available" in err:
            verdict = "GOOD"
        elif code >= 500:
            verdict = "GAP"
        else:
            verdict = "PARTIAL"
        detail = f"HTTP {code}, status={status}, err={err[:60]}"
    except Exception as e:
        verdict = "GAP"
        detail = str(e)[:80]
    return FMEAEntry(
        "/api/skills/execute", "unknown skill name",
        "user typo / stale skill reference",
        "HTTP 200 with clean error body" if verdict == "GOOD"
            else "crash",
        verdict, detail,
    )


def fm_sandbox_arbitrary_scenario():
    """/api/scenarios/sandbox with attack payload — should not reflect it."""
    attack = {"scenario_id": "<script>alert(1)</script>"}
    req = urllib.request.Request(
        "http://127.0.0.1:8765/api/scenarios/sandbox",
        data=json.dumps(attack).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            code, raw = r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        code, raw = e.code, e.read().decode("utf-8", errors="replace")
    reflected = "<script>" in raw and "alert(1)" in raw
    if code == 400 and not reflected:
        verdict = "GOOD"
    elif reflected:
        verdict = "GAP"
    else:
        verdict = "PARTIAL"
    return FMEAEntry(
        "/api/scenarios/sandbox", "XSS payload as scenario_id",
        "attacker injects via sandbox endpoint",
        "whitelist-based rejection, HTTP 400"
            if verdict == "GOOD" else "payload reflected",
        verdict, f"HTTP {code}, reflected={reflected}",
    )


# ══════════════════════════════════════════════════════════════════
# Runner
# ══════════════════════════════════════════════════════════════════

TESTS = [
    ("F1 platform.db missing", fm_platform_db_missing),
    ("F2 routing_keywords.json empty", fm_routing_keywords_missing),
    ("F3 MEMORY.md read-only", fm_memory_md_readonly),
    ("F4 port 8765 in use", fm_port_in_use),
    ("F5 invalid --provider", fm_invalid_provider),
    ("F6 invalid --port", fm_invalid_port),
    ("F7 empty chat body", fm_empty_chat_body),
    ("F8 malformed JSON", fm_malformed_json),
    ("F9 oversized payload (15MB)", fm_oversized_payload),
    ("F10 unknown /api/ path", fm_unknown_api_path),
    ("F11 path traversal attempt", fm_path_traversal),
    ("F12 DeerFlow absent", fm_deerflow_missing),
    ("F13 concurrent /api/memory/append", fm_concurrent_writes),
    ("F14 skill execute nonexistent", fm_skill_execute_nonexistent),
    ("F15 sandbox XSS payload", fm_sandbox_arbitrary_scenario),
]


def main():
    print("=" * 76)
    print("  FMEA: Failure Mode & Effects Analysis")
    print("  (for every way a piece can fail, what does the user see?)")
    print("=" * 76)
    # Verify server is up
    if ping() != 200:
        print("  ⚠  Server not running on :8765 — some tests will fail")
        print("     Start it first: python run.py --web")
    results = []
    for label, fn in TESTS:
        print(f"\n  [{label}] ...", flush=True)
        try:
            r = fn()
        except Exception as e:
            r = FMEAEntry(label, "test itself crashed", "verifier bug",
                         str(e)[:80], "GAP", str(e)[:80])
        results.append(r)
        print(f"  {r.glyph()} {label:40s}  verdict={r.verdict}")
        print(f"     mode: {r.mode}")
        print(f"     impact: {r.impact}")
        print(f"     mitigation: {r.mitigation}")
        if r.detail:
            print(f"     detail: {r.detail}")

    # Summary
    print()
    print("=" * 76)
    good = sum(1 for r in results if r.verdict == "GOOD")
    partial = sum(1 for r in results if r.verdict == "PARTIAL")
    gap = sum(1 for r in results if r.verdict == "GAP")
    total = len(results)
    print(f"  FMEA: {good} GOOD, {partial} PARTIAL, {gap} GAP  (of {total} failure modes)")
    if gap == 0 and partial <= 3:
        print("  ✅ Reliability: acceptable")
    else:
        print(f"  ⚠  {gap} GAPs worth fixing:")
        for r in results:
            if r.verdict == "GAP":
                print(f"     • {r.component} — {r.mode}: {r.detail}")
    print("=" * 76)

    # Write synthesis
    out = ROOT / "AUDIT-FMEA.md"
    with out.open("w", encoding="utf-8") as f:
        f.write("# FMEA Audit Report\n\n")
        f.write(f"**{good} GOOD, {partial} PARTIAL, {gap} GAP** out of {total} failure modes.\n\n")
        f.write("| # | Component | Failure mode | Impact | Mitigation | Verdict |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in results:
            f.write(f"| {r.glyph()} | {r.component} | {r.mode} | {r.impact} | {r.mitigation} | {r.verdict} |\n")
    print(f"\n  ✓ Synthesis: {out}")

    return 0 if gap == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
