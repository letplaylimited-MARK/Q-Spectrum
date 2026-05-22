#!/usr/bin/env python3
"""
verify-integration.py — 智腦整合驗證 v1.1
每次會話啟動時執行。逐項確認，**不跳過**。
誠實原則：有 FAIL 就不能進入下一步。

v1.1 修復:
- subprocess 使用 encoding='utf-8', errors='replace' 避免 Windows 編碼崩潰
- platform_restored.db 降級為可選（首次交付只有 platform.db）
"""
import sqlite3
import subprocess
import sys
from pathlib import Path

# Force UTF-8 output for Windows terminal compatibility
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).parent.resolve()
errors = []
warnings = []


def check(desc, condition, detail=""):
    if condition:
        print(f"  [OK] {desc}")
    else:
        print(f"  [FAIL] {desc}")
        errors.append(f"{desc}: {detail}")


def warn(desc, condition, detail=""):
    if condition:
        print(f"  [OK] {desc}")
    else:
        print(f"  [WARN] {desc}")
        warnings.append(f"{desc}: {detail}")


print()
print("=" * 60)
print("  智腦整合驗證 / Brain Integration Verification")
print("=" * 60)
print()

# ─────────────────────────────────────────────
# P0: CRITICAL — 核心檔案存在性
# ─────────────────────────────────────────────
print("  [P0] 核心檔案檢查")

check("智腦協議存在",
      (ROOT / "智腦協議-BRAIN-PROTOCOL.md").exists())

check("AGENTS.md 存在",
      (ROOT / "AGENTS.md").exists())

check("BOOT.md 存在",
      (ROOT / "BOOT.md").exists())

db_path = ROOT / "AI项目管理" / "Platform" / "db" / "platform.db"
db_exists = db_path.exists()
check("platform.db 存在", db_exists)
if db_exists:
    check("platform.db 非空", db_path.stat().st_size > 0,
          f"大小為 {db_path.stat().st_size} bytes（需要 > 0）")

# ─────────────────────────────────────────────
# P0: CRITICAL — 路徑紀律（無硬編碼 C:\Users\）
# ─────────────────────────────────────────────
print()
print("  [P0] 路徑紀律檢查（禁止 C:\\Users\\ 硬編碼）")

try:
    result = subprocess.run(
        r'rg -n "C:\\Users\\" --type py --type md .',
        shell=True, capture_output=True, cwd=ROOT,
        encoding='utf-8', errors='replace')
    violations = result.stdout.strip()
    check("無 C:\\Users\\ 硬編碼", not violations,
          f"違規：{violations[:500] if violations else 'none'}")
except Exception:
    warn("ripgrep 不可用，跳過路徑檢查", False, "需安裝 ripgrep")

# ─────────────────────────────────────────────
# P1: HIGH — 資料庫完整性
# ─────────────────────────────────────────────
print()
print("  [P1] 資料庫完整性檢查")

# v1.1: 優先使用 platform.db，platform_restored.db 作為可選備份
db_dir = ROOT / "AI项目管理" / "Platform" / "db"
platform_path = db_dir / "platform.db"
restored_path = db_dir / "platform_restored.db"

# 決定使用哪個數據庫進行驗證
if restored_path.exists():
    verify_db_path = restored_path
    check("platform_restored.db 存在", True, "使用備份數據庫驗證")
elif platform_path.exists():
    verify_db_path = platform_path
    check("platform.db 可讀取 (restored 不存在)", True,
          "首次運行時只存在 platform.db，正常")
else:
    verify_db_path = None
    check("數據庫存在", False, "platform.db 和 platform_restored.db 均不存在")

if verify_db_path:
    try:
        conn = sqlite3.connect(str(verify_db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        check(f"資料表數量 ({len(tables)}) >= 30", len(tables) >= 30,
              f"實際 {len(tables)} 表")

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ai\\_%' ESCAPE '\\'")
        ai_tables = [row[0] for row in cursor.fetchall()]
        check("ai_roles 表存在", "ai_roles" in ai_tables,
              f"ai_* 表：{ai_tables}")

        if "ai_roles" in ai_tables:
            roles = conn.execute("SELECT COUNT(*) FROM ai_roles").fetchone()[0]
            check(f"ai_roles 有 {roles} 行", roles == 15,
                  f"實際 {roles} 行，預期 15")

        if "agents" in tables:
            agents = conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
            check(f"agents 有 {agents} 行", agents > 0,
                  f"實際 {agents} 行")

        conn.close()
    except Exception as e:
        check("資料庫可讀取", False, str(e))

# ─────────────────────────────────────────────
# P1: HIGH — 測試完整性
# ─────────────────────────────────────────────
print()
print("  [P1] 測試與腳本檢查")

test_dir = ROOT / "tests"
test_files = sorted(test_dir.glob("test_*.py"))
check(f"測試檔案 ({len(test_files)}) >= 5", len(test_files) >= 5,
      f"實際 {len(test_files)} 個")

scripts_dir = ROOT / "AI项目管理" / "Platform" / "scripts"
script_files = sorted(scripts_dir.glob("*.py"))
check(f"平台腳本 ({len(script_files)}) >= 5", len(script_files) >= 5,
      f"實際 {len(script_files)} 個")

# ─────────────────────────────────────────────
# P1: HIGH — 長期記憶系統完整性
# ─────────────────────────────────────────────
print()
print("  [P1] 長期記憶系統檢查")

handoff_dir = ROOT / "_HANDOFF"
check("_HANDOFF/ 目錄存在", handoff_dir.exists())

if handoff_dir.exists():
    status_file = handoff_dir / "STATUS.md"
    check("STATUS.md 存在", status_file.exists())
    if status_file.exists():
        content = status_file.read_text(encoding="utf-8")
        check("STATUS.md 包含循環確認區", "循環確認" in content,
              "缺少循環確認檢查清單")

    reminders_file = handoff_dir / "CRITICAL-REMINDERS.md"
    check("CRITICAL-REMINDERS.md 存在", reminders_file.exists())
    if reminders_file.exists():
        content = reminders_file.read_text(encoding="utf-8")
        check("CRITICAL-REMINDERS.md 包含 P0 提醒區", "P0" in content,
              "缺少 P0 級提醒")

    memory_file = handoff_dir / "MEMORY-INDEX.md"
    check("MEMORY-INDEX.md 存在", memory_file.exists())
    if memory_file.exists():
        content = memory_file.read_text(encoding="utf-8")
        entry_count = content.count("## 記憶條目")
        check(f"MEMORY-INDEX.md 有 {entry_count} 條記憶", entry_count >= 3,
              f"實際 {entry_count} 條記憶，預期 >= 3")

# ─────────────────────────────────────────────
# P2: NORMAL — 殘留文件檢查
# ─────────────────────────────────────────────
print()
print("  [P2] 殘留文件檢查")

# P2: MCP Server exists
check("MCP Server 存在", (ROOT / "qspectrum_mcp_server.py").exists(),
      "缺少 MCP Server 文件")
check("E2E 測試存在", (ROOT / "test_e2e.py").exists(),
      "缺少端到端測試")
check("啟動腳本存在", (ROOT / "start.ps1").exists(),
      "缺少啟動腳本")

# P2: Knowledge Graph (Phase 2.1)
kg_file = ROOT / "knowledge_graph.py"
kg_test = ROOT / "test_knowledge_graph.py"
check("Knowledge Graph 存在", kg_file.exists(), "缺少 knowledge_graph.py")
if kg_file.exists():
    try:
        from knowledge_graph import ALL_OPS, EDGE_LABELS
        check(f"KG 算子數量: {len(ALL_OPS)}", len(ALL_OPS) == 21,
              f"預期 21 算子，實際 {len(ALL_OPS)}")
        check(f"KG 邊標籤數量: {len(EDGE_LABELS)}", len(EDGE_LABELS) == 19,
              f"預期 19 邊標籤，實際 {len(EDGE_LABELS)}")
    except Exception as e:
        check("KG 模組可導入", False, str(e))
check("KG 測試存在", kg_test.exists(), "缺少 test_knowledge_graph.py")

# P2: Vector Store (Phase 2.2)
vs_file = ROOT / "vector_store.py"
vs_test = ROOT / "test_vector_store.py"
check("Vector Store 存在", vs_file.exists(), "缺少 vector_store.py")
if vs_file.exists():
    try:
        import tempfile

        from vector_store import VectorStore
        _vs = VectorStore(persist_dir=tempfile.mktemp())
        check("VS 可初始化", _vs.count() > 0, f"seed count={_vs.count()}")
    except Exception as e:
        check("VS 模組可導入", False, str(e))
check("VS 測試存在", vs_test.exists(), "缺少 test_vector_store.py")

audit_dir = ROOT / "archive" / "audits"
if audit_dir.exists():
    check("審計報告已歸檔", True, "archive/audits/ 存在")
    check("原始審計文件已清理", not (ROOT / "AUDIT-20JOURNEY.md").exists(),
          "AUDIT-*.md 應移入 archive/audits/")
else:
    warn("審計報告未歸檔", False, "缺少 archive/audits/")

# ─────────────────────────────────────────────
# 總結
# ─────────────────────────────────────────────
print()
print("=" * 60)
if errors:
    print(f"  {len(errors)} 個錯誤（必須修復）")
    for e in errors:
        print(f"     x {e}")
if warnings:
    print(f"  {len(warnings)} 個警告（建議修復）")
    for w in warnings:
        print(f"     ! {w}")

if errors:
    print(f"\n  請先修復以上 {len(errors)} 個問題再繼續。")
    print("  誠實原則：不能跳過問題開始工作。")
    sys.exit(1)
else:
    print("  OK 全部檢查通過，可以開始工作")
    sys.exit(0)
