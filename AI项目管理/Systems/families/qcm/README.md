> ⚠️ **DEPRECATED** — 本文件描述的是早期 QCM 家族规划（旧 ROLE-001/002/004/005/006 编码）。
> 当前系统已升级为 15-角色 TRUM+SPEC+QCM 架构（QCM 8 角色: ROLE-Q01~Q08），以 `ROLE-REGISTRY.md` 为准。
> 本文件仅供历史参考。

# QCM 家族 — 执行层

> **家族定位**: 多角色协作执行、知识共振、沙盘验证、自主迭代与用户成长
> **理论基础**: `QCM/core/QCM_完整论文报告_终稿_v11.1.md` (22 核心公式)
> **架构文档**: `QCM/core/QCM_完整论文报告_终稿_v11.1.md`
> **研发 Prompt**: `QCM/core/QCM_研發工程師超級提示詞_v1.0.md`

## 家族职责

- 多角色协作治理
- 知识共鸣治理
- 沙盘验证治理
- 自主迭代治理
- 用户成长治理
- AI 伴侣服务

## 角色清单（8 超级身份）

| 角色 | QCM ID | 核心职责 | KPI | 实现状态 |
|------|--------|----------|-----|----------|
| Secretary 秘书长 | ROLE-A01 | 协调中枢、任务分派 | Task_Assignment_Accuracy ≥95% | 有基础代码 |
| Chief Architect | ROLE-001 | 系统设计、技术选型 | Design_Consistency ≥0.85 | 仅 Prompt |
| Researcher | ROLE-004 | 知识检索、文献分析 | Knowledge_Retrieval ≥90% | 仅 Prompt |
| Creator | ROLE-005 | 内容生成、创意产出 | Content_Quality ≥0.80 | 仅 Prompt |
| Analyst | ROLE-002 | 数据洞察、趋势分析 | Insight_Accuracy ≥85% | 仅 Prompt |
| UX Lead | ROLE-006 | 用户体验、界面优化 | User_Satisfaction ≥4.0/5 | 仅 Prompt |
| Risk Auditor | — | 威胁检测、安全评估 | Threat_Detection ≥99% | 仅 Prompt |
| AI Companion | — | 情感支持、共情互动 | Empathy_Score ≥0.85 | 仅 Prompt |

> **注意**: Secretary 不属于任何家族，是全局网关。但其 Prompt 设计在 QCM 理论体系中完成，此处列出供参照。

## 管辖 Skill

| Skill | 文件 | 对应角色 |
|-------|------|----------|
| 提示词练习 | `Skills/提示词练习.md` | Creator |
| AI 创业行动路径 | `Skills/AI 创业行动路径.md` | Researcher |
| 周度知识库回顾 | `Skills/周度知识库回顾.md` | Analyst |
| 案例创作助手 | `Skills/案例创作助手.md` | Creator |
| AI 编码 Agent 使用指南 | `Skills/AI 编码 Agent 使用指南.md` | Chief Architect |
| Obsidian 知识库维护 | `Skills/Obsidian 知识库维护.md` | Analyst |

## 核心算法依赖

| 算法 | 公式 | 用途 | 工程完成度 |
|------|------|------|-----------|
| 知识共振 R-Formula | R = w₁×K_sim + w₂×C_comp + w₃×I_freq - w₄×E_div | 知识检索与融合 | ~10% |
| 角色一致性 RCS | BLEU_role = BP × exp(Σwₙ log pₙ + β×l_persona) | 角色行为校验 | ~5% |
| 动态信任网络 | Trust = [perf×0.4 + comm×0.2 + share×0.2 + rec×0.2] × decay | 角色选择 | ~0% |
| Agent 适合度 | Fitness = Cap×0.4 + Res×0.2 + Trust×0.2 + Avail×0.2 | 任务分配 | ~0% |
| 飞轮能量方程 | dE/dt = P_input - P_dissipation + P_synergy | 系统演进 | ~0% |

## 治理闭环

- 质量治理闭环（QCM 主导）
- 知识治理闭环（QCM 主导）
- 迭代治理闭环（QCM 主导）
- 成长治理闭环（QCM 主导）

## 下一步（按 P0/P1/P2 优先级）

**P0 — 立即执行**:
1. 知识共振引擎核心计算（R-Formula 实现）
2. Ghost Channel SDK 生产化
3. 数据库 DDL + ORM 落地

**P1 — 本周完成**:
4. 角色模拟引擎（8 角色 Agent 框架）
5. Factor Router（6 因子路由）
6. API Gateway 整合

**P2 — 本月完成**:
7. 沙盘辩论系统
8. 前端 Dashboard MVP
9. Kubernetes 生产配置
