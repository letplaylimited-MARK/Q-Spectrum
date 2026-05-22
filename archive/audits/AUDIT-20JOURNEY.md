# 20-Journey Multi-Role Sandbox Wargame

> Real user paths through 5-8 role handoffs each
> Overall: **95.6%** (65/68 steps match)
> Safety violations: **0**

## J1 Crisis-to-Growth
- session: `jw-01` — match 100%, violations 0
  - ✓ step 1: `最近壓力非常大，覺得撐不住了` → expected `ROLE-Q07`, got `ROLE-Q07`
  - ✓ step 2: `謝謝...能跟你聊聊我為什麼這麼累嗎` → expected `ROLE-Q07/ROLE-Q08`, got `ROLE-Q07`
  - ✓ step 3: `我想好好調整自己，你覺得我該從哪裡開始` → expected `ROLE-Q08/ROLE-Q07`, got `ROLE-Q08`
  - ✓ step 4: `幫我規劃 90 天的成長計劃` → expected `ROLE-Q08`, got `ROLE-Q08`

## J2 Idea-to-MVP
- session: `jw-02` — match 100%, violations 0
  - ✓ step 1: `研究一下 SaaS 競品的定價策略` → expected `ROLE-Q02`, got `ROLE-Q02`
  - ✓ step 2: `基於研究結果幫我設計 MVP 架構` → expected `ROLE-Q01/ROLE-S01`, got `ROLE-Q01`
  - ✓ step 3: `寫一段 landing page 的文案` → expected `ROLE-Q03`, got `ROLE-Q03`
  - ✓ step 4: `審查一下這個 MVP 有什麼安全風險` → expected `ROLE-Q06`, got `ROLE-Q06`
  - ✓ step 5: `分析使用者註冊轉化率怎麼追蹤` → expected `ROLE-Q04`, got `ROLE-Q04`

## J3 Bug-Triage-Fix
- session: `jw-03` — match 100%, violations 0
  - ✓ step 1: `用戶回報登入後 500 錯誤，幫我審查可能原因` → expected `ROLE-Q06/ROLE-S02/ROLE-T01/ROLE-T03/ROLE-Q01`, got `ROLE-T01`
  - ✓ step 2: `確認是 DB schema 不一致，怎麼修` → expected `ROLE-S01`, got `ROLE-S01`
  - ✓ step 3: `修完後幫我寫使用者公告` → expected `ROLE-Q03`, got `ROLE-Q03`

## J4 Compliance-Audit
- session: `jw-04` — match 100%, violations 0
  - ✓ step 1: `我們的部署是否符合 GDPR 合規` → expected `ROLE-S02/ROLE-Q06`, got `ROLE-S02`
  - ✓ step 2: `如果不合規，平台應該如何決策下一步` → expected `ROLE-T01`, got `ROLE-T01`
  - ✓ step 3: `把整改流程寫成正式文件` → expected `ROLE-Q03`, got `ROLE-Q03`

## J5 Multi-Tenant-Expansion
- session: `jw-05` — match 100%, violations 0
  - ✓ step 1: `我們要從單租戶轉成多租戶 SaaS，跨項目怎麼復用` → expected `ROLE-T03`, got `ROLE-T03`
  - ✓ step 2: `DB schema 要怎麼設計才能支援租戶隔離` → expected `ROLE-S01`, got `ROLE-S01`
  - ✓ step 3: `部署時要注意哪些配置一致性問題` → expected `ROLE-S02`, got `ROLE-S02`

## J6 Disaster-Recovery
- session: `jw-06` — match 100%, violations 0
  - ✓ step 1: `DB 壞了，急救方案是什麼` → expected `ROLE-T01/ROLE-S02/ROLE-S01/ROLE-Q01/ROLE-Q03`, got `ROLE-Q01`
  - ✓ step 2: `恢復後如何驗證資料完整性` → expected `ROLE-S01/ROLE-S02`, got `ROLE-S01`
  - ✓ step 3: `規劃長期防止此類事件的演進路線` → expected `ROLE-T04`, got `ROLE-T04`

## J7 Skill-Creator
- session: `jw-07` — match 100%, violations 0
  - ✓ step 1: `我想創建一個新的技能：自動生成週報` → expected `ROLE-Q01/ROLE-Q03/ROLE-T03`, got `ROLE-Q03`
  - ✓ step 2: `幫我寫成 markdown 技能定義` → expected `ROLE-Q03`, got `ROLE-Q03`
  - ✓ step 3: `這個技能能否跨項目復用` → expected `ROLE-T03`, got `ROLE-T03`

## J8 Cross-Project-Migration
- session: `jw-08` — match 100%, violations 0
  - ✓ step 1: `把 5 個項目的技能整合到主庫，跨項目復用` → expected `ROLE-T03`, got `ROLE-T03`
  - ✓ step 2: `評估技術演進和升級風險` → expected `ROLE-T04/ROLE-Q06`, got `ROLE-T04`
  - ✓ step 3: `寫遷移執行手冊` → expected `ROLE-Q03`, got `ROLE-Q03`

## J9 Team-Burnout-Rescue
- session: `jw-09` — match 100%, violations 0
  - ✓ step 1: `團隊運營出狀況，成員都很累` → expected `ROLE-T02/ROLE-T03/ROLE-Q07`, got `ROLE-T02`
  - ✓ step 2: `我覺得壓力大，能聊聊嗎` → expected `ROLE-Q07`, got `ROLE-Q07`
  - ✓ step 3: `接下來如何重新規劃成員的成長路徑` → expected `ROLE-Q08/ROLE-T03`, got `ROLE-T03`

## J10 Research-Pub-Launch
- session: `jw-10` — match 75%, violations 0
  - ✓ step 1: `研究最新 LLM 安全評估方法` → expected `ROLE-Q02`, got `ROLE-Q02`
  - ✓ step 2: `把研究寫成技術文章` → expected `ROLE-Q03`, got `ROLE-Q03`
  - ✗ step 3: `審查文章有沒有事實錯誤` → expected `ROLE-Q06/ROLE-T03/ROLE-Q01`, got `ROLE-T01`
  - ✓ step 4: `分析文章發出去的閱讀數據怎麼追蹤` → expected `ROLE-Q04`, got `ROLE-Q04`

## J11 Cold-Start-Growth
- session: `jw-11` — match 100%, violations 0
  - ✓ step 1: `規劃 GTM 策略，獲取首批 100 用戶` → expected `ROLE-T02/ROLE-Q08/ROLE-Q05`, got `ROLE-Q05`
  - ✓ step 2: `分析現有的轉化漏斗數據` → expected `ROLE-Q04`, got `ROLE-Q04`
  - ✓ step 3: `設計 onboarding 的 UX 流程` → expected `ROLE-Q05`, got `ROLE-Q05`

## J12 Arch-Migration
- session: `jw-12` — match 100%, violations 0
  - ✓ step 1: `規劃單體到微服務的演進路線` → expected `ROLE-T04`, got `ROLE-T04`
  - ✓ step 2: `具體架構設計怎麼拆` → expected `ROLE-S01/ROLE-Q01`, got `ROLE-Q01`
  - ✓ step 3: `部署策略和回滾方案` → expected `ROLE-S02`, got `ROLE-S02`

## J13 Customer-Escalation
- session: `jw-13` — match 67%, violations 0
  - ✓ step 1: `客戶很生氣，我先安撫一下` → expected `ROLE-Q07/ROLE-T02`, got `ROLE-T02`
  - ✗ step 2: `審查到底是哪個環節出問題` → expected `ROLE-Q06/ROLE-T03/ROLE-S02`, got `ROLE-T01`
  - ✓ step 3: `修復後給客戶寫一封正式致歉信` → expected `ROLE-Q03`, got `ROLE-Q03`

## J14 Team-Onboarding
- session: `jw-14` — match 100%, violations 0
  - ✓ step 1: `幫新成員規劃成長路徑` → expected `ROLE-Q08/ROLE-T03`, got `ROLE-T03`
  - ✓ step 2: `跨家族協議和標準怎麼對齊` → expected `ROLE-S03/ROLE-S01`, got `ROLE-S01`
  - ✓ step 3: `把整個 onboarding 流程設計成 UX 體驗` → expected `ROLE-Q05`, got `ROLE-Q05`

## J15 Quarterly-OKR
- session: `jw-15` — match 100%, violations 0
  - ✓ step 1: `規劃下季度的平台戰略` → expected `ROLE-T01/ROLE-T03/ROLE-T04`, got `ROLE-T03`
  - ✓ step 2: `整理需求池並排優先級` → expected `ROLE-T02`, got `ROLE-T02`
  - ✓ step 3: `分析上季度的關鍵指標` → expected `ROLE-Q04`, got `ROLE-Q04`

## J16 Security-Incident
- session: `jw-16` — match 100%, violations 0
  - ✓ step 1: `緊急！發現平台被攻擊了，要立刻處理` → expected `ROLE-T01`, got `ROLE-T01`
  - ✓ step 2: `審計這段代碼有沒有漏洞` → expected `ROLE-Q06`, got `ROLE-Q06`
  - ✓ step 3: `Schema 是否被篡改` → expected `ROLE-S01`, got `ROLE-S01`
  - ✓ step 4: `寫事件後分析報告` → expected `ROLE-Q03`, got `ROLE-Q03`

## J17 Companion-Progression
- session: `jw-17` — match 100%, violations 0
  - ✓ step 1: `我最近情緒比較低落` → expected `ROLE-Q07`, got `ROLE-Q07`
  - ✓ step 2: `好點了。其實我想學新東西，幫我規劃學習` → expected `ROLE-Q08`, got `ROLE-Q08`
  - ✓ step 3: `從程序員成長為架構師需要什麼` → expected `ROLE-Q08`, got `ROLE-Q08`

## J18 I18n-Addition
- session: `jw-18` — match 100%, violations 0
  - ✓ step 1: `為產品加入日語支持，UX 該怎麼設計` → expected `ROLE-Q05`, got `ROLE-Q05`
  - ✓ step 2: `寫翻譯指南和術語表` → expected `ROLE-Q03`, got `ROLE-Q03`
  - ✓ step 3: `實作的架構考量是什麼` → expected `ROLE-Q01/ROLE-S01`, got `ROLE-S01`
  - ✓ step 4: `審查翻譯品質和文化合規性` → expected `ROLE-Q06/ROLE-S02`, got `ROLE-S02`

## J19 Plugin-Ecosystem
- session: `jw-19` — match 75%, violations 0
  - ✓ step 1: `規劃 plugin 體系，跨項目能復用嗎` → expected `ROLE-T03`, got `ROLE-T03`
  - ✓ step 2: `Plugin API 的架構標準` → expected `ROLE-S01`, got `ROLE-S01`
  - ✓ step 3: `寫 plugin 開發者文檔` → expected `ROLE-Q03`, got `ROLE-Q03`
  - ✗ step 4: `運營推廣怎麼做` → expected `ROLE-T02/ROLE-Q03`, got `ROLE-Q01`

## J20 Emergence-Consensus
- session: `jw-20` — match 100%, violations 0
  - ✓ step 1: `這個項目要做還是不做？我需要不同視角` → expected `ROLE-T01/ROLE-T03/ROLE-Q01/ROLE-Q06/ROLE-Q03`, got `ROLE-Q01`
  - ✓ step 2: `從風險角度怎麼看` → expected `ROLE-Q06`, got `ROLE-Q06`
  - ✓ step 3: `從用戶體驗角度怎麼看` → expected `ROLE-Q05`, got `ROLE-Q05`
  - ✓ step 4: `從成長角度怎麼看` → expected `ROLE-Q08`, got `ROLE-Q08`

