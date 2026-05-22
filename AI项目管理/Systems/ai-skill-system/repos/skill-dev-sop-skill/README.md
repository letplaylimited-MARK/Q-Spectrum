# Skill 开发工作流 SOP 工程师
## skill-dev-sop · v1.0.0

> **将任意原始材料系统化开发为可部署 AI Skill 的完整工作流引擎**

---

## 快速安装

```bash
npx skills add letplaylimited-MARK/skill-dev-sop-skill --global --yes
```

安装后，在 CodeBuddy 中输入以下任意触发词即可激活：

- 「开发Skill」
- 「我有文档要做成Skill」
- 「build skill」
- 「我想把想法做成AI能力」

---

## 这是什么？

**Skill Dev SOP Engineer** 是一个专业的 AI Skill 全生命周期开发工作流引擎。它将 Skill 开发过程拆解为严格的10个阶段，通过阶段门控机制确保每个开发步骤都有据可查、可验证。

### 核心价值

| 你有什么 | 你能得到什么 |
|---|---|
| 一个模糊的想法 | 完整的 Skill 工程包 |
| 一份文档/SOP/手册 | 可部署的 AI Skill |
| 一个粗糙的提示词草稿 | 符合格式规范的 SKILL.md |
| 一个已有的 Skill | 优化后的新版本 + Changelog |

---

## 10阶段 SOP 流程

```
阶段01 → 价值深挖      将材料转化为价值地图
阶段02 → 方向决策      生成设计约束书 Design Contract
阶段03 → 工程构建      产出 v1.0.0 完整工程包
阶段04 → 模拟测试      3类虚拟用户 + 递归自举测试
阶段05 → 自主迭代      P0/P1 缺陷自主修复 → v1.1.0
阶段06 → 使用指南      三层漏斗结构用户文档
阶段07 → 通用封装      SKILL.md 格式验证 + .skill打包
阶段08 → GitHub发布    公开仓库 + Raw链接体系
阶段09 → 安装提示词    4种跨平台安装方案
阶段10 → 全局安装      触发词验证 → SOP完成 ✅
```

---

## 工程包结构

```
skill-dev-sop-skill/
├── SKILL.md                    ← CodeBuddy 安装入口（官方格式）
├── README.md                   ← 本文件
├── LICENSE                     ← MIT 许可证
├── core/
│   ├── system-prompt-full.md   ← 完整版系统提示词（强模型推荐）
│   ├── system-prompt-lite.md   ← 精简版系统提示词（轻量模型）
│   └── activation-card.md      ← 极简激活卡片（任意平台即粘即用）
├── sub-skills/                 ← 10个原子化阶段模块
│   ├── 01-value-mining.md
│   ├── 02-direction-decision.md
│   ├── 03-engineering-build.md
│   ├── 04-simulation-test.md
│   ├── 05-autonomous-iteration.md
│   ├── 06-user-guide.md
│   ├── 07-skill-packaging.md
│   ├── 08-github-publish.md
│   ├── 09-install-prompts.md
│   └── 10-global-install.md
├── deploy/
│   ├── deploy-universal.md     ← 4种跨平台部署方案
│   └── package_skill.py        ← 打包脚本
├── docs/
│   ├── changelog.md            ← 版本历史
│   ├── design-principles.md    ← 设计原理文档
│   └── user-guide.md           ← 用户使用指南（阶段06生成）
└── references/
    └── index.md                ← 参考资料索引
```

---

## 核心设计原则

### IOSE — 子Skill拆解原则
**I**ndependent（独立）/ **O**ne-responsibility（单职责）/ **S**tructured output（结构化输出）/ **E**xplicit trigger（明确触发）

### PAST — 安装提示词原则
**P**aste-ready（即粘即用）/ **A**ctivation signal（激活信号）/ **S**elf-contained（自给自足）/ **T**rigger mapping（触发映射）

### NAD — 触发短语设计原则
**N**atural（自然）/ **A**ccurate（精准）/ **D**iverse（多样）

---

## 兼容性

| 平台 | 支持状态 |
|---|---|
| CodeBuddy | ✅ 完整支持（npx全局安装）|
| ChatGPT | ✅ 支持（激活卡片粘贴）|
| Claude | ✅ 支持（激活卡片粘贴）|
| 通义千问 | ✅ 支持（激活卡片粘贴）|
| 文心一言 | ✅ 支持（激活卡片粘贴）|
| 讯飞星火 | ✅ 支持（激活卡片粘贴）|
| Gemini | ✅ 支持（激活卡片粘贴）|

**设计原则**：零平台专属语法，模型无关设计。

---

## 与「超级提示词工程师」Skill 的关系

本Skill 与 [`super-prompt-engineer-skill`](https://github.com/letplaylimited-MARK/super-prompt-engineer-skill) 构成**自举式闭环**：

```
原始材料
  → 超级提示词工程师（加工）→  系统提示词
  → Skill Dev SOP（工程化）→  完整Skill工程包
  → 新Skill（上线后）      →  生产更多Skill
```

**推荐同时安装两个Skill：**

```bash
# 安装超级提示词工程师
npx skills add letplaylimited-MARK/super-prompt-engineer-skill --global --yes

# 安装Skill开发SOP
npx skills add letplaylimited-MARK/skill-dev-sop-skill --global --yes
```

---

## 开发背景

本Skill是用**自举式闭环工程方法论**开发的：
- 原始材料：《Skill开发工作流SOP v2.1.0》文档
- 加工工具：超级提示词工程师 Skill
- 开发流程：遵循本Skill自身描述的10阶段SOP

这意味着：**本Skill本身就是对其设计理念的最好证明**。

---

## 许可证

MIT License — 自由使用、修改、分发。

---

## 作者

**letplaylimited-MARK**

> 「每一个知识体系，都值得被系统化、被工程化、被传播。」
