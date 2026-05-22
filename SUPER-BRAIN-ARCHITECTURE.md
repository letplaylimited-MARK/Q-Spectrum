# Super Brain Architecture v2.0

> **從 4 層堆疊到 1 個乾淨模板**
> 基於 3 輪深度分析（62 項審計發現、40 資料表、22 模組、11 文件）的架構設計

---

## 根本問題

現有系統經過 4 個時代（RP → Script → Engine → MCP），每個時代直接疊加在舊時代之上，從未清理：

```
Era1: BOOT.md, SYSTEM-PROMPT.md, ACTION-PROTOCOL.md, ROLE-REGISTRY.md
  ↓
Era2: AI项目管理/ (QCM theory, SQLite, scripts, 40 tables)
  ↓
Era3: qspectrum_engine.py + 22 sub-modules (~8000 lines Python)
  ↓
Era4: qspectrum_mcp_server.py + .opencode/tools/ (18 + 5 MCP tools)
```

這導致：
- **文件膨脹**：11 個主要文件，40% 內容重複，7 處不一致
- **邏輯分散**：R formula 權重有 3 個衝突版本
- **死碼殘留**：plugin_loader.py（345 行）是唯一純死碼，但其餘模組依賴關係複雜
- **schema 漂移**：29 SQL 定義表 vs 40 實際表（11 張無定義）
- **context 消耗**：每次啟動需讀取大量文件才能進入工作狀態

---

## 核心設計原則

### 原則 1：Template / Instance 分離

```
brain-template/          ← 可複用的智腦模板（git repo）
  └── 只含框架程式碼、協定、預設設定

my-project/               ← 專案工作區（每個專案一個）
  ├── brain.yaml          ← 繼承 template + 覆蓋設定
  ├── data/               ← vector store, graph db, memory
  └── custom-skills/      ← 專案自訂技能（可選）
```

### 原則 2：Config-Driven Brain

大腦的能力（載入哪些模組、使用哪些 LLM、啟用哪些技能）由**設定檔**決定，而非程式碼 imports。

```yaml
# brain.yaml
brain:
  profile: full  # minimal | standard | full
  modules:
    conversation: true    # SmartMock LLM 對話引擎
    memory: true          # 專案記憶隔離
    skills-core: true     # 核心技能引擎
    skills-extended: false # 擴充技能（依需求啟用）
    graph: true           # 知識圖譜算子
    ghost-channel: false  # 幽靈通道（跨 instance 同步用）
  llm:
    provider: anthropic
    model: claude-4
  mcp:
    auto-bridge: true     # 自動產生 MCP tools
    port: 0               # 0 = stdio, >0 = HTTP

# 以 4 個 profile 應對不同情境：
# minimal → 純對話 + 基本記憶（適合快速問答）
# standard → 對話 + 記憶 + 技能 + 圖譜（日常開發）
# full     → 全部啟用（複雜多專案協作）
# custom   → 手動指定 modules list
```

### 原則 3：AI-as-Collaborator

15 角色不分優先級，而是作為**協作模式**：

```
使用者意圖
  │
  ▼
意圖分類器（輕量，5-10 行邏輯）
  ├── 問問題     → Research Mode (T01, T02)
  ├── 寫程式     → Development Mode (Q01-Q05)
  ├── 審查/評審  → Review Mode (Q06, Q07)
  ├── 設計/規劃  → Architecture Mode (T03-T05)
  └── 系統管理   → Admin Mode (S01-S03)
```

每個模式關聯一組角色、技能、工具。不再需要先選角色再工作。

### 原則 4：MCP Auto-Bridge

從載入的模組能力自動產生 MCP tool definitions，不需要手動維護 qspectrum_mcp_server.py。

```
能力註冊（Python decorator）
  ↓
自動掃描 @capability 裝飾器
  ↓
產生 MCP Tool Schema（含參數、描述、範例）
  ↓
暴露為 stdio MCP server（或 HTTP）
```

---

## 架構總覽

```
┌──────────────────────────────────────────────────────────────────┐
│                     PROJECT WORKSPACE                            │
│  D:\工作資料\TEST\Q-SpecTrum\                                    │
│                                                                  │
│  brain.yaml          ← 大腦設定（核心入口）                       │
│  .opencode/          ← OpenCode 整合層                          │
│  data/               ← 向量庫、圖譜、記憶                        │
│  skills/             ← 專案自訂技能                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              BRAIN TEMPLATE (reusable)                    │    │
│  │  brain-core/                                              │    │
│  │                                                           │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌──────────┐  │    │
│  │  │ Memory     │ │  Skills   │ │  Roles    │ │  Graph   │  │    │
│  │  │ Engine     │ │  Engine   │ │  Manager  │ │  Engine  │  │    │
│  │  └───────────┘ └───────────┘ └───────────┘ └──────────┘  │    │
│  │                                                           │    │
│  │  ┌───────────────────────────────────────────────────┐    │    │
│  │  │             MCP Auto-Bridge Layer                  │    │    │
│  │  └───────────────────────────────────────────────────┘    │    │
│  │                                                           │    │
│  │  ┌───────────────────────────────────────────────────┐    │    │
│  │  │             Protocol Layer                          │    │    │
│  │  │  BRAIN-PROTOCOL.md (精簡版, ~200 行)                │    │    │
│  │  │  CORE-VALUES.md (新, ~50 行)                        │    │    │
│  │  │  GLOSSARY.md (新, ~80 行)                           │    │    │
│  │  └───────────────────────────────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  LEGACY / archive/  (唯讀，不會修改，僅供參考)              │    │
│  │  BOOT.md, SYSTEM-PROMPT.md, ACTION-PROTOCOL.md, ...        │    │
│  │  審計報告 9 份 → archive/audits/                           │    │
│  │  AI项目管理/ (唯讀保留歷史資料)                              │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 元件設計

### 1. Memory Engine（記憶引擎）

**來源**：project_memory.py (1034 行) + SmartMock LLM 對話上下文

**職責**：
- 專案感知的記憶隔離（不同專案的記憶不互相污染）
- 跨會話記憶（透過向量儲存）
- 記憶分級（P0-P3，只保留 P0-P1）
- 自動摘要與知識結晶

**介面**：
```python
class MemoryEngine:
    async def store(level, content, project, tags) → id
    async def recall(query, project, level_min) → list[Memory]
    async def summarize(project) → Summary
    async def forget(ids) → None  # 明確遺忘
```

### 2. Skills Engine（技能引擎）

**來源**：real_skills.py + deerflow_real_skills.py + skill_executor.py

**職責**：
- 技能註冊與發現
- 技能執行與結果收集
- 技能組合（pipeline）

**技能清單（初始 11 個）**：
1. `file-analysis` → 分析檔案結構與依賴
2. `code-review` → 結構化程式碼審查
3. `deep-research` → 深入研究主題
4. `consulting-analysis` → 顧問級分析
5. (更多由 real_skills.py 定義)

**介面**：
```python
@capability("skill_execute", "執行一個技能")
async def skill_execute(name: str, params: dict) -> SkillResult
```

### 3. Roles Manager（角色管理器）

**來源**：SmartMock LLM (854 行)

**職責**：
- 15 角色的系統提示管理
- 協作模式路由
- 角色切換與上下文保持

**簡化角色系統**：
```
Family TRUM (5) → 技術實作
  Q01 Architect    Q02 Developer    Q03 Reviewer
  Q04 Tester       Q05 DevOps

Family SPEC (5) → 規劃與設計
  T01 Researcher   T02 Designer     T03 Coordinator
  T04 Writer       T05 Strategist

Family QCM (5) → 品質與安全
  S01 Auditor      S02 Safety       S03 Ethicist
  S04 Analyst      S05 Archivist
```

### 4. Graph Engine（圖譜引擎）

**來源**：knowledge_graph.py

**職責**：
- 21 算子操作
- 19 邊類型
- NetworkX + SQLite 持久化

**21 算子保留**（已確認 3 個 meta 合併是正確的）：
```
P01-P08: 規劃算子（Plan）
D01-D04: 開發算子（Develop）  
E01-E04: 評估算子（Evaluate）
V01-V04: 驗證算子（Verify）
M01:     元算子（Meta）
```

### 5. MCP Auto-Bridge

**來源**：qspectrum_mcp_server.py (.opencode/tools/)

**職責**：
- 自動掃描 `@capability` 裝飾器
- 產生 MCP tool schema
- 暴露為 stdio MCP server
- 支援 rate limiting、auth

---

## 遷移策略（4 階段）

### Phase 0：架構準備（現在）

- [x] 完整專案分析（完成）
- [x] 知識圖譜建立（完成）
- [ ] R formula 權重建模
- [ ] schema 定義補全（11 張表補 doc）
- [ ] 文件不一致修復（7 處）

### Phase 1：核心模板建立

建立 brain-core/ 目錄結構：

```
brain-core/
├── __init__.py
├── memory_engine.py      ← from project_memory.py
├── skills_engine.py      ← from real_skills.py + skill_executor.py
├── roles_manager.py      ← from SmartMock LLM
├── graph_engine.py       ← from knowledge_graph.py
├── mcp_auto_bridge.py    ← from qspectrum_mcp_server.py
├── config.py             ← brain.yaml 載入器
└── brain.py              ← 整合入口
```

執行步驟：
1. 建立 brain-core/（全新目錄，不影響現有系統）
2. 逐一提取核心邏輯，抽掉硬編碼路徑
3. 每個模組使用 `from legacy.xxx import YYY` 橋接
4. 逐步取代 import 路徑

### Phase 2：MCP 解耦

1. brain-core 暴露 MCP auto-bridge
2. qspectrum_mcp_server.py → 改為 thin wrapper
3. .opencode/tools/ → 從 brain-core 自動載入

### Phase 3：清理與歸檔

1. 確認無反向依賴後，歸檔 Era1-4 舊檔
2. legacy/archive/ 目錄建立
3. 審計報告合併為 FINDINGS-REGISTRY.md
4. 文件精簡（11 主文件 → 5 核心文件）

---

## 文件策略（精簡）

| 現在 (11 files) | 之後 (5 files) | 說明 |
|---|---|---|
| 智腦協議-BRAIN-PROTOCOL.md (702行) | BRAIN-PROTOCOL.md (~200行) | 精簡啟動順序 + 四級強度，移除重複 |
| AGENTS.md | → 納入 BRAIN-PROTOCOL.md | 專案規則段落 |
| SYSTEM-PROMPT.md | archive/ | Era1 產物 |
| ACTION-PROTOCOL.md | archive/ | Era1 產物 |
| BOOT.md | archive/ | Era1 產物 |
| KNOWLEDGE-INDEX.md | KNOWLEDGE.md | 知識索引精簡版 |
| MEMORY.md | → 納入 KNOWLEDGE.md | |
| SKILLS-INDEX.md | → 納入 KNOWLEDGE.md | |
| ROLE-REGISTRY.md | ROLES.md | 角色定義（精簡格式） |
| INDEX.md | → 廢止 | 被 KNOWLEDGE.md 取代 |
| MEMORY-INDEX.md | → 保留為跨會話記憶索引 | |

新增：
- CORE-VALUES.md（~50 行）：核心價值觀與誠實原則
- GLOSSARY.md（~80 行）：QCM 術語定義

---

## R Formula 權重統一（已解析）

### 實際發現

經過實際程式碼 grep 確認，存在 **3 個版本**，分別代表不同的演化階段：

| 版本 | 來源位置 | ω₁(K_sim) | ω₂(C_comp) | ω₃(I_freq) | ω₄(E_div) | 說明 |
|---|---|---|---|---|---|---|
| **A** | qspectrum_engine.py:1545, KNOWLEDGE-INDEX.md, SYSTEM-PROMPT.md, MEMORY.md, USER-GUIDE.md, 費曼卡004 | **0.35** | **0.25** | **0.25** | **0.15** | 實際運行的引擎版本，含 Formula 7 動態自適應 |
| **B** | crystallization.md, knowledge_graph.md | **0.35** | **0.30** | **0.25** | **0.10** | 理論文件變體，C_comp 更高、E_div 更低 |
| **C** | QCM_MVP.md, _INDEX.md (line 69), 完整論文報告 v11.1 (line 303) | **0.25** | **0.35** | **0.20** | **0.20** | 經 127 對工作對校準的版本（R²=0.78, RMSE=0.14） |

### 演化脈絡

```
原始理論 (A): 0.35/0.25/0.25/0.15
  ↓
理論變體 (B): 0.35/0.30/0.25/0.10  (crystallization.md 調整互補性權重)
  ↓
127對校準 (C): 0.25/0.35/0.20/0.20  (論文報告：互補性最重要)
  ↓ (但校準結果從未 merge 回引擎！)
目前引擎 (A): 0.35/0.25/0.25/0.15 + Formula 7 動態適應
```

### 關鍵洞察

引擎有 **Formula 7 動態權重自適應**（qspectrum_engine.py:1935-1984）：
- 基於過往 R 值與目標 R=0.85 的誤差（r_error = avg_r - R_TARGET）
- 持續以學習率 λ=0.1 調整權重
- 權重限幅在 [0.05, 0.50] 區間，收斂後歸一化
- **因此初始權重只是起點，系統最終會 self-correct**

### 解決方案

1. **起始權重用校準版 C**（0.25/0.35/0.20/0.20），因為它基於 127 對真實數據
2. **保留 Formula 7 動態適應**作為持續校準機制
3. **在 brain.yaml 中可配置**：

```yaml
brain:
  r_formula:
    initial_weights: [0.25, 0.35, 0.20, 0.20]  # 基於127對校準
    dynamic_adaptation: true                      # 保留Formula 7
    learning_rate: 0.1
    target_r: 0.85
    clamp: [0.05, 0.50]
```

4. 在 KNOWLEDGE.md 中記錄所有 3 個版本的歷史背景與演化脈絡

---

## 已知風險

| 風險 | 影響 | 緩解 |
|---|---|---|
| 遷移期間現有功能受損 | 已整合的 MCP tools 可能失效 | Phase 1 先建立 brain-core/，不修改現有檔案 |
| 文件精簡遺漏重要內容 | 40% 獨特內容可能被誤刪 | 先合併再刪除，每個文件歸檔前比對 diff |
| plugin_loader.py 有隱藏依賴 | 可能不只是死碼 | 先 grep 所有 import，確認 0 依賴後再刪 |
| 11 張無定義表有重要資料 | 遺失歷史記錄 | 先 dump schema + sample data，再補 doc |
| 使用者習慣舊文件位置 | 找不到關鍵資訊 | 每個 archive 檔案在頂端加 redirect notice |

---

## 詳細遷移計畫（Refactoring Plan）

### Phase 0：準備工作（本會話可執行）

**目標**：消除已知不一致，為模板提取做準備。不修改引擎程式碼。

#### 0.1 修復 7 處文件不一致
```
1. AGENTS.md: Phase 0 reference → 更新為當前階段
2. KNOWLEDGE-INDEX.md §6: row count 748→85
3. KNOWLEDGE-INDEX.md: stale boot chain reference
4. LATEST-ACTIVATION-REPORT.md: pre-fix data
5. BRAIN-KB/decisions: 落後 1 個版本
6. 智腦協議-BRAIN-PROTOCOL.md §8: stale content
7. 智腦協議-BRAIN-PROTOCOL.md §11.5: stale content
```
檢查點：跑 verify-integration.py → 31/31 [OK]

#### 0.2 補全 11 張未定義表文件
```sql
-- 對每張 undocumented 表執行：
SELECT name, sql FROM sqlite_master WHERE type='table';
SELECT * FROM <table> LIMIT 5;
-- 結果寫入 AI项目管理/Platform/db/schema/_undocumented_tables.md
```
檢查點：schema 目錄下每張表都有對應文件

#### 0.3 確認 plugin_loader.py 死碼
```bash
grep -r "plugin_loader" *.py _HANDOFF/ .opencode/ --include="*.py" --include="*.md"
# 確認 0 匹配後，移入 archive/dead/
```
檢查點：plugin_loader.py 移入 archive/dead/，verify 無報錯

#### 0.4 建立 archive/ 目錄結構
```
archive/
├── era1-rp/
│   ├── BOOT.md
│   ├── SYSTEM-PROMPT.md
│   ├── ACTION-PROTOCOL.md
│   └── ROLE-REGISTRY.md (保留根目錄副本直到 Phase 3)
├── era2-script/
│   └── AI项目管理/  (symbolic link or copy)
├── audits/
│   ├── AUDIT-20JOURNEY.md → FINDINGS-REGISTRY.md (合併)
│   ├── AUDIT-20ROUND.md
│   ├── AUDIT-20ROUND-ADVERSARIAL.md
│   ├── AUDIT-ADVERSARIAL.md (可能與上重複)
│   ├── AUDIT-FMEA.md
│   ├── AUDIT-GENERATIONAL.md
│   ├── AUDIT-REVERSE-THINKING.md
│   ├── AUDIT-LONGITUDINAL.md
│   ├── AUDIT-PERSONA-STRESSOR.md
│   └── AUDIT-INDUSTRY-WARGAME.md
└── dead/
    └── plugin_loader.py
```

---

### Phase 1：Core Template 建立

**目標**：建立 brain-core/ 目錄，從現有模組提取核心邏輯。

#### 1.1 建立 brain-core/ 骨架

```
brain-core/
├── __init__.py           # from qspectrum_engine.py (核心整合)
├── config.py             # brain.yaml 載入器 + 驗證
├── memory_engine.py      # from project_memory.py (1034行)
├── skills_engine.py      # from real_skills.py + skill_executor.py
├── roles_manager.py      # from SmartMock LLM (854行)
├── graph_engine.py       # from knowledge_graph.py
├── mcp_auto_bridge.py    # from qspectrum_mcp_server.py
├── protocol/
│   ├── __init__.py
│   ├── session.py        # 啟動順序邏輯
│   ├── sandbox.py        # 沙盤推演引擎
│   └── review.py         # 雙軌評審邏輯
└── capabilities/
    ├── __init__.py       # @capability 裝飾器定義
    └── registry.py       # 能力掃描與註冊
```

#### 1.2 提取策略

每個模組使用「橋接模式」：
```
brain-core/memory_engine.py:
  from legacy.project_memory import ProjectMemory  # 先 import 舊版
  
  class MemoryEngine:
      def __init__(self, config):
          self._legacy = ProjectMemory(...)  # 內部委託
          # 新增 config-driven 行為
      
      async def store(self, ...):
          # 新介面 → 委託給 _legacy
          return await self._legacy.store(...)
```

如此舊系統不受影響，新系統逐步取代。

#### 1.3 各模組提取步驟

| 步驟 | 模組 | 來源檔案 | 預估行數 | 依賴 |
|---|---|---|---|---|
| 1.3.1 | config.py | 新寫 | ~80 | 無 |
| 1.3.2 | capabilities/registry.py | 新寫 + qspectrum_mcp_server.py | ~60 | config.py |
| 1.3.3 | memory_engine.py | project_memory.py | ~200 | config.py |
| 1.3.4 | graph_engine.py | knowledge_graph.py | ~300 | config.py, SQLite |
| 1.3.5 | roles_manager.py | SmartMock LLM | ~250 | config.py |
| 1.3.6 | skills_engine.py | real_skills.py + skill_executor.py | ~180 | config.py, roles_manager |
| 1.3.7 | mcp_auto_bridge.py | qspectrum_mcp_server.py | ~150 | capabilities/registry |
| 1.3.8 | protocol/ | 智腦協議.md | ~120 | config.py |
| 1.3.9 | __init__.py | qspectrum_engine.py | ~100 | 以上全部 |

檢查點每個步驟完成後：`python -c "from brain_core import <module>; print('OK')"`

---

### Phase 2：MCP 解耦

**目標**：brain-core 獨立提供 MCP 服務，舊 qspectrum_mcp_server.py 變為 thin wrapper。

#### 2.1 MCP Auto-Bridge 實作

```python
# brain-core/mcp_auto_bridge.py

@dataclass
class Capability:
    name: str
    description: str
    handler: Callable
    params: list[ParamSchema]

class MCPAutoBridge:
    def __init__(self, registry: CapabilityRegistry):
        self._capabilities = registry.scan()
    
    def generate_tools(self) -> list[dict]:
        """Auto-generate MCP tool definitions from @capability decorators"""
        return [
            {
                "name": cap.name,
                "description": cap.description,
                "input_schema": {
                    "type": "object",
                    "properties": {p.name: p.schema for p in cap.params}
                }
            }
            for cap in self._capabilities
        ]
    
    async def handle_call(self, tool_name: str, args: dict) -> Any:
        cap = self._capabilities[tool_name]
        return await cap.handler(**args)
```

#### 2.2 舊 MCP Server 改造

```python
# qspectrum_mcp_server.py → thin wrapper
from brain_core import Brain

brain = Brain(config_path="brain.yaml")
bridge = brain.mcp_bridge

@mcp.tool()
async def brain_query(query: str) -> str:
    """Delegated to brain-core"""
    return await bridge.handle_call("brain_query", {"query": query})
```

#### 2.3 .opencode/tools/ 5 工具遷移

每個工具改為透過 MCP Auto-Bridge 調用：
- brain-query → Brain.query()
- role-delegate → Brain.roles.delegate()
- sandbox-drill → Brain.protocol.sandbox()
- memory-sync → Brain.memory.sync()
- verify-health → Brain.protocol.health_check()

---

### Phase 3：清理與歸檔

**目標**：刪除死碼、合併審計報告、精簡文件。此階段最後執行，確保一切正常後才清理。

#### 3.1 審計報告合併

9 份審計報告合併為 1 份 FINDINGS-REGISTRY.md：

```markdown
# Findings Registry

## 摘要
- 總發現數：62
- 已修復：4（FIXES-APPLIED.md 記錄）
- 未修復 P0：0
- 未修復 P1：7（文件不一致）

## 發現列表
| ID | 類型 | 嚴重度 | 來源審計 | 檔案 | 狀態 |
|---|---|---|---|---|---|
| F001 | 硬編碼路徑 | P1 | AUDIT-20ROUND | path_utils.py | 待修 |
| ... | ... | ... | ... | ... | ... |

## 原始審計報告
archive/audits/ 目錄下保留原始版本
```

#### 3.2 文件精簡

執行步驟：
1. 建立 KNOWLEDGE.md（從 KNOWLEDGE-INDEX.md + MEMORY.md + SKILLS-INDEX.md 合併）
2. 建立 CORE-VALUES.md（新寫）
3. 建立 GLOSSARY.md（新寫，參考 QCM-術語統一對照表.md）
4. 精簡 BRAIN-PROTOCOL.md（從 702 行 → ~200 行）
5. 原文件移入 archive/ 並在頂端加 redirect notice
6. 確認 AGENTS.md 只含 OpenCode 特有規則（非重複）

#### 3.3 刪除確認清單

每個刪除操作前必須：
```
1. grep -r "依賴名稱" . --include="*.py" --include="*.md"
2. 確認 0 匹配
3. 先移入 archive/，觀察 1 個會話週期
4. 確認無錯誤後，再永久刪除
```

---

### Phase 4：專案模板化

**目標**：brain-core 可作為獨立的 git repo 重複使用。

#### 4.1 模板提取

```bash
# 從目前專案中提取通用部分
mkdir ../qspectrum-brain-template
cp -r brain-core/ ../qspectrum-brain-template/
cp brain.yaml.example ../qspectrum-brain-template/
# ... 只留通用框架，不留專案特定資料
```

#### 4.2 新專案使用方式

```yaml
# my-new-project/brain.yaml
brain:
  template: qspectrum-brain-template@v1.0
  # 只需覆蓋專案特定的設定
  project:
    name: My New Project
    root: ./
  memory:
    path: ./data/memory
```

#### 4.3 啟動腳本

```bash
# qspectrum-brain-template/start.py
import sys
from pathlib import Path
import yaml

def main():
    config_path = Path("brain.yaml")
    if not config_path.exists():
        print("❌ 請建立 brain.yaml")
        sys.exit(1)
    
    # 載入 template（如果是繼承的）
    config = yaml.safe_load(config_path.read_text())
    if "template" in config.get("brain", {}):
        template_path = find_template(config["brain"]["template"])
        template_config = yaml.safe_load(template_path.read_text())
        # deep merge
        config = deep_merge(template_config, config)
    
    brain = Brain(config)
    brain.start()
```

---

### 時間估算

| Phase | 步驟數 | 預估工作時長 | 風險 |
|---|---|---|---|
| Phase 0 準備 | 4 子項 | 1-2 次會話 | 低 |
| Phase 1 Core Template | 9 子項 | 3-5 次會話 | 中（模組依賴複雜） |
| Phase 2 MCP 解耦 | 3 子項 | 1-2 次會話 | 中低 |
| Phase 3 清理歸檔 | 3 子項 | 1-2 次會話 | 低 |
| Phase 4 模板化 | 3 子項 | 1-2 次會話 | 低 |

總計：**7-13 次會話**（依任務大小和審查深度）

---

---

## 3 視角沙盤整合（最終執行藍圖）

執行前經過 Q01（開發者）、Q06（審計員）、T03（協調官）三視角沙盤推演。

### 沙盤結論

| 視角 | 會話估算 | 核心主張 |
|------|---------|---------|
| Q01 開發者（樂觀） | **4 會話** | 跳過 Phase 0，直接建 brain-core/，舊引擎 thin wrapper |
| Q06 審計員（悲觀） | **10-20+ 會話** | 必須先 git init + 參數化 init 測試 + 每個模組提取後行為等價驗證 |
| T03 協調官（務實） | **10-16 會話** | Phase 1 只提取 5/9 模組，e2e 替代 unit test，明確 6 項 No-Go |

### 整合計畫（T03 調和版）

```
T03 裁決：取 Q06 的安全底線，配 Q01 的加速策略
=================================================

保留 Q06 的安全底線：
  ✅ git init + 初始 commit（Phase 0 強制）
  ✅ QSpectrumEngine.__init__ 參數化測試（~200 行，保護 212 行上帝方法）
  ✅ 每個 brain-core module 提取後 import switch 測試
  ✅ bridge 模式（不是 big bang）

採納 Q01 的加速：
  ✅ Phase 0 只做最小必要（1 會話）：git init + 7 文件修復 + 死碼 archive
  ✅ 不補 11 張表文件（現在補了 Phase 1 bridge 時 schema 又會改）
  ✅ MCP Auto-Bridge 作為 Phase 1 內部設計，不是獨立 Phase
  ✅ Phase 4 模板化延後

明確 No-Go：
  ❌ 不改寫 SmartMock LLM（854 行）內部邏輯 — 只封裝介面
  ❌ 不補 13 個 untested 檔案的 unit test — 成本過高，e2e 替代
  ❌ 不遷移 AI项目管理/ 的 14 個 scripts — archive/ 後保持唯讀
  ❌ 不實現 HTTP MCP Server — stdio 就夠
  ❌ 不處理 11 張 undocumented 表的內容遷移 — 只補 schema doc
  ❌ 不重寫 deerflow_bridge.py, ghost_channel_*.py
```

### 最終 4 階段時程

```
Phase 0 ── [1 會話] 安全底線
  Step 0:  git init + git add . + git commit -m "pre-refactoring baseline"
  Step 1:  修 7 處文件不一致（只修指定位置，不探索）
  Step 2:  plugin_loader.py → archive/dead/
  Step 3:  建立 archive/ 目錄結構
  Step 4:  寫 QSpectrumEngine.__init__ 參數化測試（13 個 try/except 模擬）
  驗證點：verify-integration.py 31/31 [OK] + 新測試 PASS

Phase 1 ── [5 會話] Core Template（5/9 模組）
  Session 1: brain-core/ 骨架 + config.py（~80 行，無依賴）
             驗證: python -c "from brain_core.config import Config; print('OK')"
  Session 2: graph_engine.py bridge（唯一有測試保護的模組）
             驗證: test_knowledge_graph.py 23/23 PASS
  Session 3: mcp_auto_bridge.py + capabilities/registry.py
             驗證: brain-core MCP tools 可正常 list/call
  Session 4: __init__.py + brain.py 入口
             驗證: python -c "from brain_core import Brain; b=Brain(); print('OK')"
  Session 5: import switch — qspectrum_engine.py 改為 from brain_core import
             驗證: test_e2e.py 9/9 PASS + verify-integration.py 31/31 [OK]

       暫緩模組（有理論價值，但 bridge 提取風險 > 收益）：
  memory_engine.py  ← project_memory.py (1034行, 0測試)
  roles_manager.py  ← SmartMock LLM (854行, 0測試)  
  skills_engine.py  ← real_skills.py + deerflow_real_skills.py (代碼交織)

Phase 2 ── [2 會話] MCP 整合
  Session 1: brain-core MCP Auto-Bridge 輸出所有 tools
  Session 2: 確認 18 + 5 MCP tools 全部可通過 brain-core 調用
             舊 qspectrum_mcp_server.py 改為 thin wrapper
             驗證: test_e2e.py 全 PASS + 所有 .opencode/tools/ 正常

Phase 3+4 ── [2-4 會話] 清理 + 文件精簡
  死碼永久刪除（archive/ 觀察一週後確認無報錯）
  文件精簡: 11 → 5 核心文件（archive/ era1 + redirect notice）
  審計報告合併: 只做摘要 FINDINGS-REGISTRY.md，保留原始檔案
  模板化: brain-core/ 作為獨立 repo 的最後一步

總時長：10-12 會話（T03 最佳估算）
```

### Rollback 安全網

```
每個 checkpoint 前強制：
  git add -A && git commit -m "checkpoint: <desc>"

| Checkpoint | Rollback | 成本 |
|-----------|---------|------|
| C0 Phase 0 | git checkout . 或 rm archive/ | <1min |
| C1 每 module 提取 | 刪 brain-core/<m>.py + 恢復 import | <1min |
| C2 import switch | git checkout qspectrum_engine.py | <30s |
| C3 MCP Auto-Bridge | 關 brain.yaml feature flag | <10s |
| C4 歸檔 | cp -r archive/* ./ | <1min |
```

### 整合測試矩陣

```
┌──────────────────────────────────────────────────────────────────┐
│ 測試                     │ Phase 0 │ Phase 1 │ Phase 2 │ Ph3+4  │
├──────────────────────────────────────────────────────────────────┤
│ verify-integration.py    │ 31/31   │ 31/31   │ 31/31   │ 31/31   │
│ test_e2e.py              │ 9/9     │ 9/9     │ 9/9     │ 9/9     │
│ test_knowledge_graph.py  │ 23/23   │ 23/23   │ 23/23   │ 23/23   │
│ test_vector_store.py     │ 7/7     │ 7/7     │ 7/7     │ 7/7     │
│ init_parameterized_test  │ NEW     │ PASS    │ PASS    │ PASS    │
│ brain_core_import_test   │ -       │ NEW     │ PASS    │ PASS    │
│ mcp_auto_bridge_test     │ -       │ -       │ NEW     │ PASS    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 開發者筆記

- 此架構設計經過 3 輪分析（62 項審計發現、40 表、22 模組、11 文件）
- 所有結論基於實際程式碼分析，非猜測
- P0 問題（R formula 衝突）已在架構設計中解決
- 模組提取順序：config → capabilities → memory → graph → roles → skills → mcp → protocol
- 每個提取步驟後跑 verify-integration.py 確保沒壞
- 所有刪除操作先移入 archive/ 觀察一個會話週期
- 核心指導原則：**不破坏現有功能的前提下，逐步取代舊系統**
