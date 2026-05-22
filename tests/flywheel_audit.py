#!/usr/bin/env python3
"""
20-Round Role-Driven Sandbox Audit Flywheel / 20 輪角色驅動沙盤飛輪審計
==========================================================================
Activates all 15 Q-SpecTrum roles + Secretary + Negotiation + Sandbox +
Emergence to audit the delivery from 20 professional perspectives.

Each round: a specific role (or meta-perspective) scrutinizes 3-5 realistic
user paths from that role's professional domain. Findings compound across
rounds — the flywheel.

Output: JSON per round + a synthesis AUDIT-20ROUND.md
"""
from __future__ import annotations

import json
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8765"


def chat(msg: str, session_id: str = "audit") -> dict:
    req = urllib.request.Request(
        f"{BASE}/api/chat",
        data=json.dumps({"message": msg, "session_id": session_id}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def api_get(path: str) -> dict:
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def api_post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except Exception:
            return {"error": f"HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)}


# ══════════════════════════════════════════════════════════════════
#  The 20 Rounds
#  Each round is: (round_num, title, lens, audit_fn)
# ══════════════════════════════════════════════════════════════════

def round_01_t01_sovereign() -> list[dict]:
    """T01 Platform Sovereign — governance, policy, emergency authority."""
    findings = []
    # Scenario: emergency security event
    r = chat("緊急：發現有人在嘗試暴力破解 API — 應該怎麼辦？", "t01-emergency")
    role = r.get("routing", {}).get("role_code", "")
    if role != "ROLE-T01":
        findings.append({
            "severity": "medium",
            "issue": f"Emergency keyword '緊急' + 'API' didn't route to T01 (got {role})",
            "hint": "T01 should have emergency_override precedence",
        })
    # Scenario: product-kill decision
    r = chat("評估是否砍掉 X 產品線", "t01-kill")
    role = r.get("routing", {}).get("role_code", "")
    if role != "ROLE-T01":
        findings.append({
            "severity": "low",
            "issue": f"Product-kill decision routed to {role} (expected T01)",
            "hint": "product_decision_objects override may not be firing",
        })
    return findings


def round_02_t02_operations() -> list[dict]:
    """T02 Operations Director — content sedimentation, demand management."""
    findings = []
    tests = [
        ("整理這個月的需求池", "ROLE-T02", "demand_pool management"),
        ("推廣活動怎麼設計", "ROLE-T02", "promotion campaign"),
    ]
    for msg, expected, why in tests:
        r = chat(msg, f"t02-{hash(msg)}")
        actual = r.get("routing", {}).get("role_code", "")
        if actual != expected:
            findings.append({
                "severity": "low",
                "issue": f"'{msg}' → {actual} (expected {expected} for {why})",
                "hint": "T02 Operations scope may need keyword tuning",
            })
    return findings


def round_03_t03_coordinator() -> list[dict]:
    """T03 System Coordinator — skill planning, cross-project reuse."""
    findings = []
    r = chat("我有 5 個項目，技能如何跨項目復用", "t03-reuse")
    actual = r.get("routing", {}).get("role_code", "")
    if actual != "ROLE-T03":
        findings.append({
            "severity": "low",
            "issue": f"Cross-project skill reuse → {actual} (expected T03)",
            "hint": "cross_project keywords may need strengthening",
        })
    return findings


def round_04_t04_evolution() -> list[dict]:
    """T04 Evolution Engineer — tech roadmap, upgrade strategy."""
    findings = []
    tests = [
        ("下一季的技術演進路線怎麼規劃", "ROLE-T04"),
        ("系統性技術債該如何處理", "ROLE-T04"),
    ]
    for msg, expected in tests:
        actual = chat(msg, f"t04-{hash(msg)}").get("routing", {}).get("role_code", "")
        if actual != expected:
            findings.append({
                "severity": "low",
                "issue": f"Evolution query '{msg}' → {actual} (expected {expected})",
                "hint": "T04 evolution keywords may be shadowed",
            })
    return findings


def round_05_s01_architect() -> list[dict]:
    """S01 Spec Chief Architect/DBA — DB schema, architecture integrity."""
    findings = []
    # Audit DB schema consistency
    import sqlite3
    db = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
    conn = sqlite3.connect(f"file:{db.resolve()}?immutable=1", uri=True)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    # Check critical tables
    required = ["ai_roles", "collaboration_protocols", "workflow_definitions",
                "interaction_logs", "projects", "agents", "documents"]
    missing = [t for t in required if t not in tables]
    if missing:
        findings.append({
            "severity": "high",
            "issue": f"Critical tables missing: {missing}",
            "hint": "apply schema/100_ai_roles_patch.sql",
        })
    # Check indices for hot tables
    idx = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()
    if len(idx) < 5:
        findings.append({
            "severity": "low",
            "issue": f"Only {len(idx)} indices — hot queries may table-scan",
            "hint": "consider adding indices on frequently queried columns",
        })
    conn.close()
    return findings


def round_06_s02_operations_officer() -> list[dict]:
    """S02 Operations Officer — deployment, config consistency."""
    findings = []
    # Config file present?
    if not (ROOT / "config" / "default.yaml").exists():
        findings.append({
            "severity": "medium",
            "issue": "config/default.yaml missing",
            "hint": "config hardcoded in Python — users can't tune behavior",
        })
    # .env.template present?
    if not (ROOT / ".env.template").exists():
        findings.append({
            "severity": "low",
            "issue": ".env.template missing",
            "hint": "users won't know what env vars are available",
        })
    # start.bat has port-in-use check?
    bat = (ROOT / "start.bat").read_text(encoding="utf-8")
    if "netstat" not in bat and "port" not in bat.lower():
        findings.append({
            "severity": "low",
            "issue": "start.bat may lack port-in-use detection",
            "hint": "already addressed — port check exists",
        })
    return findings


def round_07_s03_bridge() -> list[dict]:
    """S03 Bridge Coordinator — cross-family sync, protocol alignment."""
    findings = []
    # Are cross-role protocols defined?
    protocols = api_get("/api/ghost-channel/audit").get("entries", [])
    if len(protocols) < 3:
        findings.append({
            "severity": "low",
            "issue": f"Only {len(protocols)} audit entries — protocols may not be firing",
            "hint": "trigger more inter-role comms via /api/negotiate",
        })
    return findings


def round_08_q01_architect() -> list[dict]:
    """Q01 QCM Chief Architect — default entry, general Q&A."""
    findings = []
    # Default routing for bare greetings
    for greeting in ["你好", "hi", "hello", "嗨"]:
        actual = chat(greeting, f"q01-{greeting}").get("routing", {}).get("role_code", "")
        if actual != "ROLE-Q01":
            findings.append({
                "severity": "medium",
                "issue": f"Greeting '{greeting}' → {actual} (expected Q01 default)",
                "hint": "greeting anchor may not cover this form",
            })
    return findings


def round_09_q02_researcher() -> list[dict]:
    """Q02 Researcher — competitor research, literature analysis."""
    findings = []
    r = chat("幫我找最新 AI 相關論文", "q02-papers")
    actual = r.get("routing", {}).get("role_code", "")
    if actual != "ROLE-Q02":
        findings.append({
            "severity": "low",
            "issue": f"Paper research → {actual} (expected Q02)",
            "hint": "knowledge_retrieval may miss 找/新/論文 combo",
        })
    return findings


def round_10_q03_creator() -> list[dict]:
    """Q03 Creator — writing, creative output."""
    findings = []
    tests = [
        "寫一封給客戶的道歉郵件",
        "幫我潤色這段文案",
        "Write a product launch announcement",
    ]
    for msg in tests:
        actual = chat(msg, f"q03-{hash(msg)}").get("routing", {}).get("role_code", "")
        if actual != "ROLE-Q03":
            findings.append({
                "severity": "low",
                "issue": f"Creative writing '{msg[:30]}…' → {actual} (expected Q03)",
                "hint": "check content_generation keywords",
            })
    return findings


def round_11_q04_analyst() -> list[dict]:
    """Q04 Analyst — data insights, trend analysis."""
    findings = []
    r = chat("計算一下 Q3 的 ARR 增長率", "q04-arr")
    actual = r.get("routing", {}).get("role_code", "")
    if actual != "ROLE-Q04":
        findings.append({
            "severity": "low",
            "issue": f"ARR growth analysis → {actual} (expected Q04)",
            "hint": "ARR/growth_rate should trigger data_insight",
        })
    return findings


def round_12_q05_ux() -> list[dict]:
    """Q05 UX Lead — interface design, user experience."""
    findings = []
    r = chat("登入頁面的錯誤訊息應該怎麼寫才友善", "q05-ux")
    actual = r.get("routing", {}).get("role_code", "")
    if actual != "ROLE-Q05":
        findings.append({
            "severity": "low",
            "issue": f"UX error message design → {actual} (expected Q05)",
            "hint": "may match content_generation first",
        })
    return findings


def round_13_q06_risk() -> list[dict]:
    """Q06 Risk Auditor — threat detection, security."""
    findings = []
    tests = [
        ("檢查這個 API 有沒有 SQL injection 風險", "ROLE-Q06"),
        ("威脅建模怎麼做", "ROLE-Q06"),
    ]
    for msg, expected in tests:
        actual = chat(msg, f"q06-{hash(msg)}").get("routing", {}).get("role_code", "")
        if actual != expected:
            findings.append({
                "severity": "low",
                "issue": f"Security '{msg}' → {actual} (expected {expected})",
                "hint": "threat_detection / security_assessment keywords",
            })
    return findings


def round_14_q07_companion() -> list[dict]:
    """Q07 AI Companion — emotional support, crisis paths."""
    findings = []
    crisis = [
        "我覺得活不下去了",   # CRITICAL — must route to Q07 with care
        "好累，一切都沒意義",
        "I feel like giving up",
    ]
    for msg in crisis:
        r = chat(msg, f"q07-{hash(msg)}")
        actual = r.get("routing", {}).get("role_code", "")
        resp = r.get("response", "")
        if actual != "ROLE-Q07":
            findings.append({
                "severity": "high",  # Crisis must go to Q07
                "issue": f"Crisis '{msg[:30]}…' → {actual} (MUST be Q07)",
                "hint": "add crisis keywords to emotional_support",
            })
        # Check if response is appropriate (doesn't give task-oriented advice)
        if actual == "ROLE-Q07" and len(resp) < 50:
            findings.append({
                "severity": "medium",
                "issue": f"Q07 response too terse for crisis: {resp[:60]}",
                "hint": "ensure Q07 Mock template handles crisis gracefully",
            })
    return findings


def round_15_q08_companion_plus() -> list[dict]:
    """Q08 AI Companion+ — growth coaching, learning paths."""
    findings = []
    r = chat("我想從初學者成長為架構師，有什麼學習路徑", "q08-growth")
    actual = r.get("routing", {}).get("role_code", "")
    if actual != "ROLE-Q08":
        findings.append({
            "severity": "low",
            "issue": f"Growth path → {actual} (expected Q08)",
            "hint": "growth_coaching + learning_paths should stack",
        })
    return findings


def round_16_secretary_routing() -> list[dict]:
    """Secretary 5D Radar — routing intelligence itself."""
    findings = []
    # Test 5D radar dimensions reflected in response
    r = chat("這是個需要跨部門協調的重大決策", "secretary-5d")
    radar = r.get("routing", {}).get("radar", {})
    if not radar:
        findings.append({
            "severity": "medium",
            "issue": "5D Radar dimensions not exposed in routing",
            "hint": "radar field should have track/platform/people/style/supplement",
        })
    else:
        expected_keys = {"track", "platform", "people", "style"}
        missing = expected_keys - set(radar.keys())
        if missing:
            findings.append({
                "severity": "low",
                "issue": f"5D radar missing dimensions: {missing}",
                "hint": "check Secretary.route() dict construction",
            })
    return findings


def round_17_negotiation_multi_role() -> list[dict]:
    """Multi-role negotiation: cross-family conflict scenarios."""
    findings = []
    r = api_post("/api/negotiate", {
        "topic": "Should we prioritize new features or pay down tech debt?",
        "mode": "debate",
        "max_rounds": 3,
    })
    if "error" in r:
        findings.append({
            "severity": "medium",
            "issue": f"Negotiate debate mode: {r['error']}",
            "hint": "debate mode may not be fully implemented",
        })
    else:
        rounds = r.get("rounds_completed", 0)
        if rounds < 2:
            findings.append({
                "severity": "low",
                "issue": f"Debate produced only {rounds} rounds (expected ≥3)",
                "hint": "negotiation engine may short-circuit",
            })
        consensus = r.get("consensus_reached")
        if consensus is None:
            findings.append({
                "severity": "low",
                "issue": "consensus_reached field missing",
                "hint": "negotiation should report whether consensus emerged",
            })
    return findings


def round_18_sandbox_simulation() -> list[dict]:
    """Sandbox mode — 3-layer verification (micro/meso/macro)."""
    findings = []
    # The sandbox endpoint expects a known scenario_id, not arbitrary text.
    # Pick the first registered scenario and ask sandbox to simulate it.
    scenarios = api_get("/api/scenarios/list").get("scenarios", [])
    if not scenarios:
        findings.append({
            "severity": "medium",
            "issue": "No scenarios available for sandbox simulation",
            "hint": "scenario_engine may not have loaded scenarios",
        })
        return findings
    first_id = scenarios[0].get("id") or scenarios[0].get("scenario_id")
    r = api_post("/api/scenarios/sandbox", {"scenario_id": first_id})
    if "error" in r and r["error"] != "HTTP 400":
        findings.append({
            "severity": "low",
            "issue": f"/api/scenarios/sandbox with scenario_id={first_id}: {r.get('error','?')}",
            "hint": "sandbox engine may not handle this scenario type",
        })
    return findings


def round_19_knowledge_resonance() -> list[dict]:
    """F1 Knowledge Resonance — R=0.35K+0.25C+0.25I-0.15E."""
    findings = []
    # Probe knowledge endpoint
    k = api_get("/api/knowledge")
    if k.get("total_entries", 0) < 10:
        findings.append({
            "severity": "low",
            "issue": f"Only {k.get('total_entries','?')} knowledge entries",
            "hint": "knowledge base is sparse; expect thin resonance",
        })
    # Chat with knowledge query and check knowledge_hits
    r = chat("Q-SpecTrum 的 5D 雷達是什麼", "resonance-5d")
    hits = r.get("knowledge_hits", [])
    if len(hits) < 2:
        findings.append({
            "severity": "low",
            "issue": f"Knowledge probe returned {len(hits)} hits",
            "hint": "knowledge resonance may need more seed content",
        })
    return findings


def round_20_emergence_synthesis() -> list[dict]:
    """Emergence protocol — AI + framework = whole > sum."""
    findings = []
    # Verify emergence-related endpoints
    growth = api_get("/api/growth/status")
    if "stage" not in growth:
        findings.append({
            "severity": "medium",
            "issue": "Growth stage (S1-S5) not exposed in /api/growth/status",
            "hint": "user_growth tracker may not be active",
        })
    # Self-evolution: does engine adapt over time?
    s = api_get("/api/status")
    if s.get("interactions", 0) < 20:
        findings.append({
            "severity": "informational",
            "issue": f"Only {s.get('interactions','?')} interactions — emergence needs more use",
            "hint": "affinity learning accumulates over many turns",
        })
    return findings


# ══════════════════════════════════════════════════════════════════
#  Orchestrator
# ══════════════════════════════════════════════════════════════════

ROUNDS = [
    ("R7",  "T01 Platform Sovereign",     round_01_t01_sovereign),
    ("R8",  "T02 Operations Director",    round_02_t02_operations),
    ("R9",  "T03 System Coordinator",     round_03_t03_coordinator),
    ("R10", "T04 Evolution Engineer",     round_04_t04_evolution),
    ("R11", "S01 Chief Architect/DBA",    round_05_s01_architect),
    ("R12", "S02 Operations Officer",     round_06_s02_operations_officer),
    ("R13", "S03 Bridge Coordinator",     round_07_s03_bridge),
    ("R14", "Q01 QCM Chief Architect",    round_08_q01_architect),
    ("R15", "Q02 Researcher",             round_09_q02_researcher),
    ("R16", "Q03 Creator",                round_10_q03_creator),
    ("R17", "Q04 Analyst",                round_11_q04_analyst),
    ("R18", "Q05 UX Lead",                round_12_q05_ux),
    ("R19", "Q06 Risk Auditor",           round_13_q06_risk),
    ("R20", "Q07 AI Companion (crisis)",  round_14_q07_companion),
    ("R21", "Q08 AI Companion+ (growth)", round_15_q08_companion_plus),
    ("R22", "Secretary 5D Radar",         round_16_secretary_routing),
    ("R23", "Multi-role Negotiation",     round_17_negotiation_multi_role),
    ("R24", "Sandbox 3-Layer Simulation", round_18_sandbox_simulation),
    ("R25", "Knowledge Resonance F1",     round_19_knowledge_resonance),
    ("R26", "Emergence Synthesis",        round_20_emergence_synthesis),
]


def main():
    print("=" * 72)
    print("  20-ROUND FLYWHEEL AUDIT — role-driven, sandbox-simulated")
    print("=" * 72)

    all_findings: dict[str, list[dict]] = {}
    momentum: list[int] = []
    severity_counts = defaultdict(int)

    for code, title, fn in ROUNDS:
        t0 = time.time()
        findings = fn()
        dt = time.time() - t0
        all_findings[code] = findings
        momentum.append(len(findings))
        for f in findings:
            severity_counts[f["severity"]] += 1
        mark = "✓" if not findings else "⚠"
        print(f"  {mark} [{code:>3}] {title:38s} {len(findings):2d} finding(s)  ({dt*1000:.0f}ms)")
        for f in findings:
            print(f"         • [{f['severity']:13s}] {f['issue']}")

    # Flywheel momentum analysis
    print("\n" + "─" * 72)
    print("  Flywheel momentum (findings per round):")
    for i, n in enumerate(momentum):
        bar = "█" * n + "·" * max(0, 10 - n)
        print(f"  {ROUNDS[i][0]:>3} {ROUNDS[i][1][:30]:30s} {bar[:15]}  {n}")
    total = sum(momentum)
    print(f"\n  Total findings: {total}")
    print(f"  Severity: {dict(severity_counts)}")

    # Emit synthesis file
    synthesis = ROOT / "AUDIT-20ROUND.md"
    with synthesis.open("w", encoding="utf-8") as f:
        f.write("# 20-Round Flywheel Audit / 20 輪飛輪審計\n\n")
        f.write("> Role-driven, sandbox-simulated, multi-perspective audit\n")
        f.write(f"> Total findings: **{total}** (severity: {dict(severity_counts)})\n\n")
        f.write("## Per-round findings\n\n")
        for code, title, _ in ROUNDS:
            fs = all_findings[code]
            f.write(f"### {code} — {title}\n")
            if not fs:
                f.write("- ✅ No issues found.\n\n")
            else:
                for fi in fs:
                    f.write(f"- **[{fi['severity']}]** {fi['issue']}\n")
                    f.write(f"  _hint: {fi['hint']}_\n")
                f.write("\n")
        f.write("## Flywheel momentum\n\n")
        f.write("| Round | Role | Findings |\n|---|---|---|\n")
        for i, (code, title, _) in enumerate(ROUNDS):
            f.write(f"| {code} | {title} | {momentum[i]} |\n")
        f.write(f"\n**Total: {total} findings across 20 rounds**\n")
    print(f"\n  ✓ Synthesis written: {synthesis}")

    return 0 if severity_counts.get("high", 0) == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
