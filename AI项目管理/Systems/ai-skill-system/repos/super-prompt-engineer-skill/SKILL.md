# Super Prompt Engineer Skill
# 超级提示词工程师 Skill

**Version 版本**: 1.0.0  
**Compatible Models 兼容模型**: GPT-3.5/4/4o · Claude 2/3 · Qwen 1.8B–3.5 · 文心一言 3.5/4.0 · 通义千问 · 讯飞星火 V3/V4 · Gemini · 及所有支持长文本的通用大模型  
**Language 语言**: 中文 / English（双语自适应）  
**Context Requirement 上下文需求**: ≥ 4000 tokens（完整版）/ ≥ 1500 tokens（精简版）

---

## What This Skill Does · 这个 Skill 做什么

This Skill transforms any general-purpose AI model into a **Professional Prompt Engineer**，capable of:

这个 Skill 将任何通用 AI 大模型激活为一名**专业提示词工程师**，具备以下能力：

| Capability 能力 | Trigger Keywords 触发关键词 |
|---|---|
| Prompt Optimization 提示词优化 | 优化提示词 / optimize prompt / 这个指令有问题 |
| Workflow Design 工作流设计 | 设计流程 / design workflow / 拆解步骤 |
| Report Generation 报告生成 | 生成报告 / generate report / 写复盘 |
| Pain Point Analysis 痛点梳理 | 梳理痛点 / analyze issues / 我遇到了问题 |
| Database Organization 数据库整理 | 整理数据库 / organize files / 分类归档 |
| Iteration Tracking 迭代追踪 | 记录迭代 / track iteration / 更新版本 |

---

## How to Use · 使用方法

### Method 1: Direct Injection（直接注入）
Copy the contents of `core/system-prompt-full.md` as the **System Prompt** of your AI session.  
将 `core/system-prompt-full.md` 的内容完整复制，作为 AI 对话的**系统提示词**注入。

### Method 2: File Upload（文件上传）
Upload `core/system-prompt-full.md` directly to your AI conversation.  
直接将 `core/system-prompt-full.md` 上传至 AI 对话窗口，AI 会自动读取并激活。

### Method 3: Platform Deploy（平台部署）
See `deploy/` folder for platform-specific guides.  
查看 `deploy/` 目录中各平台的专属部署指南。

---

## File Structure · 文件结构

```
super-prompt-engineer-skill/
├── skill.md                        # 本文件 / This file（Skill 入口说明）
├── core/
│   ├── system-prompt-full.md       # 完整版系统提示词（推荐，≥4000 tokens）
│   └── system-prompt-lite.md       # 精简版系统提示词（≤1500 tokens，兼容轻量模型）
├── sub-skills/
│   ├── 01-prompt-optimizer.md      # 子Skill：提示词优化
│   ├── 02-workflow-designer.md     # 子Skill：工作流设计
│   ├── 03-report-generator.md      # 子Skill：报告生成
│   ├── 04-pain-point-guide.md      # 子Skill：痛点引导
│   ├── 05-database-organizer.md    # 子Skill：数据库整理
│   └── 06-iteration-tracker.md     # 子Skill：迭代追踪
├── templates/
│   ├── prompt-optimization.md      # 提示词优化模板
│   ├── workflow-definition.md      # 工作流定义模板
│   ├── report-retrospective.md     # 复盘报告模板
│   └── database-classification.md # 数据库分类模板
├── deploy/
│   ├── deploy-chatgpt.md          # ChatGPT / GPTs 部署指南
│   ├── deploy-claude.md           # Claude Projects 部署指南
│   ├── deploy-coze.md             # Coze 部署指南
│   ├── deploy-dify.md             # Dify 部署指南
│   └── deploy-universal.md        # 通用平台部署指南
└── docs/
    ├── design-principles.md        # 设计原则说明
    └── changelog.md                # 版本更新记录
```

---

## Core Design Principles · 核心设计原则

1. **Model-Agnostic 模型无关性**: No platform-specific syntax. Works on any model.  
   无任何模型专属语法，在任意模型上零偏差运行。

2. **Bilingual Adaptive 双语自适应**: Responds in the user's language automatically.  
   自动检测用户语言，中文用户收到中文输出，英文用户收到英文输出。

3. **Graceful Degradation 能力降级**: Full features on strong models, core features on lite models.  
   强模型运行全功能，弱模型自动简化输出保证基础可用。

4. **Self-Contained 自包含**: No external dependencies required.  
   无需外部工具或依赖，投喂即运行。

5. **Iterative Evolution 迭代进化**: Built-in retrospective loop for continuous improvement.  
   内置复盘闭环，每次执行后自动优化。
