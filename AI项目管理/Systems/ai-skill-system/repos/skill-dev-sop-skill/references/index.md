# References Index — skill-dev-sop
## 参考资料索引

---

## 核心参考文档

### 1. Skill 开发工作流 SOP v2.1.0
**路径**：`/workspace/Skill开发工作流SOP与系统提示词.md`（如已推送至GitHub，见GitHub仓库）

本Skill的直接源文档。包含：
- 10阶段完整工作流逻辑
- 三档系统提示词（完整版/精简版/极简版）
- 提示词工程洞察（5种模式+4条规律）
- 真实案例附录（super-prompt-engineer-skill数据）

**版本历史**：v1.0（初稿）→ v2.0（深度优化）→ v2.1.0（补充即时定位/修复格式/完善安装方案/添加案例）

---

### 2. 超级提示词工程师 Skill（super-prompt-engineer-skill）
**GitHub**：`https://github.com/letplaylimited-MARK/super-prompt-engineer-skill`
**本地路径**：`/workspace/super-prompt-engineer-skill/SKILL.md`
**全局安装路径**：`~/.agents/skills/super-prompt-engineer/`

本Skill的「上游工具」。super-prompt-engineer 负责将原始材料加工为系统提示词，其产出作为 skill-dev-sop 的输入。两个Skill形成「自举式闭环」：

```
原始材料
  → [super-prompt-engineer] →  系统提示词
  → [skill-dev-sop]         →  完整Skill工程包
  → [发布后的Skill]          →  新的能力来开发更多Skill
```

---

### 3. CodeBuddy Skill 规范文档
**参考地址**：CodeBuddy 官方文档（`hot-skills@codebuddy-plugins-official`）

关键规范点：
- SKILL.md frontmatter 格式（name/description/allowed-tools）
- description 字符数限制：≤1024字符（字符数，非字数）
- allowed-tools 最小权限原则
- 触发词激活机制（按需激活，非常驻）
- `npx skills add [repo] --global --yes` 全局安装命令

---

## 设计方法论参考

### 语义化版本控制（Semantic Versioning）
**规范**：`MAJOR.MINOR.PATCH`
- MAJOR：不向后兼容的破坏性变更
- MINOR：向后兼容的新功能添加
- PATCH：向后兼容的缺陷修复

**在本Skill中的应用**：
- v1.0.0：初始发布
- v1.1.0：模拟测试后的P0/P1修复
- v1.x.x：功能迭代
- v2.0.0：架构重构或重大功能变更

---

### IOSE 原则来源
出处：本SOP文档内部定义，基于「单一职责原则」（SRP）和「接口隔离原则」（ISP）的AI Skill工程化适配版本。

---

### PAST 原则来源
出处：本SOP文档内部定义，基于「即插即用」（Plug-and-Play）设计思想，针对AI激活卡片的特殊约束（字符限制/跨平台兼容/零配置）。

---

### NAD 原则来源
出处：本SOP文档内部定义，基于NLP中「自然语言接口」设计最佳实践，适配AI触发词的多样性需求。

---

## 相关工具

| 工具 | 用途 | 链接 |
|---|---|---|
| npx skills CLI | Skill全局安装工具 | npm registry |
| gh CLI | GitHub仓库管理 | https://cli.github.com |
| Python 3.11 | 打包脚本/字符数验证 | 预装于沙箱环境 |
| Bash | 安装验证/文件操作 | 系统内置 |
