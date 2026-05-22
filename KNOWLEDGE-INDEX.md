# Q-SpecTrum 知识索引 / Knowledge Index

> **Purpose**: AI navigation map — tells any AI where all knowledge assets are, what they contain, how to use them
> **Read Order**: Boot Chain Layer 3 (after BOOT → SYSTEM-PROMPT → ACTION-PROTOCOL)
> **Version**: 6.1 (2026-05-10) — Updated for modern development platform transition
> **Ground Truth**: 15 roles, 40 tables, 85 rows, 12 invocable skills + 4 reference docs, 12 scenarios (68 steps), 14 engine subsystems (post-patch actuals)

---

## 1. Three Systems Overview

Q-SpecTrum knowledge divides into **three systems**. An AI must understand all three to operate correctly:

```
┌──────────────────────────────────────────────────────────┐
│                Q-SpecTrum Knowledge Map                    │
├──────────────┬──────────────┬────────────────────────────┤
│  VALUE (Why) │ FUNCTION     │ STRUCTURE (How)             │
│              │ (What)       │                             │
├──────────────┼──────────────┼────────────────────────────┤
│ Vision       │ 15 AI Roles  │ Three-Family Governance     │
│ User Growth  │ 16 Skills    │ Secretary 5D Router         │
│ Knowledge    │ 12 Scenarios │ 5-Layer Closed Loop         │
│  Resonance   │ Ghost Channel│ Emergence Protocol          │
│ Dual Flywheel│ 47-Table DB  │ 14 Engine Subsystems        │
│ Shared Brain │ Negotiation  │ Self-Evolution Mechanisms    │
└──────────────┴──────────────┴────────────────────────────┘
```

---

## 2. Value System (WHY)

Answers: why Q-SpecTrum exists, what problem it solves, core beliefs.

### Key Documents

| Priority | File | Content |
|----------|------|---------|
| ★★★ | `./SYSTEM-PROMPT.md` §0 | Product positioning — legacy mode overview |
| ★★★ | `./ACTION-PROTOCOL.md` Emergence Protocol | AI + Q-SpecTrum = emergent intelligence |
| ★★☆ | `./AI项目管理/QCM/core/` | QCM theory, knowledge crystallization, 22 formulas |
| ★★☆ | `./AI项目管理/QCM/whitepapers/` | QCM whitepapers v1.0 + v2.0 |

### Core Value Propositions

1. **Legacy Role-Playing Mode**: In the old system, the AI simulates a 15-role framework by reading text files. The modern system uses the Python engine (`qspectrum_engine.py`) + MCP tools for real execution.
2. **Communication Is the Foundation**: Ghost Channel is QCM's nervous system. Without communication, 15 roles = 15 islands, total value = 0
3. **Knowledge Resonance**: R = 0.35K + 0.25C + 0.25I - 0.15E (implemented in TF-IDF vector search)
4. **Dual-Layer Flywheel**: Inner (knowledge accumulation via 5-layer loop) + Outer (cross-project value sharing)
5. **Portable AI Governance**: One folder = one complete AI company, zero cloud dependency, any AI model

### User Growth Model (S1-S5)

```
S1 Explorer → S2 Learner → S3 Practitioner → S4 Expert → S5 Strategist
     │             │              │               │             │
Basic chat    Multi-role     Project mgmt    Custom roles   Cross-project
Single role   Skill usage    Knowledge dep.  Templates      governance
```

---

## 3. Function System (WHAT)

Answers: what Q-SpecTrum can do, what tools and capabilities exist.

### Key Documents

| Priority | File | Content |
|----------|------|---------|
| ★★★ | `./ROLE-REGISTRY.md` | 15 roles + permission matrix (single source of truth) |
| ★★★ | `./ACTION-PROTOCOL.md` | Shared Brain + Emergence Protocol + self-evolution |
| ★★☆ | `./SKILLS-INDEX.md` | 12 invocable skills for chat-mode users |
| ★★☆ | `./SCENARIOS.md` | 12 guided scenario journeys (68 steps total) |
| ★★☆ | `./scenario_engine.py` | 12 guided scenarios + AI companion + DeerFlow simulator |
| ★★☆ | `./AI项目管理/QCM/core/QCM_知识结晶完整保存版_v1.0.md` | 22 core formulas |

### 15 Roles Quick Reference

| Family | Roles | Specialty |
|--------|-------|-----------|
| **TRUM** (Strategy) | T01 Platform Sovereign, T02 Operations Director, T03 System Coordinator, T04 Evolution Engineer | Platform governance, coordination, evolution |
| **SPEC** (Architecture) | S01 Chief Architect/DBA, S02 Operations Officer, S03 Bridge Coordinator | Standards, deployment, compliance |
| **QCM** (Execution) | Q01 Chief Architect, Q02 Researcher, Q03 Creator, Q04 Analyst, Q05 UX Lead, Q06 Risk Auditor, Q07 AI Companion, Q08 AI Companion+ | Daily execution across all domains |
| **Router** | Secretary (5D Radar) | Intent classification → role routing → weight learning |

### 16 Skills — 12 Invocable + 4 Reference (in `AI项目管理/Skills/`)

AI創業行動路徑, AI編碼Agent使用指南, Agent運維助手, Obsidian知識庫維護, 全庫盤點技能, 可執行Skill包生產, 周度知識庫回顧, 技能機會總表, 提示詞練習, 新手需求分流, 案例創作助手, 模板統一入口, 記憶管理助手, 跨項目遷移驗證, Skill標準化升級, Skill質量評估

### 12 Scenario Journeys

E-commerce, Startup MVP, Data Pipeline, Content Creation, Marketing Campaign, Team Operations, API & Microservices, Product Design, Security Audit, AI Companion, Multi-project Management, Knowledge Base Construction

### 22 Core Math Formulas

See `./AI项目管理/QCM/core/QCM_知识结晶完整保存版_v1.0.md` Chapter 2.

| Formulas | Name | Purpose |
|----------|------|---------|
| F1 | Knowledge Resonance Energy | Evaluate combination value of two knowledge points (R>0.85 = emergence) |
| F2-6 | Similarity/Complementarity/Frequency/Divergence | Component calculations for F1 |
| F7 | Dynamic Weight Adjustment | Auto-calibrate formula parameters |
| F8-11 | Role Consistency | Measure role performance stability |
| F12 | Deadlock Detection | Identify decision deadlocks (87% accuracy) |
| F13-16 | Flywheel Dynamics | Inner/outer flywheel acceleration |
| F17-19 | Ghost Channel | Sync efficiency, bandwidth optimization (85% reduction) |
| F20-22 | Security & Trust | Encryption, verification, integrity (Merkle Tree) |

---

## 4. Structure System (HOW)

Answers: how Q-SpecTrum is organized, permission boundaries, file layout.

### Key Documents

| Priority | File | Content |
|----------|------|---------|
| ★★★ | `./BOOT.md` | Boot protocol — AI entry point, routing table, workflow |
| ★★★ | `./ACTION-PROTOCOL.md` | Shared Brain Protocol + Emergence Protocol |
| ★★☆ | `./AGENTS.md` | Workspace config, path rules |
| ★★☆ | `./AI项目管理/roles/` | Role definitions + collaboration rules |

### Directory Structure (Current State — 2026-04-18)

```
Q-SpecTrum(TEST)/                     ← Platform root
│
├── ── Boot Chain (THE CORE PRODUCT) ──
├── BOOT.md                           ← Layer 0: AI entry — routing table, identity, workflow
├── SYSTEM-PROMPT.md                  ← Layer 1: Core identity, governance rules
├── ACTION-PROTOCOL.md                ← Layer 2: Shared Brain + Emergence Protocol
├── KNOWLEDGE-INDEX.md                ← Layer 3: Knowledge navigation (this file)
├── MEMORY.md                         ← Layer 4: Cross-session long-term memory
├── ROLE-REGISTRY.md                  ← Layer 5: 15 roles + permission matrix
├── QUICK-START.md                    ← Human onboarding (new users start here)
├── SKILLS-INDEX.md                   ← Layer 6: 12 invocable skills for chat mode
├── SCENARIOS.md                      ← Layer 7: 12 guided scenario journeys
├── README.md                         ← Human-facing guide
├── AGENTS.md                         ← Workspace config
│
├── ── Knowledge Base ──
├── AI项目管理/                        ← Core knowledge (read-only)
│   ├── Platform/db/platform.db       ← 40 tables (post-patch; was 47 in original design) / 85 rows SQLite
│   ├── Platform/scripts/             ← Platform scripts
│   ├── Platform/standards/           ← Standards documents
│   ├── Skills/                       ← 16 skill definitions
│   ├── QCM/core/                     ← QCM theory + 22 formulas
│   ├── QCM/whitepapers/              ← Ghost Channel protocol + research papers
│   ├── QCM/papers/                   ← Academic papers
│   ├── Maps/                         ← Knowledge graphs
│   ├── roles/                        ← Role collaboration rules
│   └── Systems/                      ← System architecture (families, operator)
│
├── ── Engine (Optional Enhancement) ──
├── run.py                            ← CLI: --status / --web / --e2e
├── qspectrum_engine.py               ← Core engine: Secretary→Knowledge→LLM→Response
├── api_server.py                     ← REST API (84 handlers, port 8765)
├── scenario_engine.py                ← 12 scenarios + AI companion
├── *.py (26 total)                   ← Subsystem implementations
│
├── ── Web UI ──
├── chat.html                         ← Web chatroom interface
├── dashboard.html                    ← Management dashboard
├── index.html                        ← Landing page
├── LAUNCH.html                       ← Browser launcher
│
├── ── Cross-Session State ──
├── _HANDOFF/                         ← Session continuity
│   └── STATUS.md                     ← Project status snapshot
│
├── ── Development Support ──
├── tests/                            ← Test suites (flywheel, E2E, integration)
├── config/                           ← Configuration (default.yaml)
├── roles/                            ← Role templates and examples
│
```

### Permission Boundaries

| Operation | Who Can Do | Approval Needed |
|-----------|-----------|----------------|
| Daily project tasks | QCM | None |
| Modify project config | QCM + Spec | Spec review |
| Modify knowledge base | Spec | Trum authorization |
| Modify platform config | Trum | Double confirmation |
| Cross-family collaboration | QCM + Spec | Trum coordination |
| Delete any file | Prohibited | Human only |
| Modify path structure | Spec | Trum authorization |

---

## 5. Knowledge Memory System

### Five Memory Types

| Type | Meaning | Storage | Update Frequency |
|------|---------|---------|-----------------|
| Episodic | Specific events, decisions | `MEMORY.md` §1 | Every decision |
| Semantic | Facts, concepts, rules | `AI项目管理/QCM/core/` + `Skills/` | On discovery |
| Procedural | Skills, processes, methods | `AI项目管理/Skills/` | On process change |
| Emotional | User preferences, style | `MEMORY.md` [USER-PROFILE] | End of session |
| Somatic | System state, health | `MEMORY.md` §2 | Periodic snapshot |

### Knowledge Deposition Rules

Before ending every AI session, **must** update `MEMORY.md`:
1. New core decisions → add to §1
2. New knowledge insights → add to §3
3. Project state changes → update §2
4. Newly discovered issues → add to §4

---

## 6. Engineering Capabilities

### Database Layer (40 tables (post-patch; was 47 in original design) / 85 rows)

Location: `AI项目管理/Platform/db/platform.db` (SQLite, immutable URI for read-only access)

8 domains: Identity, Portfolio, Demand, Solution, Orchestration, Validation, Knowledge, ARCS/Tags

### Execution Engines

| Engine | Path | Capability |
|--------|------|-----------|
| QSpectrum Engine | `qspectrum_engine.py` | Full pipeline: Secretary→Knowledge→Prompt→LLM→Response |
| Scenario Engine | `scenario_engine.py` | 12 guided journeys + AI companion |
| API Server | `api_server.py` | 84 REST handlers on port 8765 |
| Agent Runtime | `AI项目管理/Platform/scripts/agent_runtime.py` | Workflow→Agent→LLM→DB chain |
| Test Suite | `tests/` | 5 validation tests (AI model, developer, nervous system, non-tech, server) |

### Routing System

| Component | Path | Function |
|-----------|------|----------|
| Routing Keywords | `routing_keywords.json` | 1,441 keywords across 74 categories |
| Secretary Router | Legacy `BOOT.md` routing table | Legacy mode routing simulation |
| F21 Decision Formula | `qspectrum_engine.py` | relevance 0.45 + affinity 0.25 + cost 0.15 + knowledge 0.15 |

---

## 7. Cross-Session Continuity Protocol

### AI Startup (Read Order — matches BOOT.md)

```
── Core (do not skip) ──
Layer 0: BOOT.md              ← Who I am, routing table, workflow
Layer 1: SYSTEM-PROMPT.md     ← Core identity and governance rules
Layer 2: ACTION-PROTOCOL.md   ← Shared Brain + Emergence Protocol + self-evolution
Layer 3: KNOWLEDGE-INDEX.md   ← Where knowledge lives (this file)
Layer 4: MEMORY.md            ← What happened, what to remember
Layer 5: ROLE-REGISTRY.md     ← 15 roles + permission matrix

── Optional (load if provided) ──
Layer 6: SKILLS-INDEX.md      ← 12 invocable skills for chat mode
Layer 7: SCENARIOS.md         ← 12 guided scenario journeys
Layer 8: AGENTS.md            ← Path and workspace rules (for file-access AIs)
Layer 9: _HANDOFF/STATUS.md   ← Project status snapshot
```

### AI Shutdown (Required Actions)

```
1. Update MEMORY.md           ← Record decisions and knowledge
2. Update _HANDOFF/STATUS.md  ← Update project status
3. Generate handoff summary   ← What next session needs to know
4. Mark incomplete items      ← Add to MEMORY.md
```

### Emergence Protocol (New in v6.0)

After Boot Chain is loaded, the AI should:
1. Run startup self-check (Boot Chain integrity + memory freshness)
2. Detect user growth stage (S1-S5)
3. Track user profile across sessions
4. Detect role gaps for unmet needs
5. Self-evolve: value system calibration, function system growth, structure system healing

See `ACTION-PROTOCOL.md` → Emergence Protocol for complete definitions.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 6.0 | 2026-04-18 | Complete rewrite: align with post-restructuring folder state, remove references to archived/missing files (THREE-SYSTEMS.md, INSTALL-GUIDE.md, DEEP-USAGE.md, Apps/, Projects/), re-add QUICK-START.md (newly created), update directory tree to actual state, add Emergence Protocol section, correct role codes (TRUM 4 roles), update API count (84 handlers), add routing system section, fix skill count (16), add self-evolution reference |
| 5.0 | 2026-04-13 | Fix role count, add scenario engine, standardize ground truth |
| 4.0 | 2026-04-12 | Closed-loop integration + document restructure |
