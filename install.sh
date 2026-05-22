#!/bin/bash

echo ""
echo "========================================"
echo "Q-SpecTrum Installation Script"
echo "Q-SpecTrum 安装脚本"
echo "========================================"
echo ""

# Check if Python is installed
echo "Checking Python installation..."
echo "检查 Python 安装情况..."

if ! command -v python3 &> /dev/null; then
    echo ""
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "错误: Python 3 未安装或未在 PATH 中"
    echo "Please install Python 3.8+ using your package manager"
    echo "请使用包管理器安装 Python 3.8+"
    echo "  macOS: brew install python3"
    echo "  Linux: sudo apt-get install python3"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python version: $PYTHON_VERSION"
echo "找到 Python 版本: $PYTHON_VERSION"
echo ""

echo "Installing requirements..."
echo "安装依赖包..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo ""
        echo "WARNING: Failed to install requirements (but continuing anyway)"
        echo "警告: 无法安装依赖包 (但继续)"
        echo ""
    fi
else
    echo "No requirements.txt found (project uses only standard library)"
    echo "未找到 requirements.txt (项目仅使用标准库)"
fi
echo ""

echo "========================================"
echo "Installation Complete"
echo "安装完成"
echo "========================================"
echo ""
echo "Starting Q-SpecTrum Web Server..."
echo "启动 Q-SpecTrum 网络服务器..."
echo ""

python3 run.py --web
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to start server"
    echo "错误: 无法启动服务器"
    echo ""
    exit 1
fi
