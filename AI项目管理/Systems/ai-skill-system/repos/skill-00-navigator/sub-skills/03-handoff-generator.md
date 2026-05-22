# Sub-Skill 03 · 交接包生成器

**所属 Skill**：Skill 00 · Navigator  
**版本**：v1.0.0  
**职责**：生成符合体系接口契约的标准化交接包 YAML

---

## 交接包 A 完整 Schema

```yaml
# 交接包 A：Navigator → 任意 Skill
# schema_version: "1.0"
# 文件：interface-contracts/s00-to-any.yaml

schema_version: "1.0"
from_skill: "skill-00-navigator"
to_skill: "skill-{XX}-{name}"          # 目标 Skill 标识符
confidence: 0.XX                        # 路由置信度 0.00-1.00
intent_type: "{INTENT_TYPE}"            # 来自意图注册表
routed_at: "{ISO8601 timestamp}"

payload:
  # ——— 核心需求信息 ———
  user_request: |
    {用户原始输入，逐字保留}
  clarified_intent: |
    {经过澄清/追问后的结构化意图描述}
  
  # ——— 上下文信息（已知时填写，未知时 null）———
  context:
    project_name: null          # 项目名称
    domain: null                # 领域（如：客户服务/电商/医疗）
    tech_stack: null            # 技术栈（如：Python/FastAPI/PostgreSQL）
    project_stage: null         # 阶段（ideation/requirements/development/testing/production）
    constraints: null           # 约束（时间/预算/团队规模）
    prior_skills_used: []       # 已使用的 Skill 列表（多 Skill 链路时）
  
  # ——— 路由元数据 ———
  routing:
    route_type: "DIRECT"        # DIRECT / CONFIRM / CLARIFY_RESOLVED
    clarify_rounds: 0           # 追问轮数（0-3）
    route_reason: |
      {1-2句说明路由理由}
    alternative_skills: []      # 备选 Skill（置信度第二高的）

# ——— 用户操作指引 ———
user_action: |
  请将此 YAML 完整复制，粘贴到 {Skill名称} 对话的第一条消息中，
  然后追加您的具体需求描述。
```

---

## 各 Skill 专用交接包模板

### → Skill 01（需求翻译官）

```yaml
schema_version: "1.0"
from_skill: "skill-00-navigator"
to_skill: "skill-01-translator"
confidence: 0.91
intent_type: "NEW_PROJECT_IDEA"
payload:
  user_request: "{原始输入}"
  clarified_intent: "用户有新的AI项目构想，需要将模糊想法结构化为精确需求文档"
  context:
    domain: "{领域或null}"
    tech_stack: "{技术栈或null}"
    project_stage: "ideation"
user_action: "粘贴到 Skill 01 对话开头，然后描述您的项目想法"
```

### → Skill 02（SOP 工程师）

```yaml
schema_version: "1.0"
from_skill: "skill-00-navigator"
to_skill: "skill-02-sop-engineer"
confidence: 0.88
intent_type: "REQUIREMENTS_EXIST"
payload:
  user_request: "{原始输入}"
  clarified_intent: "用户已有结构化需求，需要转化为可执行开发SOP"
  context:
    project_stage: "requirements"
    prior_skills_used: ["skill-01-translator"]   # 如果来自Skill01则填写
user_action: "粘贴到 Skill 02 对话开头，并附上您的需求文档"
```

### → Skill 03（开源侦察官）

```yaml
schema_version: "1.0"
from_skill: "skill-00-navigator"
to_skill: "skill-03-scout"
confidence: 0.93
intent_type: "OPEN_SOURCE_SCOUT"
payload:
  user_request: "{原始输入}"
  clarified_intent: "用户需要为项目寻找合适的开源工具/库/框架"
  context:
    tech_stack: "{技术栈}"
    domain: "{领域}"
user_action: "粘贴到 Skill 03 对话开头，描述您的技术需求"
```

### → Skill 04（执行规划官）

```yaml
schema_version: "1.0"
from_skill: "skill-00-navigator"
to_skill: "skill-04-planner"
confidence: 0.85
intent_type: "PROJECT_PLANNING"
payload:
  user_request: "{原始输入}"
  clarified_intent: "用户需要将项目方案转化为分阶段执行计划"
  context:
    project_stage: "development"
    prior_skills_used: ["skill-02-sop-engineer"]
user_action: "粘贴到 Skill 04 对话开头，附上SOP文档"
```

### → Skill 05（测试验收工程师）

```yaml
schema_version: "1.0"
from_skill: "skill-00-navigator"
to_skill: "skill-05-validator"
confidence: 0.90
intent_type: "QUALITY_CHECK"
payload:
  user_request: "{原始输入}"
  clarified_intent: "用户需要对完成的工程包进行测试验收"
  context:
    project_stage: "testing"
    prior_skills_used: ["skill-02-sop-engineer", "skill-04-planner"]
user_action: "粘贴到 Skill 05 对话开头，附上工程包和SOP"
```

---

## 交接包验证规则

生成交接包后，按以下规则自检：

| 检查项 | 规则 | 处理 |
|--------|------|------|
| schema_version | 必须为 "1.0" | 硬编码，不可修改 |
| from_skill | 必须为 "skill-00-navigator" | 硬编码 |
| to_skill | 必须在6个注册 Skill 中 | 若不匹配则报错 |
| confidence | 必须为 0.00-1.00 浮点数 | 超出范围则截断 |
| user_request | 必须保留用户原始输入 | 不可改写或摘要 |
| user_action | 必须包含目标 Skill 名称 | 不可为空 |

---

## 多 Skill 链路交接包

当用户走完整 Pipeline 时，生成路径规划交接包：

```yaml
schema_version: "1.0"
from_skill: "skill-00-navigator"
to_skill: "skill-01-translator"          # 第一站
confidence: 0.95
intent_type: "FULL_PIPELINE"
payload:
  user_request: "{原始输入}"
  clarified_intent: "完整AI项目，从需求到发布全流程"
  pipeline:
    total_steps: 5
    current_step: 1
    remaining_path:
      - step: 1
        skill: "skill-01-translator"
        status: "current"
      - step: 2
        skill: "skill-03-scout"
        status: "pending"
      - step: 3
        skill: "skill-02-sop-engineer"
        status: "pending"
      - step: 4
        skill: "skill-04-planner"
        status: "pending"
      - step: 5
        skill: "skill-05-validator"
        status: "pending"
user_action: "粘贴到 Skill 01 开头。每个 Skill 完成后会自动生成下一站交接包。"
```
