# 端到端核心链路集成测试设计

> **日期**: 2026-05-19
> **目标**: 验证 Q-SpecTrum 核心链路真正工作，而非仅验证"能启动不崩溃"
> **方法**: 方案 A（行为断言）+ 方案 B（场景集成）组合

---

## 1. 问题陈述

当前 132 个测试验证的是**结构完整性**（模块能 import、DB 能连接、API 能回应），但没有验证**行为质量**：
- Secretary 路由是否准确？
- 知识检索是否返回相关内容？
- Dual-Loop 切换是否正确？
- 记忆持久化是否工作？
- 优雅降级是否有效？

## 2. 核心链路定义

Q-SpecTrum 的核心处理链路：
```
用户输入 → Secretary 路由 → HybridModeRouter 模式选择 → KnowledgeOrchestrator 检索 → LLM 生成 → KnowledgeCrystallizer 结晶 → 响应输出
```

## 3. 测试架构

```
tests/
├── conftest.py                      # 现有 fixtures + 新增 Mock fixtures
├── test_qspectrum_engine.py         # 现有 (12 tests) — 不修改
├── test_core_modules.py             # 现有 (33 tests) — 不修改
├── test_e2e_core_pipeline.py        # 新增：8 个链路行为断言测试
└── test_e2e_scenarios.py            # 新增：6 个场景集成测试
```

## 4. 测试用例详细设计

### 4.1 行为断言测试 (test_e2e_core_pipeline.py) — 8 个测试

| # | 测试名 | 输入 | 验证点 |
|---|--------|------|--------|
| 1 | `test_simple_query_inner_loop` | "你好，帮我写个 Python 函数" | 路由→Q03, 模式→orchestrator, 有响应, 元数据完整 |
| 2 | `test_complex_query_triggers_peer_mode` | "深度分析：如何设计一个支持 10 万并发的微服务架构？" | 路由→Q01, 模式→peer, 协作≥3 轮, 结晶≥1 决策 |
| 3 | `test_cross_domain_query_negotiation` | "这个项目的技术债务如何影响安全架构？" | 路由→T04, 多源检索≥2, 响应包含安全+技术债务 |
| 4 | `test_security_sensitive_query` | "这个系统有什么安全风险？如何防护？" | 路由→Q06, confidence>0.7, 响应含威胁列表 |
| 5 | `test_ambiguous_mixed_input` | "我想做个东西，类似 shopify 但更简单，怎么开始？" | 路由→Q01(默认), 不崩溃, 响应含引导性内容 |
| 6 | `test_knowledge_retrieval_quality` | "角色路由机制" | 检索源≥2, 分数>0, 内容含路由关键词 |
| 7 | `test_memory_persistence` | "测试记忆功能" | 结晶器存在, MEMORY.md 存在, _HANDOFF 存在 |
| 8 | `test_graceful_degradation` | "测试降级" | 缺失组件时仍有响应, 元数据标明降级 |

### 4.2 场景集成测试 (test_e2e_scenarios.py) — 6 个测试

| # | 场景 | 输入 | 验证点 |
|---|------|------|--------|
| 1 | 架构设计 | "如何设计微服务架构？" | 路由→Q01, 检索→graph+vector, 响应→结构化 |
| 2 | 内容创作 | "写一篇关于 AI 的文章" | 路由→Q03, 模式→orchestrator, 响应→文章格式 |
| 3 | 数据分析 | "分析这个项目的技术趋势" | 路由→Q04, 检索→sqlite+memory, 响应→数据驱动 |
| 4 | 安全审计 | "系统有什么安全风险？" | 路由→Q06, 风险触发, 响应→威胁列表 |
| 5 | 平台战略 | "平台未来三年发展方向" | 路由→T01/T04, 模式→peer, 响应→战略规划 |
| 6 | 模糊请求 | "帮我做点什么有用的" | 路由→Q01(默认), 不崩溃, 响应→引导式 |

## 5. Mock 策略

- 使用 Mock LLM provider（避免真实 API 调用）
- Mock 响应格式：`[Mock Response] 针对：{user_message[:50]}...`
- 保留真实 Secretary、KnowledgeOrchestrator、HybridModeRouter 逻辑
- 组件失败时验证优雅降级

## 6. 验证标准

| 测试类型 | 通过标准 | 超时 | CI 集成 |
|---------|---------|------|---------|
| 行为断言 (A) | 所有 assert 通过 | <30 秒 | 每次 commit |
| 场景集成 (B) | 6 场景全部通过 | <5 分钟 | PR 时运行 |

## 7. 与现有测试关系

- 不修改现有测试
- 新增 14 个测试（8 链路 + 6 场景）
- 总计：132 + 14 = 146 个测试

## 8. 实现顺序

1. 更新 `conftest.py` — 新增 Mock fixtures
2. 创建 `test_e2e_core_pipeline.py` — 8 个链路测试
3. 创建 `test_e2e_scenarios.py` — 6 个场景测试
4. 运行验证 — `pytest tests/test_e2e_*.py -v`
5. 修复失败测试 — 调整断言或修复引擎 bug
6. 更新 CI — 确保新测试纳入 GitHub Actions
