# Q-SpecTrum Installation Guide / 安裝指南

> **Version**: 1.0 | **Last Updated**: 2026-04-20
>
> **版本**: 1.0 | **最後更新**: 2026-04-20

---

## Prerequisites / 前置需求

Choose the mode that fits your needs. Most users only need Method 1.

根據您的需求選擇合適的模式。大多數用戶只需要方法一。

| Mode / 模式 | Requirements / 需求 |
|---|---|
| **Chat Mode / Legacy** (Method 1) | An AI chat account — Claude, ChatGPT, or Gemini. Nothing to install. / 一個AI聊天帳號即可，無需安裝任何東西。 |
| **Enhanced Mode** (Method 2) | Python 3.8+ (standard library only — no pip packages). / Python 3.8+（僅使用標準庫，無需pip安裝）。 |
| **Local Model Mode** (Method 3) | Ollama or LM Studio installed locally. / 本地安裝Ollama或LM Studio。 |

---

## Method 1: Chat Mode / Legacy (Legacy Role-Playing Framework)

> **⚠️ LEGACY MODE**: This is the old role-playing approach.  
> For the real system, use the Python engine (`python`/`start.ps1`) or see `智腦協議-BRAIN-PROTOCOL.md`.

Upload the Q-SpecTrum folder to any AI model and it simulates a multi-role system via text prompts.

舊版角色扮演模式。將 Q-SpecTrum 文件夾上傳到 AI 模型，透過文本提示模擬多角色系統。

### Step 1: Prepare the core files / 準備核心文件

Upload these **6 core files** (the "Brain") to your AI platform:

將以下**6個核心文件**（即「大腦」）上傳到您的AI平台：

| # | File / 文件 | Purpose / 用途 |
|---|---|---|
| 1 | `BOOT.md` | Boot sequence and initialization / 啟動序列與初始化 |
| 2 | `SYSTEM-PROMPT.md` | Core identity and behavior rules / 核心身份與行為規則 |
| 3 | `ACTION-PROTOCOL.md` | Decision-making framework / 決策框架 |
| 4 | `KNOWLEDGE-INDEX.md` | Knowledge base index / 知識庫索引 |
| 5 | `MEMORY.md` | Persistent memory across sessions / 跨會話持久記憶 |
| 6 | `ROLE-REGISTRY.md` | Available roles and capabilities / 可用角色與能力 |

**Optional files** (upload if you want extended features):

**可選文件**（如需擴展功能可上傳）：

- `SKILLS-INDEX.md` — Detailed skill definitions / 詳細技能定義
- `SCENARIOS.md` — Pre-built workflow scenarios / 預建工作流場景
- `AGENTS.md` — Multi-agent coordination rules / 多代理協調規則

### Step 2: Upload to your AI platform / 上傳到您的AI平台

Each platform has a slightly different workflow:

每個平台的操作流程略有不同：

**Claude (Anthropic)**
- Go to [claude.ai](https://claude.ai) and open **Projects**
- Create a new Project and upload all 6 core files to the Project Knowledge
- Start a new conversation within that Project

**Claude（Anthropic）**
- 前往 [claude.ai](https://claude.ai)，打開**專案（Projects）**
- 建立新專案，將6個核心文件上傳至專案知識庫
- 在該專案中開始新對話

**ChatGPT (OpenAI)**
- Open ChatGPT and go to **Custom Instructions** or start a conversation
- Attach all 6 core files using the paperclip icon
- For persistent setup, use a GPT with the files in its Knowledge base

**ChatGPT（OpenAI）**
- 打開ChatGPT，進入**自定義指令**或開始對話
- 使用迴紋針圖標附加所有6個核心文件
- 若需持久設置，可建立GPT並將文件放入其知識庫

**Gemini (Google)**
- Open Gemini and upload all files at once in a single message
- Gemini handles bulk uploads well — no special setup needed

**Gemini（Google）**
- 打開Gemini，在單條訊息中一次上傳所有文件
- Gemini能良好處理批量上傳，無需特殊設置

### Step 3: Activate / 啟動

Send this exact message to the AI:

向AI發送以下訊息：

```
Please read BOOT.md first and follow its Boot Sequence
```

### Step 4: Verify activation / 驗證啟動

The AI should respond with a structured confirmation including:

AI應回覆一個結構化確認，包含：

- System identity acknowledgment / 系統身份確認
- Loaded roles list / 已載入角色列表
- Available capabilities summary / 可用能力摘要
- Ready status / 就緒狀態

If you see this confirmation, Q-SpecTrum is running. You are done.

如果您看到此確認訊息，Q-SpecTrum已在運行。安裝完成。

---

## Method 2: Enhanced Mode (Python Engine) / 增強模式（Python引擎）

The Python engine adds a web UI, REST API (~85 endpoints), and a precise routing engine on top of the AI-Native mode. It uses **only the Python standard library** — no pip install needed.

Python引擎在AI原生模式基礎上增加了Web介面、REST API（84個端點）和精確路由引擎。它**僅使用Python標準庫**，無需pip安裝。

### Start the engine / 啟動引擎

**macOS / Linux:**
```bash
./start.sh
```

**Windows:**
```
Double-click start.bat
```

Or run directly:
```bash
python3 run.py --web
```

### Configuration (optional) / 配置（可選）

Create a `.env` file in the project root if you want to connect a real LLM API. Without it, the engine runs in **Mock mode** — fully functional for testing.

如需連接真實LLM API，可在專案根目錄建立`.env`文件。若無此文件，引擎將以**模擬模式**運行，測試功能完全可用。

```env
# Optional — works without any of these
QSPECTRUM_API_KEY=your-api-key-here
QSPECTRUM_MODEL=claude-3-opus
QSPECTRUM_PORT=8765
```

### Access the web UI / 訪問Web介面

Open your browser and go to:

打開瀏覽器，訪問：

```
http://localhost:8765/chat.html
```

### What Enhanced Mode adds / 增強模式提供的功能

| Feature / 功能 | Description / 說明 |
|---|---|
| Web UI | Browser-based chat interface / 基於瀏覽器的聊天介面 |
| REST API | ~85 endpoints for programmatic access / ~85 個端點供程式化訪問 |
| Routing Engine | Precise role and skill routing / 精確角色與技能路由 |
| Session Management | Persistent sessions with history / 帶歷史記錄的持久會話 |

---

## Method 3: Local Model Mode / 本地模型模式

Run Q-SpecTrum entirely offline using a local LLM. Recommended for privacy-sensitive use cases.

使用本地LLM完全離線運行Q-SpecTrum。推薦用於對隱私敏感的場景。

**With Ollama:**
```bash
QSPECTRUM_LLM=ollama python3 run.py --web
```

**With LM Studio:**
```bash
QSPECTRUM_LLM=lmstudio python3 run.py --web
```

**Model requirements**: 7B+ parameter models recommended for acceptable performance. Smaller models may struggle with complex multi-role tasks.

**模型要求**：建議使用70億參數以上的模型以獲得可接受的性能。較小的模型可能難以處理複雜的多角色任務。

---

## Folder Structure Overview / 文件夾結構一覽

```
Q-SpecTrum/
├── BOOT.md                  ┐
├── SYSTEM-PROMPT.md         │
├── ACTION-PROTOCOL.md       │  Brain (6 core files)
├── KNOWLEDGE-INDEX.md       │  大腦（6個核心文件）
├── MEMORY.md                │  = THE product
├── ROLE-REGISTRY.md         ┘
├── SKILLS-INDEX.md          ─  Optional extensions / 可選擴展
├── SCENARIOS.md             ─  Optional extensions / 可選擴展
├── AGENTS.md                ─  Optional extensions / 可選擴展
├── AI項目管理/               ─  Knowledge Base / 知識庫 (reference data)
├── run.py                   ┐
├── start.sh / start.bat     │  Engine (Python) / 引擎
├── chat.html                │  Optional enhancement / 可選增強
├── *.py                     ┘
└── ...
```

**Total**: ~265 files, ~3.9 MB

**總計**：約265個文件，約3.9 MB

The 6 core `.md` files ARE the product. Everything else is optional.

6個核心`.md`文件就是產品本身。其餘一切皆為可選。

---

## Verification / 驗證安裝

### Chat / Legacy Mode

Send the activation phrase and look for the structured boot confirmation. If the AI lists its loaded roles and reports ready status, the simulation is working.

發送啟動指令，查看結構化啟動確認。如果AI列出已載入的角色並報告就緒狀態，則模擬模式正在工作。

### Enhanced Mode (Engine) / 增強模式（引擎）

```bash
python3 run.py --status
```

Expected output: system status with loaded modules, available endpoints, and mode (Mock/Live).

預期輸出：系統狀態，包含已載入模組、可用端點和模式（模擬/正式）。

### API Check / API檢查

```bash
curl http://localhost:8765/api/status
```

Expected: JSON response with `"status": "ok"` and system details.

預期：JSON回應，包含`"status": "ok"`及系統詳情。

---

## Security / 安全性

The built-in Web UI server is a **single-user development tool**, not a production service.

- **No authentication** — anyone who can reach `http://<host>:8765` can read and write files via the API, trigger chats, and modify local state.
- **Wide-open CORS** — any webpage in any browser can call the API.
- **Default binding is loopback (`127.0.0.1`)** — only your own machine can reach it.

If you need to share the server with others on your LAN, start it with:

```
python run.py --web --host 0.0.0.0
```

Only do this on trusted networks. For internet exposure, put it behind a reverse proxy (nginx/Caddy) with your own auth (HTTP basic auth, OAuth, mTLS). Do **not** expose `0.0.0.0:8765` directly to the internet.

---

**內建 Web 伺服器為單人開發工具，非生產級服務。** 預設只監聽 `127.0.0.1`，僅本機可訪問。若需區網共享，加 `--host 0.0.0.0`；若要上網，務必套反向代理加自己的認證。

---

## Troubleshooting / 常見問題

| Problem / 問題 | Solution / 解決方案 |
|---|---|
| AI didn't respond with confirmation / AI未回覆確認訊息 | Re-send: "Please read BOOT.md first and follow its Boot Sequence". Make sure BOOT.md was actually uploaded. / 重新發送啟動指令。確認BOOT.md已確實上傳。 |
| File too large to upload / 文件太大無法上傳 | Upload the 6 core `.md` files only. Skip the `AI項目管理/` folder — it is reference data, not required for boot. / 僅上傳6個核心`.md`文件。跳過`AI項目管理/`文件夾——它是參考資料，啟動不需要。 |
| Port 8765 already in use / 端口8765已被佔用 | Set `QSPECTRUM_PORT=8766` in your `.env` file (or any available port). / 在`.env`文件中設置`QSPECTRUM_PORT=8766`（或任何可用端口）。 |
| Python not found / 找不到Python | Install Python 3.8 or newer from [python.org](https://python.org). On macOS, you may need `python3` instead of `python`. / 從 [python.org](https://python.org) 安裝Python 3.8或更新版本。macOS上可能需要用`python3`而非`python`。 |
| AI loses context mid-conversation / AI在對話中失去上下文 | Start a new conversation and re-upload files. Some platforms have token limits. / 開始新對話並重新上傳文件。部分平台有token限制。 |

---

## What's Next / 下一步

You are up and running. Here is where to go from here:

您已完成安裝。以下是後續資源：

| Document / 文件 | Purpose / 用途 |
|---|---|
| `QUICK-START.md` | The 2-minute version — get started fast / 2分鐘快速入門 |
| `USER-GUIDE.md` | Daily usage patterns and commands / 日常使用模式與指令 |
| `USE-CASES.md` | Real-world examples and workflows / 真實案例與工作流程 |

---

*Q-SpecTrum — Give any AI a folder, get a company.*

*Q-SpecTrum — 給任何AI一個文件夾，獲得一家公司。*
