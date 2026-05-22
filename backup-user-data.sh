#!/bin/bash
# =============================================================================
# Q-SpecTrum User Data Backup (Linux/Mac)
# Creates a timestamped tar.gz of everything the user has personally
# accumulated — safe to restore to a fresh Q-SpecTrum folder.
# =============================================================================

cd "$(dirname "$0")"

echo ""
echo "  ╔════════════════════════════════════════════════════════════════╗"
echo "  ║             Q-SpecTrum User Data Backup                        ║"
echo "  ║                   用戶資料備份                                   ║"
echo "  ╚════════════════════════════════════════════════════════════════╝"
echo ""

TS=$(date +%Y%m%d-%H%M%S)
OUT="qspectrum-backup-${TS}.tar.gz"

echo "  Target: $OUT"
echo ""
echo "  Packing user-accumulated state..."
echo "  打包使用中累積的資料..."
echo ""

FILES=(
    "MEMORY.md"
    ".env"
    "_HANDOFF"
    "contact_channel.db"
    "project_memory.db"
    "projects.db"
    "task_manager.db"
    "knowledge_pipeline.db"
    "knowledge_checkpoint.db"
    "user_resources.db"
    "decision_layer.db"
    "result_layer.db"
    "qspectrum.db"
    "AI项目管理/Platform/db/platform.db"
)

# Only include files that exist (silence errors for missing ones)
EXISTING=()
for f in "${FILES[@]}"; do
    [ -e "$f" ] && EXISTING+=("$f")
done

if [ ${#EXISTING[@]} -eq 0 ]; then
    echo "  [!] No user data files found to back up."
    exit 1
fi

tar -czf "$OUT" "${EXISTING[@]}" 2>/dev/null

if [ -f "$OUT" ]; then
    echo "  [✓] Backup created: $OUT"
    echo "  [i] Size: $(du -h "$OUT" | cut -f1)"
    echo "  [i] Contents:"
    tar -tzf "$OUT" | head -20 | sed 's/^/      - /'
    echo ""
    echo "  To restore on a fresh Q-SpecTrum folder:"
    echo "    tar -xzf $OUT -C /path/to/new/Q-SpecTrum/"
    echo "    ./start.sh"
    echo ""
    echo "  還原步驟：  tar -xzf $OUT -C 新的/Q-SpecTrum/路徑/"
else
    echo "  [✗] Backup failed."
    exit 1
fi

echo ""
