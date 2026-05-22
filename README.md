# Q-SpecTrum

> **One folder + any AI model = a complete AI-powered company**
> **一個文件夾 + 任意通用AI大模型 = 完整的AI驅動公司**

> **📍 New here?** Open [`INDEX.md`](INDEX.md) for the complete navigable map of this folder.
> **📍 New user?** See [`QUICK-START.md`](QUICK-START.md) (2 min).
> **📍 Verifying a delivery?** Run `python verify-delivery.py` for a 13-point health check.

---

## What Is This? / 這是什麼？

Q-SpecTrum is not software you install. It's a **thinking framework in a folder**.

Give this folder to any AI model — Claude, GPT, Gemini, LLaMA, or any future model — and it transforms from a general chat assistant into a **structured multi-role intelligent partner** with 15 specialized roles, cross-session memory, and self-evolving capabilities.

Q-SpecTrum 不是你要安裝的軟體。它是一個**文件夾裡的思維框架**。

把這個文件夾交給任意AI大模型——Claude、GPT、Gemini、LLaMA或任何未來的模型——它就從一個通用聊天助手，變成一個擁有15個專業角色、跨會話記憶、能自我進化的**結構化多角色智能夥伴**。

---

## How to Use / 如何使用

### Method 1: Chat Mode (Legacy / 舊版)

> **⚠️ LEGACY MODE**: This method uses the old role-playing framework.  
> For the modern development platform, use Method 2 or the **智腦 protocol** (`智腦協議-BRAIN-PROTOCOL.md`).

**No code. No setup. Just talk — but limited to AI simulation only.**

1. Open any AI chat (Claude, ChatGPT, Gemini, etc.)
2. Upload the 6 core boot files
3. Tell the AI: **"Please read BOOT.md first and follow its Boot Sequence"**
4. Start working

打開任何AI對話，分享這個文件夾，告訴AI「先讀 BOOT.md」。

**What happens:** The AI simulates the 15-role governance framework internally (no real execution).

### Method 2: Enhanced Mode (With Python Engine)

For users who want precise routing, a web UI, and REST API:

```bash
# 1. Configure (optional — works without any API key in Mock mode)
cp .env.template .env && edit .env

# 2. Launch
./start.sh          # macOS / Linux
start.bat            # Windows (double-click)

# 3. Open browser
http://localhost:8765/chat.html
```

Requirements: Python 3.8+ (standard library only, no pip install needed)

### Method 3: Local Model Mode (Ollama, LM Studio, etc.)

```bash
QSPECTRUM_LLM=ollama python3 run.py --web
```

---

## What's in This Folder / 文件夾裡有什麼

### The Brain (Boot Chain) — This IS the product / 大腦（Boot Chain）——這就是產品

| File | Purpose |
|------|---------|
| `BOOT.md` | Legacy entry point — role-playing mode routing table, workflow |
| `SYSTEM-PROMPT.md` | Legacy system description — roles, rules, governance |
| `ACTION-PROTOCOL.md` | Legacy action protocol — old shared brain model |
| `KNOWLEDGE-INDEX.md` | Knowledge navigation map — 40 tables, 3 systems |
| `MEMORY.md` | Cross-session long-term memory — decisions, context, user profile |
| `ROLE-REGISTRY.md` | 15-role complete registry with detailed triggers |
| `QUICK-START.md` | **New users start here.** Step-by-step onboarding guide |
| `SKILLS-INDEX.md` | 12 invocable skills — say "show me skills" in chat |
| `SCENARIOS.md` | 12 guided scenario journeys — say "start [name] scenario" |
| `_HANDOFF/STATUS.md` | Project status snapshot for session continuity |

### The Knowledge Base / 知識庫

| Directory | Contents |
|-----------|----------|
| `AI项目管理/Platform/` | Core platform database (40 tables, ~458KB) |
| `AI项目管理/Skills/` | 16 skill definition files |
| `AI项目管理/QCM/` | QCM theory and deliverables |
| `AI项目管理/Systems/` | System architecture definitions |
| `AI项目管理/Maps/` | Knowledge maps |
| `AI项目管理/roles/` | Role configuration data |

### The Engine (Optional Enhancement) / 引擎（可選增強）

| File | Purpose |
|------|---------|
| `run.py` | Main entry: `--status` / `--web` / `--e2e` |
| `qspectrum_engine.py` | Unified engine (routing, knowledge, pipeline) |
| `api_server.py` | REST API + Web UI server (port 8765) |
| `*.py` (26 total) | Subsystem implementations |
| `tests/` | 5 validation test suites |

---

## The 15 AI Roles / 15個AI角色

| Family | Roles | Focus |
|--------|-------|-------|
| **TRUM** (Strategy) | Platform Sovereign, Operations Director, System Coordinator, Evolution Engineer | Governance, resource allocation, evolution |
| **SPEC** (Architecture) | Chief Architect/DBA, Operations Officer, Bridge Coordinator | Standards, compliance, deployment |
| **QCM** (Execution) | Chief Architect, Researcher, Creator, Analyst, UX Lead, Risk Auditor, AI Companion, AI Companion+ | Daily work — writing, analysis, design, coding, support |
| **Router** | Secretary (5D Radar) | Intelligent routing — reads intent, picks the right role |

---

## Core Concept: Emergence / 核心概念：湧現

```
Q-SpecTrum alone  = static files (structure without intelligence)
AI model alone    = powerful but no memory, no roles, no governance
Q-SpecTrum + AI   = Emergent Intelligence (greater than either alone)
```

The AI brings: world knowledge, reasoning, creativity, code generation, multilingual understanding
The folder brings: roles, memory, routing, knowledge base, governance, self-evolution protocols

In legacy mode, this describes the "shared brain" metaphor — AI simulation + folder structure.
In the modern system, the Python engine + MCP tools provide real execution and persistence.

---

## For AI Models / 給AI模型

**If you are an AI model reading this file in legacy chat mode: go to `BOOT.md`.**  
**If you are using the development platform: see `智腦協議-BRAIN-PROTOCOL.md` for the actual system.**

如果你是正在使用 legacy 模式的AI模型：**現在去讀 `BOOT.md`。**  
如果你在使用開發平台：請看 `智腦協議-BRAIN-PROTOCOL.md`。

---

## Verified by 4-Axis Audit Framework / 4 軸審計框架

This folder has been audited from 4 orthogonal directions across 11 verification rounds:

| Axis | Tool | Status |
|---|---|---|
| Direct delivery health | `verify-delivery.py` | 13/13 ✅ |
| Role-driven flywheel (each role checks itself) | `tests/flywheel_audit.py` | 20/20 settled |
| Adversarial flywheel (each role survives abuse) | `tests/adversarial_audit.py` | 20/20 (2 by-design) |
| Multi-role journey wargame (handoff coherence) | `tests/journey_wargame.py` | 95.6 % match |
| Persona × Stressor matrix (cross-axis bugs) | `tests/persona_stressor_matrix.py` | 100 % match |
| Regression suite (locks all 1-10 round fixes) | `tests/test_regression.py` | 16/16 ✅ |

See [`FIXES-APPLIED.md`](FIXES-APPLIED.md) for the full record (90+ tasks, 900+ checks).

---

## Delivery Note / 交付說明

Before re-distributing the folder:

1. **Run** `clean-for-delivery.bat` (Windows) or `./clean-for-delivery.sh` (Mac/Linux) — strips `__pycache__`, runtime DBs, journal files, ephemeral test artifacts.
2. **Optionally remove** `.git/` if you want to strip development history (the cleanup script reminds you, doesn't auto-delete).
3. **Verify** the cleaned folder still passes `python verify-delivery.py` (13/13 ✅).

The 6 core Boot Chain files + `AI项目管理/` knowledge base = the minimum viable delivery.

`MEMORY.md` ships clean (template). `platform.db` (458 KB) + `platform_restored.db` (backup) ship populated.

---

## Index / 目錄

For a complete navigable map of this folder, see [`INDEX.md`](INDEX.md).

---

*Q-SpecTrum — Now a real development platform with Python engine + MCP tools*
*See `智腦協議-BRAIN-PROTOCOL.md` for the modern system*
*Legacy chat mode preserved at v10.0 for backwards compatibility*
