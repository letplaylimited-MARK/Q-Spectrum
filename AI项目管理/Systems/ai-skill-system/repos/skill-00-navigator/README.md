# Skill 00 · Navigator — AI Skill 体系路由入口

> **核心职责**：分析用户意图 → 判断置信度 → 路由到正确 Skill → 输出标准化交接包

[![Version](https://img.shields.io/badge/version-v1.0.0-blue)](CHANGELOG.md)
[![System](https://img.shields.io/badge/system-v1.0-green)](../ai-skill-system/system/MASTER-BLUEPRINT.md)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

---

## 概述

Skill 00 · Navigator 是六层 AI Skill 体系的**总入口**。当用户不确定从哪里开始、或需要在多个 Skill 之间导航时，Navigator 负责：

1. **意图识别**：分析用户输入，匹配到7种意图类型
2. **置信度评估**：计算路由置信度（0-100%）
3. **路由决策**：直接路由 / 确认路由 / 追问澄清
4. **交接包生成**：输出标准化 YAML，用户手动搬运到目标 Skill

---

## 六层 Skill 体系

| Skill | 名称 | 职责 |
|-------|------|------|
| **Skill 00** | Navigator | 路由入口（本 Skill）|
| Skill 01 | 需求翻译官 | 将模糊想法结构化为需求文档 |
| Skill 02 | SOP 工程师 | 将需求转化为可执行开发 SOP |
| Skill 03 | 开源侦察官 | 搜索评估开源方案，七维度评估 |
| Skill 04 | 执行规划官 | 生成分阶段项目执行手册 |
| Skill 05 | 测试验收工程师 | 验收测试，生成发布决策报告 |

---

## 快速开始

### 方法一：激活卡激活（推荐）

复制 [`core/activation-card.md`](core/activation-card.md) 中的标准激活文本，粘贴到新对话开头。

### 方法二：系统提示词激活

将 [`core/system-prompt-full.md`](core/system-prompt-full.md) 设置为 AI 系统提示词。

### 方法三：精简版激活（token 受限）

使用 [`core/system-prompt-lite.md`](core/system-prompt-lite.md)。

---

## 路由逻辑

```
用户输入
    │
    ▼
意图识别（sub-skills/01）
    │
    ▼
置信度计算
    ├── ≥ 80% → 直接路由 → 输出交接包
    ├── 60-79% → 确认路由 → 用户确认 → 输出交接包
    └── < 60% → 追问（≤3次）→ 澄清后路由
```

---

## 文件结构

```
skill-00-navigator/
├── SKILL.md                        # Skill 元信息（≤1024字符）
├── README.md                       # 本文件
├── LICENSE                         # MIT License
├── core/
│   ├── system-prompt-full.md       # 完整系统提示词
│   ├── system-prompt-lite.md       # 精简版系统提示词
│   └── activation-card.md          # 激活卡（三档）
├── sub-skills/
│   ├── 01-intent-recognition.md    # 意图识别引擎
│   ├── 02-confidence-routing.md    # 置信度路由决策器
│   └── 03-handoff-generator.md     # 交接包生成器
└── deploy/
    └── deploy-universal.md         # 跨平台部署指南
```

---

## 交接包示例

```yaml
schema_version: "1.0"
from_skill: "skill-00-navigator"
to_skill: "skill-01-translator"
confidence: 0.91
intent_type: "NEW_PROJECT_IDEA"
payload:
  user_request: "我想做一个客户反馈分析的AI智能体"
  clarified_intent: "新AI项目，需要从需求结构化开始"
  context:
    domain: "客户服务"
    tech_stack: null
    project_stage: "ideation"
user_action: "请将此 YAML 粘贴到 Skill 01 对话开头，然后描述您的项目详情"
```

---

## 体系文档

- [体系总蓝图](../ai-skill-system/system/MASTER-BLUEPRINT.md)
- [接口契约规范](../ai-skill-system/interface-contracts/)
- [飞轮机制设计](../ai-skill-system/system/flywheel-mechanism.md)
- [系统变更日志](../ai-skill-system/system/system-changelog.md)

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2025-01 | 初始发布，支持6 Skill路由，置信度三级路由 |

---

## License

MIT © letplaylimited-MARK
