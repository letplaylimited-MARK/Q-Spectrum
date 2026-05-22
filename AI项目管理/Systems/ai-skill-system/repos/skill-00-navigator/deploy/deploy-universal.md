# Skill 00 · Navigator 跨平台部署指南

**版本**：v1.0.0  
**适用平台**：Claude.ai / Cursor / Continue / 任何支持系统提示词的 AI 工具

---

## 部署方式汇总

| 平台 | 推荐方式 | 文件 |
|------|---------|------|
| Claude.ai Projects | 系统提示词 | `core/system-prompt-full.md` |
| Claude.ai 对话 | 激活卡 | `core/activation-card.md` |
| Cursor | `.cursorrules` | `core/system-prompt-lite.md` |
| Continue (VS Code) | `config.json` systemMessage | `core/system-prompt-full.md` |
| API 直接调用 | system parameter | `core/system-prompt-full.md` |
| Token 受限平台 | 精简版 | `core/system-prompt-lite.md` |

---

## Claude.ai Projects 部署

1. 进入 Claude.ai → Projects → 新建项目「AI Skill Navigator」
2. 在 **Project Instructions** 中粘贴 `core/system-prompt-full.md` 全部内容
3. 上传参考文件（可选）：将 `sub-skills/` 三个文件上传为 Knowledge
4. 验证：输入「我想做一个AI项目」，应收到路由响应和交接包 YAML

**推荐设置**：
- Temperature: 0.3（路由任务需要一致性）
- 不需要工具调用权限（Navigator 只输出文本）

---

## 激活卡快速部署（无需配置）

1. 打开 `core/activation-card.md`
2. 复制「标准激活」文本块（```标记内的内容）
3. 粘贴到任意 AI 对话的第一条消息
4. 直接开始使用

适合：临时使用、演示、不需要持久化配置的场景。

---

## Cursor 部署

在项目根目录创建 `.cursorrules`：

```bash
# 复制精简版提示词
cat core/system-prompt-lite.md > /your-project/.cursorrules
```

或在 Cursor Settings → Rules for AI 中粘贴内容。

---

## API 调用示例

```python
import anthropic

client = anthropic.Anthropic()

# 读取系统提示词
with open("core/system-prompt-full.md", "r") as f:
    system_prompt = f.read()

message = client.messages.create(
    model="claude-opus-4-5",  # [需用户核实最新模型名称]
    max_tokens=2048,
    system=system_prompt,
    messages=[
        {"role": "user", "content": "我想做一个客户反馈分析的AI智能体"}
    ]
)

print(message.content[0].text)
```

---

## 与其他 Skill 协同工作

Navigator 是入口，与其他 Skill 的协同通过**标准化交接包**实现：

```
用户 → Navigator（路由） → 交接包 YAML
用户 → 复制交接包 → 目标 Skill（执行）
目标 Skill → 完成后输出下一个交接包
用户 → 复制交接包 → 下一个 Skill
```

**不需要 Skill 之间直接通信**，用户是数据搬运者，确保每一步都在用户掌控中。

---

## 验证部署成功

部署后，发送以下测试消息：

```
测试1（高置信度）：我想做一个分析社交媒体情绪的AI工具
期望：直接路由到 Skill 01，置信度 ≥80%，输出交接包

测试2（中置信度）：帮我找些开源库
期望：确认路由（60-79%），询问技术栈和用途

测试3（低置信度）：我需要帮助
期望：追问1（定性选择），不直接路由
```

---

## 版本要求

| 依赖 | 最低版本 | 说明 |
|------|---------|------|
| AI 模型 | Claude 3 Sonnet 或同等 | 需要良好的指令遵循能力 |
| 体系版本 | System v1.0+ | 接口契约兼容性 |
| 交接包 Schema | v1.0 | 与所有 Skill 的接口版本 |
