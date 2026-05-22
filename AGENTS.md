# Q-SpecTrum 智腦專案 — OpenCode 規則

> ✅ 4 階段遷移完成。brain_core 模組化、config-driven、模板化。
> 每次會話開始前，先讀此檔案。

## 啟動指令

每次新的 OpenCode 會話開始時，按以下順序：

1. **讀取** `智腦協議-BRAIN-PROTOCOL.md`（特別是 §1 啟動順序 + §11 記憶管理）
2. **執行** `python verify-integration.py`（逐項確認輸出，不跳過）
3. **讀取長期記憶**（三次確認，不可跳過）：
   - 3a. 讀 `_HANDOFF/STATUS.md` → 知道當前階段和待辦
   - 3b. 讀 `_HANDOFF/CRITICAL-REMINDERS.md` → 知道 P0 級未修問題
   - 3c. 讀 `_HANDOFF/MEMORY-INDEX.md` → 回顧所有已結晶知識
4. **輸出記憶讀取確認**後，再開始工作
5. **每次執行中**：反覆查閱 `CRITICAL-REMINDERS.md`
6. **會話結束前**：更新記憶（STATUS.md + CRITICAL-REMINDERS.md + MEMORY-INDEX.md）

## 核心原則

- **誠實優先**：不確定就說不確定，不 hallucinate，不偽造
- **6-Simultaneous**：邊梳理、邊記錄、邊重構、邊檢查、邊修復、邊模擬
- **3 次沙盤**：Tier 2/3 任務需從 3 個不同視角推演後再執行
- **雙軌迭代**：開發軌 + 評審軌並行，評審軌對安全問題有覆蓋權

## 專案結構

```
Q-SpecTrum/
├── 智腦協議-BRAIN-PROTOCOL.md     ← 本專案的運作系統（先讀）
├── verify-integration.py          ← 啟動時執行
├── start.py                       ← 引導腳本（brain bootstrap）
├── brain_config.py                ← 專案設定檔（profile/modules/llm）
├── archive/                       ← 歷史歸檔（era1 + audits）
│   ├── era1/                      ← BOOT.md / SYSTEM-PROMPT.md / ACTION-PROTOCOL.md
│   └── audits/                    ← 9 AUDIT-*.md + FINDINGS-REGISTRY.md
├── KNOWLEDGE-INDEX.md             ← 知識索引
├── ROLE-REGISTRY.md               ← 15 角色註冊
├── MEMORY.md                      ← 長期記憶
├── brain_core/                    ← 可複用模板套件（模組化）
│   ├── config.py / graph.py / mcp_bridge.py
│   ├── capabilities.py / brain.py / mcp_router.py
│   └── __init__.py
├── AI项目管理/                    ← 知識庫（只讀）
│   ├── Platform/db/              ← SQLite 資料庫
│   ├── Skills/                   ← 技能定義
│   ├── QCM/                      ← QCM 理論
│   └── ...
├── _HANDOFF/                      ← 跨會話狀態
├── .opencode/                     ← OpenCode 配置（待建立）
│   ├── agents/                    ← 15 角色 Agent 定義
│   ├── skills/                    ← SKILL.md 技能
│   └── tools/                     ← 自訂工具
└── config/                        ← 設定檔
```

## 已知問題（優先修復）

1. `platform.db` 為 0 bytes（需拷貝 `platform_restored.db`）
2. `AI项目管理/Platform/scripts/path_utils.py` 有 3 處 `C:\Users\` 硬編碼

## 已修復問題

3. ~~文件數字不一致（47→40 表，748→85 行）~~ ✅ 已修復
4. ~~測試殘留：`ROUND17_*`、`ORPHAN_TEST_DOC.md`~~ ✅ 已清理
5. ~~`test_ai_model.py`/`test_developer.py`/`test_nontechnical.py` GBK 編碼錯誤~~ ✅ 已修復
6. ~~`test_nervous_system.py` SQLite 臨時文件無法刪除~~ ✅ 已修復
7. ~~`test_regression.py` pytest fixture `r` 缺失~~ ✅ 已修復

## 階段狀態

- 當前階段：**Phase 0 → 4 全部完成** ✅
- 下一階段：維護模式（迭代開發 + 除錯）
- 詳見：`_HANDOFF/STATUS.md` 完整進度報告
