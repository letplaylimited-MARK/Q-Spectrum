#!/bin/bash
# =============================================================================
# Q-SpecTrum Delivery Cleanup (Linux/Mac)
# Removes development artifacts before zipping/shipping the folder.
# Safe to run repeatedly.
# =============================================================================

cd "$(dirname "$0")"

echo ""
echo "  ╔════════════════════════════════════════════════════════════════╗"
echo "  ║             Q-SpecTrum Delivery Cleanup                        ║"
echo "  ║                    交付前清理                                   ║"
echo "  ╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "  Removing development artifacts..."
echo "  清除開發殘留..."
echo ""

# Python bytecode caches
find . -type d -name __pycache__ -print -exec rm -rf {} + 2>/dev/null | sed 's/^/    [✓] removed: /'

# Ruff cache
[ -d .ruff_cache ] && rm -rf .ruff_cache && echo "    [✓] removed: .ruff_cache"

# First-run marker
[ -f .first_run_done ] && rm -f .first_run_done && echo "    [✓] removed: .first_run_done"

# Temp env files
[ -f .env.tmp ] && rm -f .env.tmp && echo "    [✓] removed: .env.tmp"

# SQLite runtime write-test artifacts
for f in .write_test* .runtime_write_test* .sqlite_write_test*; do
    [ -f "$f" ] && rm -f "$f" && echo "    [✓] removed: $f"
done

# Ephemeral files left by verification runs
for f in test_size_*.txt test_utf8.txt test_write_r4.txt test_write_*.txt; do
    [ -f "$f" ] && rm -f "$f" && echo "    [✓] removed: $f"
done

# User data backups (receiver should make their own)
for f in qspectrum-backup-*.tar.gz qspectrum-backup-*.zip; do
    [ -f "$f" ] && rm -f "$f" && echo "    [✓] removed backup: $f"
done

# Secondary runtime DB files (kept: platform.db + platform_restored.db)
for f in contact_channel.db decision_layer.db knowledge_checkpoint.db knowledge_graph.db knowledge_pipeline.db project_memory.db projects.db qspectrum.db result_layer.db task_manager.db user_resources.db; do
    [ -f "$f" ] && rm -f "$f" && echo "    [✓] removed runtime: $f"
done

# SQLite journal files (left over when engine crashes mid-write)
for f in *.db-journal *.db-wal *.db-shm; do
    [ -f "$f" ] && rm -f "$f" && echo "    [✓] removed journal: $f"
done

# DB folder write-test artifacts (created by find_writable_dir probe)
for f in "AI项目管理/Platform/db/_bintest.bin" \
         "AI项目管理/Platform/db/_writetest.txt" \
         "AI项目管理/Platform/db/.sqlite_write_test"*; do
    [ -f "$f" ] && rm -f "$f" && echo "    [✓] removed: $f"
done

# R17 reverse-thinking probe scratchpads (cowork sandbox can't unlink mid-run)
for f in ROUND17_PROBE_DRIFT_NEW_DOC.md ROUND17_PROBE_TEST.md ROUND17_TEST.md; do
    [ -f "$f" ] && rm -f "$f" && echo "    [✓] removed probe scratch: $f"
done

echo ""
echo "  ──────────────────────────────────────────────────────────────"
echo "  Delivery-ready total size:"
echo "  交付大小："
du -sh . 2>/dev/null
echo ""
echo "  NOTE: .git/ is NOT removed automatically. If you want to strip"
echo "        git history from the delivery, run:  rm -rf .git"
echo ""
echo "  備註：.git/ 不會自動清除。若要移除 git 歷史："
echo "        rm -rf .git"
echo "  ──────────────────────────────────────────────────────────────"
echo ""
