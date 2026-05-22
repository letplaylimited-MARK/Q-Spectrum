@echo off
REM ============================================================================
REM Q-SpecTrum Health Check (Windows)
REM Double-click to run a quick health check. Keeps the window open at the end
REM so you can read the result.
REM ============================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Q-SpecTrum Health Check
color 0B

echo.
echo   ╔════════════════════════════════════════════════════════════════╗
echo   ║               Q-SpecTrum Health Check                          ║
echo   ║                     健康檢查                                    ║
echo   ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM ── Find Python ──
set PYTHON=
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 set PYTHON=python3
)

if "!PYTHON!"=="" (
    echo [✗] Python not found.
    echo     Python 未安裝。請到 https://www.python.org/downloads/ 下載 Python 3.8+
    echo.
    pause
    exit /b 1
)

echo [✓] Python detected: !PYTHON!
echo.
echo   Running full system status check...
echo   執行完整系統狀態檢查中...
echo.

!PYTHON! run.py --status

echo.
echo   ──────────────────────────────────────────────────────────────
echo   Summary:  If you see "System: ALL GREEN", the system is ready.
echo             If anything shows ❌, check FIXES-APPLIED.md for help.
echo.
echo   總結：    若顯示 "System: ALL GREEN" 表示系統就緒。
echo             若有 ❌ 錯誤，請參考 FIXES-APPLIED.md
echo   ──────────────────────────────────────────────────────────────
echo.

pause
