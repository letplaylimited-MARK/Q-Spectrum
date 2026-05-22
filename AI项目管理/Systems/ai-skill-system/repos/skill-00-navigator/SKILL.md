---
name: ai-skill-navigator
description: |
  Skill 00 · Navigator，AI Skill 体系总路由入口。分析用户意图置信度（≥80%直接路由/60-79%确认/＜60%追问≤3次），精准路由到正确Skill：01需求翻译官/02SOP工程师/03开源侦察官/04执行规划官/05测试验收工程师。输出标准化交接包YAML，实现Skill间无缝衔接。
  适用场景：当用户启动新AI项目需要确定从哪里开始时；当用户不确定应该使用哪个Skill时；当用户需要走完整端到端Pipeline时触发。禁止直接执行任何任务，只做路由。
  Trigger phrases: 我想做AI项目 / 不知道从哪里开始 / 帮我路由 / 从哪个Skill开始 / 导航 / 选择Skill / start AI project / route me / which skill / navigate / I want to build an AI
allowed-tools:
  - Read
---
