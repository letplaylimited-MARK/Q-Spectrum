"""
Q-SpecTrum consolidated regression test / 回歸測試套件
====================================================
Codifies the fixes applied across verification rounds 1-5 so future changes
cannot silently break any of them.

Run with:
    python tests/test_regression.py
    python run.py --e2e        (invokes this automatically when discovered)

Exit codes:
    0 — all regressions pass
    1 — one or more regressions failed
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BASE = "http://127.0.0.1:8765"
SERVER_START_TIMEOUT = 25  # seconds


# ────────────────────────────────────────────────────────────────
# Test harness
# ────────────────────────────────────────────────────────────────
class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures: list[tuple[str, str]] = []

    def check(self, name: str, cond: bool, detail: str = ""):
        if cond:
            self.passed += 1
            print(f"  ✓ {name}")
        else:
            self.failed += 1
            self.failures.append((name, detail))
            print(f"  ✗ {name}  — {detail}")

    def summary(self):
        total = self.passed + self.failed
        rate = 100 * self.passed / max(total, 1)
        print("\n" + "=" * 60)
        print(f"  Regression Summary: {self.passed}/{total} passed ({rate:.0f}%)")
        if self.failed:
            print("\n  Failures:")
            for name, detail in self.failures:
                print(f"    • {name}: {detail}")
        print("=" * 60)
        return self.failed == 0


# ────────────────────────────────────────────────────────────────
# HTTP helpers
# ────────────────────────────────────────────────────────────────
def _request(method: str, path: str, body: dict | None = None, timeout: int = 10):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def wait_server(timeout: int = SERVER_START_TIMEOUT) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            code, _ = _request("GET", "/api/status")
            if code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


# ────────────────────────────────────────────────────────────────
# Regressions (each rounds' fixes become a test here)
# ────────────────────────────────────────────────────────────────
def test_r1_missing_tables(r: Results):
    """Round 1: ai_roles, collaboration_protocols, interaction_logs exist with
    correct row counts (patch 100_ai_roles_patch.sql must be applied)."""
    db = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
    if not db.exists() or db.stat().st_size == 0:
        r.check("R1 platform.db exists + non-empty", False, "file missing or 0 bytes")
        return
    conn = sqlite3.connect(f"file:{db.resolve()}?immutable=1", uri=True)
    roles = conn.execute("SELECT COUNT(*) FROM ai_roles").fetchone()[0]
    protos = conn.execute("SELECT COUNT(*) FROM collaboration_protocols").fetchone()[0]
    workflows = conn.execute("SELECT COUNT(*) FROM workflow_definitions").fetchone()[0]
    r.check("R1 ai_roles has 15 rows", roles == 15, f"got {roles}")
    r.check("R1 collaboration_protocols has 10 rows", protos == 10, f"got {protos}")
    r.check("R1 workflow_definitions has 4 rows", workflows == 4, f"got {workflows}")
    conn.close()


def test_r1_virtiofs_fix(r: Results):
    """Round 1: agent_runtime.py verification uses immutable URI so opening the
    DB doesn't zero it on virtiofs."""
    src = (ROOT / "AI项目管理" / "Platform" / "scripts" / "agent_runtime.py").read_text(encoding="utf-8")
    r.check(
        "R1 agent_runtime uses immutable URI for verification",
        "?immutable=1" in src and "test_uri" in src,
        "immutable URI pattern not found",
    )


def test_r2_capability_codes(r: Results):
    """Round 2: ai_roles.capabilities uses CAPABILITY_KEYWORDS codes, not prose."""
    db = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
    conn = sqlite3.connect(f"file:{db.resolve()}?immutable=1", uri=True)
    row = conn.execute(
        "SELECT capabilities FROM ai_roles WHERE role_code = 'ROLE-Q03'"
    ).fetchone()
    conn.close()
    caps = row[0] if row else ""
    r.check(
        "R2 Q03 capabilities uses codes like content_generation",
        "content_generation" in caps,
        f"got {caps!r}",
    )


def test_r3_case_insensitive_routing(r: Results):
    """Round 3: English queries with capital letters route correctly (case-
    insensitive keyword matching)."""
    code, body = _request("POST", "/api/chat", {"message": "Research our competitors"})
    role = body.get("routing", {}).get("role_code", "")
    r.check(
        "R3 English capital-letter query routes correctly",
        role == "ROLE-Q02",
        f"'Research our competitors' → {role} (expected ROLE-Q02)",
    )


def test_r3_memory_append(r: Results):
    """Round 3: /api/memory/append writes to MEMORY.md."""
    code, body = _request("POST", "/api/memory/append", {
        "kind": "insight", "entry": "REGRESSION_TEST_DO_NOT_KEEP"
    })
    r.check("R3 /api/memory/append returns status=ok", body.get("status") == "ok",
            f"HTTP {code}, body {body}")
    # Verify it landed in the file
    text = (ROOT / "MEMORY.md").read_text(encoding="utf-8")
    r.check("R3 MEMORY.md received the entry", "REGRESSION_TEST_DO_NOT_KEEP" in text,
            "entry not found in file after append")
    # Cleanup the test entry
    if "REGRESSION_TEST_DO_NOT_KEEP" in text:
        import re
        text = re.sub(r"\*\*K\d+\*\* \(.+?\) — REGRESSION_TEST_DO_NOT_KEEP\n", "", text)
        (ROOT / "MEMORY.md").write_text(text, encoding="utf-8")


def test_r3_payload_hardening(r: Results):
    """Round 3: malformed JSON and empty body return HTTP 400, not crash."""
    # Malformed JSON
    req = urllib.request.Request(
        f"{BASE}/api/skills/execute",
        data=b"not json at all",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    code = 0
    try:
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        code = e.code
    r.check("R3 malformed JSON returns HTTP 400", code == 400, f"got {code}")


def test_r3_routing_accuracy(r: Results):
    """Round 3: routing accuracy should be ≥ 85% on the 20-query benchmark."""
    tests = [
        ("我今天壓力好大，想聊聊", "ROLE-Q07"),
        ("I'm feeling overwhelmed", "ROLE-Q07"),
        ("寫一篇關於 AI 的部落格文章", "ROLE-Q03"),
        ("Write a blog post about AI", "ROLE-Q03"),
        ("分析這份銷售數據找趨勢", "ROLE-Q04"),
        ("Analyze this sales data for trends", "ROLE-Q04"),
        ("審查這段代碼有無安全漏洞", "ROLE-Q06"),
        ("Audit this code for security bugs", "ROLE-Q06"),
        ("研究一下競爭對手的產品", "ROLE-Q02"),
        ("Research our competitors", "ROLE-Q02"),
        ("設計一個登入頁面的 UX", "ROLE-Q05"),
        ("Design UX for a login flow", "ROLE-Q05"),
        ("幫我設計系統架構", "ROLE-Q01"),
        ("Help me design the architecture", "ROLE-Q01"),
        ("我想學習如何成長為更好的工程師", "ROLE-Q08"),
        ("Help me grow as an engineer", "ROLE-Q08"),
        ("平台應該禁用這個功能嗎？", "ROLE-T01"),
        ("Should the platform ban this feature?", "ROLE-T01"),
        ("規劃下一季的技術演進路線", "ROLE-T04"),
        ("你好", "ROLE-Q01"),
    ]
    hits = 0
    for q, expected in tests:
        _, body = _request("POST", "/api/chat", {"message": q})
        if body.get("routing", {}).get("role_code") == expected:
            hits += 1
    ok = hits >= int(0.85 * len(tests))
    r.check(
        f"R3 routing accuracy ≥ 85% ({hits}/{len(tests)} = {100*hits/len(tests):.0f}%)",
        ok,
        "accuracy below 85% threshold",
    )


def test_r4_all_12_scenarios(r: Results):
    """Round 4: all 12 scenarios are registered and startable."""
    _, body = _request("GET", "/api/scenarios/list")
    scenarios = body.get("scenarios", [])
    r.check("R4 12 scenarios registered", len(scenarios) == 12,
            f"got {len(scenarios)}")


def test_r4_negotiate(r: Results):
    """Round 4: /api/negotiate returns structured multi-round dialog."""
    code, body = _request("POST", "/api/negotiate", {
        "topic": "Regression test topic", "max_rounds": 2,
    })
    r.check("R4 /api/negotiate returns HTTP 200", code == 200, f"got {code}")
    r.check("R4 /api/negotiate has rounds_completed",
            isinstance(body.get("rounds_completed"), int),
            f"got {body.get('rounds_completed')}")


def test_r5_session_isolation(r: Results):
    """Round 5: different session_ids don't leak context into each other."""
    # Session A, turn 1
    _request("POST", "/api/chat", {"message": "電商網站規劃", "session_id": "rt-A"})
    # Session B, turn 1
    _request("POST", "/api/chat", {"message": "安全審計清單", "session_id": "rt-B"})
    # Session A, turn 2 — preamble (if any) should NOT reference 安全審計
    _, body = _request("POST", "/api/chat", {"message": "前端框架", "session_id": "rt-A"})
    resp = body.get("response", "")
    leak = "安全審計" in resp[:200] or "安全审计" in resp[:200]
    r.check("R5 session A doesn't see session B's topic", not leak,
            f"leaked content: {resp[:200]!r}")


def test_r5_default_loopback_bind(r: Results):
    """Round 5: default bind is 127.0.0.1, not 0.0.0.0."""
    src = (ROOT / "api_server.py").read_text(encoding="utf-8")
    r.check("R5 default --host is 127.0.0.1",
            'default="127.0.0.1"' in src,
            "default host is not 127.0.0.1")


def test_r5_db_fallback_in_status(r: Results):
    """Round 5: run.py --status uses 3-candidate DB fallback."""
    src = (ROOT / "run.py").read_text(encoding="utf-8")
    r.check("R5 status uses platform_restored fallback",
            "platform_restored.db" in src,
            "fallback not wired into status check")


# ────────────────────────────────────────────────────────────────
# Runner
# ────────────────────────────────────────────────────────────────
def main() -> int:
    print("=" * 60)
    print("  Q-SpecTrum Regression Test Suite")
    print("=" * 60)

    # First, the DB + source-code tests that don't need a server
    print("\n── Static checks (no server) ──")
    r = Results()
    test_r1_missing_tables(r)
    test_r1_virtiofs_fix(r)
    test_r2_capability_codes(r)
    test_r5_default_loopback_bind(r)
    test_r5_db_fallback_in_status(r)

    # Then check if server is already running; if not, print instructions
    print("\n── Server-dependent checks ──")
    if not wait_server(timeout=3):
        print("  ⚠  Server not running on port 8765.")
        print("     Start it in another terminal: python run.py --web")
        print("     Then re-run this script.")
        r.check("Server reachable on :8765", False, "start `python run.py --web` first")
        return 0 if r.summary() else 1

    test_r3_case_insensitive_routing(r)
    test_r3_memory_append(r)
    test_r3_payload_hardening(r)
    test_r3_routing_accuracy(r)
    test_r4_all_12_scenarios(r)
    test_r4_negotiate(r)
    test_r5_session_isolation(r)

    return 0 if r.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
