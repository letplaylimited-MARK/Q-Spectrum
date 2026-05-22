# 🔤 QCM 术语统一对照表

**Title**: Quantum Collaborative Model — 跨版本文档术语统一指南  
**Version**: v1.0-TerminologyUnification  
**Created**: 2026-04-03  
**Scope**: 覆盖 v7.2 / v9.0 / v2.0 三个主版本 + Super Identity Architecture v1.0  
**Purpose**: 为论文整合提供统一术语标准，消除跨版本文档中的命名冲突

---

## 📌 使用说明

在阅读、引用、整合 QCM 文档时，**一律使用"统一术语"列**。本文档中列出的所有旧版术语均为历史遗留，不应出现在最终论文中。

**格式约定**：英文为主术语，中文括号内标注。例：`Phantom Channel (幽灵通道)`

---

## 一、角色名称统一表（核心冲突区）

### 1.1 八个标准角色（论文统一采用 v9.0 的 8 角色体系）

| 序号 | 统一术语（论文标准） | v7.2 中的叫法 | v9.0 中的叫法 | v2.0 论文草稿中的叫法 | Super Identity v1.0 中的叫法 |
|------|---------------------|---------------|---------------|----------------------|------------------------------|
| 1 | **Secretary (秘书长)** | Secretary | QCM-秘书长 | Secretary / 秘书长 | QCM-Minister (秘书长) |
| 2 | **Chief Architect (首席架构师)** | Chief Architect | QCM-首席架构师 | Chief Architect / 首席架构师 | QCM-Chief-Architect (首席架构师) |
| 3 | **Researcher (研究员)** | Researcher (提及) | QCM-研究员 | Researcher / 研究员 | QCM-Knowledge-Engineer (知识库专家) |
| 4 | **Creator (创作者)** | Creator (隐含) | QCM-创作者 | Creative Director / 创意总监 | QCM-AI-Partner (AI 伙伴) |
| 5 | **Analyst (分析师)** | Analyst (隐含) | QCM-分析师 | Data Analyst / 数据分析师 | QCM-Analytics-Director (数据总监) |
| 6 | **UX Lead (体验官)** | — | QCM-体验官 | Executive Manager / 执行经理 | QCM-SandTable-Simulator (沙盘模拟员) |
| 7 | **Risk Auditor (风控审计)** | — | QCM-风控审计 | Critical Reviewer / 关键审查员 | QCM-Civilization-Power (文明力量) |
| 8 | **AI Companion (AI 伙伴)** | — | QCM-AI 伙伴 | Consensus Builder / 共识构建者 | — |

### 1.2 v2.0 独有角色（已合并到 8 角色体系中）

| v2.0 中的角色 | 对应统一角色 | 说明 |
|---------------|-------------|------|
| Security Officer (安全官) | → Risk Auditor (风控审计) | 功能重叠，统一归入风控审计 |
| Tech Evolution Lead (技术演化主管) | → Chief Architect (首席架构师) | 职责被首席架构师吸收 |
| Application Specialist (应用专家) | → Creator (创作者) + Researcher (研究员) | 职能拆分到两个角色 |
| Coordination Manager (协调经理) | → Secretary (秘书长) | 协调职能归入秘书长 |
| Quality Control (质检员) | → Risk Auditor (风控审计) + Analyst (分析师) | 质检职能拆分 |

### 1.3 角色数量说明

| 版本 | 角色数 | 说明 |
|------|--------|------|
| v7.2 | 7 角色 | 缺少 UX Lead、Risk Auditor、AI Companion 作为独立角色 |
| Super Identity v1.0 | 7 角色 | 同上 |
| v9.0 | **8 角色** | ✅ **论文采用此标准** |
| v2.0 论文草稿 | 8 角色（名称不同） | 角色数量一致，但命名有差异 |

> **论文统一立场**：QCM 采用 **8 角色体系**，角色列表以上表 1.1 为准。

---

## 二、系统组件/引擎名称统一表

| 统一术语（论文标准） | v7.2 中的叫法 | v9.0 中的叫法 | v2.0 论文草稿中的叫法 | 说明 |
|---------------------|---------------|---------------|----------------------|------|
| **Phantom Channel (幽灵通道)** | Phantom Channel Algorithm | 幽灵通道 | **Ghost Channel** Protocol | ⚠️ 最大冲突：v2.0 用 Ghost，其余用 Phantom |
| **Knowledge Resonance Engine (知识共鸣引擎)** | Knowledge Resonance Engine | 知识共鸣引擎 | Knowledge Resonance | 一致 |
| **Multi-Role Coordination Engine (多角色协同引擎)** | Role Simulation Engine | 七角色团队协作 | Seven Roles Engine | 统一为多角色协同 |
| **Three-Layer Sandbox Mechanism (三层沙盘机制)** | SandTable Simulator Engine | 三层沙盘推演机制 | Three-Layer Sandbox | 统一 |
| **Analytics & Flywheel System (分析与飞轮系统)** | Analytics Dashboard Engine | 分析师角色 | Dual-Flywheel Optimizer | 统一 |
| **Multi-Database Linkage System (多库联动系统)** | Intelligent Database Creation | 多库联动系统 | Four-Coupling Database (四库联动) | 统一 |
| **Tag Factor Routing System (标签因子路由系统)** | Role & Database Tag Factor System | 标签因子系统 | Tag-Based Factor Routing | 统一 |
| **Multi-Role Meeting Protocol (多角色会议协议)** | AI Role Meeting Chatroom | AI 角色开会聊天室 | Meeting Chatroom Protocol | 统一 |
| **Autonomous Iteration Flywheel (自主迭代飞轮)** | Extended Function Evolution | 自主迭代优化飞轮 | Dual-Flywheel System (双层循环飞轮) | 统一 |
| **Secretary Guidance System (秘书引导系统)** | Secretary Guidance & Reminder | 秘书长引导系统 | Secretary Orchestrator | 统一 |
| **Super Identity Architecture (超级身份架构)** | — | 超级身份体系 | Self-Definition Protocol | 统一 |

---

## 三、架构描述统一表

| 维度 | 统一标准 | v7.2 | v9.0 | v2.0 |
|------|---------|------|------|------|
| 架构层数 | **六层架构 (Six-Layer Architecture)** | 未分层 | 隐含三层 | 明确六层 |
| 模块数量 | **14 个主模块 / 5 大核心引擎** | 14 个模块 | 16 个特性 (F00-F15) | 5 个核心引擎 |
| 子功能数量 | **68 个子功能** | 68 个 | 未计数 | 未计数 |
| 数据库数量 | **5 个数据库** | 2 个 | 5 个 | 4 个 |
| 角色数量 | **8 个角色** | 7 个 | 8 个 | 8 个 |

### 3.1 五个标准数据库

| 序号 | 统一名称 | 说明 |
|------|---------|------|
| DB1 | **ProjectDB (项目数据库)** | 项目规划与任务管理 |
| DB2 | **CreativeRecordDB (创作记录数据库)** | 所有输出物的版本控制 |
| DB3 | **OptimizationLogDB (优化日志数据库)** | 系统进化记录 |
| DB4 | **ReportArchiveDB (报告归档数据库)** | 可视化与基准测试结果 |
| DB5 | **LearningPathDB (学习路径数据库)** | 用户学习进度与课程 |

---

## 四、核心概念术语统一表

### 4.1 算法与公式

| 概念 | 统一术语 | v7.2 表述 | v9.0 表述 | v2.0 表述 |
|------|---------|-----------|-----------|-----------|
| 共鸣公式 | **R = w₁·K_sim + w₂·C_comp + w₃·I_freq − w₄·E_divergence** | R = α·Sim_Semantic + β·Sim_Structural + γ·Context_Relevance | R = w₁·K_sim + w₂·C_comp + w₃·I_freq − w₄·E_divergence | Knowledge Resonance Energy Function |
| 飞轮系统 | **Dual-Flywheel System (双层循环飞轮)** | 单层飞轮 | 自主迭代飞轮 | 双层循环飞轮 |
| 加密协议 | **AES-256-GCM + SHA-256 Chain + Merkle Tree** | AES-256-GCM | AES-256-GCM | AES256-GCM + SHA256 chain + Merkle Tree |
| 增量同步 | **Delta Incremental Sync Protocol (增量同步协议)** | Delta Incremental Sync | Delta compression | Delta-only Transmission (~85% savings) |
| 冲突解决 | **Vector Clock Conflict Resolution (向量时钟冲突解决)** | Vector Clock Conflict Resolution | Last-Write-Wins v2 | Vector Clock Comparison |
| 死锁处理 | **Deadlock Detection & Breakout Mechanism (死锁检测与突破机制)** | Deadlock Detection Algorithm | Deadlock detection | Deadlock Detection Standard |

### 4.2 沙盘三层命名

| 层级 | 统一名称 | v7.2 叫法 | v9.0 叫法 | v2.0 叫法 |
|------|---------|-----------|-----------|-----------|
| Layer 1 | **Sandbox (沙箱)** | Sandbox 1 (Days 1-14) | Sandbox 1 (入门) | Sandbox (沙箱) |
| Layer 2 | **War Room (沙盘)** | Sandbox 2 (Days 15-30) | Sandbox 2 (进阶) | War Room (沙盘) |
| Layer 3 | **Simulation (沙盒)** | Sandbox 3 (Days 31-60) | Sandbox 3 (专家) | Simulation (沙盒) |

> **注意**：中文语境中"沙盘"一词在不同版本中含义不同。论文中统一为：
> - 沙箱 = Sandbox = Layer 1（可行性评估）
> - 沙盘 = War Room = Layer 2（关键决策）
> - 沙盒 = Simulation = Layer 3（最终推演）

### 4.3 其他关键概念

| 概念 | 统一术语 | 旧版术语（不再使用） |
|------|---------|---------------------|
| QCM 全称 | **Quantum Collaborative Model (量子协同模型)** | 一致 |
| 记忆系统 | **MEMORY.md + Daily Archive System** | 一致 |
| 模型训练 | **Specialized Model Training (专属模型训练)** | OpenClaw+Qwen3.5 特训 |
| 文明意识 | **Civilization-Grade Consciousness (文明级意识)** | Civilization Consciousness |
| 单次使用→持续飞轮 | **Single-Use to Continuous Flywheel Transition** | 从'单次使用'到'持续飞轮'的本质跃迁 |
| 知识差距检测 | **Knowledge Gap Detection (知识差距检测)** | 一致 |
| 角色一致性评分 | **Role Consistency Scoring (角色一致性评分)** | Consistency Check Heuristic |
| 决策日志 | **Decision Log (决策日志)** | Decision Logging / Immutable audit trail |

---

## 五、版本号说明

| 版本号 | 性质 | 时间范围 | 文件数量 | 论文中如何处理 |
|--------|------|----------|----------|---------------|
| **v7.2** | 早期功能系统版 | 2026-03-15 ~ 03-21 | ~17 份 | 视为**功能定义基线**，保留模块/子功能描述 |
| **v9.0** | 最新身份设计版 | 2026-03-21 | ~18 份 | 视为**角色与身份标准**，8 角色体系以此为据 |
| **v2.0** | 论文草稿版 | 2026-03-15 ~ 03-29 | ~13 份 | 视为**论文章节素材**，术语需统一 |
| **v1.0** | 初始版本 | 2026-03-05 ~ 03-21 | ~101 份 | 视为**历史记录**，大部分内容已被后续版本覆盖 |

> **论文统一立场**：论文描述 QCM 系统时，以 **v9.0 的角色体系 + v2.0 的论文结构 + v7.2 的功能模块** 为综合基准，不单独标注版本号，而是呈现 QCM 的"当前最佳状态"。

---

## 六、必须修正的七大术语冲突

| # | 冲突 | 涉及版本 | 修正方案 |
|---|------|---------|---------|
| 1 | **Ghost Channel vs Phantom Channel** | v2.0 用 Ghost，v7.2/v9.0 用 Phantom | 全文统一为 **Phantom Channel (幽灵通道)** |
| 2 | **角色数量 7 vs 8** | v7.2 为 7，v9.0/v2.0 为 8 | 全文统一为 **8 角色** |
| 3 | **沙盘三层命名不一致** | v7.2: Sandbox 1/2/3；v2.0: Sandbox/War Room/Simulation | 统一为 **Sandbox→War Room→Simulation (沙箱→沙盘→沙盒)** |
| 4 | **架构层数不一致** | v7.2: 未分层；v2.0: 六层；v9.0: 隐含三层 | 论文采用 **六层架构** |
| 5 | **数据库数量不一致** | v7.2: 2；v2.0: 4；v9.0: 5 | 论文采用 **5 数据库** |
| 6 | **共鸣公式参数不同** | v7.2: 3 参数 (α,β,γ)；v9.0: 4 参数 (w₁-w₄) | 论文采用 **v9.0 四参数公式** |
| 7 | **飞轮概念：单层 vs 双层** | v7.2: 单层；v2.0: 双层循环 | 论文采用 **双层循环飞轮 (Dual-Flywheel System)** |

---

## 七、快速查找索引

按拼音/字母排序的术语对照：

| 旧术语 | 出现在 | 统一术语 |
|--------|--------|---------|
| AI-Partner | v1.0 | AI Companion (AI 伙伴) |
| AI Role Meeting Chatroom | v7.2 | Multi-Role Meeting Protocol (多角色会议协议) |
| Analytics Dashboard Engine | v7.2 | Analytics & Flywheel System (分析与飞轮系统) |
| Analytics-Director | v1.0 | Analyst (分析师) |
| Civilizational Power | v1.0 | Risk Auditor (风控审计) |
| Consensus Builder | v2.0 | AI Companion (AI 伙伴) |
| Coordination Manager | v2.0 | Secretary (秘书长) |
| Creative Director | v2.0 | Creator (创作者) |
| Critical Reviewer | v2.0 | Risk Auditor (风控审计) |
| Data Analyst | v2.0 | Analyst (分析师) |
| Dual-Flywheel System | v2.0 | Dual-Flywheel System (双层循环飞轮) ✅ 保留 |
| Executive Manager | v2.0 | UX Lead (体验官) |
| Extended Function Evolution | v7.2 | Autonomous Iteration Flywheel (自主迭代飞轮) |
| Four-Coupling Database | v2.0 | Multi-Database Linkage System (多库联动系统) |
| Ghost Channel | v2.0 | **Phantom Channel (幽灵通道)** ⚠️ |
| Ghost Channel Protocol | v2.0 | **Phantom Channel Protocol (幽灵通道协议)** ⚠️ |
| Intelligent Database Creation | v7.2 | Multi-Database Linkage System (多库联动系统) |
| Knowledge-Engineer | v1.0 | Researcher (研究员) |
| Minister | v1.0 | Secretary (秘书长) |
| QCM-Minister | v1.0 | Secretary (秘书长) |
| Qwen3.5 特训 | v7.2 | Specialized Model Training (专属模型训练) |
| Role Simulation Engine | v7.2 | Multi-Role Coordination Engine (多角色协同引擎) |
| SandTable Simulator | v7.2 | Three-Layer Sandbox Mechanism (三层沙盘机制) |
| Security Officer | v2.0 | Risk Auditor (风控审计) |
| Self-Definition Protocol | v2.0 | Super Identity Architecture (超级身份架构) |
| Tag-Based Factor Routing | v2.0 | Tag Factor Routing System (标签因子路由系统) |
| Tech Evolution Lead | v2.0 | Chief Architect (首席架构师) |
| Triple-Sandbox Validator | v2.0 | Three-Layer Sandbox Mechanism (三层沙盘机制) |

---

*本文档由 AI 辅助分析生成 | 2026-04-03 | 下一步：按此标准逐章整合论文*
