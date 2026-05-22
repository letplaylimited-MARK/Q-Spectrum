# Sub-Skill 04 · 发布决策与交接包输出

**所属 Skill**：Skill 05 · Validator  
**版本**：v1.0.0  
**职责**：基于验收结果生成发布决策，输出标准化交接包

---

## 交接包：Skill 05 → 发布决策

```yaml
# 交接包 E：Validator → 发布/修复路由
# 对应接口契约：interface-contracts/s05-to-release.yaml

schema_version: "1.0"
from_skill: "skill-05-validator"
to_skill: "{user/skill-0X-name}"    # PASS→user，FAIL→修复Skill
decision: "PASS"                    # PASS / CONDITIONAL_PASS / FAIL
created_at: "{ISO8601}"

report:
  report_id: "VAL-{YYYYMMDD}-{N}"
  project_name: "{项目名称}"
  version: "{版本号}"
  overall_score: {0-100}
  
  dimension_scores:
    functional: {0-100}
    documentation: {0-100}
    executability: {0-100}
    interface: {0-100}
    security: {0-100}
  
  defect_summary:
    P0: {N}
    P1: {N}
    P2: {N}
    P3: {N}
    total: {N}
  
  decision_reason: "{客观决策理由}"
  
  # 仅 CONDITIONAL_PASS 时
  conditions:
    fix_deadline: "{日期}"
    must_fix_defects: 
      - "{P1-001}"
    revalidation_required: true
  
  # 仅 FAIL 时
  blockers:
    - id: "{P0-001}"
      description: "{阻塞原因}"
      fix_route: "skill-0X"
    
  # 飞轮数据
  flywheel_insights:
    - pattern: "{缺陷模式}"
      suggested_improvement: "{改进建议}"
      affects: "skill-0X"

user_action: |
  {根据决策不同，给出不同的下一步指引}
```

---

## 三种决策的 user_action 模板

### PASS（通过）

```yaml
user_action: |
  🎉 验收通过！项目可以发布。
  
  建议后续步骤：
  1. 执行正式发布流程（git tag, CI/CD）
  2. 归档本次验收报告
  3. 将 P2/P3 缺陷加入下个版本的改进计划
  4. 将此交接包保存，下次迭代时提供给 Skill 05 作为历史记录
```

### CONDITIONAL_PASS（条件通过）

```yaml
user_action: |
  ⚠️ 条件通过。需要在 {修复期限} 前修复以下 P1 缺陷：
  
  必须修复：
  - {P1-001}：{描述} → 路由到 {Skill XX}
  
  修复完成后，请将修复说明 + 此交接包返回给 Skill 05 复验。
  复验通过后可正式发布。
```

### FAIL（不通过）

```yaml
user_action: |
  ❌ 验收未通过。请按以下步骤处理：
  
  阻塞问题（必须修复）：
  - {P0-001}：{描述} → 路由到 {Skill XX}
  
  修复路线：
  {修复路由表}
  
  修复完成后，重新提交给 Skill 05 验收。
```

---

## 飞轮触发条件

以下情况触发飞轮机制（向上游 Skill 提供改进建议）：

| 触发条件 | 飞轮操作 |
|---------|---------|
| P0 缺陷涉及安全 | 建议 Skill 02 增加安全检查清单 |
| P1 缺陷：幻觉防护缺失 | 建议对应 Skill 在模板中强制添加标注 |
| 同类 P1 缺陷连续出现2次 | 建议在上游规则中增加该检查项 |
| P0 缺陷：接口不兼容 | 建议所有 Skill 更新接口契约版本检查 |

---

## 版本升级规则

验收结果决定版本号策略：

| 验收结果 | 已有版本 | 修复后版本 | 规则 |
|---------|---------|-----------|------|
| PASS | v1.0.0 | - | 维持 v1.0.0 发布 |
| CONDITIONAL_PASS + P1修复 | v1.0.0 | v1.0.1 | PATCH+1（bug fix）|
| FAIL + P0修复 | v1.0.0 | v1.1.0 | MINOR+1（重要修复）|
| FAIL + 架构重构 | v1.0.0 | v2.0.0 | MAJOR+1（破坏性变更）|
