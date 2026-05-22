#!/bin/bash
# =============================================================================
# Q-SpecTrum Health Check (Linux/Mac)
# Run this to get a quick health check of the system.
# =============================================================================

cd "$(dirname "$0")"

echo ""
echo "  ╔════════════════════════════════════════════════════════════════╗"
echo "  ║               Q-SpecTrum Health Check                          ║"
echo "  ║                     健康檢查                                    ║"
echo "  ╚════════════════════════════════════════════════════════════════╝"
echo ""

# Find Python
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "  [✗] Python not found."
    echo "      Python 未安裝。請到 https://www.python.org/downloads/ 下載 Python 3.8+"
    echo ""
    exit 1
fi

echo "  [✓] Python detected: $PYTHON"
echo ""
echo "  Running full system status check..."
echo "  執行完整系統狀態檢查中..."
echo ""

$PYTHON run.py --status
EXIT=$?

echo ""
echo "  ──────────────────────────────────────────────────────────────"
if [ $EXIT -eq 0 ]; then
    echo "  Summary:  If you see 'System: ALL GREEN', the system is ready."
    echo "  總結：    若顯示 'System: ALL GREEN' 表示系統就緒。"
else
    echo "  Summary:  Status check exited with errors. See output above."
    echo "  總結：    狀態檢查出現錯誤，請查看上方輸出。"
    echo "            Check FIXES-APPLIED.md for common fixes."
    echo "            參考 FIXES-APPLIED.md 了解常見修復方法。"
fi
echo "  ──────────────────────────────────────────────────────────────"
echo ""

exit $EXIT
