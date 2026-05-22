# Q-SpecTrum 智腦啟動腳本 (Windows PowerShell)
# Usage: .\start.ps1 [--provider mock|openai|anthropic]
#
# 啟動順序：
#   1. 執行 verify-integration.py（健康檢查）
#   2. 執行 test_e2e.py（端到端驗證）
#   3. 啟動 MCP Server（等待調用）

param(
    [string]$provider = "mock"
)

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ROOT

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Q-SpecTrum 智腦啟動程序" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Health Check
Write-Host "[Step 1/3] 執行整合驗證..." -ForegroundColor Yellow
python verify-integration.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "健康檢查失敗，請先修復問題。" -ForegroundColor Red
    exit 1
}
Write-Host "健康檢查通過。" -ForegroundColor Green
Write-Host ""

# Step 2: End-to-End Test
Write-Host "[Step 2/3] 執行端到端驗證..." -ForegroundColor Yellow
python test_e2e.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "端到端驗證失敗，請檢查日誌。" -ForegroundColor Red
    exit 1
}
Write-Host "端到端驗證通過。" -ForegroundColor Green
Write-Host ""

# Step 3: Start MCP Server
Write-Host "[Step 3/3] 啟動 MCP Server (provider: $provider)..." -ForegroundColor Yellow
Write-Host "MCP Server 運行中，等待 stdin 調用..." -ForegroundColor Green
Write-Host "可透過 pipe JSON-RPC 訊息至此程序。" -ForegroundColor Gray
Write-Host "範例: echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}' | python qspectrum_mcp_server.py" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan

python qspectrum_mcp_server.py --provider $provider
