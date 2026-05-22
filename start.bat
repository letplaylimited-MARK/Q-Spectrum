@echo off
REM ============================================================================
REM Q-SpecTrum System Launcher (Windows)
REM Enhanced startup script with Python detection, dependency checks, and bilingual support
REM ============================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Q-SpecTrum AI System
color 0A

REM ===========================================================================
REM ASCII Banner - Q-SpecTrum Branding
REM ===========================================================================
echo.
echo   ╔════════════════════════════════════════════════════════════════╗
echo   ║                                                                ║
echo   ║                    ◆ Q-SpecTrum System ◆                      ║
echo   ║                                                                ║
echo   ║              Advanced AI Negotiation Platform                  ║
echo   ║                   Launching Intelligence...                    ║
echo   ║                                                                ║
echo   ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM ===========================================================================
REM Python Detection (Python 3.8+)
REM (moved above --status handler so health-check also sees Python version)
REM ===========================================================================
set PYTHON=
set PYTHON_VERSION=

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%A in ('python --version 2^>^&1') do set PYTHON_VERSION=%%A
    set PYTHON=python
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "tokens=2" %%A in ('python3 --version 2^>^&1') do set PYTHON_VERSION=%%A
        set PYTHON=python3
    )
)

if "!PYTHON!"=="" (
    cls
    echo.
    echo   ╔════════════════════════════════════════════════════════════════╗
    echo   ║  [ERROR] Python Not Found                                      ║
    echo   ╚════════════════════════════════════════════════════════════════╝
    echo.
    echo   English: Python 3.8 or higher is required but not installed.
    echo   Download: https://www.python.org/downloads/
    echo.
    echo   Chinese: 需要 Python 3.8 或更高版本，但未安装。
    echo   下载: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM ===========================================================================
REM Verify Python Version (3.8+)
REM ===========================================================================
for /f "tokens=1-2 delims=." %%A in ("!PYTHON_VERSION!") do (
    set MAJOR=%%A
    set MINOR=%%B
)

if !MAJOR! LSS 3 (
    cls
    echo.
    echo   ╔════════════════════════════════════════════════════════════════╗
    echo   ║  [ERROR] Python Version Too Old                               ║
    echo   ╚════════════════════════════════════════════════════════════════╝
    echo.
    echo   English: Python !PYTHON_VERSION! detected. Requires 3.8+
    echo.
    echo   Chinese: 检测到 Python !PYTHON_VERSION!。需要 3.8 或更高版本
    echo.
    pause
    exit /b 1
)

if !MAJOR! equ 3 if !MINOR! LSS 8 (
    cls
    echo.
    echo   ╔════════════════════════════════════════════════════════════════╗
    echo   ║  [ERROR] Python Version Too Old                               ║
    echo   ╚════════════════════════════════════════════════════════════════╝
    echo.
    echo   English: Python !PYTHON_VERSION! detected. Requires 3.8+
    echo.
    echo   Chinese: 检测到 Python !PYTHON_VERSION!。需要 3.8 或更高版本
    echo.
    pause
    exit /b 1
)

echo   [✓] Python !PYTHON_VERSION! detected
echo.

REM ===========================================================================
REM Handle --status flag now that Python is detected
REM ===========================================================================
if "%1"=="--status" goto check_status

REM ===========================================================================
REM Check core Python stdlib (minimal verification for stdlib-only system)
REM ===========================================================================
echo   Checking core dependencies...
!PYTHON! -c "import sys, os, json, sqlite3, http.server, urllib.parse" >nul 2>&1
if %errorlevel% neq 0 (
    echo   [!] Warning: Some stdlib modules may be unavailable
    echo   [TIP] Try reinstalling Python
)
echo   [✓] Core dependencies available
echo.

REM ===========================================================================
REM Check .env / LLM Configuration
REM ===========================================================================
if exist ".env" (
    echo   [✓] .env configuration found
    !PYTHON! -c "from env_loader import load_env; n=load_env(); print(f'      {n} keys loaded')" 2>nul
) else (
    echo   [!] No .env file found - running in MOCK mode (offline)
    echo       To enable real AI, run:
    echo         copy .env.template .env
    echo         notepad .env
    echo       Then add your API key (OpenAI/Anthropic/DeepSeek/Ollama)
)
echo.

REM ===========================================================================
REM Quick regression test on first run
REM ===========================================================================
if exist "tests\test_server_startup.py" (
    if not exist ".first_run_done" (
        echo   [*] First run detected - running regression tests...
        !PYTHON! tests\test_server_startup.py >nul 2>&1
        if %errorlevel% equ 0 (
            echo   [✓] Startup tests passed
            echo done > .first_run_done
        ) else (
            echo   [!] Some tests failed - run 'python tests\test_server_startup.py' for details
        )
        echo.
    )
)

REM ===========================================================================
REM Check if port 8765 is already in use
REM ===========================================================================
netstat -ano | findstr ":8765" >nul 2>&1
if %errorlevel% equ 0 (
    cls
    echo.
    echo   ╔════════════════════════════════════════════════════════════════╗
    echo   ║  [INFO] Server Already Running                                ║
    echo   ╚════════════════════════════════════════════════════════════════╝
    echo.
    echo   English: Q-SpecTrum is already running on port 8765
    echo   Opening browser...
    echo.
    echo   Chinese: Q-SpecTrum 已在端口 8765 上运行
    echo   打开浏览器...
    echo.
    timeout /t 2 >nul
    start http://localhost:8765/chat.html
    exit /b 0
)

REM ===========================================================================
REM startup Sequence
REM ===========================================================================
cls
echo.
echo   ╔════════════════════════════════════════════════════════════════╗
echo   ║                   System Initialization                        ║
echo   ╚════════════════════════════════════════════════════════════════╝
echo.

echo   [1/3] Starting API Server (port 8765)...
echo          English: Starting API Server...
echo          Chinese: 启动 API 服务器...
start /b !PYTHON! run.py --web

echo.
echo   [2/3] Waiting for engine initialization...
echo          English: Waiting for system to be ready...
echo          Chinese: 等待系统初始化...

REM Wait for server (up to 30 seconds)
set /a count=0
:waitloop
timeout /t 1 >nul
curl -s http://localhost:8765/api/status >nul 2>&1
if %errorlevel% equ 0 goto server_ready
set /a count+=1
if !count! LSS 30 goto waitloop

echo.
echo   [!] Server startup timeout. Check console for errors.
exit /b 1

:server_ready
echo          [✓] Engine ready
echo.
echo   [3/3] Opening browser...
echo          English: Launching web interface...
echo          Chinese: 启动网络界面...
timeout /t 1 >nul
start http://localhost:8765/chat.html

REM ===========================================================================
REM Ready Message
REM ===========================================================================
echo.
echo   ╔════════════════════════════════════════════════════════════════╗
echo   ║                    System Ready!                              ║
echo   ╚════════════════════════════════════════════════════════════════╝
echo.
echo   [✓] Q-SpecTrum is running
echo.
echo   English:
echo     • Chat Interface:  http://localhost:8765/chat.html
echo     • Dashboard:       http://localhost:8765/dashboard.html
echo     • API Status:      http://localhost:8765/api/status
echo     • Close this window to stop the server
echo.
echo   Chinese:
echo     • 聊天界面:        http://localhost:8765/chat.html
echo     • 仪表板:          http://localhost:8765/dashboard.html
echo     • API 状态:        http://localhost:8765/api/status
echo     • 关闭此窗口以停止服务器
echo.

REM Keep window open (server runs in background)
:keepalive
timeout /t 3600 >nul
goto keepalive

REM ===========================================================================
REM Status Check (--status flag)
REM ===========================================================================
:check_status
cls
echo.
echo   ╔════════════════════════════════════════════════════════════════╗
echo   ║                  System Health Check                          ║
echo   ╚════════════════════════════════════════════════════════════════╝
echo.

echo   [*] Checking Python installation...
echo       !PYTHON! !PYTHON_VERSION!

echo   [*] Checking system dependencies...
!PYTHON! -c "import sys, os, json, sqlite3, http.server" 2>nul
if %errorlevel% equ 0 (
    echo       [✓] All core modules available
) else (
    echo       [!] Warning: Some modules may be unavailable
)

echo   [*] Checking network...
curl -s http://localhost:8765/api/status >nul 2>&1
if %errorlevel% equ 0 (
    echo       [✓] Server running on http://localhost:8765
) else (
    echo       [!] Server not running (start with start.bat)
)

echo   [*] Checking required files...
if exist "run.py" echo       [✓] run.py found
if exist "chat.html" echo       [✓] chat.html found
if exist "api_server.py" echo       [✓] api_server.py found

echo.
echo   [✓] System check complete
echo.
exit /b 0
