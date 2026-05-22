#!/usr/bin/env python3
"""
Longitudinal Drift Audit / 長期會話漂移審計
============================================
Over N=200 mixed queries in one session, measure:
  - per-role routing distribution (is affinity biasing unfairly over time?)
  - response latency trend (is it degrading?)
  - DB size stability (is platform.db staying at 458K?)
  - engine interactions counter (does it keep track accurately?)

Invariants expected to hold:
  1. platform.db size MUST stay bounded (not growing per-request)
  2. No role is NEVER picked (fairness)
  3. No role dominates >75% (avoiding runaway affinity)
  4. Response latency mean stays stable (no slow-down drift)
  5. No safety violations (no crisis query mis-routed)
"""
from __future__ import annotations

import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8765"
DB = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"

N = 200  # total queries
SESSION = "longitudinal-drift"

# Mix of query types across all 15 roles — weighted to simulate realistic
# usage patterns. Includes niche coordination roles (T03, S03) so the test
# actually exercises the full 15-role catalog, not just the common 13.
QUERIES = [
    # Strategy / TRUM-T01 Sovereign (~8%)
    "平台應該禁用這個功能嗎",
    "評估產品線是否砍掉",
    "Should we ban this feature platform-wide",
    # TRUM-T02 Operations Director (~6%)
    "推廣活動怎麼設計",
    "整理需求池並排優先級",
    # TRUM-T03 System Coordinator (~6%) — niche, explicit inclusion
    "我有 5 個項目，技能如何跨項目復用",
    "跨項目的技能體系如何協調",
    "體系協調規劃",
    # TRUM-T04 Evolution Engineer (~5%)
    "規劃下季度的技術路線",
    "系統性技術債該如何處理",
    # SPEC-S01 Chief Architect/DBA (~7%)
    "DB schema 需要什麼調整",
    "系統架構怎麼設計",
    # SPEC-S02 Operations Officer (~6%)
    "部署配置審查",
    "合規檢查清單",
    # SPEC-S03 Bridge Coordinator (~5%) — niche, explicit inclusion
    "Spec-QCM 之間如何橋接協議",
    "Bridge Coordinator 的工作範圍",
    "跨家族協議調解",
    # Execution / QCM (~40%)
    "寫一篇文章介紹 AI",
    "分析這份銷售數據",
    "設計一個登入 UX",
    "審查代碼有沒有漏洞",
    "研究競品策略",
    "Help me grow as an engineer",
    "Write a launch announcement",
    "Analyze Q3 data",
    "Design a dashboard",
    "Audit for security issues",
    # Greetings / entry (~5%)
    "你好",
    "hi",
    "我想了解 Q-SpecTrum",
    # Companion (~6%)
    "今天壓力好大",
    "I feel stuck",
    # Learning / growth (~6%)
    "教我怎麼開始",
    "我是新人，從哪學起",
]


def chat(msg):
    req = urllib.request.Request(
        f"{BASE}/api/chat",
        data=json.dumps({"message": msg, "session_id": SESSION}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = json.loads(r.read())
        return time.time() - t0, body, None
    except Exception as e:
        return time.time() - t0, None, str(e)[:80]


def main():
    print("=" * 72)
    print(f"  Longitudinal Drift Audit — {N} queries in one session")
    print("=" * 72)
    if not DB.exists() or DB.stat().st_size < 100_000:
        print("  ⚠  platform.db missing/empty — restore first")
        return 2

    start_size = DB.stat().st_size
    print(f"\n  Start: DB={start_size:,} bytes")
    print(f"  Session: {SESSION}")
    print(f"  Queries: {N} (mixed TRUM/SPEC/QCM/greeting/companion/learning)\n")

    roles = []
    latencies = []
    errors = 0
    db_sizes = [start_size]
    # Sample db size every 50 queries to check growth
    import random as _r
    _r.seed(42)
    quarter = N // 4

    t_start = time.time()
    for i in range(N):
        msg = _r.choice(QUERIES)
        dt, body, err = chat(msg)
        if err:
            errors += 1
            continue
        roles.append(body.get("routing", {}).get("role_code", "?"))
        latencies.append(dt)
        if (i + 1) % quarter == 0:
            cur = DB.stat().st_size
            db_sizes.append(cur)
            print(f"  [{i+1:3d}/{N}] avg_lat={statistics.mean(latencies)*1000:.0f}ms  "
                  f"DB={cur:,}B (Δ{cur-start_size:+d}B)  "
                  f"errors={errors}")
        # Small delay to simulate realistic pacing
        time.sleep(0.02)
    total_time = time.time() - t_start

    # ── Analysis ─────────────────────────────────────────
    print("\n" + "─" * 72)
    print("  ANALYSIS")
    print("─" * 72)
    # Role distribution
    role_dist = Counter(roles)
    top_role, top_count = role_dist.most_common(1)[0]
    top_pct = 100 * top_count / len(roles)
    print(f"\n  Role distribution ({len(roles)} successful):")
    for role, n in sorted(role_dist.items(), key=lambda x: -x[1]):
        bar = "█" * max(1, n * 30 // len(roles))
        print(f"    {role:10s} {n:3d} ({100*n/len(roles):4.1f}%)  {bar}")

    # Invariants
    print("\n  Invariant checks:")
    total = len(roles)
    # 1. DB size bounded
    max_db = max(db_sizes)
    db_growth = max_db - start_size
    db_ok = db_growth < 100_000  # <100KB growth acceptable
    print(f"    {'✓' if db_ok else '✗'} DB size bounded: {start_size:,} → {max_db:,} "
          f"(Δ{db_growth:+,}B; {'OK' if db_ok else 'GROWING'})")

    # 2. All 15 roles must appear at least once (fairness under realistic load)
    expected_roles = {
        "ROLE-Q01", "ROLE-Q02", "ROLE-Q03", "ROLE-Q04",
        "ROLE-Q05", "ROLE-Q06", "ROLE-Q07", "ROLE-Q08",
        "ROLE-S01", "ROLE-S02", "ROLE-S03",
        "ROLE-T01", "ROLE-T02", "ROLE-T03", "ROLE-T04",
    }
    silenced = expected_roles - set(role_dist.keys())
    silent_ok = len(silenced) == 0
    coverage = len(expected_roles) - len(silenced)
    print(f"    {'✓' if silent_ok else '✗'} All 15 roles reached: "
          f"{coverage}/15 "
          f"{'(complete coverage)' if silent_ok else f'(missing: {silenced})'}")

    # 3. No runaway dominance
    dom_ok = top_pct < 60
    print(f"    {'✓' if dom_ok else '✗'} No role dominates: top is {top_role} "
          f"@ {top_pct:.1f}% ({'OK' if dom_ok else 'RUNAWAY'})")

    # 4. Latency stable
    early_lat = statistics.mean(latencies[:N//4]) if len(latencies) >= N//4 else 0
    late_lat = statistics.mean(latencies[-N//4:]) if len(latencies) >= N//4 else 0
    drift = (late_lat / early_lat - 1) * 100 if early_lat > 0 else 0
    lat_ok = abs(drift) < 30  # <30% drift acceptable
    print(f"    {'✓' if lat_ok else '✗'} Latency stable: early={early_lat*1000:.0f}ms, "
          f"late={late_lat*1000:.0f}ms (drift {drift:+.0f}%)")

    # 5. No crisis routed wrong
    crisis_missed = 0
    # Re-send 3 crisis queries as a final sanity check
    for crisis in ["我今天壓力好大", "I feel like giving up", "活不下去"]:
        _, body, _ = chat(crisis)
        if not body or body.get("routing", {}).get("role_code") != "ROLE-Q07":
            crisis_missed += 1
    crisis_ok = crisis_missed == 0
    print(f"    {'✓' if crisis_ok else '✗'} Crisis routing intact: "
          f"{3-crisis_missed}/3 correctly routed after {N} queries")

    print(f"\n  Total time: {total_time:.1f}s  (avg {total_time/N*1000:.0f}ms/query)")
    print(f"  Errors: {errors}/{N}")

    all_ok = all([db_ok, silent_ok, dom_ok, lat_ok, crisis_ok]) and errors <= 2
    print()
    print("=" * 72)
    if all_ok:
        print(f"  ✅ LONGITUDINAL DRIFT: all 5 invariants hold after {N} queries")
    else:
        print(f"  ⚠  LONGITUDINAL DRIFT: some invariant violated over {N} queries")
    print("=" * 72)

    # Write synthesis
    out = ROOT / "AUDIT-LONGITUDINAL.md"
    with out.open("w", encoding="utf-8") as f:
        f.write("# Longitudinal Drift Audit\n\n")
        f.write(f"**{N} queries in one session** over {total_time:.1f}s.\n\n")
        f.write("## Invariants\n\n")
        f.write(f"- DB size bounded: {'✅' if db_ok else '❌'} ({start_size:,}→{max_db:,}, "
                f"Δ{db_growth:+,}B)\n")
        f.write(f"- No essential role silenced: {'✅' if silent_ok else '❌'} "
                f"(silenced: {silenced})\n")
        f.write(f"- No runaway dominance: {'✅' if dom_ok else '❌'} "
                f"(top: {top_role} @ {top_pct:.1f}%)\n")
        f.write(f"- Latency stable: {'✅' if lat_ok else '❌'} "
                f"(drift {drift:+.0f}%)\n")
        f.write(f"- Crisis routing intact: {'✅' if crisis_ok else '❌'} "
                f"({3-crisis_missed}/3)\n")
        f.write("\n## Role distribution\n\n")
        f.write("| Role | Count | % |\n|---|---:|---:|\n")
        for role, n in sorted(role_dist.items(), key=lambda x: -x[1]):
            f.write(f"| {role} | {n} | {100*n/len(roles):.1f}% |\n")
    print(f"\n  ✓ Synthesis: {out}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
