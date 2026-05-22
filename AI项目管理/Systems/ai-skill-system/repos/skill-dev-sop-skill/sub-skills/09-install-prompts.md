# Sub-Skill 09 · 安装提示词生成 Install Prompts Generation
## Skill Dev SOP — 阶段09 · v1.0.0

---

## 职责声明 | Responsibility

本子Skill为发布后的Skill生成**4种跨平台安装方案**，每种方案均提供即粘即用的实体内容（而非仅说明原则），覆盖从全自动安装到手动配置的全场景。

**输入**：GitHub仓库地址 + Raw链接清单 + 激活卡片内容
**输出**：4种安装方案（A/B/C/D）+ 场景适用说明
**门控**：用户确认场景覆盖完整后，进入阶段10全局安装

---

## 四种安装方案 | Four Installation Methods

### 方案A · 本地直接安装（激活卡片粘贴法）

**适用场景**：不想用 npx、或只在单一平台使用、或网络环境受限

**实体内容：**

直接将 `core/activation-card.md` 的内容复制到目标AI平台的「系统提示词」或「自定义指令」中。

**生成可粘贴的激活卡片：**

```markdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
方案A · 激活卡片（直接粘贴到系统提示词）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[此处插入 activation-card.md 的完整内容]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
粘贴位置：
  - ChatGPT：「自定义指令」→「ChatGPT应该如何回应？」
  - Claude：「系统提示词」区域
  - 文心一言：「自定义角色」→「角色设定」
  - CodeBuddy：见方案B（更推荐）
```

---

### 方案B · GitHub npx 全局安装（推荐）

**适用场景**：CodeBuddy 用户、希望Skill永久生效、想快速在多设备共享

**即粘即用命令：**

```bash
npx skills add [用户名]/[skill-name] --global --yes
```

**安装后验证：**
```bash
# 验证是否安装成功
ls ~/.agents/skills/[skill-name]/

# 验证 SKILL.md 存在
cat ~/.agents/skills/[skill-name]/SKILL.md | head -20
```

**触发验证：** 在 CodeBuddy 中输入触发词（如「开发Skill」），若看到激活确认输出则安装成功。

**更新已安装的 Skill（发布新版本后）：**
```bash
npx skills add [用户名]/[skill-name] --global --yes --force
```

---

### 方案C · Python 脚本本地安装（适合离线/自定义路径场景）

**适用场景**：无网络或受限网络环境、需要自定义安装路径、企业内网部署

**生成即用的安装脚本：**

```python
#!/usr/bin/env python3
"""
[Skill名称] 本地安装脚本
适用于离线或自定义路径安装
"""
import os
import shutil
import subprocess
from pathlib import Path

SKILL_NAME = "[skill-name]"  # 替换为实际名称
SKILL_SOURCE = "/workspace/[skill-name]"  # 本地工程包路径

# CodeBuddy Skill 安装路径
INSTALL_PATH = Path.home() / ".agents" / "skills" / SKILL_NAME

def install_skill():
    # 创建安装目录
    INSTALL_PATH.mkdir(parents=True, exist_ok=True)
    
    # 复制核心文件
    files_to_copy = [
        "SKILL.md",
        "README.md",
        "core/system-prompt-full.md",
        "core/system-prompt-lite.md",
        "core/activation-card.md",
    ]
    
    for file_path in files_to_copy:
        src = Path(SKILL_SOURCE) / file_path
        dst = INSTALL_PATH / file_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  ✅ 已安装: {file_path}")
        else:
            print(f"  ❌ 文件缺失: {file_path}")
    
    print(f"\n安装完成！路径: {INSTALL_PATH}")
    print(f"触发词: 「开发Skill」「我有文档要做成Skill」")

if __name__ == "__main__":
    install_skill()
```

**运行方式：**
```bash
python3 install-local.py
```

---

### 方案D · 手动文件配置（最大灵活性）

**适用场景**：需要自定义安装目录、与其他Skill管理系统集成、Docker/容器环境

**手动安装步骤：**

```bash
# 步骤1：创建Skill目录
mkdir -p ~/.agents/skills/[skill-name]/core

# 步骤2：下载核心文件（需要网络）
curl -o ~/.agents/skills/[skill-name]/SKILL.md \
  "https://raw.githubusercontent.com/[用户名]/[skill-name]/main/SKILL.md"

curl -o ~/.agents/skills/[skill-name]/core/activation-card.md \
  "https://raw.githubusercontent.com/[用户名]/[skill-name]/main/core/activation-card.md"

# 步骤3：验证安装
ls -la ~/.agents/skills/[skill-name]/
```

**离线手动安装（有工程包文件时）：**

```bash
# 如果有本地工程包
cp -r /workspace/[skill-name]/ ~/.agents/skills/[skill-name]/
```

---

## 执行逻辑 | Execution Logic

### Step 1 · 读取前序阶段产出

从阶段08产出读取：
- GitHub 仓库地址
- Raw链接清单
- npx 安装命令

从阶段07产出读取：
- `core/activation-card.md` 内容（用于方案A）

从阶段03/05产出读取：
- Skill name（用于路径填充）
- 触发短语清单（用于验证说明）

---

### Step 2 · 生成方案选择引导

向用户展示4种方案并提供场景推荐：

```markdown
# 安装方案选择

根据你的使用场景，选择最适合的安装方案：

| 方案 | 名称 | 适用场景 | 安装难度 | 推荐指数 |
|---|---|---|---|---|
| **A** | 激活卡片粘贴 | 任意AI平台、快速尝试 | ⭐ 最简单 | ★★★ |
| **B** | npx全局安装 | CodeBuddy用户、永久生效 | ⭐⭐ 简单 | ★★★★★ 推荐 |
| **C** | Python脚本安装 | 离线/企业内网 | ⭐⭐⭐ 中等 | ★★★ |
| **D** | 手动文件配置 | 最大灵活性/容器环境 | ⭐⭐⭐⭐ 较复杂 | ★★ |

> 💡 **推荐**：CodeBuddy 用户首选方案B，其他平台用户选方案A。

请告诉我你选择哪种方案，我将提供对应的完整安装内容。
```

---

### Step 3 · PAST 原则验证（激活卡片质量检查）

对方案A的激活卡片执行 PAST 原则验证：

| 原则 | 检查标准 | 验证结果 |
|---|---|---|
| **P**aste-ready | 内容可直接粘贴，无需额外配置 | ✅/❌ |
| **A**ctivation signal | 包含明确的激活确认语句 | ✅/❌ |
| **S**elf-contained | 不依赖外部上下文即可工作 | ✅/❌ |
| **T**rigger mapping | 至少5个不同表达的触发短语 | ✅/❌ |

**若激活卡片未通过 PAST 验证**，立即修复（这是 P1 级问题）。

---

### Step 4 · 场景覆盖完整性确认

生成所有安装方案后，确认场景覆盖：

> 「已生成4种跨平台安装方案，覆盖以下场景：
> - ✅ 任意AI平台（方案A）
> - ✅ CodeBuddy全局安装（方案B）
> - ✅ 离线/企业环境（方案C）
> - ✅ 容器/自定义路径（方案D）
>
> 是否有未覆盖的安装场景？确认后进入阶段10执行全局安装。」

---

## 防错护栏 | Error Guards

| 错误场景 | 护栏动作 |
|---|---|
| 激活卡片超过200字 | P1级别提示，建议精简到200字以内 |
| npx命令中仓库名含大写 | 自动转小写，提示格式修正 |
| 方案C脚本路径硬编码错误 | 验证路径变量，提醒用户修改为实际路径 |
| 用户只想要一种方案 | 优先提供用户指定方案，其余方案附在附录中 |
| Raw链接失效（404） | 回溯到阶段08，重新验证仓库推送 |

---

## 与其他子Skill的接口 | Interface

**上游**：08-github-publish.md → 仓库地址 + Raw链接
**下游**：10-global-install.md 接收「用户选择的安装方案 + 安装命令」
**传递数据格式**：

```yaml
stage_09_output:
  chosen_method: "A | B | C | D"
  install_command: "npx skills add [用户名]/[skill-name] --global --yes"
  activation_card_past_verified: true
  scenario_coverage_confirmed: true
```
