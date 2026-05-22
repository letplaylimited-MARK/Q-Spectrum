# 文档元数据标准（Document Metadata Schema）

## 目的

建立Markdown文档与Platform数据库实体之间的标准化关联机制，解决BUG-0001（文档到实体的链接缺失）问题。

## 元数据格式

所有纳入知识库管理的Markdown文档，必须在文件头部包含YAML格式的元数据：

```yaml
---
# 必填字段
entity_type: topic          # 实体类型
entity_code: T-001          # 实体编号
title: 如何做提示词优化      # 文档标题

# 关联字段（至少填写一个）
linked_demands:             # 关联的需求
  - DEM-0002
linked_pains:               # 关联的痛点
  - PAIN-0001
linked_projects:            # 关联的项目
  - PRJ-0001
linked_solutions:           # 关联的方案
  - SOL-0001
linked_skills:              # 关联的技能
  - S-001
linked_resources:           # 关联的资源
  - R-001

# 可选字段
created_at: 2026-04-01      # 创建日期
updated_at: 2026-04-01      # 更新日期
author: AI项目运营官         # 作者
status: active              # 状态：active/draft/archived
version: 1.0                # 版本号
tags:                       # 标签列表
  - 提示词
  - 优化
  - 入门
---
```

## 实体类型定义

| entity_type | 说明 | 编号前缀 | 对应目录 |
|-------------|------|----------|----------|
| skill | 技能文档 | S- | Skills/ |
| map | 导航文档 | M- | Maps/ |
| qcm | QCM研究文档 | QCM- | QCM/ |
| system | 系统文档 | SYS- | Systems/ |
| platform | 平台文档 | PLT- | Platform/ |
| role | 角色定义 | ROLE- | roles/ |
| demand | 需求记录 | DEM- | (database) |
| pain | 痛点记录 | PAIN- | (database) |
| solution | 方案记录 | SOL- | (database) |
| validation | 验证记录 | VAL- | (database) |
| defect | 缺陷记录 | BUG- | (database) |

## 关联规则

### 单向关联

文档A引用文档B，但B不一定引用A：

```yaml
# A.md
linked_resources:
  - R-001  # A引用了R-001
```

### 双向关联

相关文档互相引用：

```yaml
# A.md
linked_resources:
  - R-001

# R-001.md
linked_topics:
  - T-001  # R-001也引用了A（T-001）
```

### 层级关联

按层级向上/向下关联：

```
Topic (T-001)
  ├─ linked_skills: [S-001]      # 技能层
  │     └─ linked_resources: [R-001]  # 资源层
  └─ linked_demands: [DEM-0002]  # 需求层
        └─ linked_pains: [PAIN-0001]  # 痛点层
```

## 编号规则

| 类型 | 格式 | 示例 | 说明 |
|------|------|------|------|
| Topic | T-XXX | T-001 | 三位数字 |
| Skill | S-XXX | S-001 | 三位数字 |
| Resource | R-XXX | R-001 | 三位数字 |
| Project | P-XXX | P-001 | 三位数字 |
| Demand | DEM-XXXX | DEM-0001 | 四位数字 |
| Pain | PAIN-XXXX | PAIN-0001 | 四位数字 |
| Solution | SOL-XXX | SOL-001 | 三位数字 |
| Validation | VAL-XXX | VAL-001 | 三位数字 |
| Defect | BUG-XXX | BUG-001 | 三位数字 |

## 验证规则

1. **编号唯一性**：每个entity_code在整个知识库中唯一
2. **类型一致性**：entity_type与文档所在目录匹配
3. **关联有效性**：linked_*中的编号必须存在于对应目录
4. **必填完整性**：entity_type、entity_code、title必须存在

## 标签

#标准 #元数据 #文档管理 #BUG-0001
