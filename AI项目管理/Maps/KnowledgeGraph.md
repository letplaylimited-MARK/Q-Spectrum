---
entity_type: map
entity_code: M-006
title: KnowledgeGraph
created_at: 2026-04-05
updated_at: 2026-04-06
status: active
tags:
  - 导航
  - 图谱
---

# 🕸️ 知识图谱 · Knowledge Graph

> 自动生成，用于可视化 Topic / Skill / Resource / Template 之间的关联关系。

## 图例

- 🔵 Topic
- 🟢 Skill
- 🟠 Resource
- 🟣 Template

```mermaid
graph TD
    classDef Topics fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef Skills fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;
    classDef Resources fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef Templates fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;

    什么是AI协同开发["什么是AI协同开发"]:::Topics
    如何建立项目知识库["如何建立项目知识库"]:::Topics
    如何做一次周度知识库回顾["如何做一次周度知识库回顾"]:::Topics
    从学习到教学的转化路径["从学习到教学的转化路径"]:::Topics

    Agent_运维助手["Agent 运维助手"]:::Skills
    全库盘点技能["全库盘点技能"]:::Skills
    周度知识库回顾["周度知识库回顾"]:::Skills
    提示词练习["提示词练习"]:::Skills
    新手需求分流["新手需求分流"]:::Skills
    案例创作助手["案例创作助手"]:::Skills
    记忆管理助手["记忆管理助手"]:::Skills

    AI_产品与工具精选["AI 产品与工具精选"]:::Resources
    AI_学习资源精选["AI 学习资源精选"]:::Resources
    开发工具与_SaaS_产品精选["开发工具与 SaaS 产品精选"]:::Resources
    项目管理工具精选["项目管理工具精选"]:::Resources

    需求分析画布["需求分析画布"]:::Templates
    MVP构建画布["MVP构建画布"]:::Templates
    竞品分析画布["竞品分析画布"]:::Templates
    战略规划画布["战略规划画布"]:::Templates

    什么是AI协同开发 --> 如何建立项目知识库
    如何建立项目知识库 --> 如何做一次周度知识库回顾
    Agent_运维助手 --> 全库盘点技能
    全库盘点技能 --> 周度知识库回顾
    案例创作助手 --> 需求分析画布
    AI_产品与工具精选 --> 什么是AI协同开发
    AI_学习资源精选 --> 从学习到教学的转化路径
```

## 说明

当前图谱仍是轻量版，后续可继续扩大：

1. 增加更多 Topic/Skill 节点
2. 从文档中的 Markdown 链接自动提取边
3. 生成按主题分区的子图谱

## 配套导航

如果你想从不同入口理解这张图谱，可以配合以下文档使用：

- [README](../README.md) ：从项目总说明进入，再回到结构图谱
- [START-HERE](../START-HERE.md) ：从新手入口进入，再回到结构图谱
- [场景-Skill 映射表](../Maps/场景-Skill%20映射表.md) ：从使用场景反推可调用技能
- [案例索引](../Maps/案例索引.md) ：从真实案例切入，再回到图谱理解结构
- [AI-Skill-System 导航](../Maps/AI-Skill-System%20导航.md) ：查看外部 Skill 体系与本库的连接点

## 当前统计快照

> 以下数字用于帮助用户快速理解当前图谱所代表的内容规模。

- `Skills/`：16 个文件
- `Maps/`：4 个文件
- `QCM/`：核心理论与研究成果
- `Systems/`：AI Skill 体系与家族定义
- `Platform/`：数据库、标准与注册中心

这些数字代表的是当前已纳入图谱理解范围的核心资产规模，不包含脚本、归档、数据库迁移记录等运维层文件。

## 标签

#导航 #知识图谱 #可视化
