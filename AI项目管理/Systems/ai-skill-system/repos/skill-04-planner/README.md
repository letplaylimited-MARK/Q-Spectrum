# Skill 04 · Planner — AI 项目执行规划官

> **核心职责**：将 SOP 工程包转化为人可执行的分阶段操作手册

[![Version](https://img.shields.io/badge/version-v1.0.0-blue)](CHANGELOG.md)
[![System](https://img.shields.io/badge/system-v1.0-green)](../ai-skill-system/system/MASTER-BLUEPRINT.md)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

---

## 概述

Skill 04 · Planner 是六层 AI Skill 体系的**第四层**。接收来自 Skill 02（SOP 工程师）的 SOP 文档，将其转化为任何人都能按步骤执行的操作手册。

**Planner 不写代码，不做技术决策** — 它只负责将已有方案变成清晰可执行的行动计划。

---

## 核心特性

- **三层任务结构**：Phase / Task / Step，每个 Step 有唯一编号（P1-T2-S3）
- **断点可恢复**：每个 Phase 结束有状态检查点，中断后可从任意阶段重启
- **操作手册≠计划文档**：所有步骤都是可直接执行的动作（有动词、工具、预期结果）
- **时间三点估算**：乐观/正常/悲观三种估算，使用 PERT 计算期望工时
- **幻觉防护**：版本号/价格/API 限制全部标注 [需用户核实]

---

## 工作流

```
输入：SOP 工程包（来自 Skill 02）
    │
    ▼
阶段一：SOP 解析 → 输出理解摘要（等待用户确认）
    │
    ▼
阶段二：三层任务拆解 → Phase/Task/Step 结构化
    │
    ▼
阶段三：操作手册生成 → 完整 Markdown 手册
    │
    ▼
阶段四：交接包输出 → 传给 Skill 05 或用户
```

---

## 文件结构

```
skill-04-planner/
├── SKILL.md                          # Skill 元信息
├── README.md                         # 本文件
├── LICENSE                           # MIT License
├── core/
│   ├── system-prompt-full.md         # 完整系统提示词（含操作手册模板）
│   └── system-prompt-lite.md         # 精简版
├── sub-skills/
│   ├── 01-sop-parser.md              # SOP 解析器
│   ├── 02-task-breakdown.md          # 三层任务拆解器
│   ├── 03-manual-generator.md        # 操作手册生成器
│   └── 04-handoff-output.md          # 交接包输出（→用户/→Skill05）
└── deploy/
    └── deploy-universal.md           # 跨平台部署指南
```

---

## 快速开始

1. 将 `core/system-prompt-full.md` 设为系统提示词
2. 粘贴来自 Skill 02 的 SOP 工程包（或直接描述项目）
3. 确认 Planner 的解析摘要
4. 等待完整操作手册生成

---

## 操作手册结构

生成的操作手册包含：

| 章节 | 内容 |
|------|------|
| 项目概览 | 目标/交付物/成功标准/技术栈 |
| 环境配置 | 系统要求/安装步骤/验证方法 |
| 各阶段手册 | 分步操作/预期结果/验证方式 |
| FAQ | 常见问题和解决方案 |
| 断点恢复指南 | 状态查看/恢复入口对应表 |

---

## 体系位置

```
Skill 00（Navigator）→ 路由
Skill 01（翻译官）  → 需求结构化
Skill 03（侦察官）  → 技术选型
Skill 02（SOP师）   → 工程SOP  ──→  Skill 04（规划官）→ 操作手册
                                                        │
                                          ┌─────────────┘
                                          ▼
                              OpenCode / Cursor / Aider 等 Agent 执行层
                              （将操作手册作为 Prompt 输入，自主完成代码任务）
                                          │
                                          ▼
                                Skill 05（验收师）→ PASS / FAIL
```

---

## 与 OpenCode 等 Agent 工具协同

Skill 04 输出的操作手册（Markdown 格式）可直接作为 Prompt 输入到 OpenCode、Cursor、Aider 等编程 Agent，让 AI 自主完成代码层面的执行工作，形成完整的 **规划 → 执行 → 验收** 闭环。

| 文档 | 内容 |
|------|------|
| [OPENCODE_INTEGRATION.md](./OPENCODE_INTEGRATION.md) | OpenCode + 多大模型集成总览（四种方案、架构说明、效益分析） |
| [OPENCODE_QUICKSTART.md](./OPENCODE_QUICKSTART.md) | 30 分钟快速上手（Ollama / Gemini / Claude / Qwen-Agent 四套配置） |

**典型工作流：**

```
Skill 04 输出操作手册
    ↓
复制 Markdown → opencode --model gemini/pro-2.0
    ↓
OpenCode Agent Loop 自主执行（5-10 轮）
    ↓
Skill 05 验收 → PASS / FAIL
```

---

## License

MIT © letplaylimited-MARK
