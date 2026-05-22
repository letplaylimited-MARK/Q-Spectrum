# 开源技能侦察官 · Open Source Scout

> AI Skill 体系 第三层 · v1.0.0

## 简介

开源技能侦察官是六层 AI Skill 体系中的 **L1 理解层** 成员，专注于将项目需求转化为可落地的开源技能选型方案。

接收用户的项目需求描述，执行标准化的四阶段侦察流程：需求理解 → 开源搜索 → 七维度评估 → 交接包输出，最终交付一份可直接传给 SOP 工程师（Skill 02）的标准化交接包。

## 安装

### CodeBuddy（推荐）

```bash
npx skills add letplaylimited-MARK/skill-03-scout --global --yes
```

### 其他 AI 平台

将 `core/system-prompt-full.md` 内容粘贴到对应平台的系统提示词区域：

| 平台 | 粘贴位置 |
|---|---|
| ChatGPT | 自定义指令 → 「ChatGPT应该如何回应？」|
| Claude | Project Instructions |
| 通义千问 | 角色设定 |
| 文心一言 | 我的助手 → 性格与能力 |
| 讯飞星火 | 系统级提示词 |
| Gemini | Gems → Instructions |

## 触发词

中文：`寻找技能` / `开源技能推荐` / `帮我找开源方案` / `技能评估` / `选型推荐`

英文：`find open source skills` / `recommend open source tools` / `skill evaluation`

## 工作流程

```
用户需求
  │
  ▼ [阶段01/4] 需求理解
  需求分析表 + 技能需求清单（REQ-001格式）
  │ 用户确认
  ▼ [阶段02/4] 开源搜索
  每个需求 2-3 个备选方案（含开源协议/功能描述）
  │ 自动进入
  ▼ [阶段03/4] 七维度评估
  评估矩阵 + 综合得分 + 推荐选择
  │ 用户确认
  ▼ [阶段04/4] 交接包输出
  标准化 YAML 交接包（可直接传给 Skill 02）
```

## 七维度评估矩阵

| 维度 | 权重 |
|---|---|
| 功能性 | 30% |
| 易用性 | 20% |
| 性能 | 15% |
| 可维护性 | 10% |
| 社区活跃度 | 10% |
| 兼容性 | 10% |
| 文档完整性 | 5% |

## 幻觉防护

- Star 数 / 更新日期 → 强制标注 `[需用户核实]`
- 版本号 / 依赖兼容 → 标注 `执行前请验证`
- 找不到方案 → 直言声明 + 三条降级路径

## 在体系中的位置

```
Skill 00（导航官）→ Skill 03（侦察官）→ Skill 02（SOP工程师）→ Skill 05（验收工程师）
```

## 文件结构

```
skill-03-scout/
├── SKILL.md                         ← CodeBuddy 安装入口
├── README.md                        ← 本文档
├── LICENSE                          ← MIT 许可证
├── core/
│   ├── system-prompt-full.md        ← 完整版系统提示词
│   ├── system-prompt-lite.md        ← 精简版（轻量模型）
│   └── activation-card.md          ← 激活卡片（即粘即用）
├── sub-skills/
│   ├── 01-requirement-analysis.md  ← 阶段01：需求理解
│   ├── 02-open-source-search.md    ← 阶段02：开源搜索
│   ├── 03-evaluation-matrix.md     ← 阶段03：七维度评估
│   └── 04-handoff-output.md        ← 阶段04：交接包输出
├── deploy/
│   └── deploy-universal.md         ← 跨平台部署指南
└── docs/
    ├── changelog.md                 ← 版本历史
    └── design-principles.md        ← 设计原则
```

## 相关 Skill

| Skill | 用途 | 关系 |
|---|---|---|
| Skill 00 · 智能体导航官 | 意图识别路由 | 上游 |
| Skill 01 · 超级提示词工程师 | 提示词设计 | 并行协作 |
| Skill 02 · SOP 工程师 | 工程化打包 | 下游（接收交接包B）|
| Skill 04 · AI项目执行规划官 | 生成操作手册 | 下游（可接收本Skill产出）|

## 许可证

MIT License — 详见 LICENSE 文件
