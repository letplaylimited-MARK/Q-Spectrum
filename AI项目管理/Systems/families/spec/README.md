> ⚠️ **DEPRECATED** — 本文件描述的是早期 Spec 家族规划（Spec-R001/R002/R003 + 旧 ROLE-001/002/003 映射）。
> 当前系统已升级为 15-角色 TRUM+SPEC+QCM 架构，以 `ROLE-REGISTRY.md` 和 `SPEC-001/002/003` 角色卡为准。
> 本文件仅供历史参考。

# Spec 家族 — 架构层

> **家族定位**: 系统架构守护、标准合规与配置一致性
> **旧模型映射**: ROLE-001 DBA Architect 的架构职能扩展
> **架构文档**: `QCM/core/QCM_完整论文报告_终稿_v11.1.md`

## 家族职责

- 路径合规治理
- 三角色协作治理
- 主模板完整性治理
- 配置一致性治理

## 角色清单

| 角色 ID | 名称 | 核心职责 | 旧模型对应 | 实现状态 |
|---------|------|----------|-----------|----------|
| Spec-R001 | 首席架构师/DBA | 路径设计、主模板维护 | ROLE-001 DBA Architect | 部分就绪（旧模型可用） |
| Spec-R002 | 运维官 | 配置一致性、合规检查 | ROLE-002 Operator 部分 | 部分就绪（旧模型可用） |
| Spec-R003 | 协调官/QCM桥接 | Spec 与 QCM 协作 | ROLE-003 部分 | 待实现 |

## 管辖 Skill

| Skill | 文件 | 说明 |
|-------|------|------|
| 可执行 Skill 包生产 | `Skills/可执行 Skill 包生产.md` | 标准化 Skill 创建流程 |
| Agent 运维助手 | `Skills/Agent 运维助手.md` | 运维操作 SOP |

## 与旧模型的关系

Spec-R001 首席架构师直接继承 ROLE-001 DBA Architect 的全部能力，并扩展到"系统级架构守护"。
Spec-R002 运维官继承 ROLE-002 Operator 的运维职能，但将6动态能力槽位保留在 COORD-001 体系中。
Spec-R003 协调官为新增角色，负责 Spec 与 QCM 家族之间的桥接协调。

## 治理闭环

- 合规治理闭环（Spec 主导）
- 角色治理闭环（跨家族，Spec 参与标准定义）

## 下一步

1. 基于 ROLE-001 编写 Spec-R001 扩展 Prompt
2. 基于 ROLE-002/COORD-001 编写 Spec-R002 Prompt
3. 设计 Spec-R003 QCM 桥接协议
4. 创建架构审计 Skill（缺口）
5. 创建配置一致性检查 Skill（缺口）
