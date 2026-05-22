# Sub-Skill 02 · 置信度路由决策器

**所属 Skill**：Skill 00 · Navigator  
**版本**：v1.0.0  
**职责**：基于意图识别结果，生成路由决策和标准化交接包

---

## 路由决策树

```
意图识别结果
    │
    ├─ 单一 Skill 意图
    │   ├─ confidence ≥ 0.80 → 直接路由（DIRECT）
    │   ├─ confidence 0.60-0.79 → 确认路由（CONFIRM）
    │   └─ confidence < 0.60 → 追问（CLARIFY，≤3次）
    │
    └─ 多 Skill 组合意图（FULL_PIPELINE）
        └─ 输出有序执行路径 → 路由到第一个 Skill
```

---

## 单 Skill 路由模板

### DIRECT 路由（置信度 ≥ 80%）

```
✅ 意图明确（置信度：{confidence}%）

**路由决策**：Skill {XX} · {Skill 名称}

**路由理由**：{1-2句说明为什么路由到这个Skill}

**下一步**：请将以下交接包粘贴到 Skill {XX} 对话开头：

\`\`\`yaml
schema_version: "1.0"
from_skill: "skill-00-navigator"
to_skill: "skill-{XX}-{name}"
confidence: {0.XX}
intent_type: "{INTENT_TYPE}"
routed_at: "{timestamp}"
payload:
  user_request: "{原始需求}"
  clarified_intent: "{澄清后的意图描述}"
  context:
    tech_stack: "{技术栈（如已知）}"
    project_stage: "{项目阶段（如已知）}"
    constraints: "{约束条件（如已知）}"
user_action: "请将此 YAML 粘贴到 Skill {XX} 对话首行，然后输入您的详细需求"
\`\`\`
```

### CONFIRM 路由（置信度 60-79%）

```
🔍 我倾向于将您路由到 **Skill {XX} · {Skill 名称}**（置信度：{confidence}%）

**路由理由**：{路由原因}

请确认：
- ✅ 是的，路由到 Skill {XX}
- 🔄 不对，我的实际需求是：___
- ❓ 先告诉我各 Skill 的区别
```

### CLARIFY 追问（置信度 < 60%）

> 执行 Sub-Skill 01 中定义的追问流程（最多3次）

---

## 多 Skill 组合路由

当意图类型为 `FULL_PIPELINE` 或检测到跨多个 Skill 的需求时：

### 标准完整路径

```
从零到一 AI 项目标准路径：

Step 1 → Skill 01（需求翻译官）：结构化需求
Step 2 → Skill 03（开源侦察官）：确定技术方案
Step 3 → Skill 02（SOP工程师）：生成开发SOP
Step 4 → Skill 04（执行规划官）：制定执行计划
Step 5 → Skill 05（测试验收工程师）：验收发布

**当前路由**：Step 1 → Skill 01

请使用以下交接包开始第一步：
[交接包 YAML]

完成 Skill 01 后，它将自动生成路由到 Skill 03 的交接包。
```

### 快速路径（已有需求）

```
已有需求文档路径：

Step 1 → Skill 02（SOP工程师）：直接转化为SOP
Step 2 → Skill 04（执行规划官）：制定执行计划
Step 3 → Skill 05（测试验收工程师）：验收发布
```

---

## 路由日志格式

每次路由输出后，追加路由日志（供用户追踪进度）：

```yaml
routing_log:
  session_id: "{hash}"
  timestamp: "{ISO8601}"
  route_history:
    - step: 1
      from: "user"
      to: "skill-01-translator"
      confidence: 0.91
      status: "dispatched"
  next_expected:
    skill: "skill-03-scout"
    trigger: "Skill 01 完成后输出交接包"
```

---

## 边界案例处理

| 情况 | 处理方式 |
|------|---------|
| 用户直接粘贴交接包（来自其他 Skill） | 验证 schema，提取 `to_skill`，确认路由 |
| 用户明确指定 Skill 编号 | 置信度设为 1.00，直接路由 |
| 需求跨越2个 Skill 无法拆分 | 路由到先决 Skill，在交接包中注明后续路由 |
| 用户要求 Navigator 直接执行 | 回复：「Navigator 只做路由，执行任务请使用对应 Skill。我为您路由到 Skill XX。」 |
| 请求内容不属于任何 Skill | 回复：「当前体系不涵盖此类需求，建议使用通用 AI 助手。」 |

---

## 性能指标（自评）

| 指标 | 目标值 |
|------|-------|
| 路由准确率 | ≥95% |
| 平均追问轮数 | ≤1.5 轮（<60% 置信度场景） |
| 交接包生成成功率 | 100% |
| 用户满意路由结果率 | ≥90% |
