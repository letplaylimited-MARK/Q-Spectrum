---
entity_type: index
entity_code: M-005
title: AI-Skill-System 导航
created_at: 2026-04-05
updated_at: 2026-04-06
status: active
tags:
  - 导航
  - ai-skill-system
---

# AI-Skill-System 导航

## 简介

本页用于快速定位 `Systems/ai-skill-system/` 相关组件与入口，帮助用户理解该外部系统如何与当前知识库协作，而不是让它反向主导当前项目。

## 系统位置

```text
Systems/ai-skill-system/
├── repos/
│   ├── skill-00-navigator/
│   ├── skill-03-scout/
│   ├── skill-04-planner/
│   ├── skill-05-validator/
│   ├── skill-dev-sop-skill/
│   └── super-prompt-engineer-skill/
```

## 核心仓库

| Skill | 位置 | 说明 |
|---|---|---|
| Navigator (00) | `Systems/ai-skill-system/repos/skill-00-navigator/` | 意图识别与路由 |
| Scout (03) | `Systems/ai-skill-system/repos/skill-03-scout/` | 开源技术选型 |
| Planner (04) | `Systems/ai-skill-system/repos/skill-04-planner/` | 执行规划 |
| Validator (05) | `Systems/ai-skill-system/repos/skill-05-validator/` | 质量验收 |
| SOP Engineer | `Systems/ai-skill-system/repos/skill-dev-sop-skill/` | 技能开发 SOP |
| Prompt Engineer | `Systems/ai-skill-system/repos/super-prompt-engineer-skill/` | 提示词工程 |

## 与当前工作区的关系

| 本工作区文件 | 作用 |
|---|---|
| [案例索引](案例索引.md) | 可作为外部系统的使用案例入口 |
| [技能机会总表](../Skills/技能机会总表.md) | 记录与 ai-skill-system 相关的技能机会 |
| [场景-Skill 映射表](场景-Skill%20映射表.md) | 按场景找对应 Skill |

## 使用建议

1. 把它视为**外部能力来源**，而不是当前项目的主工作区。
2. 当前项目的主知识、记忆、日志、需求仍以 `AI项目管理` 为中心。
3. 如需接入其能力，优先通过文档说明、案例链接、脚本桥接，而不是直接让它覆盖当前项目结构。

## 注意事项

- 该系统是外部引入能力，不应覆盖运营官身份或当前知识库路径规范。
- 所有路径引用必须保持相对路径，基准为 `./AI项目管理/` 目录

## 相关链接

- [案例索引](案例索引.md)
- [场景-Skill 映射表](场景-Skill%20映射表.md)

## 标签

#导航 #外部系统 #ai-skill-system
