@echo off
REM ============================================================================
REM Q-SpecTrum User Data Backup (Windows)
REM Creates a timestamped zip of everything the user has personally accumulated,
REM so they can restore state to a fresh Q-SpecTrum folder or migrate machines.
REM ============================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Q-SpecTrum User Data Backup
color 0D

echo.
echo   ╔════════════════════════════════════════════════════════════════╗
echo   ║             Q-SpecTrum User Data Backup                        ║
echo   ║                   用戶資料備份                                   ║
echo   ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM Build timestamp
for /f "tokens=1-3 delims=/- " %%a in ('date /t') do set TODAY=%%c%%a%%b
for /f "tokens=1-2 delims=:" %%a in ('time /t') do set NOW=%%a%%b
set TS=%TODAY%-%NOW%
set ZIP=qspectrum-backup-%TS%.zip

echo   Target: %ZIP%
echo.
echo   Packing user-accumulated state...
echo   打包使用中累積的資料...
echo.

REM Check PowerShell availability (used for zipping)
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo   [✗] PowerShell not found — required for zip creation.
    echo   [✗] 需要 PowerShell 才能壓縮，請手動備份下列檔案。
    pause
    exit /b 1
)

REM Files/folders to back up (things the user has generated or customized):
REM  - MEMORY.md                     (cross-session notes)
REM  - .env                          (user's LLM config if set up)
REM  - _HANDOFF\                     (session handoff snapshots)
REM  - contact_channel.db, project_memory.db, projects.db, task_manager.db,
REM    knowledge_pipeline.db, user_resources.db, decision_layer.db,
REM    result_layer.db, knowledge_checkpoint.db, qspectrum.db (runtime state)
REM  - AI项目管理\Platform\db\platform.db  (custom knowledge, if edited)

echo   Creating %ZIP%...
powershell -NoProfile -Command "Compress-Archive -Force -DestinationPath '%ZIP%' -Path @('MEMORY.md','.env','_HANDOFF','contact_channel.db','project_memory.db','projects.db','task_manager.db','knowledge_pipeline.db','knowledge_checkpoint.db','user_resources.db','decision_layer.db','result_layer.db','qspectrum.db','AI项目管理/Platform/db/platform.db') 2>$null"

if exist "%ZIP%" (
    echo.
    echo   [✓] Backup created: %ZIP%
    for %%A in ("%ZIP%") do echo   [i] Size: %%~zA bytes
    echo.
    echo   To restore on a fresh Q-SpecTrum folder:
    echo     1. Extract this zip inside the target folder
    echo     2. Say "yes" to overwrite prompts
    echo     3. Run start.bat
    echo.
    echo   還原步驟：將此 zip 解壓到新的 Q-SpecTrum 資料夾內即可。
) else (
    echo   [✗] Backup failed.
)

echo.
pause
