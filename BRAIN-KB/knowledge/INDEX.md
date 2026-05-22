# BRAIN-KB Knowledge Base

> 結構化知識庫。只存 P0-P1 級結晶知識。
> 自動同步：每次會話結束時更新。

## 當前知識條目

| # | 類型 | 摘要 | 日期 |
|---|------|------|------|
| 1 | pattern | OpenCode MCP 生態為主戰場（2000+ tools） | 2026-05-09 |
| 2 | pattern | 21 智能算子 + 19 邊標籤因子 | 2026-05-09 |
| 3 | limitation | AI 無法真正自我評估（自我增強偏誤） | 2026-05-09 |
| 4 | pattern | verify-integration.py 的 warn() 語意：True=OK, False=WARN | 2026-05-10 |

## 知識條目 #1 — OpenCode MCP 生態

- 日期: 2026-05-09
- 來源: 全局審計
- 要點: 2000+ MCP tools 已存在，不應自製 (GitHub/DB/FS/Playwright)
- 應用: 封裝 engine endpoints 為 MCP 而非自架 API

## 知識條目 #2 — 21 智能算子 + 19 邊標籤

- 日期: 2026-05-09
- 來源: 知識結晶設計
- 要點: P01-P05 感知 / D01-D05 決策 / E01-E08 執行 / V01-V03 評估
- 邊標籤: SEQ/PAR/CON/LOOP 控制流 + ctx/mem/ref/sig 資料流 + 權限+資源流
- 應用: 知識圖譜設計基礎

## 知識條目 #3 — AI 自我評估限制

- 日期: 2026-05-09
- 來源: 批判性反向思考
- 要點: 同一 LLM 有自我增強偏誤，開發軌與評審軌必須使用不同視角
- 應用: 雙軌迭代設計依據

## 知識條目 #4 — verify-integration.py warn() 語意

- 日期: 2026-05-10
- 來源: P2 bug 修復
- 要點: `warn(desc, condition, detail)` 中 `condition=True` → [OK], `condition=False` → [WARN]
- 應用: 每次修改 verify-integration.py 時注意不反向
