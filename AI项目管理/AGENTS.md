# ⚠️ DEPRECATED — 本文件已過時 / This file is outdated

> **權威版本在根目錄**: `../AGENTS.md` (v5.0, 2026-04-18)
> **權威角色表在根目錄**: `../ROLE-REGISTRY.md` (15角色, v3.2)
>
> 本文件保留為歷史參考。以下內容描述的是 v1.0 時期的 3 角色舊系統（ROLE-001/002/003），
> 已被根目錄的 15 角色系統（TRUM 4 + SPEC 3 + QCM 8）完全取代。

---

# AI项目管理 母模板 - 路径与角色管控 (v3.0)

> 继承自 Q-SpecTrum 根目录 AGENTS.md, 此文件为母模板级别的补充约束。

## 合法路径

```
根目录: ./AI项目管理 (相对于 Q-SpecTrum 根目录)
```

## 已注册角色 (3 + N)

| 角色编码 | 角色名称 | 身份文件 | 激活卡 |
|---------|---------|---------|-------|
| ROLE-001 | AI 首席数据库与角色系统架构师 (SPEC-001/DBA) | `Platform/registry/identity-card.md` | `roles/SPEC-001_Chief_Architect.md` |
| ROLE-002 | AI 项目运营官 (SPEC-002/OP-001) | `Systems/operator/identities/operator.md` | `roles/SPEC-002_Operations_Officer.md` |
| ROLE-003 | AI Skill 体系协调官 (SPEC-003/COORD-001) | `Systems/operator/identities/COORDINATOR_DEFINITIVE.md` | `roles/SPEC-003_Coordination_Officer.md` |

## 6-Skill Pipeline

```
00-Navigator → 01-提示词工程师 → 02-SOP工程师 → 03-Scout → 04-Planner → 05-Validator
```

## 记忆架构 (5 层)

| 层级 | 路径 | 内容 |
|-----|------|------|
| L1 身份 | `Systems/operator/identities/` | 角色定义 |
| L2 用户 | `Systems/operator/user/PROFILE.md` | 用户偏好 |
| L3 项目 | `Systems/operator/projects/PRJ-xxx.md` | 项目状态 |
| L4 运营 | `Systems/operator/operations/LOG.md` | 执行痕迹 |
| L5 知识 | `Maps/KnowledgeGraph.md` | 知识图谱 |
