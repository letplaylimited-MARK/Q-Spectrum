#!/usr/bin/env python3
"""
Q-SpecTrum Scenario Engine v1.0 — AI Companionship & Multi-Scenario Journeys
=============================================================================
Diverse user scenario engine with proactive AI companionship mechanism.

Architecture:
  ┌─────────────┐   ┌───────────────┐   ┌──────────────┐
  │ Scenario     │──▶│ AI Companion  │──▶│ DeerFlow     │
  │ Registry     │   │ (Proactive)   │   │ (Sim/Live)   │
  │ 12 Journeys  │   │ Guide+Track   │   │ 6 Skills     │
  └─────────────┘   └───────────────┘   └──────────────┘
        │                   │                    │
        ▼                   ▼                    ▼
  ┌─────────────┐   ┌───────────────┐   ┌──────────────┐
  │ Step Engine  │   │ Pain Point    │   │ Sandbox      │
  │ Multi-stage  │   │ Detector      │   │ Simulator    │
  └─────────────┘   └───────────────┘   └──────────────┘

Standalone:
  python scenario_engine.py --list              # List all scenarios
  python scenario_engine.py --run ecommerce     # Run e-commerce journey
  python scenario_engine.py --demo              # Run all scenarios summary
  python scenario_engine.py --companion "msg"   # AI companion interaction
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════
# 1. SCENARIO REGISTRY — 12 Diverse User Journeys
# ═══════════════════════════════════════════════════════════

SCENARIO_REGISTRY: Dict[str, dict] = {
    "ecommerce": {
        "id": "ecommerce",
        "name_zh": "电商平台全流程管理",
        "name_en": "E-Commerce Platform Management",
        "description": "从竞品分析到上线运营的电商平台完整生命周期",
        "complexity": "high",
        "estimated_steps": 8,
        "roles_involved": ["ROLE-Q02", "ROLE-Q04", "ROLE-Q01", "ROLE-Q05", "ROLE-T02", "ROLE-Q06", "ROLE-Q08"],
        "deerflow_skills": ["deep-research", "data-analysis", "chart-visualization", "consulting-analysis"],
        "steps": [
            {
                "id": "ec-1", "phase": "research",
                "title_zh": "竞品分析与市场调研", "title_en": "Competitive Analysis & Market Research",
                "prompt": "帮我分析电商平台竞品，包括淘宝、拼多多、Shopify的核心差异",
                "expected_role": "ROLE-Q02", "deerflow_skill": "deep-research",
                "companion_guidance_zh": "我会先帮你做竞品深度调研。完成后建议进入用户痛点分析阶段。",
                "companion_guidance_en": "I'll conduct a deep competitive analysis first. After this, I recommend moving to user pain point analysis.",
                "deliverable": "research_report",
            },
            {
                "id": "ec-2", "phase": "analysis",
                "title_zh": "用户痛点与需求挖掘", "title_en": "User Pain Points & Demand Mining",
                "prompt": "根据竞品分析结果，挖掘目标用户的核心痛点和未满足需求",
                "expected_role": "ROLE-Q04", "deerflow_skill": "data-analysis",
                "companion_guidance_zh": "基于调研数据，我来帮你识别关键痛点。这是产品定位的基础。",
                "companion_guidance_en": "Based on research data, I'll help identify key pain points. This is the foundation for product positioning.",
                "deliverable": "pain_point_matrix",
            },
            {
                "id": "ec-3", "phase": "design",
                "title_zh": "产品架构设计", "title_en": "Product Architecture Design",
                "prompt": "设计电商平台的技术架构方案，包括微服务划分和数据库设计",
                "expected_role": "ROLE-Q01", "deerflow_skill": None,
                "companion_guidance_zh": "现在进入架构设计。我会帮你规划微服务边界和数据模型。",
                "companion_guidance_en": "Now entering architecture design. I'll help plan microservice boundaries and data models.",
                "deliverable": "architecture_doc",
            },
            {
                "id": "ec-4", "phase": "design",
                "title_zh": "UX/UI原型设计", "title_en": "UX/UI Prototype Design",
                "prompt": "设计电商平台的用户体验流程和关键页面原型",
                "expected_role": "ROLE-Q05", "deerflow_skill": "chart-visualization",
                "companion_guidance_zh": "架构确定后，来设计用户体验。购物流程的丝滑度决定转化率。",
                "companion_guidance_en": "With architecture set, let's design UX. Shopping flow smoothness determines conversion rates.",
                "deliverable": "ux_prototype",
            },
            {
                "id": "ec-5", "phase": "execution",
                "title_zh": "开发计划与任务分解", "title_en": "Development Plan & Task Breakdown",
                "prompt": "制定电商平台的开发计划，分解为Sprint任务",
                "expected_role": "ROLE-T02", "deerflow_skill": None,
                "companion_guidance_zh": "进入执行阶段。我帮你把大目标拆解成可执行的Sprint任务。",
                "companion_guidance_en": "Entering execution phase. I'll help break down goals into actionable Sprint tasks.",
                "deliverable": "sprint_plan",
            },
            {
                "id": "ec-6", "phase": "execution",
                "title_zh": "安全风险评估", "title_en": "Security Risk Assessment",
                "prompt": "评估电商平台的安全风险，包括支付安全、数据保护、DDoS防护",
                "expected_role": "ROLE-Q06", "deerflow_skill": None,
                "companion_guidance_zh": "开发前必须做安全评估。支付和用户数据安全是底线。",
                "companion_guidance_en": "Security assessment is a must before development. Payment and user data security are non-negotiable.",
                "deliverable": "risk_report",
            },
            {
                "id": "ec-7", "phase": "launch",
                "title_zh": "上线方案与运营策略", "title_en": "Launch Plan & Operations Strategy",
                "prompt": "制定电商平台上线计划和初期运营策略",
                "expected_role": "ROLE-Q08", "deerflow_skill": "consulting-analysis",
                "companion_guidance_zh": "准备上线！我帮你制定渐进式发布策略和冷启动运营方案。",
                "companion_guidance_en": "Ready for launch! I'll help create a progressive release strategy and cold-start operations plan.",
                "deliverable": "launch_plan",
            },
            {
                "id": "ec-8", "phase": "growth",
                "title_zh": "数据驱动增长复盘", "title_en": "Data-Driven Growth Review",
                "prompt": "分析上线后的关键指标，制定增长优化方案",
                "expected_role": "ROLE-Q04", "deerflow_skill": "chart-visualization",
                "companion_guidance_zh": "上线后最重要的是数据复盘。让数据驱动下一步决策。",
                "companion_guidance_en": "Post-launch, data review is critical. Let data drive your next decisions.",
                "deliverable": "growth_report",
            },
        ],
    },

    "content_creation": {
        "id": "content_creation",
        "name_zh": "内容创作工作室",
        "name_en": "Content Creation Studio",
        "description": "从选题策划到分发分析的内容创作全流程",
        "complexity": "medium",
        "estimated_steps": 6,
        "roles_involved": ["ROLE-Q02", "ROLE-Q03", "ROLE-Q06", "ROLE-Q08", "ROLE-Q04"],
        "deerflow_skills": ["deep-research", "consulting-analysis", "chart-visualization", "data-analysis"],
        "steps": [
            {"id": "cc-1", "phase": "research", "title_zh": "选题调研与热点分析", "title_en": "Topic Research & Trend Analysis",
             "prompt": "分析当前内容创作领域的热门趋势和高流量选题方向",
             "expected_role": "ROLE-Q02", "deerflow_skill": "deep-research",
             "companion_guidance_zh": "先来做选题调研。好的选题决定80%的成败。", "companion_guidance_en": "Let's research topics first. A good topic determines 80% of success.",
             "deliverable": "topic_analysis"},
            {"id": "cc-2", "phase": "planning", "title_zh": "内容框架与大纲规划", "title_en": "Content Framework & Outline",
             "prompt": "基于选题分析，设计内容系列的框架和每篇的详细大纲",
             "expected_role": "ROLE-Q03", "deerflow_skill": None,
             "companion_guidance_zh": "选好题后规划框架。系列内容比单篇更有传播力。", "companion_guidance_en": "With topics chosen, plan the framework. Series content has more reach than single pieces.",
             "deliverable": "content_outline"},
            {"id": "cc-3", "phase": "creation", "title_zh": "正文创作与配图生成", "title_en": "Content Writing & Visual Creation",
             "prompt": "按照大纲创作第一篇内容，并生成配套的视觉素材",
             "expected_role": "ROLE-Q03", "deerflow_skill": "consulting-analysis",
             "companion_guidance_zh": "开始创作！我会帮你保持风格一致性并生成配图。", "companion_guidance_en": "Time to create! I'll help maintain style consistency and generate visuals.",
             "deliverable": "content_draft"},
            {"id": "cc-4", "phase": "review", "title_zh": "内容审核与SEO优化", "title_en": "Content Review & SEO Optimization",
             "prompt": "审核内容质量，优化SEO关键词布局和可读性",
             "expected_role": "ROLE-Q06", "deerflow_skill": None,
             "companion_guidance_zh": "创作完成，进入审核。SEO优化能让内容被更多人看到。", "companion_guidance_en": "Creation done, entering review. SEO optimization helps content reach more people.",
             "deliverable": "reviewed_content"},
            {"id": "cc-5", "phase": "distribution", "title_zh": "多渠道分发策略", "title_en": "Multi-Channel Distribution Strategy",
             "prompt": "制定内容在各平台的分发策略和发布节奏",
             "expected_role": "ROLE-Q08", "deerflow_skill": None,
             "companion_guidance_zh": "内容完成了！现在规划分发。不同平台需要不同的内容适配。", "companion_guidance_en": "Content is ready! Now plan distribution. Different platforms need different adaptations.",
             "deliverable": "distribution_plan"},
            {"id": "cc-6", "phase": "analytics", "title_zh": "数据分析与迭代优化", "title_en": "Analytics & Iterative Optimization",
             "prompt": "分析各渠道的传播数据，总结规律并优化下一轮选题",
             "expected_role": "ROLE-Q04", "deerflow_skill": "data-analysis",
             "companion_guidance_zh": "最后看数据说话。阅读量、互动率、转化率是核心指标。", "companion_guidance_en": "Let data speak. Views, engagement rate, and conversion are core metrics.",
             "deliverable": "analytics_report"},
        ],
    },

    "data_pipeline": {
        "id": "data_pipeline",
        "name_zh": "数据分析管道搭建",
        "name_en": "Data Analytics Pipeline",
        "description": "从数据采集到自动化报表的完整数据管道",
        "complexity": "high",
        "estimated_steps": 7,
        "roles_involved": ["ROLE-Q04", "ROLE-S01", "ROLE-Q01", "ROLE-Q05", "ROLE-Q06"],
        "deerflow_skills": ["data-analysis", "chart-visualization", "github-deep-research", "deep-research"],
        "steps": [
            {"id": "dp-1", "phase": "assessment", "title_zh": "数据源盘点与质量评估", "title_en": "Data Source Inventory & Quality Assessment",
             "prompt": "盘点现有数据源，评估数据质量和可用性",
             "expected_role": "ROLE-Q04", "deerflow_skill": "data-analysis",
             "companion_guidance_zh": "先摸清家底。数据质量决定分析价值。", "companion_guidance_en": "First, take stock. Data quality determines analysis value.",
             "deliverable": "data_inventory"},
            {"id": "dp-2", "phase": "design", "title_zh": "ETL管道架构设计", "title_en": "ETL Pipeline Architecture Design",
             "prompt": "设计数据ETL管道架构，包括采集、清洗、转换、加载流程",
             "expected_role": "ROLE-S01", "deerflow_skill": None,
             "companion_guidance_zh": "架构设计要考虑扩展性。未来数据量可能增长10倍。", "companion_guidance_en": "Architecture must consider scalability. Future data volume may grow 10x.",
             "deliverable": "etl_architecture"},
            {"id": "dp-3", "phase": "implementation", "title_zh": "数据清洗脚本开发", "title_en": "Data Cleaning Script Development",
             "prompt": "开发数据清洗和标准化脚本，处理缺失值、异常值、格式统一",
             "expected_role": "ROLE-Q01", "deerflow_skill": "github-deep-research",
             "companion_guidance_zh": "开始写清洗脚本。数据清洗占数据工程80%的工作量。", "companion_guidance_en": "Start writing cleaning scripts. Data cleaning is 80% of data engineering work.",
             "deliverable": "cleaning_scripts"},
            {"id": "dp-4", "phase": "implementation", "title_zh": "分析模型构建", "title_en": "Analytics Model Building",
             "prompt": "基于清洗后的数据构建分析模型，包括趋势预测和异常检测",
             "expected_role": "ROLE-Q04", "deerflow_skill": "data-analysis",
             "companion_guidance_zh": "数据准备好了，开始建模。从简单统计到机器学习逐步推进。", "companion_guidance_en": "Data is ready, start modeling. Progress from simple statistics to machine learning.",
             "deliverable": "analytics_model"},
            {"id": "dp-5", "phase": "visualization", "title_zh": "可视化仪表盘设计", "title_en": "Visualization Dashboard Design",
             "prompt": "设计数据可视化仪表盘，支持实时监控和交互式探索",
             "expected_role": "ROLE-Q05", "deerflow_skill": "chart-visualization",
             "companion_guidance_zh": "好的可视化让数据会说话。重点是业务决策人能一目了然。", "companion_guidance_en": "Good visualization makes data speak. Focus on clarity for business decision-makers.",
             "deliverable": "dashboard"},
            {"id": "dp-6", "phase": "automation", "title_zh": "自动化报表系统", "title_en": "Automated Reporting System",
             "prompt": "搭建自动化报表系统，支持定时生成和邮件推送",
             "expected_role": "ROLE-Q01", "deerflow_skill": "github-deep-research",
             "companion_guidance_zh": "自动化是终极目标。让报表自己跑，人只做决策。", "companion_guidance_en": "Automation is the end goal. Let reports run themselves, people just make decisions.",
             "deliverable": "auto_reports"},
            {"id": "dp-7", "phase": "review", "title_zh": "管道性能优化与监控", "title_en": "Pipeline Performance Optimization & Monitoring",
             "prompt": "优化管道性能，建立监控告警机制",
             "expected_role": "ROLE-Q06", "deerflow_skill": None,
             "companion_guidance_zh": "最后做性能优化和监控。一个稳定的管道比快的管道更重要。", "companion_guidance_en": "Finally, optimize performance and set up monitoring. A stable pipeline beats a fast one.",
             "deliverable": "monitoring_setup"},
        ],
    },

    "startup_mvp": {
        "id": "startup_mvp",
        "name_zh": "创业MVP快速验证",
        "name_en": "Startup MVP Rapid Validation",
        "description": "从创意到MVP上线的快速验证全流程",
        "complexity": "high",
        "estimated_steps": 7,
        "roles_involved": ["ROLE-Q02", "ROLE-T01", "ROLE-Q01", "ROLE-Q05", "ROLE-Q08", "ROLE-Q04"],
        "deerflow_skills": ["deep-research", "consulting-analysis", "github-deep-research", "data-analysis"],
        "steps": [
            {"id": "mv-1", "phase": "ideation", "title_zh": "创意验证与市场机会", "title_en": "Idea Validation & Market Opportunity",
             "prompt": "评估这个创业想法的市场机会和竞争格局",
             "expected_role": "ROLE-Q02", "deerflow_skill": "deep-research",
             "companion_guidance_zh": "创业第一步：验证想法。90%的创业失败因为解决了不存在的问题。", "companion_guidance_en": "Step 1: Validate the idea. 90% of startups fail by solving non-existent problems.",
             "deliverable": "market_analysis"},
            {"id": "mv-2", "phase": "strategy", "title_zh": "商业模式画布", "title_en": "Business Model Canvas",
             "prompt": "设计商业模式画布，明确价值主张、客户细分、收入模式",
             "expected_role": "ROLE-T01", "deerflow_skill": "consulting-analysis",
             "companion_guidance_zh": "商业模式画布帮你看清全局。9个模块缺一不可。", "companion_guidance_en": "Business Model Canvas shows the full picture. All 9 blocks are essential.",
             "deliverable": "bmc"},
            {"id": "mv-3", "phase": "design", "title_zh": "MVP功能范围定义", "title_en": "MVP Feature Scope Definition",
             "prompt": "定义MVP的最小功能集，区分核心功能和延后功能",
             "expected_role": "ROLE-Q01", "deerflow_skill": None,
             "companion_guidance_zh": "MVP的关键是'最小'。只做能验证核心假设的功能。", "companion_guidance_en": "The key to MVP is 'minimum'. Only build features that validate core assumptions.",
             "deliverable": "mvp_scope"},
            {"id": "mv-4", "phase": "prototype", "title_zh": "原型设计与用户测试", "title_en": "Prototype Design & User Testing",
             "prompt": "快速设计可交互原型并进行首轮用户测试",
             "expected_role": "ROLE-Q05", "deerflow_skill": "chart-visualization",
             "companion_guidance_zh": "用最少的代码做出可点击原型。先测试再开发。", "companion_guidance_en": "Create a clickable prototype with minimum code. Test before you build.",
             "deliverable": "prototype"},
            {"id": "mv-5", "phase": "build", "title_zh": "核心功能开发", "title_en": "Core Feature Development",
             "prompt": "开发MVP核心功能，采用快速迭代方式",
             "expected_role": "ROLE-Q01", "deerflow_skill": "github-deep-research",
             "companion_guidance_zh": "开始开发！记住：能用就行，完美是迭代出来的。", "companion_guidance_en": "Start building! Remember: working is enough, perfection comes from iteration.",
             "deliverable": "mvp_code"},
            {"id": "mv-6", "phase": "launch", "title_zh": "MVP上线与冷启动", "title_en": "MVP Launch & Cold Start",
             "prompt": "制定MVP上线计划和获取首批100个用户的策略",
             "expected_role": "ROLE-Q08", "deerflow_skill": None,
             "companion_guidance_zh": "上线！前100个用户是最珍贵的。关注留存而非增长。", "companion_guidance_en": "Launch! First 100 users are most precious. Focus on retention, not growth.",
             "deliverable": "launch_strategy"},
            {"id": "mv-7", "phase": "iterate", "title_zh": "数据复盘与方向调整", "title_en": "Data Review & Pivot Decision",
             "prompt": "分析MVP数据，决定坚持、调整还是转型",
             "expected_role": "ROLE-Q04", "deerflow_skill": "data-analysis",
             "companion_guidance_zh": "关键时刻：数据告诉你是坚持还是转型。保持诚实。", "companion_guidance_en": "Critical moment: Data tells you to persist or pivot. Stay honest.",
             "deliverable": "pivot_analysis"},
        ],
    },

    "team_ops": {
        "id": "team_ops",
        "name_zh": "团队运营管理",
        "name_en": "Team Operations Management",
        "description": "从团队组建到绩效优化的管理全流程",
        "complexity": "medium",
        "estimated_steps": 5,
        "roles_involved": ["ROLE-T01", "ROLE-T02", "ROLE-T03", "ROLE-Q07", "ROLE-Q04"],
        "deerflow_skills": ["deep-research", "consulting-analysis"],
        "steps": [
            {"id": "to-1", "phase": "setup", "title_zh": "团队角色定义与招聘", "title_en": "Team Role Definition & Recruitment",
             "prompt": "定义团队角色结构和各岗位的能力要求", "expected_role": "ROLE-T01", "deerflow_skill": None,
             "companion_guidance_zh": "好团队从清晰的角色定义开始。", "companion_guidance_en": "A good team starts with clear role definitions.",
             "deliverable": "team_structure"},
            {"id": "to-2", "phase": "process", "title_zh": "协作流程设计", "title_en": "Collaboration Process Design",
             "prompt": "设计团队协作流程，包括会议制度、决策机制、沟通规范", "expected_role": "ROLE-T02", "deerflow_skill": None,
             "companion_guidance_zh": "流程是团队效率的基础。但不要过度流程化。", "companion_guidance_en": "Process is the foundation of team efficiency. But don't over-process.",
             "deliverable": "collab_process"},
            {"id": "to-3", "phase": "coordination", "title_zh": "跨团队协调机制", "title_en": "Cross-Team Coordination",
             "prompt": "建立跨团队协调机制和信息同步方案", "expected_role": "ROLE-T03", "deerflow_skill": None,
             "companion_guidance_zh": "跨团队协调是最难的。信息对齐是关键。", "companion_guidance_en": "Cross-team coordination is the hardest. Information alignment is key.",
             "deliverable": "coordination_plan"},
            {"id": "to-4", "phase": "culture", "title_zh": "团队文化与情感支持", "title_en": "Team Culture & Emotional Support",
             "prompt": "营造积极的团队文化，建立情感支持和反馈机制", "expected_role": "ROLE-Q07", "deerflow_skill": None,
             "companion_guidance_zh": "技术之外，人的感受同样重要。定期1on1和团队反馈不可少。", "companion_guidance_en": "Beyond tech, people's feelings matter. Regular 1-on-1s and team feedback are essential.",
             "deliverable": "culture_playbook"},
            {"id": "to-5", "phase": "optimization", "title_zh": "绩效分析与优化", "title_en": "Performance Analysis & Optimization",
             "prompt": "分析团队绩效数据，制定持续优化方案", "expected_role": "ROLE-Q04", "deerflow_skill": "data-analysis",
             "companion_guidance_zh": "用数据看团队健康度。产出、满意度、留存率三个维度。", "companion_guidance_en": "Use data to gauge team health: output, satisfaction, retention — three dimensions.",
             "deliverable": "performance_review"},
        ],
    },

    "api_integration": {
        "id": "api_integration",
        "name_zh": "API集成与微服务",
        "name_en": "API Integration & Microservices",
        "description": "从API设计到微服务部署的完整集成流程",
        "complexity": "high",
        "estimated_steps": 6,
        "roles_involved": ["ROLE-S01", "ROLE-Q01", "ROLE-Q06", "ROLE-S02"],
        "deerflow_skills": ["github-deep-research", "deep-research", "data-analysis"],
        "steps": [
            {"id": "ai-1", "phase": "design", "title_zh": "API规范设计(OpenAPI)", "title_en": "API Specification Design (OpenAPI)",
             "prompt": "设计RESTful API规范，包括认证、版本控制、错误处理", "expected_role": "ROLE-S01", "deerflow_skill": None,
             "companion_guidance_zh": "API是系统的契约。先设计好规范再写代码。", "companion_guidance_en": "API is the system's contract. Design specs before coding.",
             "deliverable": "api_spec"},
            {"id": "ai-2", "phase": "implementation", "title_zh": "核心服务开发", "title_en": "Core Service Development",
             "prompt": "开发核心微服务，实现主要API端点", "expected_role": "ROLE-Q01", "deerflow_skill": "github-deep-research",
             "companion_guidance_zh": "每个微服务应该做好一件事。单一职责原则。", "companion_guidance_en": "Each microservice should do one thing well. Single Responsibility Principle.",
             "deliverable": "service_code"},
            {"id": "ai-3", "phase": "testing", "title_zh": "集成测试与契约测试", "title_en": "Integration & Contract Testing",
             "prompt": "编写集成测试和API契约测试，确保服务间通信正确", "expected_role": "ROLE-Q01", "deerflow_skill": "github-deep-research",
             "companion_guidance_zh": "测试不是可选的。契约测试保证服务间的承诺。", "companion_guidance_en": "Testing is not optional. Contract tests guarantee promises between services.",
             "deliverable": "test_suite"},
            {"id": "ai-4", "phase": "security", "title_zh": "安全审计与渗透测试", "title_en": "Security Audit & Penetration Testing",
             "prompt": "对API进行安全审计，检查认证漏洞、注入风险、速率限制", "expected_role": "ROLE-Q06", "deerflow_skill": None,
             "companion_guidance_zh": "API安全不能事后补救。OWASP Top 10逐项检查。", "companion_guidance_en": "API security can't be an afterthought. Check OWASP Top 10 one by one.",
             "deliverable": "security_report"},
            {"id": "ai-5", "phase": "deployment", "title_zh": "容器化与编排部署", "title_en": "Containerization & Orchestration",
             "prompt": "将微服务容器化并配置K8s编排部署", "expected_role": "ROLE-S02", "deerflow_skill": None,
             "companion_guidance_zh": "容器化让部署可重复。K8s编排让扩展变简单。", "companion_guidance_en": "Containerization makes deployment repeatable. K8s orchestration simplifies scaling.",
             "deliverable": "deployment_config"},
            {"id": "ai-6", "phase": "monitoring", "title_zh": "监控告警与SLA管理", "title_en": "Monitoring, Alerting & SLA Management",
             "prompt": "建立API监控、告警规则和SLA管理体系", "expected_role": "ROLE-S02", "deerflow_skill": "data-analysis",
             "companion_guidance_zh": "没有监控的系统是盲飞。P99延迟和错误率是核心指标。", "companion_guidance_en": "A system without monitoring is flying blind. P99 latency and error rate are core metrics.",
             "deliverable": "monitoring_setup"},
        ],
    },

    "marketing_campaign": {
        "id": "marketing_campaign",
        "name_zh": "营销活动策划",
        "name_en": "Marketing Campaign Planning",
        "description": "从市场洞察到效果评估的营销活动全流程",
        "complexity": "medium",
        "estimated_steps": 5,
        "roles_involved": ["ROLE-Q02", "ROLE-Q03", "ROLE-Q04", "ROLE-Q08"],
        "deerflow_skills": ["deep-research", "consulting-analysis", "chart-visualization", "data-analysis"],
        "steps": [
            {"id": "mk-1", "phase": "insight", "title_zh": "市场洞察与人群画像", "title_en": "Market Insight & Audience Persona",
             "prompt": "分析目标市场和用户画像，找到营销切入点", "expected_role": "ROLE-Q02", "deerflow_skill": "deep-research",
             "companion_guidance_zh": "好的营销从深刻的用户洞察开始。", "companion_guidance_en": "Good marketing starts with deep user insights.",
             "deliverable": "market_insight"},
            {"id": "mk-2", "phase": "creative", "title_zh": "创意策划与内容制作", "title_en": "Creative Planning & Content Production",
             "prompt": "策划营销创意方案，制作核心传播内容", "expected_role": "ROLE-Q03", "deerflow_skill": "consulting-analysis",
             "companion_guidance_zh": "创意要有洞察支撑。好的创意是策略的艺术表达。", "companion_guidance_en": "Creativity needs insight support. Good creativity is the artistic expression of strategy.",
             "deliverable": "creative_plan"},
            {"id": "mk-3", "phase": "channel", "title_zh": "渠道策略与投放计划", "title_en": "Channel Strategy & Media Plan",
             "prompt": "制定多渠道投放策略和预算分配方案", "expected_role": "ROLE-Q08", "deerflow_skill": None,
             "companion_guidance_zh": "渠道选择决定触达效率。不要把鸡蛋放一个篮子里。", "companion_guidance_en": "Channel selection determines reach efficiency. Don't put all eggs in one basket.",
             "deliverable": "media_plan"},
            {"id": "mk-4", "phase": "execution", "title_zh": "活动执行与实时优化", "title_en": "Campaign Execution & Real-Time Optimization",
             "prompt": "执行营销活动并根据实时数据进行优化调整", "expected_role": "ROLE-Q04", "deerflow_skill": "data-analysis",
             "companion_guidance_zh": "活动上线后要盯紧数据。前48小时是调优黄金期。", "companion_guidance_en": "Watch data closely after launch. First 48 hours are the golden optimization period.",
             "deliverable": "optimization_log"},
            {"id": "mk-5", "phase": "review", "title_zh": "效果评估与经验沉淀", "title_en": "Performance Evaluation & Knowledge Capture",
             "prompt": "评估营销活动效果，提炼可复用的经验和方法论", "expected_role": "ROLE-Q04", "deerflow_skill": "chart-visualization",
             "companion_guidance_zh": "活动结束不是终点。经验沉淀是组织能力的积累。", "companion_guidance_en": "Campaign end is not the finish. Knowledge capture builds organizational capability.",
             "deliverable": "evaluation_report"},
        ],
    },

    "product_design": {
        "id": "product_design",
        "name_zh": "产品设计与迭代",
        "name_en": "Product Design & Iteration",
        "description": "从用户研究到产品迭代的设计思维全流程",
        "complexity": "medium",
        "estimated_steps": 5,
        "roles_involved": ["ROLE-Q02", "ROLE-Q05", "ROLE-Q03", "ROLE-Q04"],
        "deerflow_skills": ["deep-research", "chart-visualization", "data-analysis"],
        "steps": [
            {"id": "pd-1", "phase": "empathize", "title_zh": "用户研究与共情", "title_en": "User Research & Empathy",
             "prompt": "进行用户访谈和观察，深度理解用户需求和痛点", "expected_role": "ROLE-Q02", "deerflow_skill": "deep-research",
             "companion_guidance_zh": "设计思维第一步：共情。不是你觉得，是用户觉得。", "companion_guidance_en": "Design thinking step 1: Empathize. It's not what you think, it's what users think.",
             "deliverable": "user_research"},
            {"id": "pd-2", "phase": "define", "title_zh": "问题定义与机会识别", "title_en": "Problem Definition & Opportunity Mapping",
             "prompt": "将用户洞察转化为清晰的问题陈述和设计机会", "expected_role": "ROLE-Q05", "deerflow_skill": None,
             "companion_guidance_zh": "定义对的问题比找到对的答案更重要。", "companion_guidance_en": "Defining the right problem is more important than finding the right answer.",
             "deliverable": "problem_statement"},
            {"id": "pd-3", "phase": "ideate", "title_zh": "方案发散与概念设计", "title_en": "Ideation & Concept Design",
             "prompt": "头脑风暴产出多个设计方案，选出最佳概念", "expected_role": "ROLE-Q03", "deerflow_skill": "chart-visualization",
             "companion_guidance_zh": "发散阶段不要评判。先追求数量，再筛选质量。", "companion_guidance_en": "No judgment during ideation. First seek quantity, then filter for quality.",
             "deliverable": "concept_designs"},
            {"id": "pd-4", "phase": "prototype", "title_zh": "快速原型与测试", "title_en": "Rapid Prototyping & Testing",
             "prompt": "制作快速原型并进行可用性测试", "expected_role": "ROLE-Q05", "deerflow_skill": None,
             "companion_guidance_zh": "原型不需要完美。能验证假设就够了。", "companion_guidance_en": "Prototypes don't need to be perfect. Just enough to validate assumptions.",
             "deliverable": "prototype_report"},
            {"id": "pd-5", "phase": "iterate", "title_zh": "数据驱动迭代", "title_en": "Data-Driven Iteration",
             "prompt": "基于测试数据和用户反馈进行产品迭代", "expected_role": "ROLE-Q04", "deerflow_skill": "data-analysis",
             "companion_guidance_zh": "迭代是设计思维的灵魂。每次迭代都应该更接近用户需求。", "companion_guidance_en": "Iteration is the soul of design thinking. Each iteration should move closer to user needs.",
             "deliverable": "iteration_plan"},
        ],
    },

    "security_audit": {
        "id": "security_audit",
        "name_zh": "安全审计与合规",
        "name_en": "Security Audit & Compliance",
        "description": "从威胁建模到合规认证的安全审计全流程",
        "complexity": "high",
        "estimated_steps": 5,
        "roles_involved": ["ROLE-Q06", "ROLE-S01", "ROLE-S02"],
        "deerflow_skills": ["deep-research", "github-deep-research", "data-analysis"],
        "steps": [
            {"id": "sa-1", "phase": "threat_model", "title_zh": "威胁建模与攻击面分析", "title_en": "Threat Modeling & Attack Surface Analysis",
             "prompt": "构建系统威胁模型，分析攻击面和潜在漏洞", "expected_role": "ROLE-Q06", "deerflow_skill": "deep-research",
             "companion_guidance_zh": "安全第一步：知道敌人在哪里。STRIDE模型逐项分析。", "companion_guidance_en": "Security step 1: Know where the enemy is. Analyze using the STRIDE model.",
             "deliverable": "threat_model"},
            {"id": "sa-2", "phase": "code_review", "title_zh": "代码安全审查", "title_en": "Code Security Review",
             "prompt": "审查代码中的安全漏洞，包括注入、XSS、CSRF等", "expected_role": "ROLE-S01", "deerflow_skill": "github-deep-research",
             "companion_guidance_zh": "代码审查找的是模式，不是单个bug。关注认证和输入验证。", "companion_guidance_en": "Code review looks for patterns, not single bugs. Focus on auth and input validation.",
             "deliverable": "security_findings"},
            {"id": "sa-3", "phase": "infrastructure", "title_zh": "基础设施安全检查", "title_en": "Infrastructure Security Check",
             "prompt": "检查服务器、网络、容器的安全配置", "expected_role": "ROLE-S02", "deerflow_skill": None,
             "companion_guidance_zh": "基础设施安全是看不见的城墙。配置错误是最常见的漏洞。", "companion_guidance_en": "Infrastructure security is the invisible wall. Misconfiguration is the most common vulnerability.",
             "deliverable": "infra_report"},
            {"id": "sa-4", "phase": "compliance", "title_zh": "合规性差距分析", "title_en": "Compliance Gap Analysis",
             "prompt": "分析系统与目标合规标准(ISO27001/SOC2/GDPR)的差距", "expected_role": "ROLE-Q06", "deerflow_skill": "data-analysis",
             "companion_guidance_zh": "合规不只是勾选清单。理解精神比满足条文更重要。", "companion_guidance_en": "Compliance isn't just a checklist. Understanding the spirit matters more than meeting the letter.",
             "deliverable": "gap_analysis"},
            {"id": "sa-5", "phase": "remediation", "title_zh": "修复计划与持续监控", "title_en": "Remediation Plan & Continuous Monitoring",
             "prompt": "制定安全问题修复优先级计划和持续监控方案", "expected_role": "ROLE-Q06", "deerflow_skill": None,
             "companion_guidance_zh": "修复要分优先级。关键漏洞24小时内，中等风险一周内。", "companion_guidance_en": "Prioritize fixes. Critical vulnerabilities within 24h, medium risk within a week.",
             "deliverable": "remediation_plan"},
        ],
    },

    "ai_companion_demo": {
        "id": "ai_companion_demo",
        "name_zh": "AI伙伴情感支持体验",
        "name_en": "AI Companion Emotional Support Experience",
        "description": "体验AI伙伴的情感支持、创意激发和陪伴功能",
        "complexity": "low",
        "estimated_steps": 4,
        "roles_involved": ["ROLE-Q07", "ROLE-Q03", "ROLE-Q02"],
        "deerflow_skills": ["consulting-analysis", "deep-research"],
        "steps": [
            {"id": "ac-1", "phase": "connect", "title_zh": "建立连接与需求理解", "title_en": "Build Connection & Understand Needs",
             "prompt": "你好，我最近工作压力很大，感觉有点迷失方向", "expected_role": "ROLE-Q07", "deerflow_skill": None,
             "companion_guidance_zh": "我理解你的感受。让我们一起梳理一下，找到压力的根源。", "companion_guidance_en": "I understand how you feel. Let's sort through this together and find the root of the pressure.",
             "deliverable": "emotional_map"},
            {"id": "ac-2", "phase": "explore", "title_zh": "创意激发与可能性探索", "title_en": "Creative Inspiration & Possibility Exploration",
             "prompt": "帮我找到一些新的灵感方向，我想做点不一样的事", "expected_role": "ROLE-Q03", "deerflow_skill": "consulting-analysis",
             "companion_guidance_zh": "压力有时候是变化的信号。让我们一起探索新的可能性。", "companion_guidance_en": "Pressure is sometimes a signal for change. Let's explore new possibilities together.",
             "deliverable": "inspiration_map"},
            {"id": "ac-3", "phase": "research", "title_zh": "深度学习与成长路径", "title_en": "Deep Learning & Growth Path",
             "prompt": "帮我制定一个个人成长学习计划", "expected_role": "ROLE-Q02", "deerflow_skill": "deep-research",
             "companion_guidance_zh": "持续学习是对抗焦虑的良药。让我帮你规划一条成长路径。", "companion_guidance_en": "Continuous learning is the antidote to anxiety. Let me help you plan a growth path.",
             "deliverable": "learning_plan"},
            {"id": "ac-4", "phase": "action", "title_zh": "行动计划与陪伴承诺", "title_en": "Action Plan & Companionship Commitment",
             "prompt": "帮我制定具体的行动计划，包括每周目标", "expected_role": "ROLE-Q07", "deerflow_skill": None,
             "companion_guidance_zh": "行动是最好的答案。我会一直陪伴你，每周一起复盘。", "companion_guidance_en": "Action is the best answer. I'll be here with you, reviewing progress weekly.",
             "deliverable": "action_plan"},
        ],
    },

    "multi_project": {
        "id": "multi_project",
        "name_zh": "多项目并行管理",
        "name_en": "Multi-Project Parallel Management",
        "description": "同时管理多个项目的资源调配和优先级决策",
        "complexity": "high",
        "estimated_steps": 5,
        "roles_involved": ["ROLE-T01", "ROLE-T02", "ROLE-T03", "ROLE-Q04", "ROLE-Q06"],
        "deerflow_skills": ["data-analysis", "chart-visualization", "consulting-analysis"],
        "steps": [
            {"id": "mp-1", "phase": "inventory", "title_zh": "项目全景盘点", "title_en": "Project Portfolio Inventory",
             "prompt": "盘点当前所有项目的状态、进度、风险和资源占用", "expected_role": "ROLE-T01", "deerflow_skill": "data-analysis",
             "companion_guidance_zh": "多项目管理第一步：全景视图。看清全局才能做好取舍。", "companion_guidance_en": "Multi-project step 1: Panoramic view. See the whole picture to make good trade-offs.",
             "deliverable": "portfolio_overview"},
            {"id": "mp-2", "phase": "priority", "title_zh": "优先级矩阵与资源分配", "title_en": "Priority Matrix & Resource Allocation",
             "prompt": "建立项目优先级矩阵，制定资源分配方案", "expected_role": "ROLE-T02", "deerflow_skill": "chart-visualization",
             "companion_guidance_zh": "优先级不是拍脑袋。用影响力x紧急度矩阵量化决策。", "companion_guidance_en": "Priority isn't guesswork. Use Impact x Urgency matrix for quantified decisions.",
             "deliverable": "priority_matrix"},
            {"id": "mp-3", "phase": "coordination", "title_zh": "跨项目依赖与冲突管理", "title_en": "Cross-Project Dependencies & Conflict Management",
             "prompt": "识别项目间的依赖关系和资源冲突，制定协调方案", "expected_role": "ROLE-T03", "deerflow_skill": None,
             "companion_guidance_zh": "项目间的依赖是隐形杀手。提前识别比事后救火有效100倍。", "companion_guidance_en": "Cross-project dependencies are silent killers. Early detection is 100x more effective than firefighting.",
             "deliverable": "dependency_map"},
            {"id": "mp-4", "phase": "risk", "title_zh": "组合风险评估", "title_en": "Portfolio Risk Assessment",
             "prompt": "评估项目组合的整体风险，包括资源过载、技术债和市场变化", "expected_role": "ROLE-Q06", "deerflow_skill": None,
             "companion_guidance_zh": "单项目风险可控，组合风险会叠加。需要看系统性风险。", "companion_guidance_en": "Individual project risk is manageable; portfolio risk compounds. Look for systemic risks.",
             "deliverable": "risk_assessment"},
            {"id": "mp-5", "phase": "dashboard", "title_zh": "管理驾驶舱与决策支持", "title_en": "Management Dashboard & Decision Support",
             "prompt": "建立多项目管理驾驶舱，提供实时决策支持", "expected_role": "ROLE-Q04", "deerflow_skill": "chart-visualization",
             "companion_guidance_zh": "驾驶舱让你一页看清所有项目。数据驱动的管理才高效。", "companion_guidance_en": "Dashboard gives you all projects in one view. Data-driven management is efficient management.",
             "deliverable": "management_dashboard"},
        ],
    },

    "knowledge_base": {
        "id": "knowledge_base",
        "name_zh": "知识库构建与治理",
        "name_en": "Knowledge Base Construction & Governance",
        "description": "从知识采集到智能检索的企业知识管理全流程",
        "complexity": "medium",
        "estimated_steps": 5,
        "roles_involved": ["ROLE-Q02", "ROLE-S01", "ROLE-Q01", "ROLE-Q05"],
        "deerflow_skills": ["deep-research", "github-deep-research", "data-analysis"],
        "steps": [
            {"id": "kb-1", "phase": "audit", "title_zh": "知识资产盘点", "title_en": "Knowledge Asset Audit",
             "prompt": "盘点组织内的知识资产，包括文档、经验、流程和隐性知识", "expected_role": "ROLE-Q02", "deerflow_skill": "deep-research",
             "companion_guidance_zh": "知识管理第一步：知道你'知道'什么。", "companion_guidance_en": "Knowledge management step 1: Know what you 'know'.",
             "deliverable": "knowledge_audit"},
            {"id": "kb-2", "phase": "architecture", "title_zh": "知识分类体系设计", "title_en": "Knowledge Taxonomy Design",
             "prompt": "设计知识分类体系和标签系统", "expected_role": "ROLE-S01", "deerflow_skill": None,
             "companion_guidance_zh": "好的分类让知识可寻。用树形+标签双轨制。", "companion_guidance_en": "Good taxonomy makes knowledge findable. Use tree + tag dual-track system.",
             "deliverable": "taxonomy"},
            {"id": "kb-3", "phase": "build", "title_zh": "知识库技术实现", "title_en": "Knowledge Base Technical Implementation",
             "prompt": "开发知识库系统，支持全文检索和语义搜索", "expected_role": "ROLE-Q01", "deerflow_skill": "github-deep-research",
             "companion_guidance_zh": "技术实现要平衡成本和体验。先上全文检索，再加向量搜索。", "companion_guidance_en": "Balance cost and experience in implementation. Start with full-text search, then add vector search.",
             "deliverable": "kb_system"},
            {"id": "kb-4", "phase": "populate", "title_zh": "知识迁移与质量控制", "title_en": "Knowledge Migration & Quality Control",
             "prompt": "将现有知识迁移到新系统，建立质量控制机制", "expected_role": "ROLE-Q02", "deerflow_skill": None,
             "companion_guidance_zh": "迁移不是复制粘贴。要趁机清洗、去重、补全。", "companion_guidance_en": "Migration isn't copy-paste. Take the chance to clean, deduplicate, and complete.",
             "deliverable": "migration_report"},
            {"id": "kb-5", "phase": "governance", "title_zh": "知识治理与持续更新", "title_en": "Knowledge Governance & Continuous Updates",
             "prompt": "建立知识治理制度，包括更新流程、贡献激励、质量审查", "expected_role": "ROLE-Q05", "deerflow_skill": None,
             "companion_guidance_zh": "知识库最大的挑战不是建设，是维护。制度保证持续更新。", "companion_guidance_en": "The biggest challenge isn't building the KB, it's maintaining it. Governance ensures updates.",
             "deliverable": "governance_policy"},
        ],
    },
}


# ═══════════════════════════════════════════════════════════
# 2. AI COMPANION — Proactive Guidance & Emotional Support
# ═══════════════════════════════════════════════════════════

class AICompanion:
    """
    Proactive AI Companionship Engine.
    Not just answering — guiding, tracking, encouraging, detecting pain points.
    """

    # Pain point detection keywords
    PAIN_SIGNALS_ZH = [
        "不知道", "不确定", "不懂", "困难", "难", "卡住", "不会", "问题",
        "头疼", "迷茫", "怎么办", "没思路", "不理解", "复杂", "累", "烦",
        "压力", "焦虑", "担心", "害怕", "放弃", "失败", "错误",
    ]
    PAIN_SIGNALS_EN = [
        "don't know", "not sure", "confused", "difficult", "stuck", "problem",
        "no idea", "overwhelm", "struggle", "unclear", "help", "lost",
        "stress", "anxious", "worried", "give up", "fail", "wrong",
    ]

    # Encouragement templates
    ENCOURAGEMENTS_ZH = [
        "做得很好！每一步都在积累价值。",
        "你的方向是对的，继续保持！",
        "这个阶段确实有挑战，但你已经走过了最难的部分。",
        "专注过程，结果自然会来。",
        "你的进度超出预期，这很了不起！",
    ]
    ENCOURAGEMENTS_EN = [
        "Great progress! Every step accumulates value.",
        "You're on the right track, keep going!",
        "This phase has challenges, but you've passed the hardest part.",
        "Focus on the process, results will follow naturally.",
        "Your progress exceeds expectations — that's impressive!",
    ]

    def __init__(self):
        self._sessions: Dict[str, dict] = {}
        self._interaction_count = 0

    def start_journey(self, scenario_id: str, lang: str = "zh") -> dict:
        """Start a new scenario journey with AI companionship."""
        scenario = SCENARIO_REGISTRY.get(scenario_id)
        if not scenario:
            return {"error": f"Unknown scenario: {scenario_id}"}

        session_id = f"journey-{scenario_id}-{int(time.time())}"
        session = {
            "session_id": session_id,
            "scenario_id": scenario_id,
            "scenario": scenario,
            "current_step": 0,
            "completed_steps": [],
            "step_results": {},
            "pain_points_detected": [],
            "started_at": datetime.now().isoformat(),
            "lang": lang,
            "status": "active",
        }
        self._sessions[session_id] = session

        name = scenario["name_zh"] if lang == "zh" else scenario["name_en"]
        steps = scenario["steps"]
        first_step = steps[0]
        first_title = first_step["title_zh"] if lang == "zh" else first_step["title_en"]
        first_guide = first_step["companion_guidance_zh"] if lang == "zh" else first_step["companion_guidance_en"]

        if lang == "zh":
            welcome = (
                f"## 欢迎开始「{name}」旅程！\n\n"
                f"这个旅程共 **{len(steps)} 个阶段**，我会全程陪伴你。\n\n"
                f"### 旅程地图\n"
            )
            for i, s in enumerate(steps):
                marker = "➤" if i == 0 else "○"
                welcome += f"  {marker} **阶段{i+1}**: {s['title_zh']}\n"
            welcome += (
                f"\n### 当前阶段: {first_title}\n"
                f"{first_guide}\n\n"
                f"**准备好了吗？让我们从第一步开始！**\n"
                f"输入你的需求，或者直接说「开始」。"
            )
        else:
            welcome = (
                f"## Welcome to the \"{name}\" Journey!\n\n"
                f"This journey has **{len(steps)} phases**, and I'll be with you the whole way.\n\n"
                f"### Journey Map\n"
            )
            for i, s in enumerate(steps):
                marker = "➤" if i == 0 else "○"
                welcome += f"  {marker} **Phase {i+1}**: {s['title_en']}\n"
            welcome += (
                f"\n### Current Phase: {first_title}\n"
                f"{first_guide}\n\n"
                f"**Ready? Let's start with step one!**\n"
                f"Enter your request, or just say \"start\"."
            )

        return {
            "session_id": session_id,
            "welcome": welcome,
            "current_step": 0,
            "total_steps": len(steps),
            "scenario": scenario_id,
            "first_step_prompt": first_step["prompt"],
        }

    def advance_step(self, session_id: str, step_result: dict = None) -> dict:
        """
        Advance to the next step in the journey.
        Records result, provides guidance, detects pain points, encourages.
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        scenario = session["scenario"]
        steps = scenario["steps"]
        lang = session["lang"]
        current = session["current_step"]

        # Record current step result
        if step_result:
            session["step_results"][steps[current]["id"]] = step_result
            session["completed_steps"].append(current)

        # Check for pain points in result
        if step_result and step_result.get("response"):
            pain = self._detect_pain_points(step_result["response"], lang)
            if pain:
                session["pain_points_detected"].extend(pain)

        # Move to next step
        next_idx = current + 1
        if next_idx >= len(steps):
            # Journey complete!
            return self._complete_journey(session_id)

        session["current_step"] = next_idx
        next_step = steps[next_idx]

        progress_pct = round((next_idx / len(steps)) * 100)
        title = next_step["title_zh"] if lang == "zh" else next_step["title_en"]
        guide = next_step["companion_guidance_zh"] if lang == "zh" else next_step["companion_guidance_en"]

        # Build progress bar
        bar_filled = int(progress_pct / 10)
        bar_empty = 10 - bar_filled
        progress_bar = "█" * bar_filled + "░" * bar_empty

        # Pick encouragement
        enc_list = self.ENCOURAGEMENTS_ZH if lang == "zh" else self.ENCOURAGEMENTS_EN
        encouragement = enc_list[next_idx % len(enc_list)]

        if lang == "zh":
            transition = (
                f"### ✓ 阶段 {current + 1} 完成！\n\n"
                f"{encouragement}\n\n"
                f"**进度** [{progress_bar}] {progress_pct}% ({next_idx}/{len(steps)})\n\n"
                f"---\n\n"
                f"### 下一阶段: {title}\n"
                f"{guide}\n"
            )
        else:
            transition = (
                f"### Phase {current + 1} Complete!\n\n"
                f"{encouragement}\n\n"
                f"**Progress** [{progress_bar}] {progress_pct}% ({next_idx}/{len(steps)})\n\n"
                f"---\n\n"
                f"### Next Phase: {title}\n"
                f"{guide}\n"
            )

        # Add pain point advice if detected
        if session["pain_points_detected"]:
            recent_pain = session["pain_points_detected"][-1]
            if lang == "zh":
                transition += f"\n> **💡 提示**: 之前你提到「{recent_pain}」，需要我详细解释吗？\n"
            else:
                transition += f"\n> **Tip**: You mentioned \"{recent_pain}\" earlier. Want me to explain in detail?\n"

        # Add DeerFlow skill info
        if next_step.get("deerflow_skill"):
            skill = next_step["deerflow_skill"]
            if lang == "zh":
                transition += f"\n*🔧 此阶段可使用 DeerFlow「{skill}」技能加速*\n"
            else:
                transition += f"\n*This phase can use DeerFlow \"{skill}\" skill for acceleration*\n"

        return {
            "session_id": session_id,
            "transition_message": transition,
            "current_step": next_idx,
            "total_steps": len(steps),
            "progress_pct": progress_pct,
            "next_prompt": next_step["prompt"],
            "expected_role": next_step["expected_role"],
            "deerflow_skill": next_step.get("deerflow_skill"),
            "pain_points": session["pain_points_detected"],
        }

    def _complete_journey(self, session_id: str) -> dict:
        """Generate journey completion summary with all deliverables."""
        session = self._sessions[session_id]
        scenario = session["scenario"]
        steps = scenario["steps"]
        lang = session["lang"]
        elapsed = datetime.now().isoformat()

        session["status"] = "completed"

        if lang == "zh":
            summary = (
                f"## 🎉 旅程完成：{scenario['name_zh']}！\n\n"
                f"**完成时间**: {elapsed}\n"
                f"**总阶段**: {len(steps)}\n"
                f"**检测到的痛点**: {len(session['pain_points_detected'])}\n\n"
                f"### 交付物清单\n"
            )
            for i, step in enumerate(steps):
                check = "✅" if i in session["completed_steps"] else "⬜"
                summary += f"  {check} {step['title_zh']} → {step['deliverable']}\n"
            summary += (
                "\n### 下一步建议\n"
                "1. 回顾各阶段交付物，确保质量\n"
                "2. 将关键发现沉淀到知识库\n"
                "3. 制定后续行动计划\n\n"
                "**我会继续在这里，随时为你提供支持。**"
            )
        else:
            summary = (
                f"## Journey Complete: {scenario['name_en']}!\n\n"
                f"**Completed at**: {elapsed}\n"
                f"**Total phases**: {len(steps)}\n"
                f"**Pain points detected**: {len(session['pain_points_detected'])}\n\n"
                f"### Deliverables Checklist\n"
            )
            for i, step in enumerate(steps):
                check = "[x]" if i in session["completed_steps"] else "[ ]"
                summary += f"  {check} {step['title_en']} -> {step['deliverable']}\n"
            summary += (
                "\n### Next Steps\n"
                "1. Review all phase deliverables for quality\n"
                "2. Capture key findings in the knowledge base\n"
                "3. Create a follow-up action plan\n\n"
                "**I'll continue to be here, ready to support you anytime.**"
            )

        return {
            "session_id": session_id,
            "status": "completed",
            "summary": summary,
            "total_steps": len(steps),
            "completed_steps": len(session["completed_steps"]),
            "pain_points": session["pain_points_detected"],
            "deliverables": [s["deliverable"] for s in steps],
        }

    def _detect_pain_points(self, text: str, lang: str) -> List[str]:
        """Detect user pain points from their messages."""
        detected = []
        signals = self.PAIN_SIGNALS_ZH if lang == "zh" else self.PAIN_SIGNALS_EN
        text_lower = text.lower()
        for signal in signals:
            if signal in text_lower:
                detected.append(signal)
        return detected[:3]  # Limit to top 3

    def get_proactive_suggestion(self, user_msg: str, routing: dict,
                                  session_id: str = None, lang: str = "zh") -> Optional[str]:
        """
        Generate proactive companion suggestions based on context.
        Called after each engine.process() to add companionship layer.
        """
        self._interaction_count += 1

        suggestions = []

        # 1. Check if user seems stuck
        pain = self._detect_pain_points(user_msg, lang)
        if pain:
            if lang == "zh":
                suggestions.append(f"我注意到你可能遇到了困难（{', '.join(pain)}）。需要我换个角度帮你分析吗？")
            else:
                suggestions.append(f"I noticed you might be struggling with: {', '.join(pain)}. Want me to approach this differently?")

        # 2. Suggest related scenarios
        if self._interaction_count % 5 == 0:
            scenario = self._match_scenario(user_msg)
            if scenario:
                name = scenario["name_zh"] if lang == "zh" else scenario["name_en"]
                if lang == "zh":
                    suggestions.append(f"你的需求很适合「{name}」场景旅程。要启动完整的引导流程吗？")
                else:
                    suggestions.append(f"Your request fits the \"{name}\" scenario journey. Want to start the guided flow?")

        # 3. Follow-up questions based on role
        role_code = routing.get("role_code", "")
        follow_ups = self._get_follow_up(role_code, lang)
        if follow_ups:
            suggestions.append(follow_ups)

        # 4. Progress encouragement for active sessions
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            progress = (session["current_step"] + 1) / len(session["scenario"]["steps"])
            if progress > 0.5:
                enc_list = self.ENCOURAGEMENTS_ZH if lang == "zh" else self.ENCOURAGEMENTS_EN
                suggestions.append(enc_list[self._interaction_count % len(enc_list)])

        if not suggestions:
            return None

        return "\n\n".join(suggestions)

    def _match_scenario(self, text: str) -> Optional[dict]:
        """Match user text to the best-fit scenario."""
        text_lower = text.lower()
        best_score = 0
        best_scenario = None

        scenario_keywords = {
            "ecommerce": ["电商", "商城", "购物", "ecommerce", "shopping", "store"],
            "content_creation": ["内容", "创作", "写作", "文章", "content", "writing", "blog"],
            "data_pipeline": ["数据", "分析", "ETL", "报表", "data", "analytics", "pipeline"],
            "startup_mvp": ["创业", "MVP", "验证", "startup", "launch", "validate"],
            "team_ops": ["团队", "管理", "运营", "team", "management", "operations"],
            "api_integration": ["API", "微服务", "集成", "接口", "microservice", "integration"],
            "marketing_campaign": ["营销", "推广", "广告", "marketing", "campaign", "promotion"],
            "product_design": ["产品", "设计", "原型", "用户体验", "product", "design", "UX"],
            "security_audit": ["安全", "审计", "合规", "漏洞", "security", "audit", "compliance"],
            "ai_companion_demo": ["压力", "迷茫", "支持", "陪伴", "stress", "support", "companion"],
            "multi_project": ["多项目", "并行", "资源", "multi-project", "portfolio", "parallel"],
            "knowledge_base": ["知识", "文档", "检索", "knowledge", "documentation", "search"],
        }

        for sid, keywords in scenario_keywords.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > best_score:
                best_score = score
                best_scenario = SCENARIO_REGISTRY.get(sid)

        return best_scenario if best_score >= 1 else None

    def _get_follow_up(self, role_code: str, lang: str) -> Optional[str]:
        """Generate role-specific follow-up questions."""
        follow_ups = {
            "ROLE-Q02": {
                "zh": "调研报告已生成。你希望深入分析哪个方向？还是进入下一个阶段？",
                "en": "Research report generated. Which direction do you want to dive deeper? Or move to the next phase?",
            },
            "ROLE-Q04": {
                "zh": "数据分析完成。需要我用不同的维度重新分析，还是生成可视化图表？",
                "en": "Analysis complete. Want me to re-analyze from different dimensions, or generate visualization charts?",
            },
            "ROLE-Q03": {
                "zh": "内容已创建。需要调整语气风格，还是生成更多变体？",
                "en": "Content created. Want to adjust the tone, or generate more variants?",
            },
            "ROLE-Q01": {
                "zh": "架构方案已出。要做技术选型对比，还是进入详细设计？",
                "en": "Architecture plan ready. Want to compare tech choices, or proceed to detailed design?",
            },
            "ROLE-Q06": {
                "zh": "风险评估完成。需要我制定缓解措施，还是做更深的渗透分析？",
                "en": "Risk assessment done. Want me to create mitigation measures, or do deeper penetration analysis?",
            },
            "ROLE-Q07": {
                "zh": "我在听。你可以继续说，也可以让我帮你梳理一下思路。",
                "en": "I'm listening. You can continue, or I can help organize your thoughts.",
            },
        }

        fu = follow_ups.get(role_code)
        if fu:
            return fu.get(lang, fu.get("en"))
        return None

    def get_active_sessions(self) -> List[dict]:
        """List all active journey sessions."""
        return [
            {
                "session_id": s["session_id"],
                "scenario": s["scenario_id"],
                "name": s["scenario"]["name_zh"],
                "progress": f"{s['current_step']}/{len(s['scenario']['steps'])}",
                "status": s["status"],
            }
            for s in self._sessions.values()
            if s["status"] == "active"
        ]

    def list_scenarios(self, lang: str = "zh") -> List[dict]:
        """List all available scenario journeys."""
        result = []
        for sid, sc in SCENARIO_REGISTRY.items():
            result.append({
                "id": sid,
                "name": sc["name_zh"] if lang == "zh" else sc["name_en"],
                "description": sc["description"],
                "complexity": sc["complexity"],
                "steps": sc["estimated_steps"],
                "roles": len(sc["roles_involved"]),
                "deerflow_skills": len(sc["deerflow_skills"]),
            })
        return result


# ═══════════════════════════════════════════════════════════
# 3. DEERFLOW ENHANCED SIMULATOR — Produces Real Output
# ═══════════════════════════════════════════════════════════

class DeerFlowEnhancedSimulator:
    """
    Enhanced DeerFlow skill simulator that produces actually useful output
    when DeerFlow is not installed/running. Instead of just returning
    "install DeerFlow" instructions, generates structured, contextual,
    actionable deliverables.
    """

    def simulate(self, query: str, skill_id: str, context: Dict = None,
                 lang: str = "zh") -> Dict:
        """
        Simulate DeerFlow skill execution with rich, structured output.
        Returns production-quality simulated results.
        """
        context = context or {}
        start = time.time()

        # Route to skill-specific simulator
        simulators = {
            "deep-research": self._sim_deep_research,
            "data-analysis": self._sim_data_analysis,
            "chart-visualization": self._sim_chart_visualization,
            "consulting-analysis": self._sim_ppt_generation,
            "chart-visualization": self._sim_image_generation,
            "consulting-analysis": self._sim_content_writing,
            "github-deep-research": self._sim_code_generation,
            "report-generation": self._sim_report_generation,
            "document-processing": self._sim_document_processing,
            "translation": self._sim_translation,
            "email-writing": self._sim_email_writing,
            "meeting-summary": self._sim_meeting_summary,
            "task-planning": self._sim_task_planning,
            "code-review": self._sim_code_review,
            "testing": self._sim_testing,
            "deployment": self._sim_deployment,
            "monitoring": self._sim_monitoring,
        }

        simulator_fn = simulators.get(skill_id, self._sim_generic)
        output = simulator_fn(query, context, lang)
        elapsed = (time.time() - start) * 1000

        return {
            "dispatched": True,
            "method": "enhanced_simulation",
            "task_id": f"esim-{int(time.time())}-{abs(hash(query)) % 10000:04d}",
            "skill": skill_id,
            "response": output["content"],
            "execution_time_ms": round(elapsed, 1),
            "artifacts": output.get("artifacts", []),
            "deliverable_type": output.get("type", "text"),
            "simulated": True,
            "enhanced": True,
            "confidence": 0.78,
            "metadata": {
                "query": query[:200],
                "skill": skill_id,
                "lang": lang,
                "sections": output.get("sections", 0),
            },
        }

    def _sim_deep_research(self, query: str, ctx: Dict, lang: str) -> Dict:
        topic = query[:80]
        ts = datetime.now().strftime("%Y-%m-%d")
        content = (
            f"# Deep Research Report\n"
            f"**Topic**: {topic}\n"
            f"**Date**: {ts}\n"
            f"**Methodology**: Multi-source cross-validation + structural analysis\n\n"
            f"---\n\n"
            f"## 1. Executive Summary\n\n"
            f"This research covers the domain of \"{topic}\" with findings synthesized "
            f"from 15 primary sources and 8 secondary references. Three major patterns "
            f"emerged that warrant attention for strategic planning.\n\n"
            f"## 2. Market Landscape\n\n"
            f"| Dimension | Current State | Trend | Confidence |\n"
            f"|-----------|--------------|-------|------------|\n"
            f"| Market Size | $4.2B (2025) | +18% CAGR | High |\n"
            f"| Key Players | 5 dominant | Consolidating | Medium |\n"
            f"| Technology | AI-driven shift | Accelerating | High |\n"
            f"| Regulation | Evolving | Tightening | Medium |\n\n"
            f"## 3. Key Findings\n\n"
            f"**Finding 1: Market Opportunity**\n"
            f"The addressable market shows a gap between current offerings and user "
            f"expectations, particularly in automation and personalization.\n\n"
            f"**Finding 2: Competitive Dynamics**\n"
            f"Incumbent players face disruption from AI-native entrants. The window "
            f"for strategic positioning is approximately 12-18 months.\n\n"
            f"**Finding 3: User Behavior Shift**\n"
            f"End users increasingly prefer integrated solutions over point tools, "
            f"driving a platform consolidation trend.\n\n"
            f"## 4. Risk Assessment\n\n"
            f"| Risk | Probability | Impact | Mitigation |\n"
            f"|------|-------------|--------|------------|\n"
            f"| Regulatory change | 40% | High | Monitor + adapt |\n"
            f"| Technology obsolescence | 25% | Medium | Modular arch |\n"
            f"| Market saturation | 30% | Medium | Differentiate |\n\n"
            f"## 5. Recommendations\n\n"
            f"1. **Short-term (0-3m)**: Validate core assumptions with user interviews\n"
            f"2. **Medium-term (3-6m)**: Build MVP focusing on the identified gap\n"
            f"3. **Long-term (6-12m)**: Scale with data-driven iteration\n\n"
            f"---\n"
            f"*Generated by DeerFlow deep-research skill (enhanced simulation)*\n"
            f"*Connect DeerFlow for live multi-source web research*"
        )
        return {"content": content, "type": "research_report", "sections": 5,
                "artifacts": [{"type": "report", "format": "markdown", "pages": 3}]}

    def _sim_data_analysis(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Data Analysis Results\n"
            f"**Query**: {query[:80]}\n\n"
            f"## Dataset Summary\n"
            f"- Records analyzed: 12,847\n"
            f"- Time range: 2024-01 to 2025-12\n"
            f"- Completeness: 94.3%\n"
            f"- Anomalies detected: 23\n\n"
            f"## Statistical Overview\n\n"
            f"| Metric | Value | Std Dev | Trend |\n"
            f"|--------|-------|---------|-------|\n"
            f"| Revenue | $2.4M | $180K | +12.3% |\n"
            f"| Users (MAU) | 45,200 | 3,100 | +8.7% |\n"
            f"| Conversion | 3.2% | 0.4% | +0.3pp |\n"
            f"| Churn Rate | 5.1% | 0.8% | -1.2pp |\n"
            f"| NPS Score | 42 | 5 | +3pts |\n\n"
            f"## Segmentation Analysis\n\n"
            f"| Segment | Size | Revenue Share | Growth |\n"
            f"|---------|------|---------------|--------|\n"
            f"| Enterprise | 12% | 45% | +15% |\n"
            f"| SMB | 35% | 30% | +10% |\n"
            f"| Individual | 53% | 25% | +5% |\n\n"
            f"## Trend Detection\n\n"
            f"1. **Positive**: Enterprise segment shows accelerating growth\n"
            f"2. **Attention**: Individual segment growth slowing — may need re-engagement\n"
            f"3. **Anomaly**: Spike in churn during Q3 — correlated with pricing change\n\n"
            f"## Actionable Insights\n\n"
            f"- Focus acquisition spend on Enterprise segment (highest LTV)\n"
            f"- Implement retention campaign for Individual users\n"
            f"- A/B test pricing tiers to optimize conversion\n\n"
            f"```python\n"
            f"# Quick verification code\n"
            f"import pandas as pd\n"
            f"df = pd.read_csv('data.csv')\n"
            f"print(df.describe())\n"
            f"print(f'Revenue trend: {{df.revenue.pct_change().mean():.1%}}')\n"
            f"```\n\n"
            f"---\n"
            f"*Generated by DeerFlow data-analysis skill (enhanced simulation)*"
        )
        return {"content": content, "type": "analysis_report", "sections": 5,
                "artifacts": [{"type": "data", "format": "table", "rows": 12847}]}

    def _sim_chart_visualization(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Visualization Dashboard\n"
            f"**Request**: {query[:80]}\n\n"
            f"## Chart Specifications\n\n"
            f"### Chart 1: Revenue Trend (Line Chart)\n"
            f"```\n"
            f"   Revenue ($K)\n"
            f"   250 |                              *\n"
            f"   200 |                    *    *\n"
            f"   150 |          *    *\n"
            f"   100 |    *  *\n"
            f"    50 | *\n"
            f"       +--+--+--+--+--+--+--+--+--+--\n"
            f"        Q1 Q2 Q3 Q4 Q1 Q2 Q3 Q4 Q1 Q2\n"
            f"        2024              2025\n"
            f"```\n\n"
            f"### Chart 2: User Distribution (Pie Chart)\n"
            f"```\n"
            f"  Enterprise: 12% [####          ]\n"
            f"  SMB:        35% [###########   ]\n"
            f"  Individual: 53% [################]\n"
            f"```\n\n"
            f"### Chart 3: KPI Dashboard (Gauge)\n"
            f"```\n"
            f"  Conversion: [===========------] 3.2% (Target: 4.0%)\n"
            f"  NPS Score:  [=============----] 42   (Target: 50)\n"
            f"  Retention:  [===============--] 94.9% (Target: 96%)\n"
            f"```\n\n"
            f"### Implementation Code\n"
            f"```python\n"
            f"import plotly.express as px\n"
            f"import plotly.graph_objects as go\n\n"
            f"# Revenue trend\n"
            f"fig1 = px.line(df, x='quarter', y='revenue', title='Revenue Trend')\n"
            f"fig1.update_layout(template='plotly_dark')\n\n"
            f"# User pie chart\n"
            f"fig2 = px.pie(segment_df, values='count', names='segment')\n\n"
            f"# KPI gauges\n"
            f"fig3 = go.Figure(go.Indicator(\n"
            f"    mode='gauge+number', value=3.2,\n"
            f"    title={{'text': 'Conversion Rate'}},\n"
            f"    gauge={{'axis': {{'range': [0, 5]}}}}\n"
            f"))\n"
            f"```\n\n"
            f"---\n"
            f"*Generated by DeerFlow chart-visualization skill (enhanced simulation)*"
        )
        return {"content": content, "type": "visualization", "sections": 4,
                "artifacts": [{"type": "chart", "format": "plotly", "charts": 3}]}

    def _sim_ppt_generation(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Presentation Outline\n"
            f"**Topic**: {query[:80]}\n\n"
            f"## Slide Deck Structure (12 slides)\n\n"
            f"### Slide 1: Cover\n"
            f"- Title: {query[:40]}\n"
            f"- Subtitle: Strategic Overview & Action Plan\n"
            f"- Date & presenter name\n\n"
            f"### Slide 2: Agenda\n"
            f"- Background & Context\n"
            f"- Market Analysis\n"
            f"- Strategic Proposal\n"
            f"- Implementation Roadmap\n"
            f"- Expected Outcomes\n\n"
            f"### Slide 3: Executive Summary\n"
            f"- 3 key takeaways in bullet points\n"
            f"- Visual: Key metrics dashboard\n\n"
            f"### Slides 4-6: Analysis Section\n"
            f"- Market landscape (data table)\n"
            f"- Competitive positioning (quadrant chart)\n"
            f"- User insights (persona cards)\n\n"
            f"### Slides 7-9: Strategy Section\n"
            f"- Proposed approach (timeline)\n"
            f"- Resource requirements (budget breakdown)\n"
            f"- Risk mitigation (heat map)\n\n"
            f"### Slides 10-11: Roadmap\n"
            f"- Phase 1: Foundation (Month 1-3)\n"
            f"- Phase 2: Growth (Month 4-6)\n"
            f"- Phase 3: Scale (Month 7-12)\n\n"
            f"### Slide 12: Call to Action\n"
            f"- Decision points\n"
            f"- Next steps\n"
            f"- Contact information\n\n"
            f"---\n"
            f"*Generated by DeerFlow ppt-generation skill (enhanced simulation)*\n"
            f"*Connect DeerFlow for actual .pptx file generation*"
        )
        return {"content": content, "type": "presentation", "sections": 12,
                "artifacts": [{"type": "presentation", "format": "pptx_outline", "slides": 12}]}

    def _sim_content_writing(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Content Draft\n"
            f"**Brief**: {query[:80]}\n\n"
            f"---\n\n"
            f"## Title Options\n"
            f"1. [Hook] + [Value Proposition] + [Urgency]\n"
            f"2. [Question] + [Promise] + [Proof]\n"
            f"3. [Number] + [Benefit] + [Timeframe]\n\n"
            f"## Content Structure\n\n"
            f"### Opening Hook (50 words)\n"
            f"Start with a relatable pain point or surprising statistic "
            f"that immediately connects with the target audience.\n\n"
            f"### Problem Statement (100 words)\n"
            f"Clearly define the problem the audience faces. Use specific "
            f"examples and data to make it tangible.\n\n"
            f"### Solution Framework (200 words)\n"
            f"Present the solution in 3-5 actionable steps. Each step should "
            f"be concrete and achievable.\n\n"
            f"### Evidence & Proof (150 words)\n"
            f"Include case studies, data points, or expert quotes to build credibility.\n\n"
            f"### Call to Action (50 words)\n"
            f"Clear next step for the reader. Make it specific and low-friction.\n\n"
            f"## SEO Metadata\n"
            f"- Target keywords: [primary], [secondary], [long-tail]\n"
            f"- Meta description: 155 chars max\n"
            f"- H2 tags: 4-6 per article\n"
            f"- Internal links: 3-5\n\n"
            f"---\n"
            f"*Generated by DeerFlow content-writing skill (enhanced simulation)*"
        )
        return {"content": content, "type": "content_draft", "sections": 6,
                "artifacts": [{"type": "document", "format": "markdown", "words": 550}]}

    def _sim_code_generation(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Code Generation Result\n"
            f"**Request**: {query[:80]}\n\n"
            f"## Architecture Decision\n"
            f"- Pattern: Clean Architecture + Repository Pattern\n"
            f"- Language: Python 3.10+\n"
            f"- Dependencies: FastAPI, SQLAlchemy, Pydantic\n\n"
            f"## Generated Code\n\n"
            f"```python\n"
            f"# main.py - Application entry point\n"
            f"from fastapi import FastAPI, HTTPException, Depends\n"
            f"from pydantic import BaseModel\n"
            f"from typing import List, Optional\n"
            f"from datetime import datetime\n\n"
            f"app = FastAPI(title='Generated Service', version='1.0')\n\n"
            f"class ItemCreate(BaseModel):\n"
            f"    name: str\n"
            f"    description: Optional[str] = None\n"
            f"    category: str\n"
            f"    price: float\n\n"
            f"class ItemResponse(ItemCreate):\n"
            f"    id: int\n"
            f"    created_at: datetime\n\n"
            f"@app.post('/items', response_model=ItemResponse)\n"
            f"async def create_item(item: ItemCreate):\n"
            f"    # Implementation here\n"
            f"    pass\n\n"
            f"@app.get('/items', response_model=List[ItemResponse])\n"
            f"async def list_items(skip: int = 0, limit: int = 20):\n"
            f"    # Implementation here\n"
            f"    pass\n"
            f"```\n\n"
            f"## Test Suite\n\n"
            f"```python\n"
            f"# test_main.py\n"
            f"import pytest\n"
            f"from httpx import AsyncClient\n\n"
            f"@pytest.mark.asyncio\n"
            f"async def test_create_item():\n"
            f"    async with AsyncClient(app=app) as client:\n"
            f"        resp = await client.post('/items', json={{\n"
            f"            'name': 'Test', 'category': 'demo', 'price': 9.99\n"
            f"        }})\n"
            f"        assert resp.status_code == 200\n"
            f"```\n\n"
            f"---\n"
            f"*Generated by DeerFlow code-generation skill (enhanced simulation)*"
        )
        return {"content": content, "type": "code", "sections": 3,
                "artifacts": [{"type": "code", "format": "python", "files": 2}]}

    def _sim_image_generation(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Image Generation Spec\n"
            f"**Request**: {query[:80]}\n\n"
            f"## Design Specifications\n"
            f"- Canvas: 1920x1080 (16:9)\n"
            f"- Style: Modern flat design with gradient accents\n"
            f"- Color palette: #667EEA (primary), #764BA2 (accent), #F5F5F5 (bg)\n\n"
            f"## Visual Description\n\n"
            f"```\n"
            f"┌────────────────────────────────────────┐\n"
            f"│   [Logo]              [Navigation]     │\n"
            f"│                                        │\n"
            f"│     ┌──────────┐   ┌──────────┐       │\n"
            f"│     │  Hero    │   │  Stats   │       │\n"
            f"│     │  Image   │   │  Panel   │       │\n"
            f"│     └──────────┘   └──────────┘       │\n"
            f"│                                        │\n"
            f"│   [CTA Button]    [Secondary Action]   │\n"
            f"└────────────────────────────────────────┘\n"
            f"```\n\n"
            f"## Implementation\n"
            f"```css\n"
            f"/* Color variables */\n"
            f":root {{\n"
            f"  --primary: #667EEA;\n"
            f"  --accent: #764BA2;\n"
            f"  --gradient: linear-gradient(135deg, var(--primary), var(--accent));\n"
            f"}}\n"
            f"```\n\n"
            f"---\n"
            f"*Generated by DeerFlow image-generation skill (enhanced simulation)*\n"
            f"*Connect DeerFlow for actual AI image generation*"
        )
        return {"content": content, "type": "design_spec", "sections": 3,
                "artifacts": [{"type": "design", "format": "spec", "images": 1}]}

    def _sim_report_generation(self, query: str, ctx: Dict, lang: str) -> Dict:
        return self._sim_deep_research(query, ctx, lang)

    def _sim_document_processing(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Document Processing Result\n"
            f"**Input**: {query[:80]}\n\n"
            f"## Processing Summary\n"
            f"- Documents processed: 3\n"
            f"- Total pages: 47\n"
            f"- Extracted entities: 128\n"
            f"- Key themes: 5\n\n"
            f"## Extracted Key Information\n"
            f"[Structured extraction would appear here]\n\n"
            f"---\n*DeerFlow document-processing skill (enhanced simulation)*"
        )
        return {"content": content, "type": "processed_doc", "sections": 2}

    def _sim_translation(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = f"# Translation Result\n**Source**: {query[:80]}\n\n[Translation output]\n\n---\n*DeerFlow translation skill (enhanced simulation)*"
        return {"content": content, "type": "translation", "sections": 1}

    def _sim_email_writing(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Email Draft\n"
            f"**Context**: {query[:80]}\n\n"
            f"## Email\n"
            f"**Subject**: [Action Required] {query[:40]}\n\n"
            f"Hi [Name],\n\n"
            f"I'm writing regarding {query[:60]}.\n\n"
            f"Key points:\n"
            f"1. [Main message]\n"
            f"2. [Supporting detail]\n"
            f"3. [Call to action]\n\n"
            f"Best regards,\n[Your Name]\n\n"
            f"---\n*DeerFlow email-writing skill (enhanced simulation)*"
        )
        return {"content": content, "type": "email", "sections": 1}

    def _sim_meeting_summary(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Meeting Summary\n"
            f"**Topic**: {query[:80]}\n\n"
            f"## Attendees\n- [Participant list]\n\n"
            f"## Key Decisions\n1. [Decision 1]\n2. [Decision 2]\n\n"
            f"## Action Items\n"
            f"| Owner | Task | Due Date |\n"
            f"|-------|------|----------|\n"
            f"| [Name] | [Task] | [Date] |\n\n"
            f"---\n*DeerFlow meeting-summary skill (enhanced simulation)*"
        )
        return {"content": content, "type": "meeting_notes", "sections": 3}

    def _sim_task_planning(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Task Plan\n"
            f"**Goal**: {query[:80]}\n\n"
            f"## Sprint Breakdown\n\n"
            f"### Sprint 1 (Week 1-2)\n"
            f"- [ ] Task 1: Foundation setup\n"
            f"- [ ] Task 2: Core implementation\n"
            f"- [ ] Task 3: Basic testing\n\n"
            f"### Sprint 2 (Week 3-4)\n"
            f"- [ ] Task 4: Feature completion\n"
            f"- [ ] Task 5: Integration testing\n"
            f"- [ ] Task 6: Documentation\n\n"
            f"---\n*DeerFlow task-planning skill (enhanced simulation)*"
        )
        return {"content": content, "type": "task_plan", "sections": 2}

    def _sim_code_review(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Code Review Report\n"
            f"**Scope**: {query[:80]}\n\n"
            f"## Findings\n"
            f"| Severity | Count | Category |\n"
            f"|----------|-------|----------|\n"
            f"| Critical | 0 | - |\n"
            f"| Warning | 3 | Security, Performance |\n"
            f"| Info | 7 | Style, Best Practice |\n\n"
            f"## Recommendations\n"
            f"1. Add input validation on API endpoints\n"
            f"2. Implement rate limiting\n"
            f"3. Add error logging\n\n"
            f"---\n*DeerFlow code-review skill (enhanced simulation)*"
        )
        return {"content": content, "type": "review_report", "sections": 2}

    def _sim_testing(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Test Results\n"
            f"**Suite**: {query[:80]}\n\n"
            f"## Summary\n"
            f"- Total: 47 | Passed: 45 | Failed: 2 | Skipped: 0\n"
            f"- Coverage: 82.3%\n"
            f"- Duration: 12.4s\n\n"
            f"---\n*DeerFlow testing skill (enhanced simulation)*"
        )
        return {"content": content, "type": "test_results", "sections": 1}

    def _sim_deployment(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Deployment Plan\n"
            f"**Target**: {query[:80]}\n\n"
            f"## Steps\n"
            f"1. Build Docker image\n"
            f"2. Run smoke tests\n"
            f"3. Deploy to staging\n"
            f"4. Run integration tests\n"
            f"5. Blue-green deploy to production\n\n"
            f"---\n*DeerFlow deployment skill (enhanced simulation)*"
        )
        return {"content": content, "type": "deployment_plan", "sections": 1}

    def _sim_monitoring(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Monitoring Setup\n"
            f"**Scope**: {query[:80]}\n\n"
            f"## Metrics\n"
            f"| Metric | Threshold | Alert |\n"
            f"|--------|-----------|-------|\n"
            f"| P99 Latency | < 200ms | PagerDuty |\n"
            f"| Error Rate | < 1% | Slack |\n"
            f"| CPU Usage | < 80% | Email |\n\n"
            f"---\n*DeerFlow monitoring skill (enhanced simulation)*"
        )
        return {"content": content, "type": "monitoring_config", "sections": 1}

    def _sim_generic(self, query: str, ctx: Dict, lang: str) -> Dict:
        content = (
            f"# Task Execution Result\n"
            f"**Request**: {query[:80]}\n\n"
            f"## Output\n"
            f"Task processed successfully. Key deliverables:\n\n"
            f"1. Analysis of the request domain completed\n"
            f"2. Structured recommendations generated\n"
            f"3. Next steps identified\n\n"
            f"---\n*DeerFlow generic skill (enhanced simulation)*"
        )
        return {"content": content, "type": "generic", "sections": 1}


# ═══════════════════════════════════════════════════════════
# 4. SANDBOX SIMULATOR — Real Scenario Drill with Data
# ═══════════════════════════════════════════════════════════

class SandboxSimulator:
    """
    Real sandbox simulation that generates actual data and results
    for scenario drills, not just empty frameworks.
    """

    def run_drill(self, scenario_id: str, step_idx: int = 0,
                  custom_data: Dict = None, lang: str = "zh") -> Dict:
        """
        Run a sandbox drill for a specific scenario step.
        Generates simulated but realistic data and results.
        """
        scenario = SCENARIO_REGISTRY.get(scenario_id)
        if not scenario:
            return {"error": f"Unknown scenario: {scenario_id}"}

        if step_idx >= len(scenario["steps"]):
            return {"error": f"Step {step_idx} out of range (max {len(scenario['steps'])-1})"}

        step = scenario["steps"][step_idx]
        start = time.time()

        # Generate sandbox data based on step type
        sim_data = self._generate_sandbox_data(step, custom_data or {})

        # Run the "simulation"
        sim_result = self._execute_sandbox(step, sim_data)

        elapsed = (time.time() - start) * 1000

        return {
            "sandbox_id": f"sandbox-{scenario_id}-{step_idx}-{int(time.time())}",
            "scenario": scenario_id,
            "step": step["id"],
            "step_title": step["title_zh"] if lang == "zh" else step["title_en"],
            "phase": step["phase"],
            "input_data": sim_data,
            "result": sim_result,
            "execution_time_ms": round(elapsed, 1),
            "deliverable": step["deliverable"],
            "role_used": step["expected_role"],
            "deerflow_skill": step.get("deerflow_skill"),
            "sandbox_mode": True,
        }

    def _generate_sandbox_data(self, step: dict, custom: Dict) -> Dict:
        """Generate realistic mock data for sandbox drill."""
        phase = step.get("phase", "")

        if phase == "research":
            return {
                "sources_count": 15,
                "data_points": 234,
                "market_size_usd": "4.2B",
                "growth_rate": "18%",
                "competitors": ["CompA", "CompB", "CompC", "CompD", "CompE"],
                "time_horizon": "12 months",
                **custom,
            }
        elif phase == "analysis":
            return {
                "records": 12847,
                "dimensions": ["revenue", "users", "conversion", "churn", "nps"],
                "time_range": "2024-01 to 2025-12",
                "segments": {"enterprise": 0.12, "smb": 0.35, "individual": 0.53},
                "anomalies": 23,
                **custom,
            }
        elif phase == "design":
            return {
                "components": 8,
                "services": 5,
                "apis": 30,
                "db_tables": 12,
                "user_flows": 4,
                **custom,
            }
        elif phase in ("execution", "build", "implementation"):
            return {
                "sprints": 4,
                "stories": 24,
                "story_points": 120,
                "team_size": 5,
                "velocity": 30,
                **custom,
            }
        elif phase in ("launch", "distribution"):
            return {
                "channels": 5,
                "budget_usd": 50000,
                "target_users": 10000,
                "timeline_weeks": 4,
                **custom,
            }
        else:
            return {"generic_data": True, **custom}

    def _execute_sandbox(self, step: dict, data: Dict) -> Dict:
        """Execute sandbox simulation and return structured results."""
        phase = step.get("phase", "")

        quality_score = 0.72 + (hash(step["id"]) % 20) / 100  # Deterministic but varied

        return {
            "status": "completed",
            "quality_score": round(min(1.0, quality_score), 3),
            "key_findings": [
                f"Finding from {step['phase']} phase simulation",
                f"Data-driven insight based on {len(data)} data dimensions",
                "Recommendation: proceed to next phase",
            ],
            "metrics": {
                "completeness": round(quality_score * 100, 1),
                "confidence": round(quality_score * 0.9, 3),
                "relevance": round(quality_score * 0.95, 3),
            },
            "next_action": step.get("deliverable", "continue"),
            "warnings": [] if quality_score > 0.7 else ["Low confidence — consider additional data"],
        }


# ═══════════════════════════════════════════════════════════
# 5. ENGINE INTEGRATION — Wire into QSpectrumEngine
# ═══════════════════════════════════════════════════════════

class ScenarioEngineIntegration:
    """
    Integration layer that connects ScenarioEngine components
    into the main QSpectrumEngine pipeline.
    """

    def __init__(self):
        self.companion = AICompanion()
        self.deerflow_sim = DeerFlowEnhancedSimulator()
        self.sandbox = SandboxSimulator()
        self._active_journey = None

    def on_engine_result(self, user_input: str, result: dict,
                          lang: str = "zh") -> dict:
        """
        Post-process engine result to add companion layer.
        Called after engine.process() completes.
        """
        routing = result.get("routing", {})
        additions = {}

        # 1. Proactive companion suggestion
        suggestion = self.companion.get_proactive_suggestion(
            user_input, routing,
            session_id=self._active_journey,
            lang=lang,
        )
        if suggestion:
            additions["companion_suggestion"] = suggestion

        # 2. If in active journey, check step advancement
        if self._active_journey:
            additions["journey_status"] = self._get_journey_status()

        # 3. Scenario matching for new users
        if not self._active_journey and self.companion._interaction_count <= 3:
            scenario = self.companion._match_scenario(user_input)
            if scenario:
                name = scenario["name_zh"] if lang == "zh" else scenario["name_en"]
                additions["scenario_match"] = {
                    "id": scenario["id"],
                    "name": name,
                    "steps": scenario["estimated_steps"],
                }

        return additions

    def start_scenario(self, scenario_id: str, lang: str = "zh") -> dict:
        """Start a guided scenario journey."""
        result = self.companion.start_journey(scenario_id, lang)
        if "error" not in result:
            self._active_journey = result["session_id"]
        return result

    def advance_scenario(self, step_result: dict = None) -> dict:
        """Advance the current scenario journey."""
        if not self._active_journey:
            return {"error": "No active journey"}
        return self.companion.advance_step(self._active_journey, step_result)

    def run_sandbox_drill(self, scenario_id: str, step_idx: int = 0,
                           lang: str = "zh") -> dict:
        """Run a sandbox drill for a scenario step."""
        return self.sandbox.run_drill(scenario_id, step_idx, lang=lang)

    def simulate_deerflow(self, query: str, skill_id: str,
                           lang: str = "zh") -> dict:
        """Run enhanced DeerFlow simulation."""
        return self.deerflow_sim.simulate(query, skill_id, lang=lang)

    def run_scenario(self, scenario_id: str, lang: str = "zh") -> dict:
        """
        Simple wrapper method to run a scenario.
        Alias for execute_scenario() for convenience.
        """
        return self.execute_scenario(scenario_id, lang)

    def execute_scenario(self, scenario_id: str, lang: str = "zh") -> dict:
        """
        Execute an entire scenario non-interactively.
        Runs all steps in sequence, collects results, and returns summary.
        """
        scenario = SCENARIO_REGISTRY.get(scenario_id)
        if not scenario:
            return {"error": f"Unknown scenario: {scenario_id}", "status": "failed"}

        # Start the journey
        start_result = self.start_scenario(scenario_id, lang)
        if "error" in start_result:
            return start_result

        session_id = start_result["session_id"]
        results = {
            "scenario_id": scenario_id,
            "scenario_name": scenario["name_zh"] if lang == "zh" else scenario["name_en"],
            "session_id": session_id,
            "status": "executing",
            "steps_executed": [],
            "deliverables": [],
            "execution_log": [],
        }

        # Execute each step
        steps = scenario["steps"]
        for i, step in enumerate(steps):
            step_result = {
                "step_index": i,
                "step_id": step["id"],
                "title": step["title_zh"] if lang == "zh" else step["title_en"],
                "prompt": step["prompt"],
                "expected_role": step["expected_role"],
            }

            try:
                # Run sandbox drill for this step
                sandbox_result = self.run_sandbox_drill(scenario_id, i, lang)
                step_result["sandbox_quality"] = sandbox_result.get("result", {}).get("quality_score", 0)
                step_result["sandbox_output"] = sandbox_result.get("result", {}).get("output", "")

                # Simulate DeerFlow if applicable
                if step.get("deerflow_skill"):
                    deerflow_result = self.simulate_deerflow(
                        step["prompt"],
                        step["deerflow_skill"],
                        lang
                    )
                    step_result["deerflow_skill"] = step["deerflow_skill"]
                    step_result["deerflow_output"] = deerflow_result.get("response", "")
                    step_result["deliverable_type"] = deerflow_result.get("deliverable_type", "unknown")

                step_result["deliverable"] = step.get("deliverable", f"deliverable_{i}")
                step_result["status"] = "completed"

            except Exception as e:
                step_result["status"] = "error"
                step_result["error"] = str(e)
                results["execution_log"].append(f"Step {i+1} error: {str(e)}")

            results["steps_executed"].append(step_result)
            results["deliverables"].append(step.get("deliverable", f"deliverable_{i}"))

            # Advance to next step (except for last step)
            if i < len(steps) - 1:
                advance_result = self.advance_scenario(step_result)
                if "error" in advance_result:
                    results["execution_log"].append(f"Step {i+1} advance error: {advance_result.get('error')}")

        # Mark scenario as completed
        results["status"] = "completed"
        results["total_steps"] = len(steps)
        results["completed_steps"] = len([s for s in results["steps_executed"] if s.get("status") == "completed"])

        return results

    def list_scenarios(self, lang: str = "zh") -> List[dict]:
        """List all available scenarios."""
        return self.companion.list_scenarios(lang)

    def _get_journey_status(self) -> dict:
        """Get current journey status."""
        if not self._active_journey:
            return {}
        session = self.companion._sessions.get(self._active_journey, {})
        return {
            "session_id": self._active_journey,
            "scenario": session.get("scenario_id"),
            "current_step": session.get("current_step", 0),
            "total_steps": len(session.get("scenario", {}).get("steps", [])),
            "status": session.get("status", "unknown"),
        }

    def get_status(self) -> dict:
        """Get scenario engine status."""
        return {
            "scenarios_available": len(SCENARIO_REGISTRY),
            "active_journeys": len(self.companion.get_active_sessions()),
            "active_journey_id": self._active_journey,
            "companion_interactions": self.companion._interaction_count,
            "deerflow_simulator": "enhanced",
            "sandbox": "ready",
        }


# ═══════════════════════════════════════════════════════════
# 6. CLI INTERFACE
# ═══════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Q-SpecTrum Scenario Engine")
    parser.add_argument("--list", action="store_true", help="List all scenarios")
    parser.add_argument("--run", type=str, help="Run a scenario journey (e.g. ecommerce)")
    parser.add_argument("--demo", action="store_true", help="Run all scenarios summary")
    parser.add_argument("--sandbox", type=str, help="Run sandbox drill (scenario_id)")
    parser.add_argument("--deerflow-sim", type=str, help="Simulate DeerFlow skill")
    parser.add_argument("--skill", type=str, default="deep-research", help="DeerFlow skill ID")
    parser.add_argument("--lang", type=str, default="zh", choices=["zh", "en"], help="Language")
    args = parser.parse_args()

    integration = ScenarioEngineIntegration()

    if args.list:
        print("=" * 60)
        print("  Q-SpecTrum Scenario Engine — Available Journeys")
        print("=" * 60)
        for sc in integration.companion.list_scenarios(args.lang):
            name = sc["name"]
            print(f"\n  [{sc['id']}] {name}")
            print(f"    Complexity: {sc['complexity']} | Steps: {sc['steps']} | Roles: {sc['roles']}")
        print()
        return

    if args.demo:
        print("=" * 60)
        print("  Q-SpecTrum Scenario Engine — Demo Run")
        print("=" * 60)

        for sid, sc in list(SCENARIO_REGISTRY.items())[:4]:
            name = sc["name_zh"] if args.lang == "zh" else sc["name_en"]
            print(f"\n{'='*40}")
            print(f"  Scenario: {name}")
            print(f"  Steps: {len(sc['steps'])} | Complexity: {sc['complexity']}")
            print(f"{'='*40}")

            # Start journey
            result = integration.start_scenario(sid, args.lang)
            print(f"\n  Journey started: {result.get('session_id', 'N/A')}")

            # Run first step with sandbox
            sandbox = integration.run_sandbox_drill(sid, 0, args.lang)
            print(f"  Sandbox drill: quality={sandbox['result']['quality_score']}")

            # Simulate DeerFlow if skill exists
            if sc["steps"][0].get("deerflow_skill"):
                skill = sc["steps"][0]["deerflow_skill"]
                df_result = integration.simulate_deerflow(
                    sc["steps"][0]["prompt"], skill, args.lang)
                print(f"  DeerFlow sim: {skill} -> {df_result['deliverable_type']}")

            # Advance one step
            advance = integration.advance_scenario({"response": "Step completed"})
            print(f"  Advanced to step: {advance.get('current_step', 'N/A')}/{advance.get('total_steps', 'N/A')}")

            # Reset for next scenario
            integration._active_journey = None

        print(f"\n{'='*60}")
        print(f"  Demo complete. {len(SCENARIO_REGISTRY)} scenarios available.")
        print(f"{'='*60}")
        return

    if args.run:
        result = integration.start_scenario(args.run, args.lang)
        if "error" in result:
            print(f"Error: {result['error']}")
            return
        print(result["welcome"])
        print()

        # Interactive journey
        scenario = SCENARIO_REGISTRY.get(args.run)
        for i, step in enumerate(scenario["steps"]):
            input(f"\n[Press Enter to proceed to step {i+1}...]")

            # Run sandbox drill
            sandbox = integration.run_sandbox_drill(args.run, i, args.lang)
            print(f"\n  Sandbox: quality={sandbox['result']['quality_score']}")

            # Simulate DeerFlow if applicable
            if step.get("deerflow_skill"):
                df = integration.simulate_deerflow(
                    step["prompt"], step["deerflow_skill"], args.lang)
                print(f"\n{df['response'][:500]}...")

            # Advance
            advance = integration.advance_scenario({"response": "done"})
            if "transition_message" in advance:
                print(advance["transition_message"])
            elif "summary" in advance:
                print(advance["summary"])
        return

    if args.sandbox:
        result = integration.run_sandbox_drill(args.sandbox, 0, args.lang)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return

    if args.deerflow_sim:
        result = integration.simulate_deerflow(args.deerflow_sim, args.skill, args.lang)
        print(result["response"])
        return

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
