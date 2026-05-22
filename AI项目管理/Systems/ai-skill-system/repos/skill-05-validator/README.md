# Skill 05 · Validator — AI 项目测试验收工程师

> **核心职责**：执行五维度验收测试，生成客观发布决策报告

[![Version](https://img.shields.io/badge/version-v1.0.0-blue)](CHANGELOG.md)
[![System](https://img.shields.io/badge/system-v1.0-green)](../ai-skill-system/system/MASTER-BLUEPRINT.md)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

---

## 概述

Skill 05 · Validator 是六层 AI Skill 体系的**最后一道质量门禁**。接收来自 Skill 04 或 Skill 02 的工程交付物，执行系统性验收测试，给出 PASS / CONDITIONAL_PASS / FAIL 决策。

**Validator 不开发功能，不修复代码** — 它只负责发现缺陷、评估质量、推动修复。

---

## 五维度验收体系

| 维度 | 权重 | 核心问题 |
|------|------|---------|
| 功能完整性 | 40% | 是否实现了全部承诺功能？ |
| 文档完整性 | 25% | 文档是否足以让人理解和使用？ |
| 可执行性 | 20% | 用户能否按文档独立完成项目？ |
| 接口规范性 | 10% | 交接包是否符合体系契约 v1.0？ |
| 安全性 | 5% | 是否存在安全风险？ |

---

## 发布决策规则

```
PASS              P0=0, P1=0,  综合 ≥ 80%
CONDITIONAL_PASS  P0=0, P1≤3,  综合 ≥ 70%
FAIL              P0≥1  OR  (P1>3 AND 综合 < 70%)
```

---

## 缺陷优先级

| 级别 | 名称 | 典型例子 | 发布影响 |
|------|------|---------|---------|
| P0 | 阻塞级 | 硬编码API Key、核心功能完全缺失 | 立即 FAIL |
| P1 | 严重级 | 关键步骤无验证方式、环境配置缺失 | 超3个则 FAIL |
| P2 | 一般级 | FAQ 不足、估时无标注 | 不阻塞，建议修复 |
| P3 | 轻微级 | 格式不统一、命名不规范 | 记录改进 |

---

## 飞轮机制

每次验收完成后，Validator 输出**体系改进建议**：

- 发现缺陷模式 → 追溯到产生该缺陷的上游 Skill
- 建议在对应 Skill 的规则/模板中增加防护
- 驱动整个体系持续自我改进

---

## 文件结构

```
skill-05-validator/
├── SKILL.md                           # Skill 元信息
├── README.md                          # 本文件
├── LICENSE                            # MIT License
├── core/
│   ├── system-prompt-full.md          # 完整系统提示词（含报告模板）
│   └── system-prompt-lite.md          # 精简版
├── sub-skills/
│   ├── 01-material-receiver.md        # 验收材料接收器
│   ├── 02-validation-engine.md        # 五维度验收引擎
│   ├── 03-defect-reporter.md          # 缺陷分类与报告生成器
│   └── 04-release-decision.md         # 发布决策与交接包输出
└── deploy/
    └── deploy-universal.md            # 跨平台部署指南
```

---

## 快速开始

1. 将 `core/system-prompt-full.md` 设为系统提示词
2. 粘贴来自 Skill 04 的交接包（或 Skill 02 的 SOP 交接包）
3. 等待五维度验收完成
4. 接收 PASS / CONDITIONAL_PASS / FAIL 决策报告

---

## 体系位置

```
[整个执行链路]
Skill 01 → Skill 03 → Skill 02 → Skill 04
                                      │
                                      ▼
                              Skill 05（验收）
                                      │
                     ┌────────────────┼────────────────┐
                     ▼                ▼                ▼
                   PASS          COND_PASS            FAIL
                   发布           修复后复验          路由回修复Skill
```

---

## License

MIT © letplaylimited-MARK
