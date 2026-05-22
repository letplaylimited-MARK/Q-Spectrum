# 跨平台部署方案 Universal Deployment Guide
## skill-dev-sop · v1.0.0

---

## 部署方案总览

本文档为「Skill 开发工作流 SOP 工程师」Skill 提供4种跨平台安装与部署方案，覆盖从零门槛的激活卡片粘贴到企业级容器部署的全场景。

---

## 方案A · 激活卡片直接粘贴（零门槛）

**适用平台**：ChatGPT、Claude、文心一言、通义千问、讯飞星火、Gemini、任意支持系统提示词的AI平台

**步骤**：
1. 打开 `core/activation-card.md`
2. 复制全部内容
3. 粘贴到目标平台的「系统提示词」或「自定义指令」区域
4. 输入触发词验证激活

**各平台粘贴位置：**

| 平台 | 粘贴位置 |
|---|---|
| ChatGPT | 「自定义指令」→「ChatGPT应该如何回应？」|
| Claude | 「Project instructions」或对话起始系统提示 |
| 通义千问 | 「角色设定」|
| 文心一言 | 「我的助手」→「助手设置」|
| Gemini | 「Gems」→ 创建自定义Gem |
| CodeBuddy | 推荐使用方案B |

---

## 方案B · GitHub npx 全局安装（推荐，CodeBuddy优选）

**适用平台**：CodeBuddy（全功能支持，推荐）

**安装命令（一键执行）：**

```bash
npx skills add letplaylimited-MARK/skill-dev-sop-skill --global --yes
```

**安装验证：**

```bash
# 验证安装目录
ls ~/.agents/skills/skill-dev-sop/

# 验证核心文件
head -20 ~/.agents/skills/skill-dev-sop/SKILL.md
```

**更新到最新版本：**

```bash
npx skills add letplaylimited-MARK/skill-dev-sop-skill --global --yes --force
```

---

## 方案C · Python 脚本安装（离线/企业内网）

**适用场景**：无公网访问、企业内网部署、自定义安装路径

**生成安装脚本：**

将以下脚本保存为 `install.py`，运行即可安装：

```python
#!/usr/bin/env python3
"""skill-dev-sop 本地安装脚本"""
import os
import shutil
from pathlib import Path

# 配置区（根据实际情况修改）
SKILL_SOURCE = "/workspace/skill-dev-sop-skill"  # 工程包路径
SKILL_NAME = "skill-dev-sop"
INSTALL_BASE = Path.home() / ".agents" / "skills"

INSTALL_PATH = INSTALL_BASE / SKILL_NAME
INSTALL_PATH.mkdir(parents=True, exist_ok=True)

# 核心文件列表
files = [
    "SKILL.md",
    "README.md",
    "core/system-prompt-full.md",
    "core/system-prompt-lite.md",
    "core/activation-card.md",
    "docs/user-guide.md",
    "docs/changelog.md",
]

for f in files:
    src = Path(SKILL_SOURCE) / f
    dst = INSTALL_PATH / f
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        shutil.copy2(src, dst)
        print(f"✅ {f}")
    else:
        print(f"❌ 缺失: {f}")

print(f"\n安装完成: {INSTALL_PATH}")
print("触发词: 「开发Skill」「我有文档要做成Skill」")
```

**运行：**
```bash
python3 install.py
```

---

## 方案D · 手动文件配置（最大灵活性）

**适用场景**：Docker容器、CI/CD流水线、自定义AI平台集成

**手动安装步骤（需要网络）：**

```bash
# 创建安装目录
mkdir -p ~/.agents/skills/skill-dev-sop/core
mkdir -p ~/.agents/skills/skill-dev-sop/docs

# 下载核心文件
BASE_URL="https://raw.githubusercontent.com/letplaylimited-MARK/skill-dev-sop-skill/main"

curl -s -o ~/.agents/skills/skill-dev-sop/SKILL.md "$BASE_URL/SKILL.md"
curl -s -o ~/.agents/skills/skill-dev-sop/core/activation-card.md "$BASE_URL/core/activation-card.md"
curl -s -o ~/.agents/skills/skill-dev-sop/core/system-prompt-full.md "$BASE_URL/core/system-prompt-full.md"
curl -s -o ~/.agents/skills/skill-dev-sop/docs/user-guide.md "$BASE_URL/docs/user-guide.md"

echo "安装完成！"
```

**Docker 部署示例：**

```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y curl
RUN mkdir -p /root/.agents/skills/skill-dev-sop/core
RUN curl -s -o /root/.agents/skills/skill-dev-sop/SKILL.md \
    "https://raw.githubusercontent.com/letplaylimited-MARK/skill-dev-sop-skill/main/SKILL.md"
# 添加更多文件...
```

---

## 部署后验证流程

无论使用哪种方案，安装后执行以下验证：

```
安装验证步骤
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
步骤1：确认文件存在
  ls ~/.agents/skills/skill-dev-sop/SKILL.md
  → 期望：文件存在

步骤2：触发词激活测试
  输入：「开发Skill」
  → 期望：输出激活确认菜单

步骤3：功能验证
  输入：「A」（选择从零开始）
  → 期望：进入阶段01价值深挖引导

验证通过 ✅ → 部署成功
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 版本管理

| 操作 | 命令 |
|---|---|
| 安装最新版 | `npx skills add letplaylimited-MARK/skill-dev-sop-skill --global --yes` |
| 强制更新 | 同上加 `--force` |
| 查看已安装版本 | `cat ~/.agents/skills/skill-dev-sop/SKILL.md \| head -5` |
| 卸载 | `rm -rf ~/.agents/skills/skill-dev-sop/` |
