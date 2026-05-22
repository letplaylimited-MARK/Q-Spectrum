#!/bin/bash
################################################################################
# Q-SpecTrum System Launcher (Linux/Mac)
# Enhanced startup script with Python detection, dependency checks, and bilingual support
################################################################################

set -e

# ==============================================================================
# ASCII Banner - Q-SpecTrum Branding
# ==============================================================================
print_banner() {
    echo ""
    echo "  ╔════════════════════════════════════════════════════════════════╗"
    echo "  ║                                                                ║"
    echo "  ║                    ◆ Q-SpecTrum System ◆                      ║"
    echo "  ║                                                                ║"
    echo "  ║              Advanced AI Negotiation Platform                  ║"
    echo "  ║                   Launching Intelligence...                    ║"
    echo "  ║                                                                ║"
    echo "  ╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# ==============================================================================
# Helper Functions
# ==============================================================================
error_exit() {
    clear
    echo ""
    echo "  ╔════════════════════════════════════════════════════════════════╗"
    echo "  ║  [ERROR] $1"
    echo "  ╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  English: $2"
    echo ""
    echo "  Chinese: $3"
    echo ""
    exit 1
}

log_step() {
    echo "  [$1/3] $2"
    echo "         English: $3"
    echo "         Chinese: $4"
}

check_running() {
    if curl -s http://localhost:8765/api/status &>/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# ==============================================================================
# Main Script
# ==============================================================================

cd "$(dirname "$0")"

# Handle --status flag for system health check
if [ "$1" = "--status" ]; then
    clear
    echo ""
    echo "  ╔════════════════════════════════════════════════════════════════╗"
    echo "  ║                  System Health Check                          ║"
    echo "  ╚════════════════════════════════════════════════════════════════╝"
    echo ""

    # Check Python
    echo "  [*] Checking Python installation..."
    if command -v python3 &>/dev/null; then
        PYTHON="python3"
        PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
        echo "      $PYTHON $PYTHON_VERSION"
    elif command -v python &>/dev/null; then
        PYTHON="python"
        PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
        echo "      $PYTHON $PYTHON_VERSION"
    else
        echo "      [!] Python not found"
    fi

    # Check dependencies
    echo "  [*] Checking system dependencies..."
    if $PYTHON -c "import sys, os, json, sqlite3, http.server" 2>/dev/null; then
        echo "      [✓] All core modules available"
    else
        echo "      [!] Warning: Some modules may be unavailable"
    fi

    # Check network
    echo "  [*] Checking network..."
    if check_running; then
        echo "      [✓] Server running on http://localhost:8765"
    else
        echo "      [!] Server not running (start with ./start.sh)"
    fi

    # Check files
    echo "  [*] Checking required files..."
    [ -f "run.py" ] && echo "      [✓] run.py found"
    [ -f "chat.html" ] && echo "      [✓] chat.html found"
    [ -f "api_server.py" ] && echo "      [✓] api_server.py found"

    echo ""
    echo "  [✓] System check complete"
    echo ""
    exit 0
fi

# ==============================================================================
# Print Banner
# ==============================================================================
print_banner

# ==============================================================================
# Python Detection (Python 3.8+)
# ==============================================================================
PYTHON=""
PYTHON_VERSION=""

if command -v python3 &>/dev/null; then
    PYTHON="python3"
    PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
elif command -v python &>/dev/null; then
    PYTHON="python"
    PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
else
    error_exit "Python Not Found" \
        "Python 3.8 or higher is required but not installed. Download: https://www.python.org/downloads/" \
        "需要 Python 3.8 或更高版本，但未安装。下载: https://www.python.org/downloads/"
fi

# ==============================================================================
# Verify Python Version (3.8+)
# ==============================================================================
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
    error_exit "Python Version Too Old" \
        "Python $PYTHON_VERSION detected. Requires 3.8 or higher." \
        "检测到 Python $PYTHON_VERSION。需要 3.8 或更高版本。"
fi

echo "  [✓] Python $PYTHON_VERSION detected"
echo ""

# ==============================================================================
# Check core Python stdlib (minimal verification for stdlib-only system)
# ==============================================================================
echo "  Checking core dependencies..."
if $PYTHON -c "import sys, os, json, sqlite3, http.server, urllib.parse" 2>/dev/null; then
    echo "  [✓] Core dependencies available"
else
    echo "  [!] Warning: Some stdlib modules may be unavailable"
    echo "  [TIP] Try reinstalling Python"
fi
echo ""

# ==============================================================================
# Check .env / LLM Configuration
# ==============================================================================
if [ -f ".env" ]; then
    echo "  [✓] .env configuration found"
    $PYTHON -c "from env_loader import load_env; n=load_env(); print(f'      {n} keys loaded')" 2>/dev/null || true
else
    echo "  [!] No .env file found - running in MOCK mode (offline)"
    echo "      To enable real AI, run:"
    echo "        cp .env.template .env"
    echo "        nano .env   (or vim, or your editor)"
    echo "      Then add your API key (OpenAI/Anthropic/DeepSeek/Ollama)"
fi
echo ""

# ==============================================================================
# Quick regression test on first run
# ==============================================================================
if [ -d "tests" ] && [ ! -f ".first_run_done" ]; then
    echo "  [*] First run detected - running regression tests..."
    if $PYTHON tests/test_server_startup.py >/dev/null 2>&1; then
        echo "  [✓] Startup tests passed"
        echo "done" > .first_run_done
    else
        echo "  [!] Some tests failed - run 'python tests/test_server_startup.py' for details"
    fi
    echo ""
fi

# ==============================================================================
# Check if already running
# ==============================================================================
if check_running; then
    clear
    echo ""
    echo "  ╔════════════════════════════════════════════════════════════════╗"
    echo "  ║  [INFO] Server Already Running                                ║"
    echo "  ╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  English: Q-SpecTrum is already running on port 8765"
    echo "  Opening browser..."
    echo ""
    echo "  Chinese: Q-SpecTrum 已在端口 8765 上运行"
    echo "  打开浏览器..."
    echo ""

    sleep 1

    # Try to open browser (macOS or Linux)
    if command -v open &>/dev/null; then
        open http://localhost:8765/chat.html 2>/dev/null || true
    elif command -v xdg-open &>/dev/null; then
        xdg-open http://localhost:8765/chat.html 2>/dev/null || true
    fi

    exit 0
fi

# ==============================================================================
# Startup Sequence
# ==============================================================================
clear
echo ""
echo "  ╔════════════════════════════════════════════════════════════════╗"
echo "  ║                   System Initialization                        ║"
echo "  ╚════════════════════════════════════════════════════════════════╝"
echo ""

log_step "1" "Starting API Server (port 8765)" \
    "Starting API Server..." \
    "启动 API 服务器..."
echo ""

# Start server in background
$PYTHON run.py --web &
SERVER_PID=$!

log_step "2" "Waiting for engine initialization..." \
    "Waiting for system to be ready..." \
    "等待系统初始化..."
echo ""

# Wait for server (up to 30 seconds)
count=0
while [ $count -lt 30 ]; do
    if check_running; then
        break
    fi
    sleep 1
    count=$((count + 1))
done

if ! check_running; then
    echo "  [!] Server startup timeout. Check console for errors."
    exit 1
fi

echo "         [✓] Engine ready"
echo ""

log_step "3" "Opening browser..." \
    "Launching web interface..." \
    "启动网络界面..."
echo ""

sleep 1

# Try to open browser (macOS or Linux)
if command -v open &>/dev/null; then
    open http://localhost:8765/chat.html 2>/dev/null || true
elif command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:8765/chat.html 2>/dev/null || true
fi

# ==============================================================================
# Ready Message
# ==============================================================================
echo ""
echo "  ╔════════════════════════════════════════════════════════════════╗"
echo "  ║                    System Ready!                              ║"
echo "  ╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "  [✓] Q-SpecTrum is running"
echo ""
echo "  English:"
echo "    • Chat Interface:  http://localhost:8765/chat.html"
echo "    • Dashboard:       http://localhost:8765/dashboard.html"
echo "    • API Status:      http://localhost:8765/api/status"
echo "    • Press Ctrl+C to stop the server"
echo ""
echo "  Chinese:"
echo "    • 聊天界面:        http://localhost:8765/chat.html"
echo "    • 仪表板:          http://localhost:8765/dashboard.html"
echo "    • API 状态:        http://localhost:8765/api/status"
echo "    • 按 Ctrl+C 停止服务器"
echo ""

# Keep running and forward signals to the server process
trap "kill $SERVER_PID 2>/dev/null; exit 0" INT TERM
wait $SERVER_PID
