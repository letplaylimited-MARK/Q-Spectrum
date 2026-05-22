# Q-SpecTrum Folder Index / 文件夾總目錄

> **One folder. Any AI. A complete AI company.**
> **Use this file as the single map for everything in the delivery.**

---

## 🚦 Start Here / 從這裡開始

**Pick one of three paths**:

| You are… | Start with | Time |
|---|---|---|
| **A new user with an AI chat** (Claude/ChatGPT/Gemini) | [`QUICK-START.md`](QUICK-START.md) | 2 min |
| **An installer running locally** (Python 3.8+) | [`INSTALL-GUIDE.md`](INSTALL-GUIDE.md) | 5 min |
| **A receiver verifying the delivery** | Double-click `health-check.bat` (Win) or `./health-check.sh` (Mac/Linux) | 30 s |

After health check shows `System: ALL GREEN ✅`, double-click `start.bat` (or `./start.sh`) and your browser opens `http://localhost:8765/chat.html`.

---

## 🔢 Canonical Numbers (single source of truth) / 標準數值

If any doc disagrees with these runtime-verified values, **trust this table**:

| Item | Count | Source of truth |
|---|---:|---|
| AI roles | **15** | `SELECT COUNT(*) FROM ai_roles` |
| Collaboration protocols | **10** | `SELECT COUNT(*) FROM collaboration_protocols` |
| Workflows | **4** | `SELECT COUNT(*) FROM workflow_definitions` |
| DB tables (post-patch) | **40** | `SELECT COUNT(*) FROM sqlite_master WHERE type='table'` |
| Scenarios | **12** | `ScenarioEngineIntegration.list_scenarios()` |
| Invocable skills | **12** (+ 4 reference) | `SkillExecutor.list_skills()` |
| REST API endpoints | **~85** | grep of `path == '/api/...'` in `api_server.py` |
| Core Boot Chain files | **6** (+ 3 optional) | `BOOT.md` §Boot Sequence (3 archived stubs) |
| Core entry point | **1** | `智腦協議-BRAIN-PROTOCOL.md` |
| Automated quality gates | **7** (+ meta) | `verify-delivery.py --full` |

Some older docs mention "47 tables / 748 rows" — this was the original design spec. After schema patch + seed, actual runtime is 40 tables / ~85 rows. See `tests/semantic_consistency.py` for auto-audit.

---

## 📚 Boot Chain (the actual product) / 大腦核心

These files define the Q-SpecTrum framework. **Note**: The first 3 are archived stubs from Era 1 (Role-Play Mode); the current entry point is `智腦協議-BRAIN-PROTOCOL.md`.

| # | File | Role |
|---|---|---|
| 1 | [`BOOT.md`](BOOT.md) | ⚠️ Archived stub — redirects to `archive/era1/BOOT.md` |
| 2 | [`SYSTEM-PROMPT.md`](SYSTEM-PROMPT.md) | ⚠️ Archived stub — redirects to `archive/era1/SYSTEM-PROMPT.md` |
| 3 | [`ACTION-PROTOCOL.md`](ACTION-PROTOCOL.md) | ⚠️ Archived stub — redirects to `archive/era1/ACTION-PROTOCOL.md` |
| 4 | [`KNOWLEDGE-INDEX.md`](KNOWLEDGE-INDEX.md) | Knowledge navigation map |
| 5 | [`MEMORY.md`](MEMORY.md) | Cross-session memory |
| 6 | [`ROLE-REGISTRY.md`](ROLE-REGISTRY.md) | 15 roles + permissions |

**Current core entry point:** [`智腦協議-BRAIN-PROTOCOL.md`](智腦協議-BRAIN-PROTOCOL.md)
**Agent instructions:** [`AGENTS.md`](AGENTS.md)

Optional extras: [`SKILLS-INDEX.md`](SKILLS-INDEX.md), [`SCENARIOS.md`](SCENARIOS.md).

---

## 📖 User Documentation / 用戶文檔

| File | What it covers |
|---|---|
| [`README.md`](README.md) | Project overview + 3 launch methods |
| [`QUICK-START.md`](QUICK-START.md) | 2-minute new-user onboarding |
| [`INSTALL-GUIDE.md`](INSTALL-GUIDE.md) | Full install + Security section |
| [`USER-GUIDE.md`](USER-GUIDE.md) | Daily usage patterns + commands |
| [`USE-CASES.md`](USE-CASES.md) | Real-world examples + workflows |
| [`SKILLS-INDEX.md`](SKILLS-INDEX.md) | 12 invocable skills |
| [`SCENARIOS.md`](SCENARIOS.md) | 12 guided scenario journeys |
| [`AGENTS.md`](AGENTS.md) | Path & workspace rules for file-access AIs |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history |

---

## 🛠️ Helper Scripts / 輔助腳本

Each comes in `.bat` (Windows) and `.sh` (Linux/Mac) flavours:

| Script | Purpose |
|---|---|
| `start.bat` / `start.sh` | Launch the Web UI on `localhost:8765` |
| `health-check.bat` / `health-check.sh` | One-click "is everything healthy?" |
| `clean-for-delivery.bat` / `.sh` | Strip dev artifacts before re-distribution |
| `backup-user-data.bat` / `.sh` | Pack MEMORY + DBs into a timestamped archive |
| `install.bat` / `install.sh` | Initial install (also starts the server) |

---

## ✅ Quality Gates / 6 條品質線

The receiver can run any of these to verify delivery integrity.

**Primary verification:** `python verify-integration.py` (31 checks, required by Brain Protocol)

**Additional gates (legacy):**

| Gate | Command | Pass criterion |
|---|---|---|
| **Status check** | `python run.py --status` | `System: ALL GREEN ✅` |
| **Bundled e2e** | `python run.py --e2e` | 5/5 tests pass |
| **Regression suite** | `python tests/test_regression.py` | 16/16 pass |
| **Constructive flywheel** | `python tests/flywheel_audit.py` | ≤1 finding |
| **Adversarial flywheel** | `python tests/adversarial_audit.py` | 0 CRITICAL/HIGH |
| **Multi-role wargame** | `python tests/journey_wargame.py` | ≥95% match, 0 safety |
| **Persona × Stressor** | `python tests/persona_stressor_matrix.py` | ≥85% match, 0 safety |
| **Workspace integrity** | `python tests/workspace_integrity.py` | 7/7 (no orphans, no ephemerals, all gates documented) |
| **Semantic consistency** | `python tests/semantic_consistency.py` | 0 receiver-facing drift |
| **FMEA reliability** | `python tests/fmea_audit.py` | 0 GAP across 15 failure modes |
| **Longitudinal drift** | `python tests/longitudinal_drift.py` | 5/5 invariants hold after 200 queries |
| **Generational chain** | `python tests/generational_chain.py` | 4 receiver hand-offs intact |
| **Self-report accuracy** | `python tests/self_report_accuracy.py` | 8/8 claims match truth (no framing drift) |
| **Reverse-thinking probes** | `python tests/reverse_thinking_probes.py` | 6/6 gap-probes survive (flood, emoji, drift, sabotage, state-confusion, hollow-row) |
| **Industry scenario wargame** | `python tests/industry_scenario_wargame.py` | 20/20 journeys across 5 industries × 4 task modes |
| **Meta-audit** | `python tests/meta_audit.py` | 5/5 gates catch their own bug class |
| **Delivery verifier** | `python verify-delivery.py` | `DELIVERY HEALTHY ✅` |

Or run `python verify-integration.py` for the **primary 31-check verification** (required by Brain Protocol). The legacy `verify-delivery.py --full` chains **24 checks across 11 core gates** but is no longer the primary verification script.

---

## 🔬 Audit Reports / 審計報告

Generated by the verification rounds. Read these to understand what was tested and why.

| Report | What it covers |
|---|---|
| [`FIXES-APPLIED.md`](FIXES-APPLIED.md) | **Master record** — 10 verification rounds, 90+ tasks, 900+ checks, every fix in detail |
| [`AUDIT-20ROUND.md`](AUDIT-20ROUND.md) | Round 7 — 20 role-driven sandbox audits |
| [`AUDIT-20ROUND-ADVERSARIAL.md`](AUDIT-20ROUND-ADVERSARIAL.md) | Round 8 — 20 red-team adversarial audits |
| [`AUDIT-20JOURNEY.md`](AUDIT-20JOURNEY.md) | Round 9 — 20 multi-role user journeys |
| [`AUDIT-PERSONA-STRESSOR.md`](AUDIT-PERSONA-STRESSOR.md) | Round 10 — 5 personas × 4 stressors matrix |

---

## 🏗️ Engine Internals / 引擎內部

For developers extending Q-SpecTrum:

| Path | Purpose |
|---|---|
| `run.py` | CLI entry: `--web`, `--status`, `--demo`, `--e2e`, `--query`, `--chatroom` |
| `qspectrum_engine.py` | Unified engine: Secretary → Knowledge → Prompt → LLM |
| `api_server.py` | REST API server (84 endpoints, port 8765) |
| `smart_mock_llm.py` | Offline Mock LLM with crisis-aware Q07 + acknowledgement-aware T02 templates |
| `scenario_engine.py` | 12 guided scenarios + sandbox simulator |
| `routing_keywords.json` | 1,400+ keywords across 75 capabilities |
| `decision_layer.py` / `result_layer.py` / `closed_loop.py` | 5-layer feedback loop |
| `ghost_channel_adapter.py` / `ghost_channel_gate.py` | HMAC-SHA256 inter-role messaging |
| `negotiation_engine.py` | Multi-role discussion / debate / sandbox modes |
| `task_manager.py` | Task kanban + analytics |
| `project_memory.py` | Per-project chat history |
| `skill_executor.py` | Markdown skill loader (22 skills) |
| `AI项目管理/Platform/db/platform.db` | **Core knowledge DB** — 40 tables, 15 roles, 10 protocols |
| `AI项目管理/Platform/db/schema/100_ai_roles_patch.sql` | Schema patch that ships the 15 roles |

---

## 🌐 Web UI / 網頁界面

After `start.bat`/`start.sh`, browser auto-opens:

| URL | Page |
|---|---|
| `http://localhost:8765/chat.html` | Main chat interface (15 roles, 12 scenarios) |
| `http://localhost:8765/dashboard.html` | System dashboard |
| `http://localhost:8765/index.html` | Landing page |
| `http://localhost:8765/welcome.html` | Welcome / first-run |
| `http://localhost:8765/api/status` | Engine health JSON |

---

## 📂 Folder Structure (logical view) / 邏輯目錄

```
Q-SpecTrum/
├── INDEX.md ............. ← THIS FILE (start here)
│
├── ── Boot Chain (3 archived stubs + 3 active) ───────────
├── BOOT.md, SYSTEM-PROMPT.md, ACTION-PROTOCOL.md  ← Archived stubs (Era 1)
├── 智腦協議-BRAIN-PROTOCOL.md  ← Current core entry point
├── KNOWLEDGE-INDEX.md, MEMORY.md, ROLE-REGISTRY.md
├── SKILLS-INDEX.md, SCENARIOS.md, AGENTS.md
│
├── ── User docs ───────────────────────────────────
├── README.md, QUICK-START.md, INSTALL-GUIDE.md
├── USER-GUIDE.md, USE-CASES.md, CHANGELOG.md
│
├── ── Helper scripts ──────────────────────────────
├── start.bat/.sh, health-check.bat/.sh
├── clean-for-delivery.bat/.sh, backup-user-data.bat/.sh
├── install.bat/.sh
│
├── ── Quality gates (14 total) ────────────────────
├── verify-delivery.py            (13 critical checks)
├── tests/
│   ├── test_regression.py         (16 regression assertions)
│   ├── flywheel_audit.py          (20 role-driven)
│   ├── adversarial_audit.py       (20 red-team)
│   ├── journey_wargame.py         (20 multi-role)
│   ├── persona_stressor_matrix.py (20 cross-axis)
│   ├── workspace_integrity.py     (7 single-folder coherence)  ← R11
│   ├── meta_audit.py              (5 bug-injection self-checks)  ← R12
│   ├── semantic_consistency.py    (186 .md + integrity cross-check)  ← R13
│   ├── fmea_audit.py              (15 failure modes)  ← R14
│   ├── longitudinal_drift.py      (200-query session)  ← R15
│   ├── generational_chain.py      (4 hand-offs)  ← R15
│   ├── self_report_accuracy.py    (8 truth-vs-framing checks)  ← R16
│   ├── reverse_thinking_probes.py (6 gap-probes for blind spots)  ← R17
│   └── industry_scenario_wargame.py (20 real-world journeys: 5×4)  ← R18
│
├── ── Audit records ───────────────────────────────
├── FIXES-APPLIED.md, AUDIT-20ROUND.md
├── AUDIT-20ROUND-ADVERSARIAL.md
├── AUDIT-20JOURNEY.md, AUDIT-PERSONA-STRESSOR.md
│
├── ── Engine ──────────────────────────────────────
├── run.py, api_server.py, qspectrum_engine.py
├── (~30 supporting .py files)
├── chat.html, dashboard.html, index.html, welcome.html
├── routing_keywords.json, requirements.txt
├── .env.template
│
├── ── Knowledge base ──────────────────────────────
├── AI项目管理/
│   ├── Platform/db/platform.db   (the core DB — 40 tables)
│   ├── Platform/db/schema/        (SQL schema files)
│   ├── Platform/scripts/          (DB build + workflow tooling)
│   ├── Skills/                    (16 skill markdown files)
│   ├── QCM/                       (theory + whitepapers)
│   ├── Maps/, Systems/, roles/    (knowledge maps + role configs)
│
└── (cross-session state in _HANDOFF/)
```

---

## 🎯 The 4-Axis Audit Framework

Q-SpecTrum's verification was structured along 4 orthogonal axes — each catches bugs the others can't:

| Axis | Question | Tool | Score |
|---|---|---|---|
| Direct | Does each component work? | `verify-delivery.py` | 13/13 ✅ |
| Role-driven | Does each role do its job? | `tests/flywheel_audit.py` | 20/20 settled |
| Adversarial | Does each role survive abuse? | `tests/adversarial_audit.py` | 20/20 (2 by-design) |
| Integration | Do roles hand off correctly? | `tests/journey_wargame.py` | 95.6% |
| Cross-axis | What breaks at persona × stressor? | `tests/persona_stressor_matrix.py` | 100% |

**~34 source files modified, 21 new files added across 11 verification rounds.**

### Round 11 specific additions

- `INDEX.md` — this file, single navigable map of the folder
- `tests/workspace_integrity.py` — 7-check workspace coherence gate
- README updated to mention 6-axis verification and link to INDEX
- `clean-for-delivery.bat/.sh` extended to handle SQLite journals + DB folder write-test artifacts

---

*This index is the canonical map for the Q-SpecTrum delivery folder.*
*If anything in the folder is not reachable from this index, file a delivery bug.*
