# Sub-Skill 01 · SOP 解析器

**所属 Skill**：Skill 04 · Planner  
**版本**：v1.0.0  
**职责**：接收并解析来自 Skill 02 的 SOP 工程包，提取可规划信息

---

## 输入来源

| 来源 | 格式 | 触发场景 |
|------|------|---------|
| Skill 02（SOP 工程师） | 交接包 YAML + SOP 文档 | 标准流程 |
| Skill 00（Navigator） | 交接包 YAML | 直接路由 |
| 用户直接输入 | 自然语言描述 | 无 SOP 文档时 |

---

## 解析提取清单

从 SOP 文档中提取以下信息：

### 1. 项目基本信息

```yaml
project_info:
  name: "{项目名称}"
  domain: "{领域}"
  objective: "{项目目标一句话}"
  success_criteria: 
    - "{验收标准1}"
    - "{验收标准2}"
  total_estimated_hours: {X}
  deadline: "{截止日期或null}"
```

### 2. 技术栈清单

```yaml
tech_stack:
  language: "{主要编程语言}"
  framework: "{主框架}"
  dependencies:
    - name: "{包名}"
      version: "{版本} [需用户核实]"
      purpose: "{用途}"
  external_services:
    - name: "{服务名}"
      type: "API/Database/Storage"
      requires_key: true/false
  infrastructure:
    - "{部署环境}"
```

### 3. 开发阶段划分

```yaml
phases:
  - phase_id: "P1"
    name: "{阶段名称}"
    objective: "{阶段目标}"
    estimated_days: {X}
    deliverables:
      - "{交付物1}"
    tasks: []    # Phase 2 阶段拆解后填充
```

### 4. 约束与风险

```yaml
constraints:
  hard:
    - "{硬性约束（不可改变的）}"
  soft:
    - "{软性约束（可协商的）}"
risks:
  - id: "RISK-01"
    description: "{风险描述}"
    probability: "high/medium/low"
    mitigation: "{缓解措施}"
```

---

## 解析输出格式

完成解析后，输出以下确认摘要（等待用户确认再继续）：

```
📋 SOP 解析完成，请确认以下理解：

**项目**：{项目名称}
**目标**：{目标一句话}
**技术栈**：{主要技术}
**阶段数**：{X} 个阶段
**预计工时**：{X} 小时 [估算，请根据实际调整]

**识别到的约束**：
- {约束1}
- {约束2}

**未在 SOP 中找到的信息**（需要您补充）：
- [ ] {缺失信息1}（将影响：{哪个步骤}）
- [ ] {缺失信息2}

请确认以上理解是否正确，或指出需要修正的地方：
A) ✅ 确认正确，开始生成手册
B) 🔧 需要修正：___
C) ➕ 补充缺失信息：___
```

---

## 无 SOP 文档时的降级处理

当用户直接描述项目（无 SOP 文档时）：

```
检测到未提供 SOP 文档。

为生成准确的操作手册，请提供以下信息：

必须项：
1. 项目目标（做什么）
2. 主要技术栈（用什么技术）
3. 主要功能模块（分几个部分）

可选项：
4. 时间预算
5. 团队规模
6. 特殊约束

或者，建议先使用 Skill 02（SOP 工程师）生成 SOP，
再使用本 Skill 生成操作手册，效果更好。
```

---

## 解析质量检查

| 检查项 | 合格标准 | 失败处理 |
|--------|---------|---------|
| 项目目标清晰度 | 一句话可描述 | 追问用户 |
| 技术栈完整性 | 主要依赖全部列出 | 标注 [待补充] |
| 阶段划分合理性 | 3-6个阶段，无跳跃 | 重新拆解 |
| 验收标准可测量 | 有具体数字/状态 | 标注 [需量化] |
