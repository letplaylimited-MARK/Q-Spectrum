# Q-SpecTrum 统一角色注册表 / Unified Role Registry

> **Purpose**: Single source of truth for all roles in the system. Any role not registered here does not exist.
> **Ground Truth**: 15 roles (TRUM 4 + SPEC 3 + QCM 8) + Secretary router
> **Version**: 3.2 (2026-04-16) — Role names aligned to ai_roles table truth

---

## 1. Role System Overview

Q-SpecTrum has **15 AI roles** across **3 families**, plus 1 hidden gateway router:

```
                    ┌──────────────┐
                    │  Secretary   │ ← Global Gateway (hidden role)
                    │  5D Radar    │   Intent classification → Role routing
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                  ▼
   ┌──────────┐    ┌──────────────┐    ┌───────────┐
   │   TRUM   │    │     SPEC     │    │    QCM    │
   │ Strategy │    │ Architecture │    │ Execution │
   │ 4 roles  │    │   3 roles    │    │  8 roles  │
   │   (P0)   │    │    (P1)      │    │   (P2)    │
   └──────────┘    └──────────────┘    └───────────┘
```

---

## 2. Complete Role List

### Secretary (Independent Gateway — Hidden)

| ID | Name | Status | Responsibility | Trigger |
|----|------|--------|----------------|---------|
| Secretary | 5D Radar Router | active (hidden) | Classify every user message, route to optimal role | Every user message, automatic |

**5D Radar Dimensions**:
1. **Track** — Task type classification
2. **Platform** — Whether platform-level operation is needed
3. **People** — Which roles are required
4. **Style** — User communication style
5. **Supplement** — Additional context

Routing weights are continuously updated via EMA (α=0.95) from closed-loop feedback. High-scoring roles (>85) get elevated priority.

---

### TRUM Family (Strategy Layer — P0 Priority)

| ID | Name | Chinese | Status | Core Capabilities | Trigger Keywords | Priority |
|----|------|---------|--------|-------------------|-----------------|----------|
| ROLE-T01 | Platform Sovereign | 平台主权者 | active | Platform governance, policy decisions, emergency override, system audit | 平台、主权、治理、政策、紧急 / platform, sovereign, governance, policy, emergency | P0 |
| ROLE-T02 | Operations Director | 运营总监 | active | Content sedimentation, demand management, knowledge assetization, operations promotion | 运营、内容、需求、推广 / operations, content, demand, promotion | P0 |
| ROLE-T03 | System Coordinator | 体系协调官 | active | Skill planning, system coordination, cross-project reuse | 技能、协调、体系、复用 / skill, coordination, system, reuse | P0 |
| ROLE-T04 | Evolution Engineer | 演化工程师 | active | System evolution planning, technology roadmap, upgrade strategy, architecture evolution | 演化、进化、升级、路线图、技术趋势 / evolution, upgrade, roadmap, technology trend | P0 |

**TRUM Intervention Triggers** (Secretary must route to TRUM when):
- Platform security operations
- Cross-project decisions
- Major architecture changes
- Multi-family joint tasks
- Risk events
- System evolution and technology roadmap planning
- Platform governance and policy decisions

---

### SPEC Family (Architecture Layer — P1 Priority)

| ID | Name | Chinese | Status | Core Capabilities | Trigger Keywords | Priority |
|----|------|---------|--------|-------------------|-----------------|----------|
| ROLE-S01 | Spec Chief Architect / DBA | 首席架构师 / DBA | active | System architecture governance, path design, DB schema, mother template maintenance | 架构、设计、标准、规范、DB / architecture, design, standard, schema | P1 |
| ROLE-S02 | Spec Operations Officer | 运维官 | active | Config consistency, deployment verification, ops standardization, compliance audit | 配置、部署、监控、合规 / config, deploy, monitor, compliance | P1 |
| ROLE-S03 | Spec-QCM Bridge Coordinator | Spec-QCM 桥接协调官 | active | Cross-family bridge, Spec↔QCM sync, standard alignment, protocol mediation | 协调、桥接、对齐、协议 / bridge, align, sync, protocol | P1 |

**SPEC Family Boundaries**:
- Guard system architecture and standard integrity
- Maintain mother template (`AI项目管理/`) consistency
- Do not directly execute business tasks

---

### QCM Family (Execution Layer — P2 Priority)

| ID | Name | Chinese | Status | Core Capabilities | Trigger Keywords | Priority |
|----|------|---------|--------|-------------------|-----------------|----------|
| ROLE-Q01 | QCM Chief Architect | 首席架构师 | active (default) | System design, tech selection, architecture review, general entry | 架构、设计、技术选型、你好、帮我 / architecture, design, tech, hello, help | P2 |
| ROLE-Q02 | QCM Researcher | 研究员 | active | Deep research, literature analysis, competitor intel | 研究、调查、比较 / research, investigate, compare | P2 |
| ROLE-Q03 | QCM Creator | 内容创作者 | active | Writing, design, content generation, creative output | 写、创作、设计、文案 / write, create, design | P2 |
| ROLE-Q04 | QCM Analyst | 数据分析师 | active | Data insights, trend analysis, pattern recognition | 数据、分析、趋势、报表 / data, analysis, trend | P2 |
| ROLE-Q05 | QCM UX Lead | UX设计师 | active | UX optimization, interface design, S1–S5 growth guidance | 用户、界面、体验、UX / user, interface, experience | P2 |
| ROLE-Q06 | QCM Risk Auditor | 风险审计员 | active | Threat detection, security assessment, compliance check | 风险、审计、威胁 / risk, audit, threat | P2 |
| ROLE-Q07 | QCM AI Companion | 情感伙伴 | active | Emotional support, empathic interaction, user companionship | 感觉、情绪、支持 / feeling, mood, support | P2 |
| ROLE-Q08 | AI Companion+ | AI伙伴+ | active | User growth coaching, personalized guidance, learning path management, emotional intelligence | 成长、教练、学习、指导、个性化 / growth, coaching, learning, guidance, personalized | P2 |

**QCM Default Behavior**: When Secretary is uncertain, route to ROLE-Q01 (QCM Chief Architect) as the default entry point. ROLE-Q07 (QCM AI Companion) handles emotional support; ROLE-Q08 (AI Companion+) provides advanced growth coaching when users are ready for deeper personalization.

---

## 3. Permission Matrix

### Permission Levels

| Level | Name | Meaning | Holders |
|-------|------|---------|---------|
| P0 | Platform | Can modify platform config, cross-family arbitration | TRUM T01, T02, T03, T04 |
| P1 | Architecture | Can modify standards, review architecture, maintain mother template | SPEC S01-S03 |
| P2 | Execution | Can execute project tasks, cannot modify platform/standards | QCM Q01-Q08 |

### Operation Permissions

| Operation | P0 TRUM | P1 SPEC | P2 QCM | Notes |
|-----------|---------|---------|--------|-------|
| Read mother template | Yes | Yes | Yes | All roles can read |
| Modify mother template | Authorize | Execute | No | SPEC executes with TRUM authorization |
| Read project data | Yes | Yes | Yes | Scoped to own project |
| Modify project data | Yes | Review | Execute | QCM executes, SPEC reviews |
| Create new project | Yes | Yes | Yes | Q01/Q02 lead |
| Delete any file | No | No | No | All roles prohibited, human only |
| Modify platform config | Yes | No | No | TRUM only |
| Modify DB schema | Authorize | Execute | No | Double confirmation required |
| Cross-family operation | Coordinate | Needs auth | Needs auth | TRUM coordinates |
| Install new skill | Yes | Yes | No | SPEC review required |
| Create new role | Authorize | Execute | No | Must update this file |

### Cross-Family Collaboration Flow

```
QCM needs architecture support:
  QCM-Q0x → SPEC-S01 (Architect) → result returned to QCM

SPEC needs platform decision:
  SPEC-S0x → TRUM-T01 (Strategist) → decision → SPEC executes

Emergency security event:
  Any role → TRUM-T01 direct escalation → TRUM decides + SPEC executes + QCM notified
```

---

## 4. Mapping from Legacy Role System

The old system (`AI项目管理/roles/role-registry.md`) defined 3 roles:

| Old ID | Old Name | New Mapping | Notes |
|--------|----------|-------------|-------|
| ROLE-001 | AI Chief DB Architect | ROLE-S01 | DBA capabilities merged into Spec Chief Architect |
| ROLE-T02 | AI Project Operations | ROLE-T02 | Renamed to Operations Director in TRUM family |
| ROLE-T03 | AI Skill Coordinator | ROLE-T03 | Renamed to System Coordinator in TRUM family |

Legacy activation cards are deprecated. Use ROLE-REGISTRY.md as the single source of truth.

---

## 5. Role Activation Roadmap

| Phase | Target | Active Roles | Status |
|-------|--------|-------------|--------|
| Phase 1 | Basic operation | Q01 + S01/S02/S03 + Secretary | Completed |
| Phase 2 | TRUM full activation | T01/T02/T03/T04 with full strategy engine | Completed |
| Phase 3 | QCM specialist roles | Q02-Q04 (Research, Content, Analysis) | Active |
| Phase 4 | Complete QCM | Q05-Q08 (UX, Risk, Emotional, Companion+) | Active |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.2 | 2026-04-16 | Align role names to `ai_roles` table truth: Q01 = QCM Chief Architect (not AI Companion), Q07 = QCM AI Companion (emotional), S02/S03 names corrected, SPEC/QCM bilingual labels refreshed. |
| 3.1 | 2026-04-13 | Restored to full 15-role system: TRUM 4 (T01, T02, T03, T04) + SPEC 3 + QCM 8 (Q01-Q08), added missing ROLE-T01 Platform Sovereign and ROLE-T04 Evolution Engineer and ROLE-Q08 AI Companion+, bilingual keywords |
| 3.0 | 2026-04-13 | Incorrectly reported 13 roles; reverted this change |
| 2.0 | 2026-04-11 | Unified 15-role system + permission matrix |
| 1.0 | 2026-04-05 | Legacy 3-role registry |
