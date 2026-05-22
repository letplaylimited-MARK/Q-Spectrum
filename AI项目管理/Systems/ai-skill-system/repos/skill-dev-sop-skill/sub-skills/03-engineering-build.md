# Sub-Skill 03 · 工程构建 Engineering Build
## Skill Dev SOP — 阶段03 · v1.0.0

---

## 职责声明 | Responsibility

本子Skill是整个SOP的**核心生产阶段**，接收设计约束书，输出 v1.0.0 完整工程包。工程包包含所有可交付文件：SKILL.md、系统提示词（三档）、子Skill模块、使用指南草稿、工程目录结构。

**输入**：已确认的设计约束书 Design Contract
**输出**：v1.0.0 完整工程包（标准目录结构 + 全部核心文件）
**门控**：用户确认文件结构后，按需展开每个文件内容

---

## 执行逻辑 | Execution Logic

### Step 1 · 工程目录规划

根据设计约束书生成标准目录结构，展示给用户确认后开始生成：

```
[skill-name]/
├── SKILL.md                    ← CodeBuddy 官方格式入口（必须）
├── README.md                   ← 项目说明 + 快速开始
├── LICENSE                     ← MIT 许可证
├── core/
│   ├── system-prompt-full.md   ← 完整版系统提示词（~4000 tokens）
│   ├── system-prompt-lite.md   ← 精简版系统提示词（~1500 tokens）
│   └── activation-card.md      ← 极简激活卡片（≤200字，PAST原则）
├── sub-skills/                 ← 子Skill模块（按需生成）
│   ├── [阶段名].md
│   └── ...
├── deploy/
│   └── deploy-universal.md     ← 跨平台部署方案
├── docs/
│   ├── changelog.md            ← 版本历史
│   └── design-principles.md    ← 设计原理文档
└── references/                 ← 参考资料索引
    └── index.md
```

**确认提问**：
> 「以上是工程包的完整目录结构，是否符合你的期望？如有调整请告知，确认后我将逐一生成每个文件。」

---

### Step 2 · SKILL.md 生成规范

SKILL.md 是整个工程包最关键的文件，必须严格遵循 CodeBuddy 官方格式规范：

**格式规范检查清单：**

```yaml
# 必须通过的格式检查
格式要求：
  □ YAML frontmatter 以三横线开始和结束
  □ name: 全小写 + 连字符（kebab-case），无空格无特殊字符
  □ description: 字符数 ≤ 1024（字符≠字数，需精确计算）
  □ description 包含：功能摘要 + 使用场景 + 触发短语（中英双语）
  □ allowed-tools: 最小权限原则，只声明实际需要的工具
  □ 正文：角色定义 + 激活输出 + 核心工作流 + 执行原则
```

**description 字符数计算方法：**

```python
# 验证 description 是否超过 1024 字符
description = """..."""
print(f"字符数: {len(description)}")
# 汉字算1个字符，英文字母算1个字符
# 目标：≤1024字符
```

**SKILL.md 正文核心结构：**

1. **角色定义**（Role Identity）
   - 名称、版本、核心职责
   - 语言约定
   - 工作模式声明

2. **激活确认输出**（Activation Response）
   - 固定的激活输出模板（用代码块包裹，避免与正文混淆）
   - 引导用户选择起点的菜单（A/B/C/D选项）

3. **核心工作流**（Core Workflow）
   - 阶段映射表（快速定位用）
   - 每个阶段的执行逻辑摘要
   - 门控条件说明

4. **执行原则**（Execution Principles）
   - E1~E7原则（来自SOP文档标准）
   - 用户引导机制
   - 防错护栏

---

### Step 3 · 三档系统提示词生成

**档位一：完整版（Full Version）**

- 适用：支持长上下文的强推理模型（GPT-4, Claude, Gemini Pro等）
- 长度：3000~5000 tokens
- 内容：完整角色定义 + 全部阶段逻辑 + 所有原则 + 话术模板 + 输出格式
- 格式：结构化Markdown，**避免多层嵌套代码块**（P0级格式规范）

**档位二：精简版（Lite Version）**

- 适用：中等能力模型或上下文受限场景
- 长度：1000~2000 tokens
- 内容：角色定义 + 阶段流程图 + 关键门控 + 核心执行原则
- 特点：砍掉话术模板，保留逻辑骨架

**档位三：极简激活卡（Activation Card）**

- 适用：任意平台「即粘即用」场景
- 长度：≤200字
- 遵循 PAST 原则：
  - **P**aste-ready（直接粘贴可用）
  - **A**ctivation signal（内含明确触发词）
  - **S**elf-contained（自给自足，无需其他上下文）
  - **T**rigger mapping（包含3~5个不同表达的触发短语）

**激活卡片模板：**

```
你是[Skill名称]。当用户输入以下触发词时立即激活：
[触发词1] / [触发词2] / [触发词3]

激活后输出：
[激活回复内容，包含引导菜单]

执行原则：[2-3条最核心原则]
```

---

### Step 4 · 子Skill模块生成策略

根据设计约束书的C1（交付形态）决定子Skill数量：

| 复杂度 | 子Skill数量 | 适用场景 |
|---|---|---|
| 简单 | 1~3个 | 单一功能Skill |
| 中等 | 4~6个 | 多流程Skill |
| 复杂 | 7~10个 | 完整SOP工作流Skill |

**子Skill文件命名规范：**
- `[NN]-[kebab-case-name].md`
- 例：`01-value-mining.md`, `07-skill-packaging.md`

**每个子Skill文件必须包含：**
1. 职责声明（输入/输出/门控）
2. 执行逻辑（Step by Step）
3. 防错护栏（错误场景对照表）
4. 输出模板（用户可直接参考的输出示例）
5. 接口定义（与上下游子Skill的数据传递格式）

---

### Step 5 · 工程包完整性验证

在所有文件生成后，执行完整性自检：

```
工程包完整性检查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ SKILL.md 存在且格式合规
□ description 字符数 ≤ 1024
□ allowed-tools 已声明（最小权限）
□ 三档系统提示词均已生成
□ 子Skill模块数量符合设计约束
□ README.md 包含快速开始指南
□ LICENSE 文件存在
□ changelog.md 记录 v1.0.0 初始版本
□ deploy-universal.md 包含4种安装方案
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
通过：[N]/9 项
```

**门控提问：**
> 「v1.0.0 工程包已生成完毕，完整性检查 [N]/9 项通过。请确认文件内容是否符合预期，或指出需要调整的部分。确认后进入阶段04模拟测试。」

---

## IOSE 子Skill拆解原则应用

构建子Skill时，每个子模块必须满足 IOSE 原则：

| 原则 | 全称 | 在子Skill中的体现 |
|---|---|---|
| **I**ndependent | 独立性 | 每个子Skill可单独调用，不强依赖其他子Skill |
| **O**ne-responsibility | 单一职责 | 每个子Skill只负责SOP的1个阶段，不跨阶段 |
| **S**tructured output | 结构化输出 | 每个子Skill有固定的输出模板 |
| **E**xplicit trigger | 明确触发 | 每个子Skill有明确的「进入条件」和「退出条件」 |

---

## 防错护栏 | Error Guards

| 错误场景 | 护栏动作 |
|---|---|
| description 超过1024字符 | 立即截断并提示：「description已超限，已自动精简至[N]字符」 |
| allowed-tools 声明了过多工具 | 警告并建议最小权限方案 |
| SKILL.md 正文包含嵌套代码块 | P0格式错误，立即修复（改为段落描述或单层代码块） |
| 子Skill之间有循环依赖 | 重新设计接口，消除循环 |
| 工程包文件缺失 | 列出缺失文件，等待用户确认后补全 |
| 用户要求跳过子Skill直接到SKILL.md | 建议：「子Skill是模块化设计的基础，建议保留；若时间紧迫，可先生成SKILL.md，后续补全」 |

---

## 输出模板 | Output Template

```markdown
## 🔨 工程构建完成 · 阶段03完成

**Skill名称**：[name]
**版本**：v1.0.0
**文件总数**：[N]个

### 工程包目录树
[目录结构]

### 关键文件摘要
| 文件 | 大小 | 状态 |
|---|---|---|
| SKILL.md | [N]字符 | ✅ 格式合规 |
| system-prompt-full.md | ~[N] tokens | ✅ 已生成 |
| system-prompt-lite.md | ~[N] tokens | ✅ 已生成 |
| activation-card.md | [N]字 | ✅ ≤200字 |

### 完整性检查
[检查报告]

---
🚦 **阶段03门控**：确认工程包后进入阶段04模拟测试
```

---

## 与其他子Skill的接口 | Interface

**上游**：02-direction-decision.md → 已确认的设计约束书
**下游**：04-simulation-test.md 接收「v1.0.0 完整工程包路径 + 文件清单」
**传递数据格式**：

```yaml
stage_03_output:
  package_path: "/workspace/[skill-name]/"
  skill_md_char_count: [N]
  file_count: [N]
  completeness_score: "[N]/9"
  version: "1.0.0"
```
