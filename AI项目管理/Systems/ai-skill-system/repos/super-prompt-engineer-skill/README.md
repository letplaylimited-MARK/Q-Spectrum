# 超级提示词工程师 Skill
# Super Prompt Engineer Skill

> 通用AI大模型提示词工程师 — 兼容 GPT / Claude / Qwen / 文心一言 / 通义千问 / 讯飞星火 / Gemini

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](./CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Models](https://img.shields.io/badge/models-GPT%20%7C%20Claude%20%7C%20Qwen%20%7C%20文心%20%7C%20通义%20%7C%20星火-orange.svg)](#兼容模型)

---

## 这是什么？

一个将**任意 AI 大模型激活为专业提示词工程师**的 Skill，具备 6 项核心能力，中英双语，零平台专属语法，投喂即用。

| 能力 | 触发词 |
|---|---|
| 🔧 提示词优化 | 优化提示词 / optimize prompt |
| 🗂️ 工作流设计 | 设计工作流 / design workflow |
| 📊 报告生成 | 生成报告 / generate report |
| 🎯 痛点引导 | 梳理痛点 / analyze issues |
| 🗄️ 数据库整理 | 整理数据库 / organize files |
| 🔄 迭代追踪 | 记录迭代 / track iteration |

---

## 快速开始（3 种方式）

### 方式一：即粘即用（最快，30秒）

复制 [`activation-card.md`](./core/activation-card.md) 全文 → 粘贴到任意 AI 对话开头发送 → 立即激活。

### 方式二：完整系统提示词（推荐，5分钟）

复制 [`core/system-prompt-full.md`](./core/system-prompt-full.md) 全文 → 作为 AI 的 System Prompt 注入。

### 方式三：CodeBuddy Skill 安装（持久化）

在 CodeBuddy 中输入以下提示词直接安装：

```
请从以下 GitHub 地址安装 Skill：
https://github.com/letplaylimited-MARK/super-prompt-engineer-skill

下载 SKILL.md 文件内容，按照 CodeBuddy Skill 标准格式激活「超级提示词工程师」角色与全部6项能力。
```

或直接下载安装包：[`super-prompt-engineer.skill`](./super-prompt-engineer.skill)

---

## 文件结构

```
super-prompt-engineer-skill/
├── SKILL.md                          # CodeBuddy Skill 标准格式（核心）
├── super-prompt-engineer.skill       # 打包安装文件
├── README.md                         # 本文件
├── CHANGELOG.md                      # 版本更新记录
├── core/
│   ├── system-prompt-full.md         # 完整版系统提示词（~4000 tokens）
│   ├── system-prompt-lite.md         # 精简版（~1500 tokens，兼容轻量模型）
│   └── activation-card.md            # 极简激活卡片（30秒即用）
├── sub-skills/
│   ├── 01-prompt-optimizer.md        # 子Skill：提示词优化
│   ├── 02-workflow-designer.md       # 子Skill：工作流设计
│   ├── 03-report-generator.md        # 子Skill：报告生成
│   ├── 04-pain-point-guide.md        # 子Skill：痛点引导
│   ├── 05-database-organizer.md      # 子Skill：数据库整理
│   └── 06-iteration-tracker.md       # 子Skill：迭代追踪
├── deploy/
│   └── deploy-universal.md           # 8大平台部署指南
└── docs/
    ├── 完整用户使用指南.md             # 完整使用指南
    ├── design-principles.md           # 设计原则
    ├── simulated-usage-report.md      # 模拟用户测试报告
    └── CHANGELOG.md                   # 版本历史
```

---

## 兼容模型

| 模型 | 兼容性 | 说明 |
|---|---|---|
| GPT-4o / GPT-4 / GPT-3.5 | ✅ 完整 | 最佳性能 |
| Claude 3.5 / 3 / 2 | ✅ 完整 | 推荐配合 Projects 使用 |
| Qwen 7B–3.5 | ✅ 完整 | 中文优化输出 |
| 文心一言 3.5 / 4.0 | ✅ 完整 | 中文优先模式 |
| 通义千问 Turbo / Plus | ✅ 完整 | 全能力激活 |
| 讯飞星火 V3 / V4 | ✅ 完整 | 全能力激活 |
| Gemini Pro | ✅ 完整 | 英文优先模式 |
| 任意 ≥4K 上下文模型 | ✅ 兼容 | 上下文受限时用精简版 |

---

## 各平台部署

详见 [`deploy/deploy-universal.md`](./deploy/deploy-universal.md)，覆盖：

- ChatGPT Custom Instructions / GPTs
- Claude Projects
- Coze Bot
- Dify / FastGPT
- 文心一言 / 通义千问 / 讯飞星火
- API 调用（Python / Node.js / HTTP）
- 企业私有化部署

---

## 设计原则

- **模型无关性**：零平台专属语法，任意模型零偏差运行
- **中英双语自适应**：自动检测用户语言
- **优雅降级**：强模型全功能，弱模型核心功能保底
- **自包含**：无外部依赖，投喂即运行
- **内置进化**：自动复盘触发，持续迭代优化

---

## 版本历史

见 [`CHANGELOG.md`](./CHANGELOG.md)

**当前版本 v1.1.0** — 基于3类用户模拟测试，修复7项真实缺陷（激活引导、温度智能化、自动复盘触发等）

---

## License

MIT License — 自由使用、修改、分发
