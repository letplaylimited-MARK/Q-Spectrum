# Q-SpecTrum Quick Start / 快速開始

> **Read time: 2 minutes | 閱讀時間：2 分鐘**
> **⚠️ LEGACY MODE**: This describes the old role-playing chat approach.  
> For the real development platform, see `智腦協議-BRAIN-PROTOCOL.md` or run `python qspectrum_mcp_server.py`.

---

## Step 1: Open Any AI Chat / 打開任何 AI 對話

Open your preferred AI chat interface:
- ChatGPT (chat.openai.com)
- Claude (claude.ai)
- Gemini (gemini.google.com)
- Any other AI model that accepts file uploads

打開你常用的 AI 對話界面（ChatGPT、Claude、Gemini 等任何支持文件上傳的 AI）。

---

## Step 2: Upload These 6 Files / 上傳這 6 個文件

Upload **exactly these files** from this folder:

| # | File | Purpose |
|---|------|---------|
| 1 | `BOOT.md` | AI entry point — tells the AI who it is |
| 2 | `SYSTEM-PROMPT.md` | Core identity and behavior rules |
| 3 | `ACTION-PROTOCOL.md` | Shared Brain Protocol + Emergence |
| 4 | `KNOWLEDGE-INDEX.md` | Knowledge navigation map |
| 5 | `MEMORY.md` | Cross-session memory |
| 6 | `ROLE-REGISTRY.md` | 15 roles + permissions |

**Optional but recommended** — also upload:
- `SKILLS-INDEX.md` — unlocks 12 invocable skills in chat
- `SCENARIOS.md` — unlocks 12 guided scenario journeys
- `AGENTS.md` — path and workspace rules (for AIs with file access)

按順序上傳以上 6 個核心文件。可選上傳 SKILLS-INDEX.md、SCENARIOS.md 和 AGENTS.md 解鎖更多功能。

---

## Step 3: Say This / 輸入這句話

Type exactly:

> **Please read BOOT.md first and follow its Boot Sequence to load all files.**

Or in Chinese / 或用中文：

> **請先讀取 BOOT.md，按照 Boot Sequence 載入所有文件。**

---

## Step 4: Wait for Confirmation / 等待確認

The AI will read all files and display a confirmation like:

```
Q-SpecTrum v10.0 Active
15 Roles Ready | Memory Loaded | Secretary Online
How can I help you today?
```

If you see this, the system is ready. If not, say: **"Please confirm Q-SpecTrum activation status."**

AI 讀取完畢後會顯示啟動確認。如果沒有看到確認訊息，請輸入：「請確認 Q-SpecTrum 啟動狀態。」

---

## Step 5: Try These Starter Prompts / 試試這些提示

| What to Say | What Happens | Role |
|-------------|--------------|------|
| "Help me plan a new e-commerce project" | Strategic project planning | T03 System Coordinator |
| "Write a blog post introducing AI in 2026" | Content creation | Q03 Creator |
| "Analyze this data and find patterns" | Data analysis | Q04 Analyst |
| "Review this code for security issues" | Security audit | Q06 Risk Auditor |
| "I'm feeling overwhelmed, can we talk?" | Emotional support | Q07 AI Companion |
| "Show me available skills" | Skill catalog | Secretary |
| "Start the startup MVP scenario" | Guided 7-step journey | Multi-role |

每個提示會自動路由到最合適的角色。試試看！

---

## What Just Happened? / 發生了什麼？

When you loaded the Boot Chain, the AI transformed from a general chatbot into a **structured, multi-role AI company**:

- **15 specialized roles** across 3 governance families are now active
- **Secretary routing** automatically picks the best role for each request
- **Memory system** preserves knowledge across sessions
- **12 skills + 12 scenario journeys** are available on demand

This is the legacy role-playing mode — the AI simulates the 15-role framework internally.

當你載入 Boot Chain 後，AI 在 legacy 模式中模擬 15 角色框架。

---

## Need More? / 需要更多？

- **Skills**: Say "show me available skills" or see `SKILLS-INDEX.md`
- **Scenarios**: Say "start [scenario name] scenario" or see `SCENARIOS.md`
- **Engine Mode**: For Web UI + API, run `./start.sh` (requires Python 3.8+)
- **Full Guide**: See `README.md` for complete documentation

---

*Q-SpecTrum — Now a real development platform (see `智腦協議-BRAIN-PROTOCOL.md`)*
*Legacy chat mode preserved for backwards compatibility*
*Q-SpecTrum — 現代開發平台（見 `智腦協議-BRAIN-PROTOCOL.md`）*
