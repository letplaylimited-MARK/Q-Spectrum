# Sub-Skill 02 · 五维度验收引擎

**所属 Skill**：Skill 05 · Validator  
**版本**：v1.0.0  
**职责**：按五个维度执行系统性验收测试，生成客观评分

---

## 维度一：功能完整性（权重 40%）

**核心问题**：「交付物是否实现了承诺的全部功能？」

### 评分标准

| 得分 | 标准 |
|------|------|
| 90-100% | 所有核心功能实现，边界条件处理完善，错误处理完整 |
| 75-89% | 所有核心功能实现，少数边界条件未处理 |
| 60-74% | 大多数核心功能实现，有明显功能缺失 |
| 40-59% | 核心功能部分实现，有 P1 级功能缺失 |
| 0-39% | 核心功能严重缺失，P0 级问题存在 |

### 检查清单

```yaml
functional_checks:
  - id: "F-01"
    check: "所有 test_targets 中的功能是否全部存在"
    method: "逐项对照交接包中的 test_targets"
    defect_level: "P0（核心功能）/ P1（次要功能）"
    
  - id: "F-02"
    check: "边界条件是否有处理"
    method: "查找空输入/超长输入/异常值的处理逻辑"
    defect_level: "P1（无处理）/ P2（处理不完整）"
    
  - id: "F-03"
    check: "错误处理是否完善"
    method: "查找 try-catch/error handling 相关内容"
    defect_level: "P1（完全无错误处理）/ P2（部分缺失）"
    
  - id: "F-04"
    check: "API 接口设计是否符合 SOP 规范"
    method: "对照 SOP 中的接口定义"
    defect_level: "P1（不符合）/ P2（部分偏差）"
```

---

## 维度二：文档完整性（权重 25%）

**核心问题**：「文档是否足以让人理解和使用这个项目？」

### 检查清单

```yaml
documentation_checks:
  - id: "D-01"
    check: "所有步骤有明确描述（无模糊表达）"
    method: "扫描'完善'/'优化'/'改进'等模糊动词"
    defect_level: "P2"
    
  - id: "D-02"
    check: "版本号标注 [需用户核实]"
    method: "搜索版本号格式（x.y.z），验证是否有[需用户核实]"
    defect_level: "P1（缺少标注，可能误导用户）"
    
  - id: "D-03"
    check: "API 端点/价格/限制标注 [需用户核实]"
    method: "搜索 API/endpoint/pricing 相关内容"
    defect_level: "P1（缺少标注）"
    
  - id: "D-04"
    check: "估时标注 [估算，请根据实际调整]"
    method: "搜索时间估算相关内容"
    defect_level: "P2（缺少标注）"
    
  - id: "D-05"
    check: "README 包含：概述/安装/使用/贡献"
    method: "检查 README.md 结构"
    defect_level: "P2（缺少主要章节）/ P3（格式问题）"
```

---

## 维度三：可执行性（权重 20%）

**核心问题**：「用户能否按文档独立完成项目？」

### 检查清单

```yaml
executability_checks:
  - id: "E-01"
    check: "环境配置章节完整（系统要求/安装命令/验证方式）"
    method: "查找环境配置相关章节"
    defect_level: "P1（缺失环境配置）/ P2（不完整）"
    
  - id: "E-02"
    check: "每个步骤有可执行命令或明确操作"
    method: "扫描无命令的'软性'步骤"
    defect_level: "P1（多于3个软性步骤）/ P2（1-2个）"
    
  - id: "E-03"
    check: "每个步骤有预期结果描述"
    method: "检查 expected_output 字段"
    defect_level: "P2（超过20%步骤缺少）"
    
  - id: "E-04"
    check: "每个步骤有验证方式"
    method: "检查 verify 字段"
    defect_level: "P1（超过30%步骤缺少验证）"
    
  - id: "E-05"
    check: "断点恢复指南完整"
    method: "查找状态保存和恢复章节"
    defect_level: "P2（缺少断点恢复）"
    
  - id: "E-06"
    check: "FAQ 覆盖主要步骤类型"
    method: "对照步骤类型检查 FAQ 覆盖"
    defect_level: "P3（FAQ 不足3条）"
```

---

## 维度四：接口规范性（权重 10%）

**核心问题**：「交接包是否符合体系接口契约 v1.0？」

### 检查清单

```yaml
interface_checks:
  - id: "I-01"
    check: "schema_version 为 '1.0'"
    defect_level: "P0（版本不兼容）"
    
  - id: "I-02"
    check: "必填字段完整（from_skill/to_skill/payload/user_action）"
    defect_level: "P1（缺少必填字段）"
    
  - id: "I-03"
    check: "user_action 包含明确的用户操作指引"
    defect_level: "P2（user_action 为空或模糊）"
    
  - id: "I-04"
    check: "to_skill 指向正确的下游 Skill"
    defect_level: "P1（路由错误）"
```

---

## 维度五：安全性（权重 5%）

**核心问题**：「是否存在安全风险？」

### 检查清单

```yaml
security_checks:
  - id: "S-01"
    check: "无硬编码 API Key / 密码 / 密钥"
    method: "搜索 api_key= / password= / secret= 等硬编码模式"
    defect_level: "P0（存在硬编码凭证）"
    
  - id: "S-02"
    check: "敏感配置使用 .env 或环境变量"
    method: "查找环境变量使用说明"
    defect_level: "P1（未使用环境变量管理凭证）"
    
  - id: "S-03"
    check: ".env 在 .gitignore 中"
    method: "检查 .gitignore 内容"
    defect_level: "P1（.env 可能被提交）"
```

---

## 综合得分计算

```python
def calculate_total_score(scores):
    weights = {
        'functional':      0.40,
        'documentation':   0.25,
        'executability':   0.20,
        'interface':       0.10,
        'security':        0.05
    }
    total = sum(scores[dim] * weight for dim, weight in weights.items())
    return round(total, 2)

# 示例
scores = {
    'functional': 90,
    'documentation': 85,
    'executability': 80,
    'interface': 95,
    'security': 100
}
# total = 90×0.4 + 85×0.25 + 80×0.2 + 95×0.1 + 100×0.05 = 87.75%
```
