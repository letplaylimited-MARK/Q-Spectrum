@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo.
echo ========================================
echo Q-SpecTrum Installation Script
echo Q-SpecTrum 安装脚本
echo ========================================
echo.

echo Checking Python installation...
echo 检查 Python 安装情况...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo 错误: Python 未安装或未在 PATH 中
    echo Please install Python 3.8+ from https://www.python.org
    echo 请从 https://www.python.org 安装 Python 3.8+
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%
echo 找到 Python 版本: %PYTHON_VERSION%
echo.

echo Installing requirements...
echo 安装依赖包...
if exist requirements.txt (
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo WARNING: Failed to install requirements (but continuing anyway)
        echo 警告: 无法安装依赖包 (但继续)
        echo.
    )
) else (
    echo No requirements.txt found (project uses only standard library)
    echo 未找到 requirements.txt (项目仅使用标准库)
)
echo.

echo ========================================
echo Installation Complete
echo 安装完成
echo ========================================
echo.
echo Starting Q-SpecTrum Web Server...
echo 启动 Q-SpecTrum 网络服务器...
echo.

python run.py --web
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start server
    echo 错误: 无法启动服务器
    echo.
    pause
    exit /b 1
)

pause
