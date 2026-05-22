# Sub-Skill 08 · GitHub 发布 GitHub Publish
## Skill Dev SOP — 阶段08 · v1.0.0

---

## 职责声明 | Responsibility

本子Skill将完整工程包推送到 GitHub 公开仓库，建立标准化的文件树和 Raw 链接体系，为阶段09的安装提示词和阶段10的全局安装提供地址基础。

**输入**：v1.1.0 完整工程包（已格式验证通过）
**输出**：GitHub 公开仓库 + 完整文件树 + Raw 链接清单
**门控**：文件树验证通过（关键文件均可访问）后，进入阶段09

---

## 执行逻辑 | Execution Logic

### Step 1 · GitHub 仓库信息收集

在开始推送前，收集必要信息：

**需要用户提供：**

```
仓库信息确认
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GitHub 用户名：[用户输入]
仓库名称：[skill-name]（通常与Skill的name字段一致）
仓库可见性：公开（Public）← 必须公开，否则npx无法安装
仓库描述：[自动生成，用户可修改]
默认分支：main
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**自动生成仓库描述（基于SKILL.md description前100字符）：**

```python
# 提取description前100字符作为仓库描述
skill_description = """[SKILL.md中的description内容]"""
repo_description = skill_description[:100].replace('\n', ' ').strip()
```

---

### Step 2 · 推送前准备

**初始化 Git 仓库（若尚未初始化）：**

```bash
cd /workspace/[skill-name]
git init
git branch -M main
```

**创建 `.gitignore`（排除不需要推送的文件）：**

```bash
cat > .gitignore << 'EOF'
# Python 缓存
__pycache__/
*.pyc
*.pyo

# 临时文件
*.tmp
*.log

# 打包产物（避免二进制文件污染仓库）
*.skill

# 系统文件
.DS_Store
Thumbs.db
EOF
```

**注意**：`.skill` 文件不推送到 GitHub（是打包产物），GitHub 仓库只包含源文件。

---

### Step 3 · 创建 GitHub 仓库

使用 `gh` CLI 创建公开仓库：

```bash
# 创建仓库
gh repo create [用户名]/[skill-name] \
  --public \
  --description "[自动生成的仓库描述]" \
  --source=. \
  --remote=origin \
  --push

# 验证推送成功
gh repo view [用户名]/[skill-name]
```

**若仓库已存在（迭代发布场景）：**

```bash
git remote add origin https://github.com/[用户名]/[skill-name].git
git add .
git commit -m "feat: [skill-name] v1.1.0 — [简短描述]"
git push -u origin main
```

---

### Step 4 · 推送文件树标准化

确保以下文件树完整推送，不遗漏任何关键文件：

**必须包含的文件（缺失则停止发布）：**

| 文件路径 | 重要性 | 说明 |
|---|---|---|
| `SKILL.md` | 🔴 P0必须 | CodeBuddy 安装入口 |
| `README.md` | 🟡 P1应有 | 项目说明（GitHub首页展示）|
| `LICENSE` | 🟡 P1应有 | 开源许可证 |
| `core/system-prompt-full.md` | 🟡 P1应有 | 完整版系统提示词 |
| `core/system-prompt-lite.md` | 🟢 P2建议 | 精简版系统提示词 |
| `core/activation-card.md` | 🟡 P1应有 | 极简激活卡片 |
| `docs/user-guide.md` | 🟡 P1应有 | 用户使用指南 |
| `docs/changelog.md` | 🟡 P1应有 | 版本历史 |

---

### Step 5 · Raw 链接体系生成

推送完成后，生成关键文件的 Raw 访问链接：

**Raw 链接格式：**
```
https://raw.githubusercontent.com/[用户名]/[仓库名]/main/[文件路径]
```

**自动生成的完整链接清单：**

```markdown
# Raw 链接清单

## 核心安装链接
- SKILL.md：
  https://raw.githubusercontent.com/[用户名]/[skill-name]/main/SKILL.md

## 系统提示词链接
- 完整版：
  https://raw.githubusercontent.com/[用户名]/[skill-name]/main/core/system-prompt-full.md
- 精简版：
  https://raw.githubusercontent.com/[用户名]/[skill-name]/main/core/system-prompt-lite.md
- 激活卡片：
  https://raw.githubusercontent.com/[用户名]/[skill-name]/main/core/activation-card.md

## 文档链接
- 使用指南：
  https://raw.githubusercontent.com/[用户名]/[skill-name]/main/docs/user-guide.md
- Changelog：
  https://raw.githubusercontent.com/[用户名]/[skill-name]/main/docs/changelog.md

## npx 安装命令
npx skills add [用户名]/[skill-name] --global --yes
```

---

### Step 6 · 文件树验证

发布后，通过访问 Raw 链接验证文件可达性：

```bash
# 验证 SKILL.md 可访问
curl -s -o /dev/null -w "%{http_code}" \
  "https://raw.githubusercontent.com/[用户名]/[skill-name]/main/SKILL.md"
# 期望输出：200

# 验证目录树
gh repo view [用户名]/[skill-name] --json files
```

**文件树验证报告：**

```
文件树验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SKILL.md            → [200/404]
README.md           → [200/404]
core/system-prompt-full.md → [200/404]
core/activation-card.md    → [200/404]
docs/user-guide.md  → [200/404]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
通过：[N]/5 项
```

**门控条件**：SKILL.md 必须可访问（HTTP 200），其余文件建议可访问。

---

### Step 7 · 发布完成汇报

```markdown
## 🚀 GitHub 发布完成 · 阶段08

**仓库地址**：https://github.com/[用户名]/[skill-name]
**发布版本**：v1.1.0
**文件数量**：[N] 个文件

### 快速安装命令
```bash
npx skills add [用户名]/[skill-name] --global --yes
```

### 文件树验证
[验证报告]

---
🚦 **阶段08门控**：SKILL.md 可访问，进入阶段09生成安装提示词
```

---

## 防错护栏 | Error Guards

| 错误场景 | 护栏动作 |
|---|---|
| 仓库设为私有 | 强制提示：「必须设为公开仓库，否则 npx 安装会失败」|
| SKILL.md 未在根目录 | 提示文件位置错误，必须在根目录 |
| Raw链接返回404 | 检查文件是否实际推送，等待1~2分钟后重试（GitHub CDN延迟）|
| 用户名/仓库名含大写字母 | 提示 npm registry 不支持大写，建议改为全小写+连字符 |
| 仓库名与Skill name不一致 | 提示可能导致混淆，建议保持一致 |
| git push 失败（权限） | 检查 gh auth status，引导用户重新登录 |

---

## 与其他子Skill的接口 | Interface

**上游**：07-skill-packaging.md → 格式验证通过的工程包
**下游**：09-install-prompts.md 接收「GitHub 仓库地址 + Raw链接清单」
**传递数据格式**：

```yaml
stage_08_output:
  github_repo: "https://github.com/[用户名]/[skill-name]"
  skill_md_raw_url: "https://raw.githubusercontent.com/[用户名]/[skill-name]/main/SKILL.md"
  npx_install_command: "npx skills add [用户名]/[skill-name] --global --yes"
  file_tree_verified: true
  published_version: "1.1.0"
```
