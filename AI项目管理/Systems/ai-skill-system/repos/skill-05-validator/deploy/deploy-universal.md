# Skill 05 · Validator 跨平台部署指南

**版本**：v1.0.0

---

## 部署方式

| 平台 | 推荐文件 | 说明 |
|------|---------|------|
| Claude.ai Projects | `core/system-prompt-full.md` | Project Instructions |
| 对话激活 | `core/system-prompt-lite.md` | 粘贴到对话开头 |
| API | `core/system-prompt-full.md` | system parameter |

---

## 验证部署

发送测试消息：
```yaml
schema_version: "1.0"
from_skill: "skill-04-planner"
to_skill: "skill-05-validator"
payload:
  project_name: "测试项目"
  version: "v1.0.0"
test_targets:
  - id: "TT-01"
    description: "核心功能验收"
    pass_criteria: "功能完整"
```

期望行为：
1. 确认接收，列出验收维度
2. 执行五维度评分
3. 输出 PASS/FAIL/CONDITIONAL_PASS 决策
4. 附带飞轮改进建议

---

## 配置建议

- Temperature: 0.1（验收需要最高一致性）
- 禁止 Extended Thinking（避免主观推理影响客观评分）
