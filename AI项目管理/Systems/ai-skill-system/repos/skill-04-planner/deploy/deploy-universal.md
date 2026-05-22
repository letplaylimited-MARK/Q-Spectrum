# Skill 04 · Planner 跨平台部署指南

**版本**：v1.0.0

---

## 部署方式

| 平台 | 推荐文件 | 说明 |
|------|---------|------|
| Claude.ai Projects | `core/system-prompt-full.md` | 上传为 Project Instructions |
| 对话激活 | `core/system-prompt-lite.md` | 粘贴到对话开头 |
| Cursor / Continue | `core/system-prompt-lite.md` | 设为 AI Rules |
| API | `core/system-prompt-full.md` | system parameter |

---

## 前置条件

使用 Skill 04 前，建议已完成：
- **Skill 02 输出**：SOP 工程包（最佳效果）
- 或：Skill 01 的需求文档（次优）
- 或：直接描述项目（基础效果）

---

## 验证部署

发送测试消息：
```
我有以下项目需要生成操作手册：
- 目标：用Python构建情绪分析API
- 技术栈：FastAPI + HuggingFace Transformers
- 阶段：数据处理/模型集成/API开发/测试
```

期望行为：
1. 输出解析摘要（等待确认）
2. 确认后输出分阶段操作手册
3. 每个步骤有 P-T-S 编号和验证方式
4. 版本号标注 [需用户核实]

---

## 温度设置

推荐 Temperature: 0.2（操作手册需要高确定性，减少随机性）
