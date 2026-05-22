# 版本历史 · Changelog
## 智能体导航官 · AI Navigator

---

## v1.0.1 — 2025年（当前版本）

### 修复与完善

**修复（P1）**：
- 统一 `from_skill` 标识符：`"skill-00"` → `"skill-00-navigator"`，与体系接口契约对齐

**文档（P3）**：
- 新增 `docs/changelog.md` 和 `docs/design-principles.md`
- activation-card.md 补充使用示例

---

## v1.0.0 — 2025年（首发版本）

### 首次发布

**新增**：
- 置信度三级路由（≥80%直接路由 / 60-79%确认 / <60%追问≤3次）
- 七种意图类型注册表（NEW_PROJECT_IDEA / REQUIREMENTS_EXIST / OPEN_SOURCE_SCOUT 等）
- 多 Skill 组合路由（有序执行路径 Step 1→2→3→4→5）
- 标准化交接包 A（YAML格式，含 intent_type/confidence/routing_reason）
- 三档激活卡（单行版/标准版/极简版）
- Skill 能力注册表（六 Skill 精确边界）
- 防错护栏（三次追问后强制路由到 Skill 01）

**技术规格**：
- SKILL.md description：394字符（合规，≤1024）
- 触发词：中文8个，英文6个
- 工程包文件数：10个

---

## 已知限制

| 编号 | 限制 | 计划版本 |
|---|---|---|
| LIM-001 | 用户需手动搬运交接包，非自动路由 | System v2.0.0（平台编排层）|
| LIM-002 | 置信度由 AI 主观判断，偶有误判 | v1.1.0（增加意图确认机制）|

---

## 未来路线图

### v1.1.0（计划）
- 新增「意图历史」：在同一对话中记住上一次路由结果，避免重复追问
- 增加「快速模式」：用户明确说出 Skill 编号时直接确认，不经过置信度计算

### v2.0.0（远期）
- 与平台编排引擎集成，实现真实的 Skill 间自动调用（非手动搬运）
