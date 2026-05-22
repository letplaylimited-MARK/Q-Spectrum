# 新项目创建标准化工具

## 强制合规规则
✅ 所有新项目必须创建在 Q-SpecTrum 根目录下的 `Projects\` 目录
✅ 禁止使用带空格的项目名称
✅ 所有生成文件必须存储在合法路径下

## 快速创建新项目函数
```powershell
function New-QSpecProject {
    <#
    .SYNOPSIS
    创建符合规范的Q-SpecTrum新项目
    .PARAMETER ProjectName 项目名称，禁止包含空格
    .EXAMPLE
    New-QSpecProject -ProjectName "AI-Skill-System"
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$ProjectName
    )
    # 校验项目名称是否包含空格
    if ($ProjectName -match "\s") {
        Write-Error "❌ 项目名称不能包含空格，请使用横杠(-)或下划线(_)代替"
        return
    }
    $projectPath = Join-Path (Split-Path $PSScriptRoot -Parent) "Projects\$ProjectName"
    if (-not (Test-Path -Path $projectPath)) {
        New-Item -Path $projectPath -ItemType Directory -Force
        Write-Host "✅ 新项目已创建：$projectPath"
        # 创建基础目录结构
        New-Item -Path "$projectPath\Docs" -ItemType Directory -Force
        New-Item -Path "$projectPath\Assets" -ItemType Directory -Force
        New-Item -Path "$projectPath\Scripts" -ItemType Directory -Force
        New-Item -Path "$projectPath\Tests" -ItemType Directory -Force
        Write-Host "✅ 已创建基础项目目录结构：Docs/Assets/Scripts/Tests"
    } else {
        Write-Warning "⚠️ 项目已存在：$projectPath"
    }
}
```

## 路径合法性校验函数
```powershell
function Test-ValidPath {
    <#
    .SYNOPSIS
    校验路径是否符合Q-SpecTrum合规要求
    .PARAMETER Path 要校验的路径
    #>
    param(
        [string]$Path
    )
    $errors = @()
    # 检查是否包含空格
    if ($Path -match "\s") {
        $errors += "❌ 路径包含空格"
    }
    # 检查是否在Q-SpecTrum目录下
    if (-not ($Path -like "*Q-SpecTrum*")) {
        $errors += "❌ 路径不在合法总工作区Q-SpecTrum下"
    }
    if ($errors.Count -eq 0) {
        Write-Host "✅ 路径合法：$Path"
        return $true
    } else {
        Write-Host "⚠️ 路径校验失败："
        $errors | ForEach-Object { Write-Host $_ }
        return $false
    }
}
```

## 使用说明
1. 加载函数：将上述代码复制到PowerShell中执行
2. 创建项目：运行`New-QSpecProject -ProjectName "项目名称"`
3. 校验路径：运行`Test-ValidPath -Path "要校验的路径"`