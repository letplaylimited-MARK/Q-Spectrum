@echo off
REM ============================================================================
REM Q-SpecTrum Delivery Cleanup (Windows)
REM Removes development artifacts before zipping/shipping the folder.
REM Safe to run repeatedly.
REM ============================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Q-SpecTrum Delivery Cleanup
color 0E

echo.
echo   ╔════════════════════════════════════════════════════════════════╗
echo   ║             Q-SpecTrum Delivery Cleanup                        ║
echo   ║                    交付前清理                                   ║
echo   ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo   Removing development artifacts...
echo   清除開發殘留...
echo.

REM Python bytecode caches
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d" 2>nul
        echo     [✓] removed: %%d
    )
)

REM Ruff cache
if exist .ruff_cache (
    rmdir /s /q .ruff_cache 2>nul
    echo     [✓] removed: .ruff_cache
)

REM First-run marker
if exist .first_run_done (
    del /q .first_run_done 2>nul
    echo     [✓] removed: .first_run_done
)

REM Temp env files from test runs
if exist .env.tmp (
    del /q .env.tmp 2>nul
    echo     [✓] removed: .env.tmp
)

REM SQLite runtime write-test artifacts
for %%f in (.write_test* .runtime_write_test* .sqlite_write_test*) do (
    if exist "%%f" (
        del /q "%%f" 2>nul
        echo     [✓] removed: %%f
    )
)

REM Ephemeral files left by verification / testing runs
for %%f in (test_size_*.txt test_utf8.txt test_write_r4.txt test_write_*.txt) do (
    if exist "%%f" (
        del /q "%%f" 2>nul
        echo     [✓] removed: %%f
    )
)

REM User data backups (receiver should make their own)
for %%f in (qspectrum-backup-*.tar.gz qspectrum-backup-*.zip) do (
    if exist "%%f" (
        del /q "%%f" 2>nul
        echo     [✓] removed backup: %%f
    )
)

REM SQLite journal files
for %%f in (*.db-journal *.db-wal *.db-shm) do (
    if exist "%%f" (
        del /q "%%f" 2>nul
        echo     [✓] removed journal: %%f
    )
)

REM DB folder write-test artifacts
for %%f in ("AI项目管理\Platform\db\_bintest.bin" "AI项目管理\Platform\db\_writetest.txt") do (
    if exist "%%f" (
        del /q "%%f" 2>nul
        echo     [✓] removed: %%f
    )
)

REM R17 reverse-thinking probe scratchpads
for %%f in (ROUND17_PROBE_DRIFT_NEW_DOC.md ROUND17_PROBE_TEST.md ROUND17_TEST.md) do (
    if exist "%%f" (
        del /q "%%f" 2>nul
        echo     [✓] removed probe scratch: %%f
    )
)

REM Secondary DB files (keep only platform.db + platform_restored.db)
for %%f in (contact_channel.db decision_layer.db knowledge_checkpoint.db knowledge_graph.db knowledge_pipeline.db project_memory.db projects.db qspectrum.db result_layer.db task_manager.db user_resources.db) do (
    if exist "%%f" (
        del /q "%%f" 2>nul
        echo     [✓] removed runtime: %%f
    )
)

echo.
echo   ──────────────────────────────────────────────────────────────
echo   Delivery-ready size:
echo   交付大小：
dir /s /a | findstr "File(s)" | findstr /v "Dir(s)"
echo.
echo   NOTE: .git/ is NOT removed automatically. If you want to strip
echo         git history from the delivery, run:  rmdir /s /q .git
echo.
echo   備註：.git/ 不會自動清除。若要移除 git 歷史：
echo         rmdir /s /q .git
echo   ──────────────────────────────────────────────────────────────
echo.

pause
