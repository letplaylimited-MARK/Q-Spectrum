# Universal Platform Deployment Guide
# 通用平台部署指南

> 本指南覆盖所有主流 AI 平台的部署方式，从最简单到最完整，按平台分类说明。

---

## 🌐 通用原则 · Universal Principles

无论哪个平台，部署遵循同一逻辑：

> **「将 `core/system-prompt-full.md` 的内容作为 System Prompt 注入，即完成部署。」**

精简模型或上下文受限时，使用 `core/system-prompt-lite.md`。

---

## 平台一：ChatGPT / GPTs

### 方式 A · Custom Instructions（个人使用）
1. 进入 ChatGPT → 右上角头像 → Settings → Personalization → Custom Instructions
2. 在「How would you like ChatGPT to respond?」栏中，粘贴 `core/system-prompt-full.md` 全文
3. 保存后，每次新对话自动激活

### 方式 B · GPTs Builder（团队/发布使用）
1. 进入 ChatGPT → Explore GPTs → Create
2. 在「Instructions」区域粘贴 `core/system-prompt-full.md` 全文
3. 在「Conversation Starters」添加触发话术（见下方触发词清单）
4. 发布后可生成分享链接供团队使用

**推荐触发词 Starters**:
- "激活超级提示词工程师 / Activate Super Prompt Engineer"
- "帮我优化这个提示词"
- "设计一个工作流"
- "梳理我的使用痛点"

---

## 平台二：Claude / Claude Projects

### 方式 A · Project Instructions（推荐）
1. 进入 Claude → Projects → New Project
2. 在「Project Instructions」中粘贴 `core/system-prompt-full.md` 全文
3. 该 Project 下所有对话均自动激活 Skill

### 方式 B · 会话首条消息
在对话开始时，将 `core/system-prompt-full.md` 作为第一条消息发送，AI 将在该会话内保持角色。

---

## 平台三：Coze（字节跳动）

1. 进入 Coze → 创建 Bot
2. 在「人设与回复逻辑」中粘贴 `core/system-prompt-full.md` 全文
3. 在「开场白」中填写激活确认语
4. 发布为个人/团队/公开 Bot

**支持功能**: 可在 Coze 的工作流中将 6 个子 Skill 映射为独立工作流节点，实现可视化编排。

---

## 平台四：Dify

1. 进入 Dify → 创建应用 → 选择「聊天助手」
2. 在「系统提示词」中粘贴 `core/system-prompt-full.md` 全文
3. 可选：将 6 个子 Skill 创建为独立的「工具」节点
4. 发布为 API 或 Web 应用

**进阶功能**: 在 Dify 的「知识库」中上传 `templates/` 目录中的所有模板文件，使 AI 可检索调用完整模板内容。

---

## 平台五：文心一言 / 千帆平台

1. 进入文心一言 → 创建应用
2. 在「系统提示词」中粘贴 `core/system-prompt-full.md` 全文（中文优化版）
3. 文心一言对中文理解优化，建议保留双语版本以获得最佳效果

---

## 平台六：通义千问 / 阿里云百炼

1. 进入阿里云百炼 → 创建应用
2. 在「系统提示词」中粘贴 `core/system-prompt-full.md` 全文
3. 可配合阿里云的「长期记忆」插件实现跨会话持久化

---

## 平台七：讯飞星火

1. 进入讯飞开放平台 → 创建应用
2. 在系统提示词配置区粘贴 `core/system-prompt-full.md` 全文
3. 星火 V4 支持长文本，推荐使用完整版提示词

---

## 平台八：任意 API 调用（开发者）

```python
# Python 示例 · Python Example
import openai  # 或其他模型 SDK / or other model SDK

with open("core/system-prompt-full.md", "r", encoding="utf-8") as f:
    system_prompt = f.read()

response = openai.chat.completions.create(
    model="gpt-4o",  # 替换为目标模型 / Replace with target model
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "帮我优化这个提示词：[你的提示词]"}
    ],
    temperature=0  # 遵循Skill设计原则 / Follow Skill design principle
)
```

```javascript
// Node.js 示例 · Node.js Example
const fs = require('fs');
const OpenAI = require('openai');

const systemPrompt = fs.readFileSync('core/system-prompt-full.md', 'utf8');
const client = new OpenAI();

const response = await client.chat.completions.create({
  model: 'gpt-4o',
  messages: [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: '帮我设计一个工作流' }
  ],
  temperature: 0
});
```

---

## 触发词完整清单 · Full Trigger Keyword List

### 中文触发词
| 能力 | 触发词 |
|---|---|
| 全功能激活 | 激活超级提示词工程师 / 开始工作 / 全流程启动 |
| 提示词优化 | 优化提示词 / 这个指令有问题 / 提示词跑偏了 / 让AI更精准 |
| 工作流设计 | 设计工作流 / 拆解步骤 / 帮我规划流程 / 制定执行方案 |
| 报告生成 | 生成报告 / 写复盘 / 输出进度报告 / 总结一下 |
| 痛点引导 | 梳理痛点 / 我遇到了问题 / 帮我分析 / AI用起来不顺 |
| 数据库整理 | 整理数据库 / 分类文件 / 归档记录 / 建立知识库 |
| 迭代追踪 | 记录迭代 / 更新版本 / 这次优化了什么 / 建立变更日志 |

### English Trigger Keywords
| Capability | Trigger Keywords |
|---|---|
| Full Activation | activate super prompt engineer / start full workflow |
| Prompt Optimization | optimize prompt / fix my prompt / prompt not working |
| Workflow Design | design workflow / break this down / plan this task |
| Report Generation | generate report / write retrospective / summarize |
| Pain Point Analysis | analyze issues / what's wrong / pain points |
| Database Organization | organize files / structure database / archive records |
| Iteration Tracking | track iteration / log this change / version update |
