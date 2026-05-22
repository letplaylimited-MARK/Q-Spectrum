# Dual-Loop Brain Architecture Design Spec

**Date**: 2026-05-17  
**Status**: Draft — Pending User Approval  
**Author**: Q-SpecTrum Brain Session  
**Version**: 1.0

---

## 1. Problem Statement

Q-SpecTrum 的 Knowledge 檢索目前是「邏輯概念」而非「真正的全域搜索能力」。知識檢索只在本地 SQLite + 內存字典中做關鍵詞匹配（token overlap + CJK substring），然後把片段塞給 LLM。LLM 被當作「被調用的後端服務」，而不是「協作夥伴」。

**根本問題**：
1. 檢索單一：僅內存 `_store` 中匹配，DB documents、Vector Store、Knowledge Graph 各自孤立
2. 被動填充：檢索結果塞入 prompt，LLM 無法主動請求更多上下文
3. 無外部能力：無法調用 Web Search、DeerFlow 研究、Real Skills 等外部資源
4. 角色不對等：Q-SpecTrum 是「編排者」，LLM 是「服務」，缺乏對等協作

**用戶願景**：Q-SpecTrum 成為**超級智腦節點**，與通用 AI 大模型形成**對等協作關係**（Hybrid 模式）：
- 日常任務：Q-SpecTrum 作為編排者（Orchestrator）
- 複雜任務：Q-SpecTrum 作為對等協作者（Peer Collaborator），與 LLM 展開多輪辯論/協商
- 調動所有能力：Skills/MCP/LSP/Workflows/Plugins/Agents 相互補足，形成閉環循環

---

## 2. Architecture Overview: Dual-Loop Brain

### 2.1 Core Concept

雙環智腦架構在現有 Q-SpecTrum 引擎之上建立兩層協作模式：

```
                    ┌──────────────────────────────────────────────┐
                    │          外環：Peer 協作環 (Peer Loop)        │
                    │                                              │
                    │  適用：複雜任務、架構設計、深度研究、安全審計  │
                    │  模式：Q-SpecTrum ↔ LLM 對等協作、多輪辯論    │
                    │  能力：技能編排 + 知識結晶 + 審閱裁決          │
                    │                                              │
                    │  ┌────────────────────────────────────────┐   │
                    │  │  PeerCollaborationEngine               │   │
                    │  │  ├── DebateProtocol (多輪辯論)          │   │
                    │  │  ├── SkillOrchestrator (技能編排)       │   │
                    │  │  ├── KnowledgeCrystallizer (知識結晶)   │   │
                    │  │  └── FinalArbiter (最終裁決)            │   │
                    │  └────────────────────────────────────────┘   │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
                    │         Hybrid Mode Router (模式路由器)       │
                    │                                              │
                    │  ┌────────────────────────────────────────┐   │
                    │  │  IntentClassifier (意圖分類)            │   │
                    │  │  ComplexityScorer (複雜度評分)          │   │
                    │  │  ModeSelector (模式選擇)                │   │
                    │  │  ThresholdConfig (可配置閾值)           │   │
                    │  └────────────────────────────────────────┘   │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
                    │         內環：Orchestrator 環 (Inner Loop)    │
                    │                                              │
                    │  適用：日常問答、角色體驗、文件查詢、簡單任務  │
                    │  模式：現有 5 層閉環 Pipeline（優化版）        │
                    │                                              │
                    │  ┌────────────────────────────────────────┐   │
                    │  │  Secretary → Knowledge → Prompt → LLM  │   │
                    │  │  → Response → Sedimentation → Feedback │   │
                    │  │                                        │   │
                    │  │  新增：UniversalKnowledgeOrchestrator  │   │
                    │  │  (多源知識融合 + 智能檢索)              │   │
                    │  └────────────────────────────────────────┘   │
                    └──────────────────────────────────────────────┘
```

### 2.2 Dual-Loop Relationship

| 維度 | 內環 (Orchestrator) | 外環 (Peer Collaborator) |
|------|---------------------|--------------------------|
| **角色** | Q-SpecTrum 作為編排者 | Q-SpecTrum 作為對等協作者 |
| **LLM 關係** | LLM 是「被調用的服務」 | LLM 是「協作夥伴」 |
| **交互輪次** | 單輪（輸入→輸出） | 多輪（辯論→審閱→修正→裁決） |
| **知識檢索** | 多源融合（本地+MCP+外部） | 深度檢索 + 動態補充 |
| **技能調用** | 自動匹配 + 執行 | 編排式調用 + 結果匯入 |
| **延遲** | 低（<3s） | 中（5-30s，取決於輪次） |
| **Token 消耗** | 低 | 中高 |

### 2.3 Backward Compatibility

- **向後兼容**：現有 `process()` pipeline 完全保留，作為內環的基礎
- **漸進實施**：先升級 Knowledge 檢索（內環優化），再加外環協作
- **配置驅動**：通過 `brain_config.py` 控制模式切換閾值
- **零破壞**：所有現有 MCP 工具、Skills、DeerFlow 集成保持不變

---

## 3. Inner Loop: Universal Knowledge Orchestrator

### 3.1 Problem Diagnosis

現有 `KnowledgeResonance.search()` 的核心問題：
1. **檢索單一**：僅 `token overlap + CJK substring` 在內存 `_store` 中匹配
2. **知識孤立**：DB documents、Vector Store、Knowledge Graph、MCP Tools 各自獨立
3. **被動填充**：檢索結果塞入 prompt，LLM 無法主動請求更多上下文
4. **無外部能力**：無法調用 Web Search、DeerFlow 研究、Real Skills 等外部資源

### 3.2 New Architecture

```python
class UniversalKnowledgeOrchestrator:
    """
    多源知識編排器 — 統一調度所有知識來源，生成融合上下文。
    
    檢索流程：
    1. Query Expansion: 擴展用戶查詢（同義詞、相關概念）
    2. Parallel Retrieval: 並行從多源檢索
    3. Fusion & Dedup: 融合結果、去重、關聯
    4. Confidence Scoring: 為每條知識計算置信度
    5. Context Assembly: 組裝為 LLM 可理解的上下文
    """
    
    SOURCES = {
        "memory": "KnowledgeResonance (R-Formula 內存搜索)",
        "sqlite": "platform.db documents/knowledge_items 表",
        "vector": "VectorStore (TF-IDF 語義搜索)",
        "graph": "KnowledgeGraph (21 算子關聯查詢)",
        "skills": "RealSkills (5 個本地技能)",
        "deerflow": "DeerFlow (deep-research, data-analysis 等)",
        "mcp": "MCP Tools (18 工具元數據)",
        "web": "Web Search (可選，需 API)",
        "files": "專案文件系統 (markdown/python 等)",
    }
    
    async def retrieve(self, query: str, mode: str = "orchestrator",
                       max_sources: int = 5) -> KnowledgeContext:
        """
        多源檢索入口。
        mode="orchestrator": 快速檢索（內環），取 top-3 來源
        mode="peer": 深度檢索（外環），取 top-5+ 來源，含外部搜索
        """
```

### 3.3 Retrieval Strategy Table

| 查詢類型 | 啟用來源 | 說明 |
|---------|---------|------|
| 技術問答 | memory + sqlite + graph | 本地知識為主 |
| 代碼審查 | memory + skills + files | 結合 RealSkills |
| 深度研究 | memory + vector + deerflow + web | 需要外部研究 |
| 架構設計 | memory + graph + mcp + skills | 需要系統視圖 |
| 安全審計 | memory + graph + skills + deerflow | 需要威脅情報 |
| 日常對話 | memory + sqlite | 快速響應 |

### 3.4 Integration with Existing `process()`

```python
# 現有 process() 中 Step 2 的升級：
# 舊：knowledge_ctx = self.prompt_builder.build_knowledge_context(user_input)
# 新：
knowledge_ctx = await self.knowledge_orchestrator.retrieve(
    query=user_input,
    mode=self.hybrid_router.select_mode(user_input),
)
system_prompt = self.prompt_builder.build_system_prompt(
    routing["role_code"],
    knowledge_context=knowledge_ctx.to_prompt_text(),
)
```

---

## 4. Outer Loop: Peer Collaboration Protocol

### 4.1 Collaboration Protocol

```python
class PeerCollaborationEngine:
    """
    對等協作引擎 — Q-SpecTrum 與 LLM 展開多輪辯論/協商。
    
    協作流程（標準 3-5 輪）：
    Round 1: Framework Proposal
      Q-SpecTrum → 提出分析框架、知識上下文、約束條件
    
    Round 2: LLM Generation
      LLM → 基於框架生成初稿、方案、代碼
    
    Round 3: Q-SpecTrum Review
      Q-SpecTrum → 審閱初稿，補充知識，標記問題，提出修正
    
    Round 4: LLM Revision
      LLM → 基於審閱意見修正
    
    Round 5: Final Arbitration
      Q-SpecTrum → 最終裁決，知識結晶，沉澱到記憶系統
    """
```

### 4.2 Skill Orchestrator

```python
class SkillOrchestrator:
    """
    在協作過程中動態調用技能，將結果匯入上下文。
    
    調用時機：
    - Round 1 前：預檢索相關技能
    - Round 3 審閱時：調用驗證技能（code-review, data-analysis）
    - Round 5 裁決時：調用沉澱技能（content-sedimentation）
    """
```

### 4.3 Knowledge Crystallizer

```python
class KnowledgeCrystallizer:
    """
    將協作結果沉澱為 P0-P1 知識。
    
    結晶流程：
    1. 提取關鍵決策點（Decision Extraction）
    2. 驗證知識正確性（Verification）
    3. 去重 + 關聯（Dedup + Link）
    4. 寫入記憶系統（Deposit）
    5. 更新知識圖譜（Graph Update）
    """
```

---

## 5. Hybrid Router & Mode Switching

### 5.1 Intent Classifier

```python
class HybridModeRouter:
    """
    混合模式路由器 — 決定每次請求走內環還是外環。
    
    判斷維度：
    1. 意圖類型（問答/創作/研究/設計/審計/協商）
    2. 複雜度評分（基於詞彙、概念數量、跨域程度）
    3. 風險等級（安全/架構/數據完整性）
    4. 知識缺口（本地知識是否足夠）
    5. 用戶階段（S1-S5，高級用戶更可能觸發外環）
    """
```

### 5.2 Mode Selection Rules

| 觸發條件 | 模式 | 說明 |
|---------|------|------|
| 簡單問答、角色體驗、文件查詢 | 內環 | 快速響應 |
| 架構設計、多角色協商、深度研究 | 外環 | 需要深度協作 |
| 安全審計、系統重構、跨域問題 | 外環 | 高風險任務 |
| 知識缺口檢測 | 外環 | 需要外部資源 |
| 用戶明確要求「深度/全面/多輪」 | 外環 | 用戶意圖 |
| 用戶說「狀態/查詢/幫助/你好」 | 內環 | 簡單任務 |

### 5.3 Configuration-Driven

```yaml
# brain_config.yaml (新增配置項)
hybrid_mode:
  enabled: true
  mode_threshold: 0.6          # 複雜度閾值，超過走外環
  max_collaboration_rounds: 5  # 外環最大協作輪次
  knowledge_sources:
    orchestrator: ["memory", "sqlite", "graph"]
    peer: ["memory", "sqlite", "graph", "vector", "deerflow", "skills", "web"]
  force_outer_keywords: ["深度", "全面", "多輪", "辯論", "協作", "deep", "comprehensive"]
  force_inner_keywords: ["狀態", "查詢", "幫助", "你好", "status", "help"]
  user_stage_override:
    S1: "orchestrator"  # 初學者強制內環
    S5: "auto"          # 專家級自動切換
```

---

## 6. Implementation Plan

### Phase 1: Inner Loop Knowledge Orchestration Upgrade (1-2 sessions)

| Step | Task | File | Verification |
|------|------|------|--------------|
| 1.1 | Create `UniversalKnowledgeOrchestrator` skeleton | `brain_core/knowledge_orchestrator.py` | import test |
| 1.2 | Implement Query Expansion | same | query expansion test |
| 1.3 | Implement Parallel Retrieval (memory + sqlite + graph) | same | multi-source retrieval test |
| 1.4 | Implement Fusion & Confidence Scoring | same | fusion result test |
| 1.5 | Integrate into existing `process()` Step 2 | `qspectrum_engine.py` | e2e 9/9 PASS |

### Phase 2: Hybrid Router Implementation (1 session)

| Step | Task | File | Verification |
|------|------|------|--------------|
| 2.1 | Create `HybridModeRouter` | `brain_core/hybrid_router.py` | import test |
| 2.2 | Implement Complexity Scorer | same | scoring test |
| 2.3 | Implement Mode Selector | same | mode switching test |
| 2.4 | Configuration-driven (brain_config.yaml) | `brain_config.py` | config test |

### Phase 3: Outer Loop Collaboration Protocol (2-3 sessions)

| Step | Task | File | Verification |
|------|------|------|--------------|
| 3.1 | Create `PeerCollaborationEngine` | `brain_core/peer_collaboration.py` | import test |
| 3.2 | Implement DebateProtocol (multi-round debate) | same | debate flow test |
| 3.3 | Implement SkillOrchestrator | `brain_core/skill_orchestrator.py` | skill orchestration test |
| 3.4 | Implement KnowledgeCrystallizer | `brain_core/knowledge_crystallizer.py` | crystallization test |
| 3.5 | Integrate into `process()` outer loop path | `qspectrum_engine.py` | e2e test |

### Phase 4: Integration & Optimization (1 session)

| Step | Task | Verification |
|------|------|--------------|
| 4.1 | Inner + Outer loop full integration | verify-integration 31/31 |
| 4.2 | Performance optimization (caching, parallelism) | latency test |
| 4.3 | Documentation update | KNOWLEDGE-INDEX.md update |

### Total Duration: 5-7 sessions

### Rollback Safety Net

Each Phase completion forces a git commit. Rollback at any time.

---

## 7. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Phase 1 changes break existing pipeline | High | Keep existing `build_knowledge_context()` as fallback |
| Outer loop token explosion | Medium | Configurable max_rounds, early termination |
| Mode switching false positives | Low | Configurable threshold, force keywords |
| Performance degradation | Medium | Async retrieval, caching, parallel execution |
| Complexity increases maintenance burden | Medium | Clear module boundaries, comprehensive tests |

---

## 8. Success Criteria

1. **Functional**: `process()` supports both orchestrator and peer modes
2. **Quality**: Knowledge context quality improves (measured by LLM response relevance)
3. **Performance**: Inner loop latency < 3s, outer loop < 30s
4. **Compatibility**: All existing tests pass (e2e 9/9, verify-integration 31/31)
5. **Configurability**: Mode threshold, sources, and keywords are configurable

---

*End of Spec — Pending User Approval*
