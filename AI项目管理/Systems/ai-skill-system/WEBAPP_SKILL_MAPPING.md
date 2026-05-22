# WebApp 与 Skill 集成映射指南

> **版本**: v1.0.0  
> **创建**: 2026-04-05  
> **用途**: 解决 `ai-skill-web-app` 与 `deer-flow` Skills 之间的调用与映射关系，实现"文档即代码"的集成。

---

## 🎯 核心问题

*   **现状**: `ai-skill-web-app` 是一个 Next.js 应用，提供多种执行模式（单 Skill、协调官、圆桌等）。
*   **现状**: `deer-flow` 提供了标准化的 Skills（如 `consulting-analysis`, `data-analysis` 等）。
*   **痛点**: 用户在 WebApp 中选择某个模式时，不知道底层调用的是哪个 Skill 文档，也不知道如何自定义。

---

## 🔗 映射关系表 (Mapping Table)

### 1. WebApp 执行模式 vs Skill 文档

| WebApp 模式 | 对应 Skill/配置 | 说明 | 自定义方式 |
| :--- | :--- | :--- | :--- |
| **单 Skill 模式** | `skills/public/{skill_name}/SKILL.md` | 直接调用指定的 Skill | 修改对应 `SKILL.md` 内容 |
| **协调官模式** | `SUPER-SYSTEM-PROMPT.md` | 使用全局协调官提示词 | 修改根目录下的 `SUPER-SYSTEM-PROMPT.md` |
| **全自动模式** | `skills/public/bootstrap/SKILL.md` | 自动规划并执行任务 | 修改 `bootstrap`  Skill |
| **圆桌审议** | `skills/public/consulting-analysis/SKILL.md` | 多角色协作分析 | 修改 `consulting-analysis` Skill |
| **深度精炼** | `skills/public/deep-research/SKILL.md` | 针对特定问题深入研究 | 修改 `deep-research` Skill |

### 2. 前端组件 vs 后端 Skill 配置

| WebApp 组件/页面 | 关联 Skill 配置 | 数据流向 |
| :--- | :--- | :--- |
| `SkillSelector` (技能选择器) | `skills/public/` 目录列表 | 读取目录 -> 渲染列表 -> 用户选择 -> 加载 `SKILL.md` |
| `PromptInput` (提示词输入) | `SKILL.md` 中的 `激活词` | 用户输入 -> 匹配激活词 -> 触发对应 Skill 流程 |
| `OutputViewer` (结果展示) | `SKILL.md` 中的 `交付物` | 执行结果 -> 按照交付物格式渲染 (Markdown/Chart) |

---

## 🛠️ 集成实施步骤

### 第一步：配置 Skill 注册表
在 WebApp 的配置文件中（如 `config/skills.json`），注册可用的 Skills：

```json
[
  {
    "id": "consulting-analysis",
    "name": "咨询分析",
    "path": "../deer-flow/skills/public/consulting-analysis/SKILL.md",
    "description": "提供结构化的商业咨询分析报告",
    "icon": "chart-bar"
  },
  {
    "id": "data-analysis",
    "name": "数据分析",
    "path": "../deer-flow/skills/public/data-analysis/SKILL.md",
    "description": "处理数据并生成可视化图表",
    "icon": "table"
  }
]
```

### 第二步：实现动态加载
在 WebApp 中编写一个 Loader，根据用户选择，动态读取对应的 `SKILL.md` 内容，并将其作为 System Prompt 发送给 LLM。

```typescript
// 伪代码示例
async function loadSkill(skillId: string): Promise<string> {
  const skillConfig = SKILLS_REGISTRY.find(s => s.id === skillId);
  if (!skillConfig) throw new Error("Skill not found");
  
  // 读取 Markdown 文件内容
  const skillContent = await fs.readFile(skillConfig.path, 'utf-8');
  return skillContent;
}
```

### 第三步：前端展示优化
在 WebApp 的"技能详情"页面，直接渲染 `SKILL.md` 的内容，让用户知道当前 AI 正在遵循什么规则工作。

---

## 📂 目录结构建议

```text
ai-skill-system/
├── repos/
│   ├── ai-skill-web-app/       # Web 应用
│   │   ├── config/
│   │   │   └── skills.json     # [新增] Skill 注册表
│   │   └── src/
│   │       └── utils/
│   │           └── skillLoader.ts # [新增] 动态加载器
│   └── deer-flow/              # Skill 定义源
│       └── skills/
│           └── public/         # 标准化 Skills
└── WEBAPP_SKILL_MAPPING.md     # [本文件] 映射说明
```

---

*本指南由 AI Skill 体系协调官创建，旨在打通 WebApp 与 Skill 文档的壁垒*
