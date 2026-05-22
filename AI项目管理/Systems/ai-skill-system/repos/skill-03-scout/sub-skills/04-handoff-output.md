# Sub-Skill 04 · 交接包输出 Handoff Package Output
## 阶段 04/4

---

## 职责声明

| 项目 | 内容 |
|---|---|
| 输入 | 阶段03 用户确认的推荐方案 + 完整需求清单 |
| 输出 | 标准化交接包 YAML（可直接传给 Skill 02 / Skill 04）|
| 门控条件 | 用户确认交接包内容正确后，本次侦察任务完成 |
| 禁止行为 | 不在交接包中填入 [需用户核实] 的实时数据（用 ai_inference 标注代替）|

---

## 交接包类型说明

| 目标 | 场景 | 交接包内容侧重 |
|---|---|---|
| Skill 02（SOP工程师）| 需要工程化打包 | evaluation_matrix + packaging_request + gaps_found |
| Skill 04（执行规划官）| 需要生成操作手册 | selected_solutions + tech_stack + integration_architecture |
| Skill 01（提示词工程师）| 某需求需要提示词设计 | 口头描述，不用标准交接包格式 |
| Skill 05（测试验收工程师）| 需要验收评估 | 完成 Skill 02/04 后由它们向 Skill 05 传递 |

---

## 执行逻辑

### Step 1：汇总确认内容

整理以下信息：
- 所有 REQ 的选定方案（含安装命令）
- gaps_found 列表（若有）
- 用户确认的技术栈
- packaging_request（Skill 名称 + 核心能力 + 子Skill数量）

### Step 2：生成交接包 B（传给 Skill 02）

```yaml
handoff:
  schema_version: "1.0"
  from_skill: "skill-03-scout"
  to_skill: "skill-02-sop-engineer"
  payload:
    requirement_list:
      - id: "REQ-001"
        description: "[需求描述]"
        priority: "must_have"
        category: "[类别]"
    evaluation_matrix:
      - req_id: "REQ-001"
        selected_solution:
          name: "[方案名称]"
          score: [综合得分]
          install_command: "pip install [包名]  # 执行前请验证版本"
          license: "[开源协议]"
          data_verified_by: "ai_inference（需用户核实实时数据）"
        dimension_scores:
          functionality: [1-5]
          usability: [1-5]
          performance: [1-5]
          maintainability: [1-5]
          community_activity: [1-5]
          compatibility: [1-5]
          documentation: [1-5]
    selected_solutions:
      "REQ-001": "[方案名称]"
    gaps_found: []
    packaging_request:
      skill_name: "[项目名称（小写-连字符格式）]"
      core_capabilities:
        - "[核心能力1]"
        - "[核心能力2]"
      sub_skills_count: [数量]
      tech_stack: "[技术栈，如 Python 3.10+]"
  user_action: "将此交接包复制，粘贴到 Skill 02（SOP工程师）的对话开头，进入工程化打包流程"
  created_at: "[当前日期]"
```

### Step 3：说明使用方式

向用户说明三步操作：

    使用方式：
    1. 复制上方交接包的完整内容（从 "handoff:" 到最后一行）
    2. 打开 Skill 02（SOP工程师）的新对话
    3. 粘贴内容并发送 → Skill 02 会自动识别并进入工程化打包流程

### Step 4：提供可选的体系路由建议

```
体系路由建议：
- 若需要工程化打包 → Skill 02（SOP工程师）使用以上交接包
- 若需要生成完整操作手册 → Skill 04（执行规划官），描述项目需求即可
- 若有 gaps_found 需定制开发 → 优先 Skill 02，告知 gaps_found 内容
- 若需要优化某子功能的提示词 → Skill 01（超级提示词工程师）
- 若项目完成后需要验收 → Skill 05（测试验收工程师）
```

---

## 防错护栏

| 场景 | 处理方式 |
|---|---|
| 交接包中 ai_inference 数据需要填入 | 必须标注 `data_verified_by: "ai_inference（需用户核实实时数据）"` |
| skill_name 包含空格或大写 | 自动转换为小写-连字符格式（如 customer-feedback-analyzer）|
| gaps_found 不为空 | 在交接包中保留 gaps_found 字段，Skill 02 会识别并进入对应处理流程 |
| 用户不需要传给 Skill 02 | 输出简化版（仅选型报告），不强制要求交接包格式 |
| packaging_request 信息不完整 | 追问：「请提供一个项目名称（用于 Skill 名称），以及核心能力列表」|

---

## 输出模板

```markdown
## 执行摘要 [阶段04/4]
侦察任务完成。共评估 N 个需求，推荐方案已确认，X 个 gaps_found 已记录。

## 核心产出

标准化交接包（传给 Skill 02）：

[完整 YAML 交接包]

使用方式：
1. 复制以上交接包完整内容
2. 打开 Skill 02（SOP工程师）新对话
3. 粘贴发送，Skill 02 自动识别并进入工程化流程

## 质量自检
| 检查项 | 状态 |
|---|---|
| 所有字段完整，无遗漏 | ✅ |
| data_verified_by 已标注 ai_inference | ✅ |
| gaps_found 已包含（若有）| [✅/N/A] |
| skill_name 格式合规（小写-连字符）| ✅ |

## 下一步
侦察任务完成。
体系路由建议：
- 工程化打包 → Skill 02（粘贴以上交接包）
- 操作手册 → Skill 04（描述项目需求）
- 提示词优化 → Skill 01

感谢使用开源技能侦察官！如需对同一项目的其他需求进行评估，直接描述新需求即可。
```
