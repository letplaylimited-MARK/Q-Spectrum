# Sub-Skill 04 · 交接包输出（Skill 04 → Skill 05）

**所属 Skill**：Skill 04 · Planner  
**版本**：v1.0.0  
**职责**：生成符合 s04-to-user.yaml 和 s02-to-s05.yaml 规范的交接包

---

## 交接包：Skill 04 → 用户（操作手册交付）

此包在生成操作手册后立即输出，供用户直接使用。

```yaml
# 交接包 D：Planner → 用户
# 对应接口契约：interface-contracts/s04-to-user.yaml

schema_version: "1.0"
from_skill: "skill-04-planner"
to_skill: "user"
created_at: "{ISO8601}"

manual_metadata:
  project_name: "{项目名称}"
  manual_version: "v1.0"
  based_on_sop: "{SOP版本}"
  total_phases: {N}
  total_tasks: {M}
  total_steps: {K}
  estimated_hours:
    optimistic: {X}
    normal: {Y}
    pessimistic: {Z}
    expected: {E}    # PERT计算值

environment:
  os: "{操作系统要求}"
  language_version: "{语言版本} [需用户核实]"
  key_dependencies:
    - name: "{包名}"
      version: "{版本} [需用户核实]"
  external_services:
    - "{服务名（需要API Key/账号）}"

execution_phases:
  - id: "P0"
    name: "{阶段名}"
    tasks: {N}
    steps: {M}
    estimated_hours: {X}
    checkpoint_criteria:
      - "{检查项1}"
      - "{检查项2}"

breakpoint_recovery:
  state_file: ".project_state"
  recovery_guide: "见手册 第X章"

faq_count: {N}
notes: "{任何需要提醒用户的事项}"

user_action: |
  操作手册已生成完毕。
  
  开始前，请确认：
  1. 环境已满足系统要求（见第二章）
  2. 已获取所有必要的 API Key 和账号权限
  3. 已将 [需用户核实] 的版本号替换为实际版本
  
  如需测试验收，请在完成后将此交接包传给 Skill 05。
```

---

## 交接包：Skill 04 → Skill 05（验收请求）

当项目执行完成，用户请求验收时，输出此包：

```yaml
# 交接包 D→E：Planner → Validator
# 对应接口契约：interface-contracts/s02-to-s05.yaml（扩展）

schema_version: "1.0"
from_skill: "skill-04-planner"
to_skill: "skill-05-validator"
created_at: "{ISO8601}"

package_metadata:
  project_name: "{项目名称}"
  version: "v1.0.0"
  package_type: "execution_manual"
  source_sop: "{SOP版本号}"

test_targets:
  - id: "TT-01"
    description: "所有 Phase 检查点验证"
    type: "checkpoint_verification"
    pass_criteria: "全部 {N} 个检查点通过"
    
  - id: "TT-02"
    description: "操作手册完整性验证"
    type: "manual_completeness"
    pass_criteria: "所有步骤有 ID / 工具 / 验证方式"
    
  - id: "TT-03"
    description: "幻觉防护标注完整性"
    type: "hallucination_guard"
    pass_criteria: "版本号/价格/API限制全部标注[需用户核实]"
    
  - id: "TT-04"
    description: "断点恢复可用性"
    type: "recovery_guide"
    pass_criteria: "所有 Phase 在恢复表中有条目"

quality_requirements:
  completeness: 0.95      # ≥95% 步骤完整
  clarity: 0.90           # ≥90% 步骤有明确验证方式
  safety: 1.00            # 100% 幻觉防护标注

defect_history: []        # Skill 05 发现缺陷后回填

user_action: "请将此交接包粘贴到 Skill 05 对话开头，请求验收"
```

---

## 使用说明

### 三步使用流程

1. **使用 Skill 04 生成操作手册**  
   将 SOP 工程包（来自 Skill 02）粘贴给 Skill 04，得到完整操作手册

2. **按手册执行项目**  
   遵循操作手册，完成所有 Phase/Task/Step  
   每个 Phase 完成后保存状态（`echo "PHASE_X=COMPLETE" >> .project_state`）

3. **请求验收**  
   将操作手册 + 上方交接包传给 Skill 05，获得发布决策

---

## 体系路由建议

```
Skill 04 完成后的推荐下一步：

若执行完成 → Skill 05（测试验收工程师）验收
若执行中遇到技术问题 → Skill 02（SOP工程师）修订SOP
若需要更换技术方案 → Skill 03（开源侦察官）重新评估
```
