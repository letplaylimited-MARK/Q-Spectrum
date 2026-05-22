# 跨平台部署指南 · Deploy Universal
## 开源技能侦察官 v1.0.0

---

## 方案 A：CodeBuddy 全局安装（推荐）

```bash
npx skills add letplaylimited-MARK/skill-03-scout --global --yes
```

安装后输入触发词即可激活：`寻找技能` / `开源技能推荐` / `帮我找开源方案`

---

## 方案 B：其他 AI 平台（系统提示词粘贴）

### 完整版（推荐 GPT-4 / Claude / Gemini Pro 等强模型）

将 `core/system-prompt-full.md` 全文复制，粘贴到对应平台：

| 平台 | 粘贴位置 |
|---|---|
| ChatGPT | 设置 → 自定义指令 → 「ChatGPT应该如何回应？」|
| Claude | Projects → Project Instructions |
| 通义千问 | 角色设定区域 |
| 文心一言 | 我的助手 → 助手设置 → 性格与能力 |
| 讯飞星火 | 系统级提示词 |
| Gemini | Gems → Instructions |

### 精简版（免费版 / 轻量模型）

将 `core/system-prompt-lite.md` 全文复制，粘贴方式同上。

### 激活卡片版（最快 · 临时使用）

将 `core/activation-card.md` 全文复制，粘贴到任意 AI 对话第一条消息发送。

---

## 方案 C：手动文件配置（最大灵活性）

```bash
# 克隆仓库
git clone https://github.com/letplaylimited-MARK/skill-03-scout

# 查看三档提示词
cat skill-03-scout/core/system-prompt-full.md
cat skill-03-scout/core/system-prompt-lite.md
cat skill-03-scout/core/activation-card.md
```

---

## 激活验证

安装完成后，输入以下触发词验证激活：

| 触发词 | 预期响应 |
|---|---|
| `寻找技能` | 输出「✅ 开源技能侦察官已就绪」+ 激活菜单 |
| `帮我找开源方案` | 同上 |
| `find open source skills` | 同上（英文激活）|

---

## Raw GitHub 链接

| 文件 | 链接 |
|---|---|
| 完整版提示词 | https://raw.githubusercontent.com/letplaylimited-MARK/skill-03-scout/main/core/system-prompt-full.md |
| 精简版提示词 | https://raw.githubusercontent.com/letplaylimited-MARK/skill-03-scout/main/core/system-prompt-lite.md |
| 激活卡片 | https://raw.githubusercontent.com/letplaylimited-MARK/skill-03-scout/main/core/activation-card.md |
| SKILL.md | https://raw.githubusercontent.com/letplaylimited-MARK/skill-03-scout/main/SKILL.md |
