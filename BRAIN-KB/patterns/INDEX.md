# BRAIN-KB Patterns

> 可復用的解決方案和模式索引。
> 積累到 3 次以上經驗後結晶。

## 當前模式

| # | 名稱 | 分類 | 案例數 | 狀態 |
|---|------|------|--------|------|
| 1 | PathGuard FORBIDDEN_PATTERNS 跨平台寫法 | 路徑安全 | 1 | 待驗證 |
| 2 | 記憶三次確認 + 寫入閘門 | 記憶管理 | 1 | 待驗證 |

### Pattern #1: PathGuard 跨平台安全模式

```
問題: 需要阻止特定目錄被寫入，但 drive letter 因環境不同
解法: 只用 Users\xxx\Desktop（不含 C:\），匹配所有 drive letter
案例: path_utils.py FORBIDDEN_PATTERNS
驗證: 跨 Windows 環境有效
```

### Pattern #2: 記憶三次確認 + 寫入閘門

```
問題: 跨會話記憶容易遺失或雜亂
解法: 啟動前讀取(STATUS+REMINDERS+INDEX) → 執行中反覆查閱 REMINDERS → 結束前寫回
閘門: 只寫 P0-P1 級可驗證事實
案例: _HANDOFF/ 系統設計
```
