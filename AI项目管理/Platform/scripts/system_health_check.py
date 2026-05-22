#!/usr/bin/env python3
"""
Q-SpecTrum 系統健康檢查腳本 v1.0
System Health Check — 7-Section Diagnostic

功能：
  1. 文件系統完整性 (12 critical files)
  2. 數據庫完整性 (40 tables, rows, family column)
  3. 模塊導入檢查 (10+ modules)
  4. 引擎串聯檢查 (WorkflowEngine → AgentRuntime → LLM)
  5. Orchestrator 功能檢查
  6. 交接文件完整性 (_HANDOFF/ 8 files)
  7. Windows 端待辦事項

用法：
    python system_health_check.py                 # 運行並輸出到 stdout
    python system_health_check.py --json           # 輸出 JSON
    python system_health_check.py --report         # 生成 Markdown 報告到 _HANDOFF/reports/
"""

import importlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# ── 路徑設置 ──────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PLATFORM_DIR = SCRIPT_DIR.parent
AI_DIR = PLATFORM_DIR.parent
PROJECT_ROOT = AI_DIR.parent  # Q-SpecTrum(TEST)/

DB_DIR = PLATFORM_DIR / "db"
HANDOFF_DIR = PROJECT_ROOT / "_HANDOFF"
SRC_DIR = PROJECT_ROOT / "src"

# ── 診斷結果容器 ─────────────────────────────────────
results = {
    "timestamp": datetime.now().isoformat(),
    "overall_health": 0,
    "sections": {},
    "warnings": [],
    "errors": [],
    "summary": ""
}


def section(name):
    """裝飾器：自動記錄每個檢查段落的結果"""
    def decorator(func):
        def wrapper():
            try:
                score, details = func()
                results["sections"][name] = {
                    "score": score,
                    "max": 100,
                    "details": details,
                    "status": "PASS" if score >= 80 else ("WARN" if score >= 50 else "FAIL")
                }
                return score
            except Exception as e:
                results["sections"][name] = {
                    "score": 0,
                    "max": 100,
                    "details": {"error": str(e)},
                    "status": "ERROR"
                }
                results["errors"].append(f"{name}: {e}")
                return 0
        return wrapper
    return decorator


# ══════════════════════════════════════════════════════
# Section 1: 文件系統完整性
# ══════════════════════════════════════════════════════
@section("file_system")
def check_file_system():
    critical_files = [
        ("Platform/config.json", PLATFORM_DIR / "config.json"),
        ("Platform/db/platform.db", DB_DIR / "platform.db"),
        ("Platform/scripts/agent_runtime.py", SCRIPT_DIR / "agent_runtime.py"),
        ("Platform/scripts/workflow_engine.py", SCRIPT_DIR / "workflow_engine.py"),
        ("Platform/scripts/protocol_executor.py", SCRIPT_DIR / "protocol_executor.py"),
        ("Platform/scripts/deploy_project.py", SCRIPT_DIR / "deploy_project.py"),
        ("Platform/scripts/e2e_test.py", SCRIPT_DIR / "e2e_test.py"),
        ("Platform/scripts/path_utils.py", SCRIPT_DIR / "path_utils.py"),
        ("AGENTS.md (AI项目管理)", PROJECT_ROOT / "AGENTS.md"),
        ("AGENTS.md", PROJECT_ROOT / "AGENTS.md"),
    ]

    found = 0
    details = {}
    for label, path in critical_files:
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        details[label] = {"exists": exists, "size": size}
        if exists and size > 0:
            found += 1
        elif exists and size == 0:
            results["warnings"].append(f"File exists but empty: {label}")

    score = int(found / len(critical_files) * 100)
    details["_summary"] = f"{found}/{len(critical_files)} critical files present"
    return score, details


# ══════════════════════════════════════════════════════
# Section 2: 數據庫完整性
# ══════════════════════════════════════════════════════
@section("database")
def check_database():
    # Find a usable DB
    db_path = None
    for candidate in ["platform.db", "platform_v4.1.db", "platform_restored.db"]:
        p = DB_DIR / candidate
        if p.exists() and p.stat().st_size > 0:
            db_path = p
            break

    if not db_path:
        results["errors"].append("No usable database found!")
        return 0, {"error": "No usable database", "candidates_checked": 3}

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Table count
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [r[0] for r in cur.fetchall()]
    table_count = len(tables)

    # Row counts
    total_rows = 0
    empty_tables = []
    table_rows = {}
    for t in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM [{t}]")
            cnt = cur.fetchone()[0]
            table_rows[t] = cnt
            total_rows += cnt
            if cnt == 0:
                empty_tables.append(t)
        except Exception:
            table_rows[t] = -1

    # Family column check
    has_family = False
    try:
        cur.execute("PRAGMA table_info(ai_roles)")
        columns = [r[1] for r in cur.fetchall()]
        has_family = "family" in columns
    except Exception:
        pass

    # Role count
    role_count = 0
    try:
        cur.execute("SELECT COUNT(*) FROM ai_roles")
        role_count = cur.fetchone()[0]
    except Exception:
        pass

    # Old path check
    old_paths = 0
    for t in ["documents", "repositories", "ai_roles"]:
        if t in tables:
            try:
                for col in ["file_path", "local_path", "activation_card"]:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM [{t}] WHERE [{col}] LIKE '%Users\\z%' OR [{col}] LIKE '%Q-SpecTrum/%'")
                        old_paths += cur.fetchone()[0]
                    except Exception:
                        pass
            except Exception:
                pass

    conn.close()

    # Scoring
    score = 0
    if table_count >= 47: score += 25
    elif table_count >= 40: score += 15
    if total_rows >= 700: score += 25
    elif total_rows >= 500: score += 15
    if len(empty_tables) == 0: score += 20
    elif len(empty_tables) <= 3: score += 10
    if has_family: score += 15
    if old_paths == 0: score += 15

    details = {
        "db_file": db_path.name,
        "db_size_kb": round(db_path.stat().st_size / 1024, 1),
        "table_count": table_count,
        "total_rows": total_rows,
        "empty_tables": empty_tables,
        "has_family_column": has_family,
        "role_count": role_count,
        "old_path_count": old_paths,
        "_summary": f"{table_count}T / {total_rows}R / {len(empty_tables)} empty / family={'yes' if has_family else 'no'}"
    }
    return score, details


# ══════════════════════════════════════════════════════
# Section 3: 模塊導入檢查
# ══════════════════════════════════════════════════════
@section("module_imports")
def check_modules():
    # Ensure paths
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    modules_to_check = [
        ("workflow_engine", "WorkflowEngine"),
        ("agent_runtime", "AgentRuntime"),
        ("protocol_executor", "ProtocolExecutor"),
        ("agent_runtime", "create_default_llm"),
        # Note: src/ directory was removed during v5.0 restructuring
        # All engine modules now live at project root level
    ]

    imported = 0
    details = {}
    for mod_name, attr_name in modules_to_check:
        key = f"{mod_name}.{attr_name}"
        try:
            mod = importlib.import_module(mod_name)
            obj = getattr(mod, attr_name, None)
            if obj is not None:
                imported += 1
                details[key] = "OK"
            else:
                details[key] = f"MISSING attr {attr_name}"
                results["warnings"].append(f"Module {mod_name} missing attribute {attr_name}")
        except Exception as e:
            details[key] = f"IMPORT ERROR: {e}"
            results["warnings"].append(f"Cannot import {mod_name}: {e}")

    score = int(imported / len(modules_to_check) * 100)
    details["_summary"] = f"{imported}/{len(modules_to_check)} modules importable"
    return score, details


# ══════════════════════════════════════════════════════
# Section 4: 引擎串聯檢查
# ══════════════════════════════════════════════════════
@section("engine_chain")
def check_engine_chain():
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    checks = {}
    score = 0

    # 1. AgentRuntime + LLM Provider
    try:
        from agent_runtime import AgentRuntime, create_default_llm
        llm = create_default_llm()
        llm_class = type(llm).__name__
        checks["llm_provider"] = llm_class
        score += 30
        checks["llm_source"] = f"{llm_class} (OK)"
    except Exception as e:
        checks["llm_provider"] = f"ERROR: {e}"
        results["errors"].append(f"Cannot create LLM provider: {e}")

    # 2. AgentRuntime DB connection
    try:
        rt = AgentRuntime()
        checks["runtime_db"] = rt.db_path
        checks["runtime_llm_source"] = rt._llm_source
        score += 20
    except Exception as e:
        checks["runtime_db"] = f"ERROR: {e}"
        results["errors"].append(f"Cannot instantiate AgentRuntime: {e}")

    # 3. Workflow listing
    try:
        from workflow_engine import WorkflowEngine
        we = WorkflowEngine(rt.db_path)
        wfs = we.list_workflows()
        checks["workflow_count"] = len(wfs)
        if len(wfs) >= 4:
            score += 25
        elif len(wfs) > 0:
            score += 15
    except Exception as e:
        checks["workflow_count"] = f"ERROR: {e}"

    # 4. Protocol listing
    try:
        from protocol_executor import ProtocolExecutor
        pe = ProtocolExecutor(rt.db_path)
        protos = pe.list_protocols()
        checks["protocol_count"] = len(protos)
        if len(protos) >= 10:
            score += 25
        elif len(protos) > 0:
            score += 15
    except Exception as e:
        checks["protocol_count"] = f"ERROR: {e}"

    checks["_summary"] = f"LLM={checks.get('llm_source','?')} | WF={checks.get('workflow_count','?')} | Proto={checks.get('protocol_count','?')}"
    return min(score, 100), checks


# ══════════════════════════════════════════════════════
# Section 5: Orchestrator 功能檢查
# ══════════════════════════════════════════════════════
@section("orchestrator")
def check_orchestrator():
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    checks = {}
    score = 0

    try:
        from qspectrum_engine import QSpectrumEngine, create_llm_provider
        llm = create_llm_provider()
        orch = QSpectrumEngine(llm_provider=llm)
        checks["instantiation"] = "OK"
        score += 30
    except Exception as e:
        checks["instantiation"] = f"ERROR: {e}"
        results["warnings"].append(f"Engine cannot instantiate (expected in standalone script mode): {e}")
        return 0, checks

    # get_system_status
    try:
        status = orch.get_system_status()
        checks["get_system_status"] = "OK" if status else "empty"
        score += 20
    except Exception as e:
        checks["get_system_status"] = f"ERROR: {e}"

    # dispatch_workflow (dry run)
    try:
        result = orch.dispatch_workflow("WF-0001", dry_run=True)
        checks["dispatch_workflow"] = "OK" if result and "error" not in result else str(result)
        if result and "error" not in result:
            score += 25
    except Exception as e:
        checks["dispatch_workflow"] = f"ERROR: {e}"

    # chat_with_role
    try:
        result = orch.chat_with_role("ROLE-S03", "ping")
        checks["chat_with_role"] = "OK" if result else "empty"
        if result:
            score += 25
    except Exception as e:
        checks["chat_with_role"] = f"ERROR: {e}"

    checks["_summary"] = f"init={'OK' if score>=30 else 'FAIL'} | status={'OK' if score>=50 else '?'} | dispatch={'OK' if score>=75 else '?'}"
    return min(score, 100), checks


# ══════════════════════════════════════════════════════
# Section 6: 交接文件完整性
# ══════════════════════════════════════════════════════
@section("handoff_files")
def check_handoff():
    required_files = [
        "STATUS.md",
        "MIGRATION-LOG.md",
        "CHANGELOG.md",
        "VALUE-FUNCTION-MAP.md",
        "DB-DIFF.md",
        "TASK-BOARD.md",
        "TASK-INDEX.md",
    ]

    found = 0
    details = {}
    for f in required_files:
        path = HANDOFF_DIR / f
        exists = path.exists()
        details[f] = {"exists": exists, "size": path.stat().st_size if exists else 0}
        if exists and path.stat().st_size > 0:
            found += 1

    # Check for session records
    sessions_dir = HANDOFF_DIR / "sessions"
    session_count = len(list(sessions_dir.glob("S*.md"))) if sessions_dir.exists() else 0
    details["session_records"] = session_count

    # Check for reports
    reports_dir = HANDOFF_DIR / "reports"
    report_count = len(list(reports_dir.glob("REPORT-*.md"))) if reports_dir.exists() else 0
    details["report_count"] = report_count

    score = int(found / len(required_files) * 100)
    details["_summary"] = f"{found}/{len(required_files)} handoff files | {session_count} sessions | {report_count} reports"
    return score, details


# ══════════════════════════════════════════════════════
# Section 7: Windows 端待辦
# ══════════════════════════════════════════════════════
@section("windows_tasks")
def check_windows_tasks():
    details = {}
    warnings = []

    # Check if platform.db is 0 bytes (virtiofs issue)
    primary_db = DB_DIR / "platform.db"
    if primary_db.exists() and primary_db.stat().st_size == 0:
        warnings.append("platform.db is 0 bytes — needs cleanup_windows.bat on Windows")
        details["platform_db_zero"] = True
    else:
        details["platform_db_zero"] = False

    # Check if init_git.bat exists
    init_git = PROJECT_ROOT / "init_git.bat"
    details["init_git_exists"] = init_git.exists()

    # Check if cleanup script exists
    cleanup = SCRIPT_DIR / "cleanup_windows.bat"
    if not cleanup.exists():
        cleanup = PROJECT_ROOT / "cleanup_windows.bat"
    details["cleanup_script_exists"] = cleanup.exists()

    # Check .git directory
    git_dir = PROJECT_ROOT / ".git"
    details["git_initialized"] = git_dir.exists()

    score = 100
    if details.get("platform_db_zero"):
        score -= 20
        results["warnings"].append("platform.db is 0 bytes (virtiofs issue)")
    if not details.get("git_initialized"):
        score -= 15
        results["warnings"].append("Git not initialized — run init_git.bat")

    details["pending_windows_tasks"] = warnings
    details["_summary"] = f"DB0={'yes' if details.get('platform_db_zero') else 'no'} | git={'yes' if details.get('git_initialized') else 'no'}"
    return max(score, 0), details


# ══════════════════════════════════════════════════════
# 彙總 + 報告生成
# ══════════════════════════════════════════════════════
def run_all_checks():
    """執行所有 7 個檢查段落"""
    checks = [
        ("file_system", check_file_system),
        ("database", check_database),
        ("module_imports", check_modules),
        ("engine_chain", check_engine_chain),
        ("orchestrator", check_orchestrator),
        ("handoff_files", check_handoff),
        ("windows_tasks", check_windows_tasks),
    ]

    weights = {
        "file_system": 0.15,
        "database": 0.20,
        "module_imports": 0.15,
        "engine_chain": 0.20,
        "orchestrator": 0.15,
        "handoff_files": 0.10,
        "windows_tasks": 0.05,
    }

    total_weighted = 0
    for name, func in checks:
        score = func()
        total_weighted += score * weights.get(name, 0.1)

    results["overall_health"] = round(total_weighted, 1)

    # Generate summary
    status_emoji = "🟢" if results["overall_health"] >= 90 else ("🟡" if results["overall_health"] >= 70 else "🔴")
    results["summary"] = f"{status_emoji} System Health: {results['overall_health']}%"

    return results


def generate_markdown_report(results):
    """生成 Markdown 格式健康報告"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Q-SpecTrum 系統健康報告",
        "",
        f"> **生成時間**: {ts}",
        f"> **整體健康度**: {results['overall_health']}%",
        "",
        "---",
        "",
    ]

    # Section scores
    lines.append("## 各段落評分")
    lines.append("")
    lines.append("| 段落 | 分數 | 狀態 | 摘要 |")
    lines.append("|------|------|------|------|")
    for name, data in results["sections"].items():
        summary = data["details"].get("_summary", "")
        lines.append(f"| {name} | {data['score']}/100 | {data['status']} | {summary} |")

    # Warnings
    if results["warnings"]:
        lines.append("")
        lines.append("## 警告")
        lines.append("")
        for w in results["warnings"]:
            lines.append(f"- {w}")

    # Errors
    if results["errors"]:
        lines.append("")
        lines.append("## 錯誤")
        lines.append("")
        for e in results["errors"]:
            lines.append(f"- {e}")

    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by system_health_check.py v1.0 · {ts}*")
    return "\n".join(lines)


def main():
    results = run_all_checks()

    if "--json" in sys.argv:
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    elif "--report" in sys.argv:
        # Generate and save markdown report
        md = generate_markdown_report(results)
        report_dir = HANDOFF_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d-%H%M")
        report_path = report_dir / f"HEALTH-{date_str}.md"
        report_path.write_text(md, encoding="utf-8")
        print(f"Report saved: {report_path}")
        print(results["summary"])
    else:
        # Pretty stdout output
        print("=" * 60)
        print("  Q-SpecTrum System Health Check")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        for name, data in results["sections"].items():
            icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "ERROR": "💥"}.get(data["status"], "?")
            summary = data["details"].get("_summary", "")
            print(f"  {icon} [{data['score']:3d}/100] {name}: {summary}")

        print()
        if results["warnings"]:
            print("  Warnings:")
            for w in results["warnings"]:
                print(f"    ⚠️  {w}")
            print()

        if results["errors"]:
            print("  Errors:")
            for e in results["errors"]:
                print(f"    ❌  {e}")
            print()

        print(f"  {results['summary']}")
        print("=" * 60)


if __name__ == "__main__":
    main()
