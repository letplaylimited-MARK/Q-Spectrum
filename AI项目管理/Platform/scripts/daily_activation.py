#!/usr/bin/env python3
"""
Q-SpecTrum 每日激活 + 記憶傳承腳本 v1.0
Daily Activation & Memory Inheritance Protocol

功能：
  1. 讀取 _HANDOFF/ 交接文件，生成記憶摘要（Context Briefing）
  2. 執行系統健康檢查（調用 system_health_check.py）
  3. 掃描最新 Session 記錄，提取未完成任務
  4. 生成「每日激活報告」供新對話使用
  5. 追加到 _HANDOFF/ACTIVATION-LOG.md 形成歷史鏈

設計原則：
  - 每次新對話開啟時，AI 讀取最新的激活報告即可快速恢復上下文
  - 激活報告包含：系統健康狀態 + 記憶摘要 + 待辦事項 + 建議行動
  - 報告格式精簡，控制在 200 行以內，避免消耗 context window

用法：
    python daily_activation.py                    # 生成當日激活報告
    python daily_activation.py --check-only       # 只執行健康檢查不生成報告
    python daily_activation.py --json             # JSON 格式輸出
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ── 路徑設置 ──────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PLATFORM_DIR = SCRIPT_DIR.parent
AI_DIR = PLATFORM_DIR.parent
PROJECT_ROOT = AI_DIR.parent  # Q-SpecTrum(TEST)/

HANDOFF_DIR = PROJECT_ROOT / "_HANDOFF"
SESSIONS_DIR = HANDOFF_DIR / "sessions"
REPORTS_DIR = HANDOFF_DIR / "reports"


def read_file_safe(path, max_lines=None):
    """安全讀取文件，返回內容字串"""
    try:
        text = path.read_text(encoding="utf-8")
        if max_lines:
            lines = text.split("\n")
            return "\n".join(lines[:max_lines])
        return text
    except Exception:
        return ""


def extract_latest_sessions(max_count=3):
    """從 TASK-INDEX.md 提取最近的 Session 記錄"""
    index_path = HANDOFF_DIR / "TASK-INDEX.md"
    if not index_path.exists():
        return []

    content = read_file_safe(index_path)
    # Parse the table rows (skip header)
    sessions = []
    for line in content.split("\n"):
        if line.startswith("|") and "---" not in line and "Timestamp" not in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4:
                sessions.append({
                    "timestamp": parts[0],
                    "session": parts[1],
                    "action": parts[2],
                    "tasks": parts[3],
                    "notes": parts[4] if len(parts) > 4 else ""
                })

    return sessions[:max_count]


def extract_pending_tasks():
    """從 STATUS.md 提取未完成任務"""
    pending = {"p0": [], "p1": [], "p2": []}

    for filename in ["STATUS.md"]:
        path = HANDOFF_DIR / filename
        if not path.exists():
            continue

        content = read_file_safe(path)
        current_priority = None

        for line in content.split("\n"):
            if "P0" in line and ("串聯" in line or "核心" in line):
                current_priority = "p0"
            elif "P1" in line and ("交付" in line or "最終" in line):
                current_priority = "p1"
            elif "P2" in line:
                current_priority = "p2"
            elif line.strip().startswith("- [ ]") and current_priority:
                task = line.strip().replace("- [ ] ", "").strip()
                # Remove bold markers
                task = re.sub(r'\*\*(.+?)\*\*', r'\1', task)
                # Dedup by task key (text before first colon)
                task_key = task.split(":")[0].strip() if ":" in task else task
                all_existing_keys = []
                for pl in pending.values():
                    all_existing_keys.extend(t.split(":")[0].strip() for t in pl)
                if task and task_key not in all_existing_keys:
                    pending[current_priority].append(task)

    return pending


def extract_system_overview():
    """從 STATUS.md 提取系統概覽"""
    path = HANDOFF_DIR / "STATUS.md"
    if not path.exists():
        return {}

    content = read_file_safe(path)

    # Extract key metrics from the overview table
    overview = {}
    for line in content.split("\n"):
        if "整體成熟度" in line:
            match = re.search(r'(\d+\.?\d*/10)', line)
            if match:
                overview["maturity"] = match.group(1)
        elif "v1.0 就緒度" in line:
            match = re.search(r'~?(\d+)%', line)
            if match:
                overview["readiness"] = f"{match.group(1)}%"
        elif "E2E 測試" in line:
            match = re.search(r'(\d+/\d+)', line)
            if match:
                overview["e2e_tests"] = match.group(1)
        elif "DB" in line and "表" in line:
            match = re.search(r'(\d+)表/(\d+)行', line)
            if match:
                overview["db_tables"] = match.group(1)
                overview["db_rows"] = match.group(2)

    return overview


def run_health_check():
    """調用 system_health_check.py 獲取健康報告"""
    try:
        # Import and run directly
        sys.path.insert(0, str(SCRIPT_DIR))
        import system_health_check as shc
        return shc.run_all_checks()
    except Exception as e:
        return {"overall_health": -1, "error": str(e), "sections": {}, "warnings": [], "errors": [str(e)]}


def generate_activation_report():
    """生成完整的每日激活報告"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    # 1. Run health check
    health = run_health_check()

    # 2. Extract memory context
    recent_sessions = extract_latest_sessions(5)
    pending_tasks = extract_pending_tasks()
    overview = extract_system_overview()

    # 3. Build activation report
    report = {
        "activation_date": date_str,
        "activation_time": time_str,
        "system_health": health["overall_health"],
        "overview": overview,
        "recent_sessions": recent_sessions,
        "pending_tasks": pending_tasks,
        "warnings": health.get("warnings", []),
        "errors": health.get("errors", []),
        "section_scores": {
            name: {"score": data["score"], "status": data["status"]}
            for name, data in health.get("sections", {}).items()
        }
    }

    # 4. Generate Markdown
    md_lines = [
        "# Q-SpecTrum 每日激活報告",
        "",
        f"> **日期**: {date_str} {time_str}",
        f"> **系統健康度**: {health['overall_health']}%",
        "> **用途**: 新對話開始時讀取此文件快速恢復上下文",
        "",
        "---",
        "",
        "## 1. 系統狀態快照",
        "",
    ]

    # Overview
    if overview:
        md_lines.append("| 指標 | 值 |")
        md_lines.append("|------|-----|")
        for k, v in overview.items():
            label = {"maturity": "整體成熟度", "readiness": "v1.0 就緒度", "e2e_tests": "E2E 測試", "db_tables": "DB 表數", "db_rows": "DB 行數"}.get(k, k)
            md_lines.append(f"| {label} | {v} |")
        md_lines.append("")

    # Section scores
    md_lines.append("### 健康檢查各段落")
    md_lines.append("")
    md_lines.append("| 段落 | 分數 | 狀態 |")
    md_lines.append("|------|------|------|")
    for name, data in report["section_scores"].items():
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(data["status"], "?")
        md_lines.append(f"| {name} | {data['score']}/100 | {icon} {data['status']} |")
    md_lines.append("")

    # Warnings & errors
    if report["warnings"] or report["errors"]:
        md_lines.append("### 需要關注")
        md_lines.append("")
        for w in report["warnings"]:
            md_lines.append(f"- ⚠️ {w}")
        for e in report["errors"]:
            md_lines.append(f"- ❌ {e}")
        md_lines.append("")

    # Recent sessions
    md_lines.append("## 2. 最近工作記錄")
    md_lines.append("")
    if recent_sessions:
        md_lines.append("| Session | 行動 | 任務 | 備註 |")
        md_lines.append("|---------|------|------|------|")
        for s in recent_sessions:
            md_lines.append(f"| {s['session']} | {s['action']} | {s['tasks']} | {s['notes']} |")
    else:
        md_lines.append("_無記錄_")
    md_lines.append("")

    # Pending tasks
    md_lines.append("## 3. 待完成任務")
    md_lines.append("")
    for priority in ["p0", "p1", "p2"]:
        tasks = pending_tasks.get(priority, [])
        if tasks:
            label = {"p0": "P0 — 核心串聯", "p1": "P1 — 最終交付", "p2": "P2 — 中期目標"}.get(priority, priority)
            md_lines.append(f"### {label}")
            md_lines.append("")
            for t in tasks:
                md_lines.append(f"- [ ] {t}")
            md_lines.append("")

    # Suggested next actions
    md_lines.append("## 4. 建議下一步行動")
    md_lines.append("")

    suggestions = []
    if health["overall_health"] < 80:
        suggestions.append("系統健康度低於 80%，優先修復紅色/黃色段落")
    if any("platform.db" in w for w in report["warnings"]):
        suggestions.append("在 Windows 端運行 cleanup_windows.bat 修復 platform.db")
    if pending_tasks.get("p0"):
        suggestions.append(f"P0 待辦: {pending_tasks['p0'][0]}")
    elif pending_tasks.get("p1"):
        suggestions.append(f"P1 待辦: {pending_tasks['p1'][0]}")
    if not suggestions:
        suggestions.append("所有核心任務已完成，可推進 P1/P2 項目")

    for s in suggestions:
        md_lines.append(f"1. {s}")

    md_lines.append("")
    md_lines.append("---")
    md_lines.append(f"*Generated by daily_activation.py v1.0 · {date_str} {time_str}*")

    return report, "\n".join(md_lines)


def save_activation_report(md_content, json_data):
    """保存激活報告到 _HANDOFF/"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d-%H%M")

    # Save the latest activation report (separate file, not overwriting STATUS.md template)
    latest_path = HANDOFF_DIR / "LATEST-ACTIVATION-REPORT.md"
    latest_path.write_text(md_content, encoding="utf-8")

    # Also save a timestamped copy
    archive_path = REPORTS_DIR / f"ACTIVATION-{date_str}.md"
    archive_path.write_text(md_content, encoding="utf-8")

    # Save JSON
    json_path = REPORTS_DIR / f"ACTIVATION-{date_str}.json"
    json_path.write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8"
    )

    # Append to activation log
    log_path = HANDOFF_DIR / "ACTIVATION-LOG.md"
    if not log_path.exists():
        log_path.write_text(
            "# Q-SpecTrum 激活日誌\n\n"
            "> 每日激活記錄，形成記憶傳承鏈\n\n"
            "---\n\n"
            "| 日期 | 時間 | 健康度 | 警告數 | 錯誤數 | 待辦(P0/P1/P2) |\n"
            "|------|------|--------|--------|--------|----------------|\n",
            encoding="utf-8"
        )

    # Append new row
    p0 = len(json_data.get("pending_tasks", {}).get("p0", []))
    p1 = len(json_data.get("pending_tasks", {}).get("p1", []))
    p2 = len(json_data.get("pending_tasks", {}).get("p2", []))
    warn_count = len(json_data.get("warnings", []))
    err_count = len(json_data.get("errors", []))

    new_row = f"| {json_data['activation_date']} | {json_data['activation_time']} | {json_data['system_health']}% | {warn_count} | {err_count} | {p0}/{p1}/{p2} |\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(new_row)

    return latest_path, archive_path


def main():
    if "--check-only" in sys.argv:
        health = run_health_check()
        print(health.get("summary", "Health check complete"))
        return

    json_data, md_content = generate_activation_report()

    if "--json" in sys.argv:
        print(json.dumps(json_data, indent=2, ensure_ascii=False, default=str))
        return

    # Save reports
    latest, archive = save_activation_report(md_content, json_data)

    # Print summary
    print("=" * 60)
    print("  Q-SpecTrum Daily Activation Report")
    print(f"  {json_data['activation_date']} {json_data['activation_time']}")
    print("=" * 60)
    print()
    print(f"  System Health: {json_data['system_health']}%")
    print(f"  Warnings: {len(json_data.get('warnings', []))}")
    print(f"  Errors: {len(json_data.get('errors', []))}")
    print()

    p = json_data.get("pending_tasks", {})
    print(f"  Pending Tasks: P0={len(p.get('p0',[]))} | P1={len(p.get('p1',[]))} | P2={len(p.get('p2',[]))}")
    print()
    print(f"  Latest report: {latest}")
    print(f"  Archive: {archive}")
    print()
    print("  [Memory Inheritance Protocol]")
    print("  New sessions should read: _HANDOFF/STATUS.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
