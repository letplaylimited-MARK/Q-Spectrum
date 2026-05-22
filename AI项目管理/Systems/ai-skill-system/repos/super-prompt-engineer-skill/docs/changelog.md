# Changelog · 版本更新记录

## v1.1.0 · 2025-07-15

**类型**: Minor Release · 基于模拟用户使用的自主优化版本  
**触发机制**: 3类用户（小白/企业/开发者）模拟执行 → 发现10项真实缺陷 → P0/P1级缺陷自主修复  
**模拟执行报告**: 详见 `docs/simulated-usage-report.md`

### 修复内容（P0 级）

**Fix #1 · 激活引导优化** (`core/system-prompt-full.md`)
- 问题: 激活后仅列出能力清单，用户不知下一步该说什么
- 修复: 在激活确认末尾增加主动引导首句，提供 A/B/C 三个场景选项，降低首次使用门槛

**Fix #3 · 提示词优化温度建议智能化** (`sub-skills/01-prompt-optimizer.md`)
- 问题: 所有优化后提示词统一写死「温度=0」，对内容创作场景是错误建议
- 修复: 增加任务类型判断逻辑（执行型/创作型/混合型），分别推荐 0 / 0.7-0.9 / 0.4-0.6 温度

**Fix #5 · 自动复盘触发机制** (`core/system-prompt-full.md`)
- 问题: 复盘完全依赖用户主动触发，实际使用率接近零
- 修复: 新增 P8 原则「自动复盘触发」：用户发出结束信号或单次会话执行 3+ 任务时，自动输出≤50字简短复盘

### 修复内容（P1 级）

**Fix #2 · 信息收集渐进化** (`sub-skills/01-prompt-optimizer.md`)
- 问题: Step 1 一次要求三项信息，对小白用户造成压力
- 修复: 改为「渐进式单问」——首先只问提示词本身，其他信息根据内容自动推断或稍后询问

**Fix #10 · 防御性回复人性化** (`core/system-prompt-full.md`)
- 问题: 防御触发时回复「无法执行该操作」，生硬且无引导
- 修复: 改为「说明冲突原因 + 提供合法调整路径」的友好格式

### 修复内容（P1 级 · 其他文件）

**Fix #4 · 工作流最后一列自适应** (`sub-skills/02-workflow-designer.md`)
- 问题: 「关联模板」列对普通用户是无意义的噪音
- 修复: 根据用户类型自动切换最后一列为「工具/平台」（普通用户）或「关联模板」（开发者）

**Fix #7 · 报告类型兜底规则** (`sub-skills/03-report-generator.md`)
- 问题: 5种固定报告类型无法覆盖用户的多样化文档需求
- 修复: 新增「通用结构化文档」兜底类型，并触发主动询问目的与受众的引导话术

### 待修复（列入 v1.2.0）

- [ ] **#6** 增加团队协作场景专属处理逻辑（多人提示词库共享、版本冲突处理）
- [ ] **#8** 增加中英混用提示词的语言统一处理规则
- [ ] **#9** 新增极简 API 版（<200 tokens）供开发者使用
- [ ] 增加行业专属扩展包（教育/营销/研发/法律/医疗）
- [ ] 增加多模态任务支持（图像、音频提示词优化）

---

## v1.0.0 · 2025-01-01

**类型**: Major Release · 首次发布  
**基于**: 通用AI大模型超级提示词工程师训练文档 V4.0 终极整合版

### 新增内容
- `skill.md` — Skill 入口说明文件（中英双语）
- `core/system-prompt-full.md` — 完整版系统提示词（~4000 tokens）
- `core/system-prompt-lite.md` — 精简版系统提示词（~1500 tokens）
- `sub-skills/01-prompt-optimizer.md` — 提示词优化子Skill
- `sub-skills/02-workflow-designer.md` — 工作流设计子Skill
- `sub-skills/03-report-generator.md` — 报告生成子Skill
- `sub-skills/04-pain-point-guide.md` — 痛点引导子Skill
- `sub-skills/05-database-organizer.md` — 数据库整理子Skill
- `sub-skills/06-iteration-tracker.md` — 迭代追踪子Skill
- `deploy/deploy-universal.md` — 通用平台部署指南（含8大平台）
- `docs/design-principles.md` — 设计原则说明

### 核心设计决策
1. 采用「模型无关性」设计，零平台专属语法
2. 全程中英双语并排，支持所有主流中英文模型
3. 完整版 + 精简版双轨，支持强/弱模型优雅降级
4. 6个子Skill原子化拆解，支持独立使用与自由组合

