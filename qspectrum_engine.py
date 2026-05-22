"""
Q-SpecTrum Unified Engine v1.0
================================
THE SINGLE ENTRY POINT that ties everything together.

This is not a framework. This is the REAL pipeline:
  User Input → Secretary Routing → Role Selection → DB Context → LLM Call → Response

Usage:
  python qspectrum_engine.py                     # Interactive chat
  python qspectrum_engine.py --demo              # Run demo scenarios
  python qspectrum_engine.py --query "你的问题"   # Single query

LLM Modes (set via env or --provider):
  QSPECTRUM_LLM=mock      Mock responses (default, always works)
  QSPECTRUM_LLM=openai    OpenAI API (needs OPENAI_API_KEY)
  QSPECTRUM_LLM=anthropic Anthropic API (needs ANTHROPIC_API_KEY)
  QSPECTRUM_LLM=ollama    Local Ollama (needs ollama running)

Architecture:
  ┌─────────┐   ┌───────────┐   ┌────────────┐   ┌─────┐
  │  User   │──▶│ Secretary │──▶│ Role Engine │──▶│ LLM │
  │  Input  │   │ (Router)  │   │ (from DB)  │   │     │
  └─────────┘   └───────────┘   └────────────┘   └──┬──┘
                                                     │
  ┌─────────┐   ┌───────────┐   ┌────────────┐      │
  │Response │◀──│ Knowledge │◀──│  Protocol  │◀─────┘
  │         │   │ Crystalize│   │  Executor  │
  └─────────┘   └───────────┘   └────────────┘
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# brain_core — extracted modular components (Phase 1)
try:
    from brain_core.config import detect_writable_dir, find_db_path
    from brain_core.graph import GraphEngine
    _HAS_BRAIN_CORE = True
except ImportError:
    _HAS_BRAIN_CORE = False

# Dual-Loop Brain Architecture (Phase 1-2)
try:
    from brain_core.knowledge_orchestrator import UniversalKnowledgeOrchestrator
    _HAS_KNOWLEDGE_ORCHESTRATOR = True
except ImportError:
    _HAS_KNOWLEDGE_ORCHESTRATOR = False

try:
    from brain_core.hybrid_router import HybridModeRouter
    _HAS_HYBRID_ROUTER = True
except ImportError:
    _HAS_HYBRID_ROUTER = False

try:
    from brain_core.peer_collaboration import PeerCollaborationEngine
    _HAS_PEER_COLLABORATION = True
except ImportError:
    _HAS_PEER_COLLABORATION = False

try:
    from brain_core.skill_orchestrator import SkillOrchestrator
    _HAS_SKILL_ORCHESTRATOR = True
except ImportError:
    _HAS_SKILL_ORCHESTRATOR = False

try:
    from brain_core.knowledge_crystallizer import KnowledgeCrystallizer
    _HAS_KNOWLEDGE_CRYSTALLIZER = True
except ImportError:
    _HAS_KNOWLEDGE_CRYSTALLIZER = False

# Auto-load .env (if present) so OPENAI_API_KEY etc. are visible.
# Zero-dependency, shell env still wins over file values.
try:
    from env_loader import load_env as _qsp_load_env
    _qsp_load_env()
except Exception:
    pass

# Negotiation Engine — multi-role collaboration
try:
    from negotiation_engine import NegotiationEngine
    _HAS_NEGOTIATION = True
except ImportError:
    _HAS_NEGOTIATION = False

# Project Memory Isolation — multi-project chatroom switching (Point #19)
try:
    from project_memory import ChatroomSessionController, ProjectMemoryManager
    _HAS_PROJECT_MEMORY = True
except ImportError:
    _HAS_PROJECT_MEMORY = False

# Global Search Engine — cross-project/knowledge/skills search (Point #18)
try:
    from global_search import GlobalSearchEngine
    _HAS_GLOBAL_SEARCH = True
except ImportError:
    _HAS_GLOBAL_SEARCH = False

# YAML Pluggable Role Configuration (Point #15)
try:
    from role_config import YAMLRoleLoader
    _HAS_ROLE_CONFIG = True
except ImportError:
    _HAS_ROLE_CONFIG = False

# Contact Channel — customer service & developer contact (Point #20)
try:
    from contact_channel import ContactChannel
    _HAS_CONTACT = True
except ImportError:
    _HAS_CONTACT = False

# Task Manager — visual task/workflow management (Point #10)
try:
    from task_manager import TaskManager
    _HAS_TASK_MANAGER = True
except ImportError:
    _HAS_TASK_MANAGER = False

# Scenario Engine — diverse user journeys + AI companionship (Point #7, #8)
try:
    from scenario_engine import DeerFlowEnhancedSimulator, ScenarioEngineIntegration
    _HAS_SCENARIO_ENGINE = True
except ImportError:
    _HAS_SCENARIO_ENGINE = False

# ═══════════════════════════════════════════════════════════
# 1. DATABASE LAYER — Read roles, protocols, workflows from DB
# ═══════════════════════════════════════════════════════════

class QSpectrumDB:
    """Immutable read-only access to platform.db."""

    def __init__(self, db_path=None):
        if db_path is None:
            base = Path(__file__).parent / "AI项目管理" / "Platform" / "db"
            for candidate in ["platform.db", "platform_restored.db", "platform_v4.1.db"]:
                p = base / candidate
                if p.exists() and p.stat().st_size > 0:
                    db_path = p
                    break
            if db_path is None:
                raise FileNotFoundError("No usable platform.db found")

        uri = f"file:{Path(db_path).resolve()}?immutable=1"
        self.conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._roles = {}
        self._protocols = {}
        self._custom_roles = {}  # YAML-loaded custom roles (Point #15)
        self._load_all()

    def _load_all(self):
        # Load roles
        for row in self.conn.execute("SELECT * FROM ai_roles ORDER BY role_code"):
            r = dict(row)
            # Parse capabilities from JSON string
            caps = r.get("capabilities", "")
            if isinstance(caps, str):
                try:
                    r["capabilities_list"] = json.loads(caps)
                except (json.JSONDecodeError, TypeError):
                    r["capabilities_list"] = [c.strip() for c in caps.split(",") if c.strip()]
            self._roles[r["role_code"]] = r

        # Load protocols
        for row in self.conn.execute("SELECT * FROM collaboration_protocols ORDER BY protocol_code"):
            self._protocols[dict(row)["protocol_code"]] = dict(row)

    def get_role(self, code):
        return self._roles.get(code) or self._custom_roles.get(code)

    def get_all_roles(self):
        merged = dict(self._roles)
        merged.update(self._custom_roles)
        return merged

    def get_roles_by_family(self, family):
        return {k: v for k, v in self._roles.items() if v.get("family") == family}

    def get_protocol(self, code):
        return self._protocols.get(code)

    def get_all_protocols(self):
        return dict(self._protocols)

    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def close(self):
        self.conn.close()


# ═══════════════════════════════════════════════════════════
# 2. SECRETARY — The routing brain
# ═══════════════════════════════════════════════════════════

class Secretary:
    """
    Five-Dimensional Radar Scanner + Role Router.
    Routes user requests to the best-fit role from the DB.

    Keywords are loaded from routing_keywords.json (extracted for maintainability).
    To edit routing behavior, modify the JSON file instead of this code.
    """

    # ─── Load keywords from external JSON (or fallback to minimal inline set) ───
    _KEYWORDS_LOADED = False

    @classmethod
    def _load_keywords(cls):
        """Load routing keywords from routing_keywords.json (once)."""
        if cls._KEYWORDS_LOADED:
            return
        json_path = Path(__file__).parent / "routing_keywords.json"
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    kw = json.load(f)
                cls.TRUM_KEYWORDS = kw.get("trum_keywords", cls.TRUM_KEYWORDS)
                cls.SPEC_KEYWORDS = kw.get("spec_keywords", cls.SPEC_KEYWORDS)
                cls.CAPABILITY_KEYWORDS = kw.get("capability_keywords", cls.CAPABILITY_KEYWORDS)
                weights = kw.get("f21_weights", {})
                cls.F21_W_RELEVANCE = weights.get("relevance", cls.F21_W_RELEVANCE)
                cls.F21_W_AFFINITY = weights.get("affinity", cls.F21_W_AFFINITY)
                cls.F21_W_COST = weights.get("cost", cls.F21_W_COST)
                cls.F21_W_KNOWLEDGE = weights.get("knowledge", cls.F21_W_KNOWLEDGE)
                cls._KEYWORDS_LOADED = True
                return
            except Exception:
                pass  # Fall through to inline defaults
        cls._KEYWORDS_LOADED = True

    # ─── Minimal inline fallback (full set lives in routing_keywords.json) ───
    TRUM_KEYWORDS = [
        "平台", "戰略", "战略", "全局", "strategy", "strategic", "platform", "cross-project",
        "重大決策", "重大决策", "跨族", "治理", "governance",
        "platform strategy", "跨項目", "跨项目", "平台級", "平台级", "cross-team",
        "規劃", "规划", "plan", "planning", "sprint", "迭代", "運營", "运营", "管理",
        "協調", "协调", "coordinate", "coordination", "技能體系", "技能体系", "skill system",
        "里程碑", "milestone", "分工", "团队分工", "團隊分工",
        "预算", "預算", "budget", "资源分配", "資源分配", "resource allocation",
        "team performance", "direction", "roadmap", "priority", "priorities",
        "okr", "objective", "kpi target", "quarterly", "annual",
        # T01 Sovereign keywords (strategic decision-making)
        "決策", "决策", "vision", "願景", "愿景", "企業級", "企业级", "executive",
        "方向", "direction", "戰略方向", "战略方向", "戰略規劃", "战略规划",
        # T02 Operations keywords (operational execution/efficiency)
        "效率", "效率", "流程", "流程優化", "流程优化", "process", "CI/CD", "自動化", "自动化",
        "運維", "运维", "部署", "deployment",
        # T03 Liaison keywords (external relations/investor/customer)
        "客戶", "客户", "customer", "投資", "投资", "investor", "對外", "对外", "external",
        "合作", "collaboration", "partnership", "商務", "商务", "business",
        # T04 Evolution keywords (technical debt/refactoring/migration)
        "技術債務", "技术债务", "tech debt", "演進", "演进", "重構", "重构", "refactor",
        "升級", "升级", "upgrade", "遷移", "迁移", "migration",
    ]
    # NOTE: "風險預警"/"风险预警" removed from TRUM_KEYWORDS.
    # Risk detection/assessment is QCM execution (ROLE-Q06 Risk Officer).
    # Only cross-project/platform-level strategic risk goes to Trum.
    SPEC_KEYWORDS = [
        "標準", "标准", "合規審計", "合规审计", "配置", "路徑", "路径", "schema", "migration",
        "standard", "數據庫設計", "数据库设计", "規範", "规范", "母盤", "母盘",
        "schema governance", "path audit",
        "數據庫", "数据库", "database", "表結構", "表结构", "DDL", "SQL",
        "validate", "驗證", "验证", "template", "模板", "consistency", "一致性",
        "運行狀態", "运行状态", "运维", "運維", "系统状态", "系統狀態",
        "index", "indexes", "optimize", "devops", "ops",
        # S01 Architect keywords (system architecture/distributed/scalability)
        "架構設計", "架构设计", "架構", "架构", "分佈式", "分布式", "distributed",
        "高可用", "可擴展", "可扩展", "scalable", "系統設計", "系统设计",
        # S02 Guardian keywords (standards/best practices/code review)
        "最佳實踐", "最佳实践", "best practice", "代碼審查", "代码审查", "code review",
        "規範", "规范", "convention", "風格", "风格",
        # S03 Auditor keywords (audit/performance/data integrity/indexing)
        "性能", "performance", "索引", "index",
        "數據完整性", "数据完整性", "data integrity",
    ]
    # NOTE: "架構"/"architecture"/"設計"/"design" removed from SPEC_KEYWORDS
    # because they cause routing conflicts with QCM Chief Architect.
    # These go to QCM first; if Spec validation is needed, the system adds it.

    # Capability → keyword mapping for fine-grained role matching
    CAPABILITY_KEYWORDS = {
        "system_design": ["設計", "设计", "架構", "架构", "design", "architecture",
                          "模塊", "模块", "module", "微服務", "微服务", "microservice",
                          "遷移", "迁移", "重構", "重构", "refactor",
                          "工作流", "workflow", "自动化", "自動化", "automation",
                          "审核", "審核", "流程", "分佈式", "分布式", "distributed",
                          "高可用", "可擴展", "可扩展", "scalable", "並發", "并发"],
        "tech_selection": ["技術選型", "技术选型", "tech", "selection", "framework",
                          "工具", "技術棧", "技术栈", "tech stack", "選型", "选型"],
        "knowledge_retrieval": ["研究", "調研", "调研", "research", "文獻", "文献",
                               "分析報告", "分析报告", "best practice", "最佳實踐", "最佳实践",
                               "調查", "调查", "investigate", "市場", "市场", "market",
                               "比較", "比较", "compare", "搜索", "搜尋", "搜寻",
                               "開源", "开源", "open source", "github", "開源項目",
                               "竞品", "競品", "用户画像", "用戶畫像",
                               # S063-R3: Clinical/guideline/latest retrieval (Q02 Researcher)
                               "指南", "guideline", "guidelines",
                               "临床", "臨床", "clinical",
                               "最新", "latest", "newest", "recent",
                               "总结", "總結", "summarize", "总结最新",
                               "找论文", "找文獻", "找文献", "find paper",
                               "查找", "找到", "look up"],
        "literature_analysis": ["論文", "论文", "paper", "文獻", "文献", "literature", "學術", "学术"],
        "content_generation": ["寫", "写", "創作", "创作", "write", "create",
                              "文檔", "文档", "document", "報告", "报告", "draft",
                              "撰寫", "撰写", "生成", "generate", "blog", "博客", "文章",
                              "PPT", "ppt", "簡報", "简报", "演示", "presentation", "幻燈片", "幻灯片",
                              "介紹", "介绍", "产品", "產品", "方案", "proposal",
                              "邮件", "郵件", "email", "摘要", "summary", "翻译", "翻譯",
                              "文案", "copywriting", "稿件", "通訊", "通讯", "newsletter",
                              # S063-R2: short-video / script / screenplay content types
                              "脚本", "腳本", "script", "剧本", "劇本", "screenplay",
                              "短视频", "短視頻", "short video", "video script",
                              "视频脚本", "視頻腳本",
                              # S063-R2: Q&A paper, exam, lesson/course materials
                              "考题", "考題", "exam", "试卷", "試卷", "test paper",
                              "教案", "lesson plan", "讲稿", "講稿",
                              # S067: curriculum / course-outline content creation
                              # (P26 teacher-curriculum was losing to Q08
                              # Companion+ because "课程" matched learning_paths
                              # while Q03 had no curriculum-design vocabulary.)
                              "课程大纲", "課程大綱", "syllabus", "course outline",
                              "课堂活动", "課堂活動", "class activity",
                              "教学大纲", "教學大綱", "teaching outline",
                              "课程设计", "課程設計", "curriculum design",
                              "课程安排", "課程安排", "course schedule",
                              "每周目标", "每週目標", "weekly objective",
                              # S063-R2: intent letter / agreement wording
                              "意向书", "意向書", "letter of intent",
                              "合同", "合約", "合约", "contract", "agreement",
                              "协议", "協議", "保密协议", "保密協議", "NDA",
                              "声明", "聲明", "declaration",
                              "备忘录", "備忘錄", "memo"],
        "creative_output": ["創意", "创意", "creative", "設計方案", "设计方案",
                           "brainstorm", "原型", "prototype",
                           # S063-R3: Campaign/activity planning (Q03 Creator)
                           "活动规划", "活動規劃", "campaign plan",
                           "促销活动", "促銷活動", "promotion campaign",
                           "营销活动", "營銷活動", "marketing campaign",
                           "周年庆", "週年慶", "anniversary celebration",
                           "发布活动", "發布活動", "launch event",
                           # S063-R3 adversarial: business review deck / QBR (Q03)
                           "deck", "review deck", "qbr", "board deck",
                           "business review", "qbr deck", "投资人路演", "投資人路演"],
        "data_insight": ["數據", "数据", "data", "分析", "analysis", "趨勢", "趋势",
                        "trend", "KPI", "metrics", "指標", "指标", "統計", "统计",
                        "dashboard", "瓶頸", "瓶颈", "bottleneck", "timeline",
                        "時間線", "时间线", "進度", "进度", "盤點", "盘点",
                        "體檢", "体检", "健康度", "营销策略", "營銷策略",
                        "营收", "營收", "季度", "Q1", "Q2", "Q3", "Q4",
                        # S063-R3: user behavior / activity data (Q04 Analyst)
                        "用户行为", "用戶行為", "user behavior", "行为数据", "行為數據",
                        "behavior data", "用户数据", "用戶數據", "解读",
                        "漏斗", "funnel", "conversion", "转化率", "轉化率",
                        "流量", "traffic", "留存", "retention",
                        # S063-R3: small-business ops data (T02 crossover OK)
                        "库存", "庫存", "inventory", "收银", "收銀", "POS",
                        "门店", "門店", "store operations",
                        # S066: financial-analyst vocabulary (Q04 Analyst)
                        "burn rate", "burn-rate", "burn_rate", "燃烧率",
                        "runway", "cash runway", "现金跑道", "現金跑道",
                        "再融资", "再融資", "refinance", "funding round",
                        "ARR", "arr", "MRR", "mrr", "LTV", "ltv", "CAC",
                        "净利润", "淨利潤", "net profit", "毛利率", "毛利",
                        "gross margin", "现金流", "現金流", "cash flow",
                        "流失率", "churn rate", "续费率", "續費率",
                        "renewal rate", "nps", "NPS", "cohort", "队列分析",
                        "貢獻率", "贡献率", "contribution margin",
                        "使用率", "utilization", "活跃度", "活躍度"],
        "trend_analysis": ["趨勢", "趋势", "trend", "forecast", "預測", "预测",
                          "季度", "quarter", "预算", "預算", "budget"],
        "ux_optimization": ["用戶", "用户", "體驗", "体验", "ux", "ui",
                           "界面", "interface", "用戶體驗", "用户体验",
                           "user experience", "可用性", "usability",
                           "布局", "layout", "友好", "交互", "互動",
                           "wireframe", "mockup", "原型图", "原型圖",
                           # S063-R3: Process/flow optimization (Q05 UX Lead)
                           "流程优化", "流程優化", "process optimization",
                           "优化流程", "優化流程", "optimize process",
                           "业务流程", "業務流程", "business process"],
        "threat_detection": ["安全", "風險", "风险", "風險點", "风险点",
                            "security", "risk", "審計", "审计", "audit",
                            "vulnerability", "漏洞", "威脅", "威胁", "threat",
                            "評估風險", "评估风险", "assessment", "launch",
                            "上線", "上线", "風險評估", "风险评估", "安全評估",
                            "合规", "合規", "質量", "质量", "quality",
                            "优化", "優化", "检查", "檢查", "PCI-DSS", "pci-dss",
                            "合規性", "合规性", "compliance",
                            # S063-R3: contract clause risk (Q06 Risk Auditor, not Q03 Creator)
                            "合同条款", "合約條款", "contract clause",
                            "条款风险", "條款風險", "clause risk",
                            "合同风险", "合同風險", "contract risk",
                            "条款", "條款", "terms",
                            # S063-R3 adversarial: credential exfil / injection → Q06
                            "credential", "credentials", "secret", "secrets",
                            "api key", "api keys", "password", "token",
                            "dump all", "dump secrets", "exfiltrate",
                            "admin mode", "sudo", "root access",
                            "bypass security", "reveal all",
                            # S067: Threat-modeling / STRIDE vocabulary (P29).
                            # Long keywords get higher weight (weight = 1 + min(1.5, len/4)),
                            # so "威胁建模" (len 4 → weight 2.0) outweighs Q04's "数据"
                            # (len 2 → weight 1.5) for a STRIDE query that has both terms.
                            "stride", "威胁建模", "威脅建模",
                            "threat model", "threat modeling", "threat modelling",
                            "attack surface", "攻击面", "攻擊面",
                            "安全风险分析", "安全風險分析",
                            "数据隔离", "數據隔離", "data isolation",
                            "多租户安全", "多租戶安全", "tenant isolation"],
        # S066 FIX: Q07 emotional_support narrowed to true emotional-anchor
        # vocabulary. Removed overly generic words (使用/了解/introduce/guide/
        # tutorial/what is/how do i/explain/怎么/怎麼/帮助/幫助/help/教我)
        # that were incidentally matching operational queries (P16 文献综述,
        # P17 React perf, P20 使用率, P21 burn rate, P22 改写文档, P23 测试矩阵)
        # and siphoning them into the AI Companion role. Those generic help
        # intents now correctly route via family defaults to Q03 Creator.
        "emotional_support": ["聊聊天", "聊聊", "陪我", "陪陪",
                             "难过", "難過", "开心", "開心",
                             "孤独", "孤獨", "想哭", "痛苦",
                             "沮丧", "沮喪", "委屈", "崩溃", "崩潰"],
        "skill_planning": ["技能", "skill", "規劃", "规划", "plan", "協調", "协调",
                          "里程碑", "milestone", "分工", "团队", "團隊",
                          "戰略", "战略", "路線圖", "路线图", "roadmap", "願景", "愿景", "vision",
                          "企業級", "企业级", "executive", "方向", "決策", "决策"],
        "db_architecture": ["數據庫", "数据库", "database", "SQL",
                           "表結構", "表结构", "table structure",
                           "schema", "DDL", "索引", "index",
                           "SQL查詢", "SQL查询", "SQL query", "数据库查询", "數據庫查詢"],
        "config_consistency": ["配置", "config", "環境", "环境", "environment",
                              "部署", "deploy", "deployment", "production",
                              "運維", "运维", "devops", "CI/CD", "ci/cd", "上線", "上线",
                              "發布", "发布", "release", "运行状态", "運行狀態",
                              "状态", "狀態", "pipeline", "test", "tests", "testing",
                              "unit test", "integration", "server", "hosting"],
        "cross_family_bridge": ["橋接", "桥接", "bridge", "同步", "sync", "協調", "协调"],
        "prompt_engineering": ["prompt", "提示詞", "提示词", "模板", "template"],
        "content_sedimentation": ["沉澱", "沉淀", "記錄", "记录", "日誌", "日志", "log", "歸檔", "归档"],
        "operation_promotion": ["運營", "运营", "推廣", "推广", "operation", "promotion",
                               "投資", "投资", "investor", "客戶", "客户", "customer",
                               "對外", "对外", "external", "合作", "collaboration", "partnership",
                               "商務", "商务", "business",
                               # S063-R3: Demand pool / backlog ops (T02 Operations Director)
                               "需求池", "需求清单", "需求清單", "demand pool", "backlog",
                               "优先级", "優先級", "priority", "prioritize",
                               "迭代池", "待办池", "待辦池",
                               "整理需求", "梳理需求", "安排需求"],
        # Q08 Companion+ capabilities
        "growth_coaching": ["成長", "成长", "growth", "學習", "学习", "learning",
                           "進步", "进步", "progress", "提升", "improve",
                           "職業", "职业", "career", "发展", "發展"],
        "learning_paths": ["學習路線", "学习路线", "learning path", "課程", "课程",
                          "教程", "tutorial", "培訓", "培训", "training"],
        "personalized_guidance": ["個性化", "个性化", "personalized", "定制", "定製",
                                  "建議", "建议", "advice", "推荐", "推薦"],
        "emotional_intelligence": ["情緒", "情绪", "emotion", "情感", "feeling",
                                   "心理", "mental", "壓力", "压力", "stress",
                                   "心情", "焦慮", "焦虑", "anxiety"],
        # Q01 Architect capabilities
        "design_consistency": ["一致性", "consistency", "規範", "规范", "standard",
                              "設計規範", "设计规范", "design system"],
        "architecture_review": ["架構審查", "架构审查", "architecture review",
                               "代碼審查", "代码审查", "code review", "評審", "评审"],
        # Additional missing capabilities
        "information_fusion": ["整合", "integrate", "融合", "fusion", "彙總", "汇总",
                              "綜合", "综合", "synthesize"],
        "interface_design": ["界面設計", "界面设计", "ui design", "介面", "頁面", "页面",
                            "前端", "frontend", "交互設計", "交互设计"],
        "user_growth_guidance": ["成長指導", "成长指导", "用戶成長", "用户成长",
                                "引導", "引导", "onboarding"],
        # Missing Trum role capabilities (ROLE-T01, ROLE-T04)
        "platform_governance": ["平台治理", "平台管理", "governance", "policy",
                               "政策", "決策", "决策", "主权", "sovereignty",
                               "權限", "权限", "permission", "authorization",
                               # S063-R3: Platform-level strategy direction (T01 Sovereign)
                               "战略方向", "戰略方向", "strategy direction",
                               "平台战略", "平台戰略", "platform strategy",
                               "未来三年", "未來三年", "three-year", "3 year strategy",
                               "长期战略", "長期戰略", "long-term strategy",
                               "制定战略", "制定戰略", "set strategy",
                               # S063-R3: Product-line portfolio decisions (T01 Sovereign)
                               "产品线", "產品線", "product line",
                               "业务线", "業務線", "business line",
                               "产品组合", "產品組合", "product portfolio",
                               "砍掉", "kill product", "discontinue product"],
        "emergency_override": ["緊急", "紧急", "emergency", "馬上", "马上", "immediately",
                              "立刻", "urgent", "override", "bypass"],
        "system_audit": ["審計", "审计", "audit", "檢查", "检查", "inspection",
                        "評估", "评估", "assessment", "合規", "合规", "compliance"],
        "evolution_planning": ["演化", "evolution", "規劃", "规划", "路線圖", "路线图",
                              "roadmap", "升級", "升级", "upgrade", "strategy",
                              "下一季度", "next quarter", "technical roadmap",
                              "技術債務", "技术债务", "tech debt", "演進", "演进",
                              "重構", "重构", "refactor", "遷移", "迁移", "migration",
                              # S063-R3: Tech debt short forms + long-term impact (T04)
                              "技术债", "技術債", "technical debt",
                              "系统性技术债", "系統性技術債", "systemic debt",
                              "长期影响", "長期影響", "long-term impact",
                              "长期演化", "長期演化", "long-term evolution"],
        "tech_roadmap": ["路線圖", "路线图", "roadmap", "技術路線", "技术路线",
                        "planning", "策略", "strategy", "演進", "演进"],
        "upgrade_strategy": ["升級策略", "升级策略", "upgrade", "strategy",
                            "遷移", "迁移", "migration", "evolution"],
        "architecture_evolution": ["架構演進", "架构演进", "evolution", "architecture",
                                  "改進", "改进", "improvement", "upgrade",
                                  # S063-R3: T04 Architecture evolution & tech debt impact
                                  "技术债", "技術債", "技术债务", "技術債務",
                                  "tech debt", "technical debt",
                                  "长期影响", "長期影響", "long-term impact"],
        "role_registry": ["角色", "role", "註冊", "注册", "registry", "系統", "系统",
                         "架構師", "架构师", "architect", "角色系統"],
        "protocol_design": ["協議", "协议", "protocol", "設計", "设计", "design",
                           "路由", "routing", "規則", "规则"],
        "context_routing": ["路由", "routing", "上下文", "context", "決策", "决策",
                           "routing logic", "decision"],
        "quality_acceptance": ["驗收", "验收", "acceptance", "質量", "质量", "quality",
                              "檢查", "检查", "審查", "审查", "review"],
        "cross_project_reuse": ["跨項目", "跨项目", "cross-project", "復用", "复用",
                               "reuse", "共享", "share", "組件", "组件"],
        "value_judgment": ["價值判斷", "价值判断", "value", "judgment", "評估", "评估"],
        "system_coordination": ["協調", "协调", "coordination", "系統", "系统",
                               "整合", "整合", "integration", "統一"],
        # Additional spec capabilities
        "path_design": ["路徑設計", "路径设计", "path design", "路徑", "路径", "path"],
        "template_maintenance": ["模板", "template", "維護", "维护", "maintenance"],
        "schema_governance": ["schema", "治理", "governance", "管理", "management"],
        "compliance_audit": ["合規審計", "合规审计", "compliance audit", "合規檢查", "合规检查"],
        "compliance_check": ["合規", "合规", "compliance", "檢查", "检查"],
        "ops_standardization": ["運維標準化", "运维标准化", "ops standard"],
        "deployment_verification": ["部署驗證", "部署验证", "deployment verify"],
        "spec_qcm_sync": ["Spec-QCM同步", "spec qcm sync", "synchronization"],
        "standard_alignment": ["標準對齐", "标准对齐", "standard alignment"],
        "best_practice_review": ["最佳實踐", "最佳实践", "best practice", "代碼審查", "代码审查",
                                "code review", "規範", "规范", "convention", "標準", "标准"],
        "protocol_mediation": ["協議調解", "协议调解", "protocol mediation"],
        # Additional QCM capabilities
        "empathic_interaction": ["同理心", "empathy", "emotional", "interaction"],
        "user_companionship": ["用戶陪伴", "用户陪伴", "companionship", "伴侶"],
        "motivation_coaching": ["激勵教導", "激励教导", "motivation", "coaching"],
        "flywheel_monitoring": ["飛輪監控", "飞轮监控", "flywheel", "monitoring"],
        "kpi_tracking": ["KPI追蹤", "kpi tracking", "metrics"],
        "quality_gate": ["質量門禁", "质量门禁", "quality gate", "quality check"],
        "risk_scoring": ["風險評分", "风险评分", "risk score"],
        "security_assessment": ["安全評估", "安全评估", "security assessment"],
        "sandbox_verification": ["沙盒驗證", "沙盒验证", "sandbox verify"],
        "r_formula_compute": ["R公式計算", "r formula", "knowledge"],
        "s1_s5_progression": ["S1-S5進展", "s1 s5 progression",
                              # S063-R3: Sprint/iteration planning (Q05 UX/Growth)
                              "迭代", "sprint", "迭代计划", "迭代計劃",
                              "版本计划", "版本計劃", "version plan",
                              "下个版本", "下個版本", "next version",
                              "发版", "發版", "release plan", "roadmap"],
        "dynamic_slots_planner": ["動態槽位規劃", "动态槽位规划", "dynamic slots plan"],
        "dynamic_slots_operator": ["動態槽位操作", "动态槽位操作", "dynamic slots"],
        "dynamic_slots_auditor": ["動態槽位審計", "动态槽位审计", "dynamic slots audit"],
        "dynamic_slots_bridge": ["動態槽位橋接", "动态槽位桥接", "dynamic slots bridge"],
        "qcm_bridge_sync": ["QCM橋接同步", "qcm bridge sync"],
        "path_audit": ["路徑審計", "路径审计", "path audit"],
        "system_architecture": ["系統架構", "系统架构", "system architecture"],
        "policy_decisions": ["政策決策", "政策决策", "policy decision"],
        "document_writing": ["文檔撰寫", "文档撰写", "document writing"],
    }

    # ═══════════════════════════════════════════════════════════
    # Formula 21: D(input) = argmax_r [w_rel·Rel + w_aff·Aff + w_cost·(1-Cost) + w_growth·Growth]
    # Multi-factor decision routing with argmax scoring
    # ═══════════════════════════════════════════════════════════
    F21_W_RELEVANCE = 0.45    # Weight for keyword/capability relevance
    F21_W_AFFINITY = 0.25     # Weight for feedback-loop affinity
    F21_W_COST = 0.15         # Weight for inverse cost (prefer lower cost)
    F21_W_KNOWLEDGE = 0.15    # Weight for knowledge depth with role

    def __init__(self, db: QSpectrumDB, feedback_fn=None, knowledge_resonance=None,
                 cost_bridge=None):
        self._load_keywords()  # Load from routing_keywords.json if available
        self.db = db
        self.roles = db.get_all_roles()
        self._feedback_fn = feedback_fn  # Closed-loop affinity function
        self._knowledge = knowledge_resonance  # F21: KnowledgeResonance instance
        self._cost_bridge = cost_bridge  # F21: CostFunctionBridge instance

    def route(self, user_input: str, context: dict = None) -> dict:
        """
        Analyze user input and route to the best role.

        Returns:
            {
                "family": "trum"|"spec"|"qcm",
                "role_code": "ROLE-xxx",
                "role_name": "...",
                "confidence": 0.0-1.0,
                "radar": {...},  # Five-dimension scan
                "reasoning": "..."
            }
        """
        context = context or {}
        text = user_input.lower()

        # Step 1: Five-Dimensional Radar Scan
        radar = self._scan_radar(text, context)

        # Step 2: Family routing
        family = self._route_family(text, radar)

        # Step 3: Role selection within family
        role_code, confidence, reasoning = self._select_role(text, family)

        return {
            "family": family,
            "role_code": role_code,
            "role_name": self.roles.get(role_code, {}).get("role_name", role_code),
            "confidence": confidence,
            "radar": radar,
            "reasoning": reasoning,
        }

    def _scan_radar(self, text, context):
        """Five-Dimensional Radar: Track, Platform, People, Style, Supplement."""
        radar = {}

        # Track: What type of task?
        if any(k in text for k in ["項目", "项目", "project", "任務", "任务", "task",
                                    "工作流", "workflow", "规划", "規劃", "plan",
                                    "管理", "里程碑", "分工"]):
            radar["track"] = "project"
        elif any(k in text for k in ["研究", "research", "調研", "调研", "分析", "analysis",
                                      "竞品", "市场", "市場"]):
            radar["track"] = "research"
        elif any(k in text for k in ["寫", "写", "創作", "创作", "write", "create",
                                      "設計", "设计", "design", "PPT", "ppt"]):
            radar["track"] = "creative"
        elif any(k in text for k in ["數據", "数据", "data", "統計", "统计", "metrics",
                                      "预算", "營收", "营收"]):
            radar["track"] = "analytics"
        else:
            radar["track"] = context.get("track", "general")

        # Platform: Platform-level?
        radar["platform"] = any(k in text for k in self.TRUM_KEYWORDS)

        # People: Cross-team?
        radar["people"] = any(k in text for k in ["跨", "cross", "團隊", "team", "協作", "collaborate"])

        # Style
        if any(k in text for k in ["緊急", "urgent", "馬上", "立刻"]):
            radar["style"] = "urgent"
        elif any(k in text for k in ["正式", "formal", "報告", "report"]):
            radar["style"] = "formal"
        else:
            radar["style"] = "casual"

        # Supplement: complexity score
        word_count = len(text.split())
        radar["complexity"] = min(1.0, word_count / 50)

        return radar

    def _route_family(self, text, radar):
        """Determine which family handles this request.

        Uses weighted scoring across all families, not just keyword threshold.
        Trum: strategic/planning/coordination/management
        Spec: standards/compliance/DBA/schema/governance
        QCM: execution (analysis/research/content/UX/risk/companion)
        """
        # Score each family by keyword matches
        trum_score = sum(1 for k in self.TRUM_KEYWORDS if k in text)
        spec_score = sum(1 for k in self.SPEC_KEYWORDS if k in text)

        # Also score by capability keywords → family mapping
        cap_family_scores = {"trum": 0, "spec": 0, "qcm": 0}
        # S063-R2 Fix: trum_caps was missing several real TRUM capabilities,
        # causing TRUM role keywords (system_audit, value_judgment, system_coordination,
        # tech_roadmap, etc.) to be mis-scored as QCM. Now includes ALL real TRUM caps
        # (see ai_roles.capabilities for T01-T04 in platform.db).
        trum_caps = {
            # T01 Platform Sovereign
            "platform_governance", "policy_decisions", "emergency_override", "system_audit",
            # T02 Operations Director
            "content_sedimentation", "operation_promotion", "value_judgment",
            # T03 System Coordinator
            "skill_planning", "system_coordination", "cross_project_reuse", "quality_acceptance",
            "qcm_bridge_sync", "dynamic_slots_planner", "dynamic_slots_auditor",
            "dynamic_slots_bridge", "dynamic_slots_operator",
            # T04 Evolution Engineer
            "evolution_planning", "tech_roadmap", "upgrade_strategy", "architecture_evolution",
        }
        spec_caps = {
            "db_architecture", "config_consistency", "cross_family_bridge",
            "path_design", "template_maintenance", "schema_governance",
            "compliance_check", "compliance_audit", "ops_standardization", "deployment_verification",
            "spec_qcm_sync", "standard_alignment", "protocol_mediation", "path_audit",
            # NOTE: "system_design" REMOVED from spec_caps — it belongs to Q01 (QCM Chief Architect).
            # system_design keywords ("设计","架构") are too broad and were routing design queries
            # to SPEC instead of QCM. SPEC's architecture role (S01) has "system_architecture"
            # and "db_architecture" which are specific enough.
            "best_practice_review"
        }
        for cap, keywords in self.CAPABILITY_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in text)
            if hits > 0:
                if cap in trum_caps:
                    cap_family_scores["trum"] += hits
                elif cap in spec_caps:
                    cap_family_scores["spec"] += hits
                else:
                    cap_family_scores["qcm"] += hits

        # Combine keyword + capability scores
        final_scores = {
            "trum": trum_score + cap_family_scores["trum"],
            "spec": spec_score + cap_family_scores["spec"],
            "qcm": cap_family_scores["qcm"],
        }

        # Strong single indicators
        if any(k in text for k in ["跨項目", "跨项目", "平台級", "平台级",
                                    "cross-project", "platform strategy"]):
            final_scores["trum"] += 3

        # Tech debt/evolution is explicitly TRUM (T04 Evolution role)
        # S063 R2 Fix: add shorter forms "技术债"/"技術債" (without 务/務) to catch variants
        tech_debt = ["技術債務", "技术债务", "技術債", "技术债", "tech debt", "technical debt",
                     "演進", "演进", "重構", "重构", "refactor",
                     "升級", "升级", "遷移", "迁移"]
        if any(td in text for td in tech_debt):
            final_scores["trum"] += 3

        # Content creation override: if user wants to "write/create" something,
        # that's QCM execution even if topic matches Trum keywords.
        # e.g. "写推广文案" is QCM content, not Trum operations.
        content_verbs = ["寫", "写", "創作", "创作", "write", "create",
                         "文案", "draft", "撰寫", "撰写", "生成",
                         "准备一份", "準備一份", "起草", "起草一份"]
        has_content_verb = any(v in text for v in content_verbs)
        if has_content_verb:
            final_scores["qcm"] += 4
            # When content verbs co-occur with TRUM topics (tech debt, strategy etc),
            # the user ACTION is "writing about X" → QCM content creation, not TRUM planning.
            # Suppress TRUM tech_debt boost entirely so QCM's content creation intent prevails.
            if any(td in text for td in tech_debt):
                final_scores["trum"] -= 3

        # Content/campaign planning override: "规划/策划/制定" + content/campaign artifact
        # is QCM content creation (not TRUM skill_planning).
        # e.g. "规划营销日历", "策划周年庆活动", "制定内容营销方案" → QCM
        content_artifacts = ["营销", "營銷", "marketing", "内容", "內容", "content",
                             "日历", "日曆", "calendar", "活动", "活動", "campaign",
                             "促销", "促銷", "promotion", "发布", "發布", "launch",
                             "博客", "blog", "文章", "article", "PRD", "prd",
                             "版本", "version", "迭代", "iteration", "sprint",
                             "培训", "培訓", "training program",
                             "教学", "教學", "教案", "lesson plan",
                             "演示", "demo", "presentation",
                             # S066 FIX: growth/marketing/GTM artifacts that were
                             # being siphoned to SPEC via "上线" (config_consistency)
                             # false positives (see P14 growth-marketer persona).
                             "获客", "獲客", "cold start", "冷启动", "冷啟動",
                             "acquisition", "gtm", "go-to-market",
                             "funnel", "漏斗", "增长", "增長", "growth",
                             "conversion", "转化", "轉化"]
        planning_verbs = ["规划", "規劃", "策划", "策劃", "制定",
                          "plan", "计划", "計劃", "organize",
                          # S066 FIX: "设计一个方案/计划" is a content-plan verb
                          # for GTM work, not SPEC architecture design.
                          "设计一个", "設計一個", "设计一套", "設計一套",
                          "设计方案", "設計方案"]
        has_content_artifact = any(ca in text for ca in content_artifacts)
        has_planning_verb = any(pv in text for pv in planning_verbs)
        if has_content_artifact and has_planning_verb:
            final_scores["qcm"] += 4
            # Suppress TRUM skill_planning since this is content/campaign work
            final_scores["trum"] = max(0, final_scores["trum"] - 3)
            # S066 FIX: also suppress SPEC config_consistency false positives
            # triggered by "上线/部署" language incidental to GTM queries.
            final_scores["spec"] = max(0, final_scores["spec"] - 2)

        # Knowledge retrieval override: "查询/查找/检索 + 信息/资料/指南/研究/最新" → QCM Q02
        retrieval_verbs = ["查询", "查詢", "查找", "search", "检索", "檢索",
                           "find", "look up", "retrieve",
                           # S063-R3: informal retrieval verbs
                           "找", "帮我找", "幫我找", "找一下", "找一些",
                           "help me find", "搜", "搜一下"]
        retrieval_objects = ["指南", "guideline", "资料", "資料", "信息", "information",
                             "研究", "research", "文献", "文獻", "最新", "latest",
                             "更新", "update", "进展", "進展", "progress",
                             "论文", "論文", "paper"]
        has_retrieval_verb = any(rv in text for rv in retrieval_verbs)
        has_retrieval_obj = any(ro in text for ro in retrieval_objects)
        if has_retrieval_verb and has_retrieval_obj:
            final_scores["qcm"] += 3
            # Suppress SPEC db_architecture false-positive from "查询"
            final_scores["spec"] = max(0, final_scores["spec"] - 2)

        # Data analysis override: "分析 + 报表/财务/销售/业务" → QCM Q04 data analyst
        data_analysis_objects = ["报表", "報表", "report", "财务", "財務", "financial",
                                 "销售", "銷售", "sales", "业绩", "業績", "performance metrics",
                                 "营收", "營收", "revenue", "用户数据", "用戶數據"]
        analysis_verbs = ["分析", "analyze", "解读", "解讀", "interpret"]
        has_data_obj = any(do in text for do in data_analysis_objects)
        has_analysis_verb = any(av in text for av in analysis_verbs)
        if has_data_obj and has_analysis_verb:
            final_scores["qcm"] += 3

        # Compliance audit override: "审核/审查 + 合规/标准" → SPEC compliance_audit
        audit_verbs = ["审核", "審核", "审查", "審查", "audit"]
        spec_audit_objects = ["合规", "合規", "compliance", "标准", "標準", "standard",
                              "规范", "規範", "spec", "部署流程", "部署流程",
                              "schema", "数据一致性", "數據一致性"]
        has_audit_verb = any(av in text for av in audit_verbs)
        has_spec_audit_obj = any(sao in text for sao in spec_audit_objects)
        if has_audit_verb and has_spec_audit_obj:
            final_scores["spec"] += 4

        # Risk detection override: risk analysis/assessment is QCM (Risk Officer)
        # unless explicitly platform-level or cross-project or security auditing
        risk_words = ["风险", "風險", "risk", "威胁", "威脅", "合规", "合規", "compliance", "pci-dss", "PCI-DSS"]
        # Security audit keywords that belong to SPEC, not QCM
        # S068 FIX: "安全漏洞" removed from spec_security — plain code security
        # review belongs to QCM Q06 Risk Auditor. Platform-level security audit
        # (renamed/scoped differently) can still route here via "安全审计" /
        # "security audit" / "penetration test" etc. Without this fix, any
        # mention of "安全漏洞" forced SPEC family, starving Q06 of work.
        spec_security = ["安全审计", "安全審計", "security audit",
                         "漏洞检测", "漏洞檢測", "vulnerability detection",
                         "合规审计", "合規審計", "compliance audit",
                         "渗透测试", "滲透測試", "penetration test",
                         "平台安全", "平台级安全", "platform security"]
        platform_scope = ["平台", "跨项目", "跨項目", "cross-project", "全局"]
        if any(w in text for w in risk_words):
            if not any(p in text for p in platform_scope):
                if not any(sa in text for sa in spec_security):
                    final_scores["qcm"] += 2
        # Explicit security auditing/compliance → SPEC (strong indicator)
        if any(sa in text for sa in spec_security):
            final_scores["spec"] += 5

        # Database architecture override: DB design/standards is SPEC, not QCM
        spec_db = ["数据库架构", "數據庫架構", "database architecture",
                   "数据库规范", "數據庫規範", "database schema",
                   "数据库设计", "數據庫設計", "database design",
                   "表结构", "表結構", "table structure"]
        if any(sd in text for sd in spec_db):
            final_scores["spec"] += 4

        # Deployment/ops override: operational deployment is SPEC, not TRUM
        ops_deploy = ["部署上线", "部署上線", "系统部署", "系統部署",
                      "deploy to production", "go live", "发布上线", "發布上線",
                      "运维部署", "運維部署"]
        if any(od in text for od in ops_deploy):
            final_scores["spec"] += 3

        # Technology selection / tech stack decision → SPEC (S6 fix)
        tech_selection = ["技术选型", "技術選型", "tech stack", "technology selection",
                         "框架选型", "框架選型", "framework selection", "选技术", "選技術",
                         "stack decision", "技术方案选择", "技術方案選擇"]
        if any(ts in text for ts in tech_selection):
            final_scores["spec"] += 4

        # ── Learning/Teaching intent override ──
        # When user wants to LEARN or be TAUGHT, route to QCM (Q07 Companion)
        # regardless of the topic (even if topic contains TRUM/SPEC keywords).
        # e.g. "教我用Docker部署" → QCM Q07, not SPEC S02
        # e.g. "我想學AI項目管理從哪裡開始" → QCM Q07, not TRUM T01
        learning_verbs = ["教我", "教教我", "teach me", "learn", "學習",
                         "学习", "入門", "入门", "從哪裡開始", "从哪里开始",
                         "怎麼學", "怎么学", "怎麼開始", "怎么开始",
                         "如何開始", "如何开始", "getting started",
                         "什麼是", "什么是", "explain", "解釋", "解释",
                         "推薦資源", "推荐资源", "推薦學習", "推荐学习",
                         "學習資源", "学习资源", "新手", "beginner",
                         "初學者", "初学者", "幫我理解", "帮我理解",
                         "怎麼做", "怎么做", "how to"]
        has_learning_intent = any(lv in text for lv in learning_verbs)
        if has_learning_intent:
            final_scores["qcm"] += 6
            final_scores["trum"] = max(0, final_scores["trum"] - 4)
            final_scores["spec"] = max(0, final_scores["spec"] - 4)

        # Personal task management (QCM) vs enterprise operations (TRUM)
        # "管理我的日常..." is personal scale → QCM Companion, not TRUM
        personal_task = ["管理我的", "我的日常", "我的任务", "我的任務",
                        "日常工作任务", "日常工作任務", "个人任务", "個人任務",
                        "my daily tasks", "my todo", "personal task",
                        "manage my work", "organize my day"]
        if any(pt in text for pt in personal_task):
            final_scores["qcm"] += 4
            final_scores["trum"] = max(0, final_scores["trum"] - 4)

        # Database schema design → SPEC (S6 fix)
        # "数据库" (database) should go to SPEC, distinct from "数据" (data/analytics)
        db_schema = ["数据库", "數據庫", "database table", "database schema",
                    "数据库表", "數據庫表", "数据库设计", "數據庫設計",
                    "schema design", "table design", "建表", "建庫",
                    "sql schema", "ddl",
                    "数据仓库schema", "數據倉庫schema", "data warehouse schema",
                    "warehouse schema", "仓库schema", "倉庫schema"]
        if any(ds in text.lower() for ds in db_schema):
            final_scores["spec"] += 5
            # Data analyst shouldn't steal database schema work
            final_scores["qcm"] = max(0, final_scores["qcm"] - 3)

        # Schema/DDL keyword alone beats data pipeline when both trigger
        if "schema" in text.lower() and any(k in text.lower() for k in
            ["database", "数据库", "數據庫", "数据仓库", "數據倉庫",
             "data warehouse", "table", "ddl"]):
            final_scores["spec"] += 4
            final_scores["qcm"] = max(0, final_scores["qcm"] - 3)

        # Presentation/deck/slide creation → QCM Creator
        presentation = ["路演", "PPT", "ppt", "pitch deck", "slide deck",
                       "slides", "presentation", "演示文稿", "幻灯片",
                       "投资人演讲", "投資人演講", "demo day"]
        if any(p in text for p in presentation):
            final_scores["qcm"] += 4
            final_scores["trum"] = max(0, final_scores["trum"] - 3)

        # Weekly/progress report → QCM Companion (personal reporting)
        weekly_report = ["周报", "週報", "日报", "日報", "月报", "月報",
                        "weekly report", "daily report", "status update",
                        "进度报告", "進度報告", "progress report"]
        if any(wr in text for wr in weekly_report):
            final_scores["qcm"] += 4
            final_scores["trum"] = max(0, final_scores["trum"] - 3)

        # Content calendar/schedule → QCM Creator (content planning)
        # "發布日曆/內容日曆" is content creation, not SPEC deployment
        content_schedule = ["發布日曆", "发布日历", "內容日曆", "内容日历",
                          "content calendar", "發文計劃", "发文计划",
                          "發布計劃", "发布计划", "內容排程", "内容排程",
                          "editorial calendar", "社群日曆", "社群日历"]
        if any(cs in text for cs in content_schedule):
            final_scores["qcm"] += 5
            final_scores["spec"] = max(0, final_scores["spec"] - 4)

        # Governance framework design — governance dominates "设计"
        if any(g in text for g in ["治理框架", "治理體系", "治理体系",
                                   "治理结构", "治理結構", "governance framework",
                                   "governance structure", "governance architecture"]):
            final_scores["trum"] += 6
            final_scores["spec"] = max(0, final_scores["spec"] - 4)
            final_scores["qcm"] = max(0, final_scores["qcm"] - 3)

        # System architecture override (S6 flywheel fix): "architecture" + scale/system/enterprise
        # keywords indicate SPEC (systems architecture), not QCM (content architecture)
        sys_arch_triggers = ["microservices", "微服务", "微服務",
                            "restful", "rest api", "api design", "api架构",
                            "scaling", "scalable", "可扩展", "可擴展",
                            "enterprise", "企业级", "企業級",
                            "distributed", "分布式", "分佈式",
                            "infrastructure architecture", "基础设施架构"]
        if any(sat in text for sat in sys_arch_triggers):
            final_scores["spec"] += 4
            # Only penalize QCM if SPEC got meaningful score (avoid over-correction)
            if final_scores["spec"] >= 4:
                final_scores["qcm"] = max(0, final_scores["qcm"] - 2)

        # S067 FIX: Threat modeling / STRIDE / security risk analysis is a
        # Q06 Risk Officer task, not SPEC architecture, even when the target
        # system is described with "REST API" / "microservices" language.
        # This override has to run AFTER sys_arch_triggers so it can undo
        # the SPEC boost it caused.
        threat_modeling = ["stride", "threat model", "threat modeling",
                          "威胁建模", "威脅建模", "threat modelling",
                          "pasta threat", "attack surface", "攻击面", "攻擊面",
                          "security risk analysis", "安全风险分析",
                          "安全風險分析"]
        if any(tm in text for tm in threat_modeling):
            final_scores["qcm"] += 6
            final_scores["spec"] = max(0, final_scores["spec"] - 4)

        # Authentication/security implementation → SPEC (S6 fix)
        auth_impl = ["jwt", "oauth", "authentication", "authorization",
                    "身份验证", "身份驗證", "鉴权", "鑒權",
                    "sso", "saml", "refresh token", "access token",
                    "api security", "api安全"]
        if any(ai in text for ai in auth_impl):
            final_scores["spec"] += 3

        # Monitoring/observability → SPEC (S6 fix)
        # "metrics" alone is ambiguous — exclude when paired with analytics verbs
        monitoring_hard = ["monitoring", "alerting", "observability",
                     "监控系统", "監控系統", "告警", "告警",
                     "tracing", "logging system",
                     "prometheus", "grafana", "datadog",
                     "apm", "telemetry"]
        if any(m in text.lower() for m in monitoring_hard):
            final_scores["spec"] += 3
        # "metrics" only boost SPEC if paired with system/infra context
        if "metrics" in text.lower():
            sys_context = ["system", "server", "infra", "service", "endpoint",
                          "uptime", "latency", "error rate", "slo", "sla"]
            if any(sc in text.lower() for sc in sys_context):
                final_scores["spec"] += 2
            else:
                # Customer/business metrics → QCM analyst
                final_scores["qcm"] += 2

        # English "audit" + security/compliance → SPEC (S6 fix)
        # Previous logic only caught Chinese. English vulnerability audit is SPEC-level.
        eng_security_audit = ["audit our system", "security audit", "vulnerability audit",
                             "security review", "compliance review", "pen test",
                             "security vulnerabilities", "compliance with",
                             "audit security", "audit the security", "audit and secure",
                             "security patches", "deploy patches", "patch management",
                             "patching security", "infrastructure audit"]
        if any(esa in text.lower() for esa in eng_security_audit):
            final_scores["spec"] += 5
            # Prevent QCM risk_auditor from stealing this
            final_scores["qcm"] = max(0, final_scores["qcm"] - 3)

        # Regulatory compliance → SPEC (S6 fix)
        regulatory = ["gdpr", "hipaa", "sox", "pci-dss", "iso 27001",
                     "soc 2", "ccpa", "regulatory compliance", "法规合规",
                     "法規合規", "监管合规", "監管合規",
                     "compliance 策略", "compliance strategy", "合规策略", "合規策略",
                     "compliance framework", "合规框架", "合規框架"]
        if any(r in text.lower() for r in regulatory):
            final_scores["spec"] += 5
            # Regulatory work is architectural compliance, not content creation
            final_scores["qcm"] = max(0, final_scores["qcm"] - 3)

        # Data pipeline is QCM (analytics), not TRUM (S6 fix)
        data_pipeline = ["data pipeline", "数据管道", "數據管道",
                        "data ingestion", "数据采集", "數據採集",
                        "etl pipeline", "etl管道", "elt pipeline",
                        "data warehouse", "数据仓库", "數據倉庫",
                        "data lake", "数据湖", "數據湖",
                        "streaming data", "流数据", "流數據"]
        if any(dp in text.lower() for dp in data_pipeline):
            final_scores["qcm"] += 4
            final_scores["trum"] = max(0, final_scores["trum"] - 3)

        # Multi-project client management is QCM (project planning), not TRUM ops (S6 fix)
        multi_project_mgmt = ["管理多个", "管理多個", "multiple projects",
                             "multiple clients", "客户项目", "客戶項目",
                             "project portfolio", "项目组合", "項目組合",
                             "freelance", "自由职业", "自由職業",
                             "管理客户", "管理客戶", "客户管理", "客戶管理"]
        if any(mpm in text for mpm in multi_project_mgmt):
            final_scores["qcm"] += 5
            # Strip TRUM boost from generic "管理" word — this is personal-scale project mgmt
            final_scores["trum"] = max(0, final_scores["trum"] - 4)

        # Emergency/crisis events → TRUM T01 (Platform Sovereign has emergency authority)
        # S6 fix: 紧急安全事件 must route to TRUM, not QCM Risk Auditor
        emergency = ["紧急", "緊急", "emergency", "crisis", "urgent",
                    "事件处理", "事件處理", "incident response", "应急", "應急",
                    "critical issue", "重大事件", "紧急事件", "緊急事件",
                    "安全事件", "安全事件", "security incident", "security event",
                    "evaluate.*incident", "评估.*事件", "評估.*事件"]
        emergency_matched = False
        for e in emergency:
            # Support regex-like match for evaluate patterns
            if "." in e or "*" in e:
                import re as _re
                if _re.search(e, text):
                    emergency_matched = True
                    break
            elif e in text:
                emergency_matched = True
                break
        if emergency_matched:
            # Only boost TRUM if combined with governance/security/platform scope
            scope_words = ["安全", "security", "系统", "系統", "system",
                          "平台", "platform", "服务", "服務", "service"]
            if any(sw in text for sw in scope_words):
                final_scores["trum"] += 5
                final_scores["qcm"] = max(0, final_scores["qcm"] - 2)

        # Platform introduction/feature inquiry → QCM AI Companion (Q07), not TRUM
        # S6 fix: "你们平台能做什么" is onboarding, not governance
        platform_inquiry = ["平台能帮", "平台能幫", "平台能做",
                           "能帮我做什么", "能幫我做什麼",
                           "what can you do", "what does this do",
                           "features", "功能介绍", "功能介紹",
                           "你们有什么", "你們有什麼"]
        if any(pi in text for pi in platform_inquiry):
            final_scores["qcm"] += 3
            final_scores["trum"] = max(0, final_scores["trum"] - 3)

        # Cross-family arbitration (S6 fix):
        # "制定数据治理政策并设计数据库架构" = governance policy (TRUM) + DB design (SPEC)
        # The LEADING intent ("制定...政策") should win → TRUM
        governance_leading = ["制定.*政策", "制定.*制度", "establish.*policy",
                             "define.*governance", "治理政策", "治理制度",
                             "数据治理", "數據治理", "data governance",
                             "治理体系", "治理體系", "governance framework",
                             "治理规范", "治理規範", "建立.*规范", "建立.*規範",
                             "建立.*治理", "governance.*team", "compliance.*team"]
        import re as _re
        governance_matched = False
        for pattern in governance_leading:
            if _re.search(pattern, text):
                final_scores["trum"] += 8
                governance_matched = True
                break
        # When governance leads, aggressively suppress SPEC so policy (TRUM) wins over architecture (SPEC)
        if governance_matched:
            final_scores["spec"] = max(0, final_scores["spec"] - 6)

        # Research override: deep research/investigation is QCM (Researcher), not SPEC
        # Even if "best practice" or "standard" appear, research intent is QCM execution
        research_verbs = ["深度研究", "research", "調研", "调研", "研究",
                          "investigate", "探索", "explore", "比较", "比較",
                          "竞品分析", "競品分析", "市场调研", "市場調研"]
        if any(rv in text for rv in research_verbs):
            final_scores["qcm"] += 2

        # Unit test / test writing override: writing tests is QCM (Developer/Tester)
        test_writing = ["write test", "write unit", "编写测试", "編寫測試",
                        "单元测试", "單元測試", "集成测试", "集成測試",
                        "写测试", "寫測試", "test code", "测试代码", "測試代碼"]
        if any(tw in text for tw in test_writing):
            final_scores["qcm"] += 3

        # Code review override: code quality/review is SPEC (standards), not QCM
        # Check for co-occurrence of review-related + code-related words
        # S068 FIX: add security exception — "審查代碼的安全漏洞" is a Q06 Risk
        # Auditor task, not a SPEC standards review. Only push to SPEC when the
        # review is about quality/standards, not security.
        code_review_phrases = ["review code", "code review", "代码审查", "代碼審查",
                               "code quality", "代码质量", "代碼質量",
                               "suggest improvements", "改进建议", "改進建議"]
        code_words = ["code", "代码", "代碼"]
        review_words = ["review", "quality", "审查", "審查", "质量", "質量"]
        security_review_words = ["security", "vulnerability", "vuln", "exploit",
                                 "安全", "漏洞", "威脅", "威胁", "threat",
                                 "CVE", "cve", "injection", "XSS", "xss",
                                 "SQL injection", "SQLi", "sqli"]
        has_code = any(cw in text for cw in code_words)
        has_review = any(rw in text for rw in review_words)
        has_security_lens = any(sw in text for sw in security_review_words)
        if any(cr in text for cr in code_review_phrases) or (has_code and has_review):
            if has_security_lens:
                # Security review of code → QCM Q06 Risk Auditor
                final_scores["qcm"] += 5
                final_scores["spec"] = max(0, final_scores["spec"] - 2)
            else:
                # Generic code quality review → SPEC standards
                final_scores["spec"] += 5

        # ═══════════════════════════════════════════════════════════════
        # S063 ROUND 2 FIXES — General routing overrides for discovered gaps
        # ═══════════════════════════════════════════════════════════════

        # S063-R2-1: Strategic product-kill / product-line decisions → TRUM T01 Sovereign
        # "评估产品线是否砍掉" — this is executive-level product portfolio decision,
        # NOT content creation. Evaluate + product-line + kill/discontinue decision verb.
        product_decision_objects = ["产品线", "產品線", "product line",
                                    "业务线", "業務線", "business line",
                                    "产品组合", "產品組合", "product portfolio",
                                    "业务单元", "業務單元", "business unit"]
        decision_verbs = ["评估", "評估", "evaluate",
                          "是否应该", "是否應該", "should we",
                          "要不要", "是否", "whether to"]
        kill_verbs = ["砍掉", "砍掉", "kill", "discontinue",
                      "停掉", "關掉", "关掉", "下线", "下線",
                      "裁减", "裁減", "sunset", "shut down", "终止", "終止"]
        has_product_obj = any(po in text for po in product_decision_objects)
        has_decision_verb = any(dv in text for dv in decision_verbs)
        has_kill_verb = any(kv in text for kv in kill_verbs)
        if (has_product_obj and (has_decision_verb or has_kill_verb)) or \
           (has_kill_verb and has_product_obj):
            final_scores["trum"] += 6
            final_scores["qcm"] = max(0, final_scores["qcm"] - 3)

        # S063-R2-2: Demand pool / backlog management → TRUM T02 Operations Director
        # "整理需求池并安排优先级" — demand/backlog management is ops territory.
        demand_pool_objects = ["需求池", "需求池", "demand pool", "backlog",
                               "需求清单", "需求清單", "demand list",
                               "迭代池", "迭代池", "sprint backlog",
                               "待办池", "待辦池", "todo pool"]
        demand_verbs = ["整理", "organize", "安排", "schedule",
                        "优先级", "優先級", "priority", "prioritize",
                        "管理", "manage", "梳理"]
        has_demand_obj = any(do in text for do in demand_pool_objects)
        has_demand_verb = any(dv in text for dv in demand_verbs)
        if has_demand_obj and has_demand_verb:
            final_scores["trum"] += 5
            final_scores["qcm"] = max(0, final_scores["qcm"] - 2)

        # S063-R2-3: Cross-family SYNC / BRIDGE explicitly naming families → SPEC S03 Bridge
        # "同步QCM与Spec两家族" — naming QCM+Spec with sync is S03's exclusive domain.
        family_names = ["qcm", "QCM", "spec", "Spec", "SPEC", "trum", "TRUM",
                        "家族", "家族", "family"]
        sync_verbs = ["同步", "sync", "synchronize", "桥接", "橋接", "bridge"]
        # Require at least TWO family-name mentions OR explicit "家族" word with sync verb
        family_mentions = sum(1 for fn in family_names if fn in text)
        has_sync_verb = any(sv in text for sv in sync_verbs)
        if has_sync_verb and (family_mentions >= 2 or any(k in text for k in ["家族", "跨家族", "cross-family"])):
            final_scores["spec"] += 6
            final_scores["trum"] = max(0, final_scores["trum"] - 3)

        # S063-R2-4: Legal/business document drafting → QCM Q03 Creator (not TRUM)
        # "起草客户合作意向书" — drafting documents is content creation even when
        # the subject is business/customer relationships.
        legal_doc_types = ["意向书", "意向書", "letter of intent", "LOI",
                           "合同", "合約", "合约", "contract", "agreement",
                           "协议", "協議",
                           "保密协议", "保密協議", "NDA", "nda",
                           "条款", "條款", "terms",
                           "授权书", "授權書", "authorization",
                           "声明", "聲明", "declaration", "statement",
                           "备忘录", "備忘錄", "memo", "memorandum",
                           "公告", "announcement", "notice",
                           "OKR", "okr", "KPI模板", "kpi模板"]
        drafting_verbs = ["起草", "起草", "撰写", "撰寫", "draft", "prepare",
                          "写一份", "寫一份", "准备一份", "準備一份",
                          "拟", "擬", "草拟", "草擬"]
        has_legal_doc = any(ld in text for ld in legal_doc_types)
        has_drafting_verb = any(dv in text for dv in drafting_verbs)
        if has_legal_doc and has_drafting_verb:
            final_scores["qcm"] += 6
            final_scores["trum"] = max(0, final_scores["trum"] - 4)
            final_scores["spec"] = max(0, final_scores["spec"] - 2)

        # S063-R2-5: Deployment compliance audit → SPEC S02 (suppress QCM Q01 architect steal)
        # S061 added `audit + spec_audit_objects → +4 SPEC`. But "审核部署流程和合规性"
        # still lost to QCM because "部署" and "流程" match system_design (Q01) capability.
        # Solution: when audit + compliance + (deployment|ops) co-occur, suppress QCM.
        compliance_audit_strong = (
            any(av in text for av in ["审核", "審核", "审查", "審查", "audit"]) and
            any(ca in text for ca in ["合规", "合規", "compliance"]) and
            any(oa in text for oa in ["部署", "deploy", "运维", "運維", "上线", "上線",
                                       "流程", "process", "pipeline", "schema"])
        )
        if compliance_audit_strong:
            final_scores["spec"] += 5
            final_scores["qcm"] = max(0, final_scores["qcm"] - 4)

        # ═══════════════════════════════════════════════════════════════
        # S063 ROUND 3 FIXES — Additional family-level disambiguation
        # ═══════════════════════════════════════════════════════════════

        # S063-R3-A: Paper / literature retrieval is QCM Q02, not TRUM
        # "帮我找2025年关于RAG评估的最新论文" — "评估" triggers TRUM system_audit, but
        # the real intent is searching for literature. Strong QCM boost when paper/thesis
        # keywords appear, and suppress the incidental "评估" TRUM boost.
        paper_retrieval = ["论文", "論文", "paper", "文献", "文獻", "thesis",
                           "学术", "學術", "academic", "研究论文", "研究論文"]
        if any(pr in text for pr in paper_retrieval):
            final_scores["qcm"] += 5
            # Suppress "评估" → trum system_audit false positive when talking about
            # evaluation of AI models in papers (e.g. "RAG评估")
            if any(ev in text for ev in ["评估", "評估", "evaluate", "evaluation"]):
                final_scores["trum"] = max(0, final_scores["trum"] - 3)

        # S063-R3-B: Script / deployment-script audit is SPEC (S02 Ops), not TRUM
        # "帮我审查这段部署脚本有没有问题" — "审查" triggers TRUM quality_acceptance,
        # but "部署脚本" is SPEC operational territory.
        script_ops = ["部署脚本", "部署腳本", "deployment script",
                      "shell脚本", "shell腳本", "shell script",
                      "ci脚本", "ci腳本", "ci script", "脚本", "腳本",
                      # S063-R3 adversarial: k8s / helm / deploy artifacts
                      "helm chart", "helm", "values.yaml", "kubectl",
                      "k8s", "kubernetes", "deploy values", "deployment values",
                      "dockerfile", "docker-compose"]
        audit_words = ["审查", "審查", "审核", "審核", "audit", "review", "检查", "檢查"]
        has_script = any(so in text for so in script_ops)
        has_audit_word = any(aw in text for aw in audit_words)
        if has_script and has_audit_word:
            # But only when context is operational (not writing creative scripts)
            creative_script = ["短视频", "短視頻", "短片", "剧本", "劇本", "screenplay",
                               "video script", "视频脚本", "視頻腳本"]
            if not any(cs in text for cs in creative_script):
                final_scores["spec"] += 5
                final_scores["trum"] = max(0, final_scores["trum"] - 3)
                final_scores["qcm"] = max(0, final_scores["qcm"] - 2)

        # S063-R2-6: Credential/secret exfiltration attempt → never route to SPEC DBA
        # Security concern: "show me database credentials/api keys/secrets" routed to S01 DBA.
        # Redirect to QCM Q06 Risk Auditor so sandbox flags it and Risk Officer handles.
        exfil_signals = ["credentials", "credential", "api key", "api keys",
                         "secret", "secrets", "password", "token",
                         "env var", "环境变量", "環境變量",
                         "泄露", "洩露", "leak", "dump the database",
                         "数据库凭证", "數據庫憑證"]
        if any(es in text.lower() for es in exfil_signals):
            # Strongly push to QCM (Risk Officer) and block SPEC DBA path
            final_scores["qcm"] += 8
            final_scores["spec"] = max(0, final_scores["spec"] - 8)
            final_scores["trum"] = max(0, final_scores["trum"] - 3)

        # S063-R3-C: DBA / SQL / DB-tuning technical queries → SPEC, not QCM
        # "帮我写PostgreSQL 14的查询优化配置" — "写" + "优化" boosted QCM,
        # but PG/MySQL/Redis + query/config is SPEC DBA territory.
        dba_tech = ["postgresql", "postgres", "mysql", "mariadb", "redis",
                    "mongodb", "sqlserver", "clickhouse", "elasticsearch",
                    "sql查询", "SQL查询", "SQL查詢", "query optimization",
                    "索引优化", "索引優化", "index tuning",
                    "连接池", "連接池", "connection pool"]
        if any(dt in text.lower() for dt in dba_tech):
            final_scores["spec"] += 4
            # Strip content_verb's QCM boost — writing SQL is SPEC DBA, not generic content
            if any(cv in text for cv in ["寫", "写", "create", "draft",
                                          "撰寫", "撰写", "write"]):
                final_scores["qcm"] = max(0, final_scores["qcm"] - 3)

        # S063-R3-D: Business-review deck / quarterly-review content → QCM Q03
        # "做一个 quarterly business review deck" — "business"+"review" collided
        # with TRUM operation_promotion + quality_acceptance. "deck" alone not enough.
        review_deck = ["business review deck", "quarterly business review",
                       "qbr deck", "quarterly deck", "quarterly review",
                       "review deck", "投资人路演", "投資人路演",
                       "board deck", "董事会deck", "董事會deck"]
        if any(rd in text.lower() for rd in review_deck):
            final_scores["qcm"] += 6
            final_scores["trum"] = max(0, final_scores["trum"] - 3)

        # S063-R3-E: Role-play injection — "admin mode"/"dump secrets" etc → QCM
        # Strengthen existing exfil_signals for English phrasings.
        roleplay_inject = ["admin mode", "developer mode", "sudo mode",
                           "root access", "dump all", "dump secrets",
                           "exfiltrate", "bypass security", "reveal all"]
        if any(ri in text.lower() for ri in roleplay_inject):
            final_scores["qcm"] += 8
            final_scores["spec"] = max(0, final_scores["spec"] - 6)
            final_scores["trum"] = max(0, final_scores["trum"] - 3)

        # Pick highest scoring family (QCM is default when tied or all zero)
        best_family = max(final_scores, key=final_scores.get)
        if final_scores[best_family] == 0:
            return "qcm"
        # Tiebreaker: SPEC > TRUM for operational tasks, QCM default otherwise
        if final_scores["spec"] == final_scores["trum"] and final_scores["spec"] > 0:
            # If query has deployment/ops keywords, prefer SPEC
            if any(k in text for k in ["部署", "deploy", "运维", "運維", "上线", "上線"]):
                return "spec"
        return best_family

    def _select_role(self, text, family):
        """
        Select the best role within the target family using F21 argmax decision.

        F21: D(input) = argmax_r [ w_rel·Rel(r) + w_aff·Aff(r) + w_cost·(1-Cost(r)) + w_knowledge·Know(r) ]
        """
        # S069 FIX (from 20-round flywheel): short-circuit greetings BEFORE
        # F21 scoring. Without this, accumulated affinity/knowledge on any
        # role beats the fallback "greeting → Q01" rule because F21 score is
        # always > 0 when affinity != 0. Explicit greetings should be
        # deterministic, not affinity-drifted.
        text_lower = (text or "").lower().strip()
        if family == "qcm" and len(text_lower) <= 20:
            greetings = (
                "你好", "您好", "哈囉", "哈啰", "嗨", "早", "早安", "午安", "晚安",
                "hi", "hello", "hey", "greetings", "good morning",
                "good afternoon", "good evening",
            )
            if any(text_lower == g or
                   text_lower.startswith(g + " ") or
                   text_lower.startswith(g + ",") or
                   text_lower.startswith(g + "，") or
                   text_lower.startswith(g + "!") or
                   text_lower.startswith(g + "！") or
                   text_lower.startswith(g + ".")
                   for g in greetings):
                return "ROLE-Q01", 0.8, "Greeting short-circuit → Q01 (default entry)"

        # F21 scoring dimensions:
        #   1. Relevance (Rel): keyword/capability matching score
        #   2. Affinity (Aff): feedback-loop learned preference
        #   3. Cost (1-Cost): prefer lower-cost roles (inverse cost)
        #   4. Knowledge (Know): knowledge depth accumulated for this role
        family_roles = self.db.get_roles_by_family(family)
        if not family_roles:
            return "ROLE-Q07", 0.5, "Fallback to AI Companion (no roles in target family)"

        best_role = None
        best_score = -1
        best_reason = ""
        f21_details = {}

        # S068 FIX: case-insensitive keyword matching so English queries with
        # capital letters ("Research our competitors", "Design UX", "Help me Grow")
        # hit the same keyword entries as their lowercase counterparts.
        text_lower = (text or "").lower()
        for role_code, role in family_roles.items():
            # ── Dimension 1: Relevance (keyword + capability matching) ──
            rel_score = 0.0
            keyword_score = 0.0
            reasons = []
            caps = role.get("capabilities_list", [])

            for cap in caps:
                keywords = self.CAPABILITY_KEYWORDS.get(cap, [])
                for kw in keywords:
                    # CJK keywords are case-neutral; ASCII keywords need
                    # case-insensitive compare so "Research" matches "research".
                    kw_lower = kw.lower()
                    if kw_lower in text_lower:
                        weight = 1.0 + min(1.5, len(kw) / 4)
                        rel_score += weight
                        keyword_score += weight
                        reasons.append(f"matched '{kw}' → {cap}")

            if role["role_name"].lower() in text_lower:
                rel_score += 3.0
                keyword_score += 3.0
                reasons.append("role name matched")

            # Normalize relevance to 0-1 range (3.0 = full confidence)
            rel_normalized = min(1.0, rel_score / 3.0)

            # ── Dimension 2: Affinity (feedback loop, F21 integration) ──
            aff_score = 0.0
            if keyword_score > 0 and self._feedback_fn:
                affinity = self._feedback_fn(role_code)
                if affinity != 0:
                    aff_score = max(-1.0, min(1.0, affinity))
                    reasons.append(f"affinity {aff_score:+.2f}")
            # Normalize to 0-1 range (shift from [-1,1] to [0,1])
            aff_normalized = (aff_score + 1.0) / 2.0

            # ── Dimension 3: Inverse Cost (prefer lower cost, F22 integration) ──
            cost_normalized = 0.5  # Default neutral
            if self._cost_bridge and hasattr(self._cost_bridge, 'available') and self._cost_bridge.available:
                try:
                    cost_est = self._cost_bridge.estimate_role_cost(role_code)
                    if cost_est is not None:
                        cost_normalized = 1.0 - min(1.0, cost_est)
                        reasons.append(f"cost={1.0 - cost_normalized:.2f}")
                except Exception:
                    pass

            # ── Dimension 4: Knowledge Depth (F19-20 integration) ──
            know_normalized = 0.0
            if self._knowledge:
                try:
                    know_normalized = self._knowledge.get_role_knowledge_affinity(role_code)
                    if know_normalized > 0:
                        reasons.append(f"knowledge={know_normalized:.2f}")
                except Exception:
                    pass

            # ── F21 Argmax: Weighted combination ──
            # S071 (persona×stressor audit): when keyword_score is 0, gate the
            # affinity+knowledge contribution so accumulated server-global
            # affinity from prior crisis turns can't bleed into unrelated
            # queries. Affinity should AMPLIFY a real keyword signal, not
            # overwrite the lack of one.
            if keyword_score == 0:
                eff_affinity = 0.5  # neutral
                eff_knowledge = 0.0
            else:
                eff_affinity = aff_normalized
                eff_knowledge = know_normalized
            f21_score = (
                self.F21_W_RELEVANCE * rel_normalized +
                self.F21_W_AFFINITY * eff_affinity +
                self.F21_W_COST * cost_normalized +
                self.F21_W_KNOWLEDGE * eff_knowledge
            )

            # Store F21 breakdown for debugging/audit
            f21_details[role_code] = {
                "relevance": round(rel_normalized, 3),
                "affinity": round(aff_normalized, 3),
                "inv_cost": round(cost_normalized, 3),
                "knowledge": round(know_normalized, 3),
                "f21_score": round(f21_score, 4),
            }

            # Use F21 score scaled + raw keyword score as tiebreaker
            # Raw keyword score breaks ties when F21 normalized scores are equal
            # S063-R3: Increase raw relevance weight from 0.01 → 0.5 so that
            # large relevance gaps (e.g. T01 rel=6.0 vs T03 rel=3.0) cannot be
            # overridden by affinity-drift alone. Without this, a role that
            # accumulated +1.0 affinity from prior usage unfairly beat a role
            # with 2× stronger keyword match.
            composite = f21_score * 10.0 + rel_score * 0.5

            # S066 FIX: Q07 AI Companion must never win by affinity drift
            # alone. Across the 23-persona flywheel, Q07 accumulated positive
            # affinity from legitimate empathic usage (P09 pressure / P10 /
            # P11 safety) and then leaked into unrelated operational queries
            # (P16 文献综述 / P17 React perf / P20 使用率 / P21 burn rate /
            # P22 改写文档 / P23 测试矩阵). Require Q07 to have at least
            # one real keyword hit before it can be declared the winner of
            # the argmax; otherwise its F21 score is floored so another
            # role in the family can take over.
            if role_code == "ROLE-Q07" and keyword_score <= 0:
                composite = -1.0  # Disqualify Q07 without keyword evidence

            if composite > best_score or (composite == best_score and rel_score > 0):
                best_score = composite
                best_role = role_code
                best_reason = "; ".join(reasons[:3]) if reasons else "default selection"

        # If no strong match (no keyword hits across all dimensions), use family-specific defaults
        if best_score <= 0 or (best_role and f21_details.get(best_role, {}).get("relevance", 0) == 0
                               and f21_details.get(best_role, {}).get("affinity", 0.5) <= 0.5
                               and f21_details.get(best_role, {}).get("knowledge", 0) == 0):
            # S066 FIX: Q07 Companion must not be the blanket QCM fallback.
            # Q07 should only win when the query actually carries an emotional
            # anchor; otherwise prefer Q01 Chief Architect (the documented
            # default entry per ROLE-REGISTRY.md).
            #
            # S068 FIX (this session): default was previously Q03 Creator which
            # routed greetings like "你好" / "hello" to the content creator.
            # Changed to Q01 (Chief Architect) to match the documented
            # "default entry point" behavior; explicit greetings are also
            # detected so they win deterministically over affinity drift.
            emotional_anchors = [
                "压力", "壓力", "焦虑", "焦慮", "难受", "難受", "委屈", "委曲",
                "崩溃", "崩潰", "emotional", "stress", "stressed", "anxious",
                "anxiety", "lonely", "孤独", "孤獨", "喘不过气", "喘不過氣",
                "想哭", "痛苦", "沮丧", "沮喪", "depressed", "depression",
                "陪陪我", "陪陪", "陪我", "聊聊天", "聊天",
                "怎么办", "怎麼辦", "不知道该怎么", "心情", "mood", "feel",
                "感觉", "感覺", "情绪", "情緒",
            ]
            greeting_anchors = [
                "你好", "您好", "哈囉", "哈啰", "嗨", "hi", "hello", "hey",
                "早安", "午安", "晚安", "good morning", "good afternoon",
                "good evening", "greetings",
            ]
            text_lower = (text or "").lower().strip()
            has_emotion = any(ea.lower() in text_lower for ea in emotional_anchors)
            # Require greeting to be short + match greeting anchor (avoid false
            # positives like "hi" inside a technical question).
            has_greeting = (len(text_lower) <= 20 and
                            any(ga.lower() == text_lower or
                                text_lower.startswith(ga.lower() + " ") or
                                text_lower.startswith(ga.lower() + ",") or
                                text_lower.startswith(ga.lower() + "，") or
                                text_lower.startswith(ga.lower() + ".")
                                for ga in greeting_anchors))
            if has_emotion:
                qcm_default, qcm_reason = ("ROLE-Q07",
                    "Emotional anchor detected → AI Companion")
            elif has_greeting:
                qcm_default, qcm_reason = ("ROLE-Q01",
                    "Greeting detected → default entry (Chief Architect)")
            else:
                qcm_default, qcm_reason = ("ROLE-Q01",
                    "No hard keyword match → default entry (Chief Architect)")
            defaults = {
                "qcm": (qcm_default, qcm_reason),
                "trum": ("ROLE-T01", "No keyword match, defaulting to Sovereign"),
                "spec": ("ROLE-S01", "No keyword match, defaulting to Architect"),
            }
            role_code, reason = defaults.get(family, (qcm_default, "Ultimate fallback"))
            return role_code, 0.3, reason

        confidence = min(1.0, best_score / 3.0)

        # Append F21 summary to reasoning
        if best_role in f21_details:
            d = f21_details[best_role]
            best_reason += f" | F21[R={d['relevance']},A={d['affinity']},C={d['inv_cost']},K={d['knowledge']}]"

        return best_role, confidence, best_reason


# ═══════════════════════════════════════════════════════════
# 3. PROMPT BUILDER — Assemble system prompts from DB
# ═══════════════════════════════════════════════════════════

class KnowledgeResonance:
    """
    Sync wrapper around the Knowledge Resonance R-Formula.
    Bridges the knowledge retrieval async layer into the sync engine.

    R = 0.35×K_sim + 0.25×C_comp + 0.25×I_freq - 0.15×E_div

    This is NOT a stub — it's the actual formula with five memory types:
      Episodic (project history), Semantic (facts/standards),
      Procedural (skills/SOPs), Emotional (preferences), Somatic (runtime state)
    """

    W_SIM = 0.35
    W_COMP = 0.25
    W_FREQ = 0.25
    W_DIV = 0.15

    # Formula 7 parameters
    LAMBDA = 0.1      # Learning rate for weight adjustment
    R_TARGET = 0.85   # Target resonance value
    K_DECAY = 0.05    # Exponential decay constant
    CALIBRATION_INTERVAL = 10  # Calibrate every N searches

    def __init__(self, db: QSpectrumDB):
        self.db = db
        self._store = {}
        self._next_id = 1
        self._recent_r_values = []  # Track last 20 R-values
        self._search_count = 0  # Track searches for calibration trigger
        self._growth_snapshots = []  # F19: Track growth rate snapshots
        self._seed_from_db()
        self._load_persisted_state()  # Restore F7 weights + F19 snapshots from checkpoint

    def _seed_from_db(self):
        """Seed knowledge from DB tables: documents, knowledge_items, skill_definitions."""
        # Seed from documents table
        try:
            for row in self.db.query("SELECT title, file_path, doc_type FROM documents LIMIT 50"):
                r = dict(row)
                self._add("semantic", r["title"], [r.get("doc_type", "doc")],
                          source="platform.db/documents", importance=0.6, verified=True)
        except Exception:
            pass

        # Seed from skill_definitions
        try:
            for row in self.db.query("SELECT skill_name, description, category FROM skill_definitions LIMIT 30"):
                r = dict(row)
                self._add("procedural", f"{r['skill_name']}: {r.get('description', '')}",
                          [r.get("category", "skill")],
                          source="platform.db/skills", importance=0.7, verified=True)
        except Exception:
            pass

        # Seed from ai_roles (core system knowledge)
        for code, role in self.db.get_all_roles().items():
            caps = role.get("capabilities", "")
            self._add("semantic",
                       f"角色 {role['role_name']} ({code}): {caps[:100]}",
                       [role.get("family", "qcm"), "role"],
                       source="platform.db/ai_roles", importance=0.8, verified=True)

        # Seed system knowledge
        system_knowledge = [
            ("semantic", "Q-SpecTrum 三家族架構: Trum(戰略) + Spec(架構) + QCM(執行)",
             ["architecture", "governance"], 0.9),
            ("semantic", "Secretary 五維雷達: Track/Platform/People/Style/Supplement",
             ["secretary", "routing", "radar"], 0.9),
            ("procedural", "路由流程: Secretary→家族分配→角色選擇→LLM→知識沉澱",
             ["routing", "pipeline", "workflow"], 0.9),
            ("procedural", "QoS 三級: best_effort / assured / guaranteed",
             ["qos", "quality"], 0.7),
            ("procedural", "ARCS 協議: 10個跨家族協作協議, ProtocolExecutor 觸發",
             ["arcs", "protocol", "collaboration"], 0.8),
        ]
        for mtype, content, tags, importance in system_knowledge:
            self._add(mtype, content, tags, source="system", importance=importance, verified=True)

        # Seed from Skills/ directory (16 skill files: 12 invocable + 4 reference)
        self._seed_skills()

        # Seed DeerFlow capability knowledge
        self._seed_deerflow()

    def _seed_skills(self):
        """Load AI项目管理/Skills/*.md as procedural knowledge."""
        skills_dir = Path(__file__).parent / "AI项目管理" / "Skills"
        if not skills_dir.exists():
            return
        for md_file in sorted(skills_dir.glob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8", errors="ignore")[:500]
                # Extract title from YAML frontmatter or first heading
                title = md_file.stem
                for line in text.split("\n"):
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip()
                        break
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
                # Extract activation keywords
                activation = []
                in_activation = False
                for line in text.split("\n"):
                    if "激活词" in line or "激活詞" in line:
                        in_activation = True
                        continue
                    if in_activation and line.strip().startswith("- "):
                        kw = line.strip().lstrip("- `").rstrip("`").strip()
                        if kw:
                            activation.append(kw)
                    elif in_activation and not line.strip().startswith("- "):
                        in_activation = False
                # Extract family tag
                family_tag = "qcm"
                if "family: trum" in text:
                    family_tag = "trum"
                elif "family: spec" in text:
                    family_tag = "spec"
                content = f"技能 {title}"
                if activation:
                    content += f" (激活詞: {', '.join(activation[:4])})"
                self._add("procedural", content,
                          [family_tag, "skill"] + activation[:3],
                          source=f"Skills/{md_file.name}", importance=0.7, verified=True)
            except Exception:
                pass

    def _seed_deerflow(self):
        """Register DeerFlow capabilities as system knowledge."""
        deerflow_dir = Path(__file__).parent / "DeerFlow"
        if not deerflow_dir.exists():
            return
        deerflow_knowledge = [
            ("procedural",
             "DeerFlow 超級 Agent 引擎: LangGraph 多Agent調度, 支持 deep-research/data-analysis/consulting-analysis/github-deep-research/chart-visualization/find-skills 共6種真實技能",
             ["deerflow", "agent", "langraph", "research", "automation"], 0.8),
            ("procedural",
             "DeerFlow 集成: 可讀寫 Q-SpecTrum 項目文件, 執行 Python/Shell 腳本, 批量文檔處理, Web搜索",
             ["deerflow", "integration", "file", "script", "batch"], 0.7),
            ("procedural",
             "DeerFlow 啟動: 執行 start.sh (or start.bat on Windows) 或 python run.py --web",
             ["deerflow", "startup", "launch"], 0.6),
            ("procedural",
             "DeerFlow 真實技能目錄 (6 executors): deep-research/data-analysis/consulting-analysis/github-deep-research/chart-visualization/find-skills",
             ["deerflow", "skills", "capability"], 0.7),
        ]
        for mtype, content, tags, importance in deerflow_knowledge:
            self._add(mtype, content, tags, source="KNOWLEDGE-INDEX.md", importance=importance, verified=True)

        # Seed from ai-skill-system repos
        self._seed_skill_repos()

    def _seed_skill_repos(self):
        """Register ai-skill-system repos as procedural knowledge."""
        repos_dir = Path(__file__).parent / "AI项目管理" / "Systems" / "ai-skill-system" / "repos"
        if not repos_dir.exists():
            return
        repo_knowledge = {
            "skill-00-navigator": ("意圖識別+信心路由+交接生成, 自動判斷用戶需求並分發到正確技能",
                                   ["navigator", "intent", "routing", "分流", "意圖"]),
            "skill-03-scout": ("開源偵察: 7維評估矩陣(活躍度/社區/文檔/許可/性能/集成/安全)",
                               ["scout", "open source", "evaluation", "開源", "評估"]),
            "skill-04-planner": ("SOP→可執行手冊: 將標準操作流程轉為Phase-Task-Step結構",
                                 ["planner", "sop", "plan", "規劃", "手冊"]),
            "skill-05-validator": ("5維驗收: 功能40%+性能25%+安全20%+兼容10%+文檔5%",
                                   ["validator", "acceptance", "驗收", "測試", "quality"]),
            "skill-dev-sop-skill": ("技能開發SOP: 10階段技能開發流程(需求→設計→實現→測試→部署)",
                                    ["skill dev", "sop", "development", "開發"]),
            "super-prompt-engineer-skill": ("高級提示詞工程: 結構化提示設計+優化+評估",
                                            ["prompt", "engineering", "提示詞", "模板"]),
            "deer-flow": ("DeerFlow 完整源碼: LangGraph Agent框架+多Agent調度+沙箱執行",
                          ["deerflow", "source", "langraph", "agent"]),
        }
        for repo_name, (desc, tags) in repo_knowledge.items():
            repo_path = repos_dir / repo_name
            if repo_path.exists():
                self._add("procedural",
                          f"ai-skill-system/{repo_name}: {desc}",
                          tags + ["ai-skill-system"],
                          source=f"ai-skill-system/repos/{repo_name}",
                          importance=0.65, verified=True)

    def _load_persisted_state(self):
        """Restore F7 calibrated weights and F19 growth snapshots from checkpoint DB."""
        try:
            import sqlite3
            db_path = Path(__file__).parent / "knowledge_checkpoint.db"
            if not db_path.exists():
                return
            conn = sqlite3.connect(str(db_path), timeout=5)
            conn.row_factory = sqlite3.Row

            # Restore F7 weights
            try:
                rows = conn.execute("SELECT key, value FROM calibration_state").fetchall()
                weight_map = {r["key"]: r["value"] for r in rows}
                if "W_SIM" in weight_map:
                    self.W_SIM = weight_map["W_SIM"]
                    self.W_COMP = weight_map.get("W_COMP", self.W_COMP)
                    self.W_FREQ = weight_map.get("W_FREQ", self.W_FREQ)
                    self.W_DIV = weight_map.get("W_DIV", self.W_DIV)
            except Exception:
                pass  # Table may not exist yet

            # Restore F19 growth snapshots
            try:
                rows = conn.execute(
                    "SELECT timestamp, experience, spread, dK_dt, total_knowledge "
                    "FROM growth_snapshots ORDER BY id DESC LIMIT 50"
                ).fetchall()
                self._growth_snapshots = [
                    {"timestamp": r["timestamp"], "E": r["experience"],
                     "S": r["spread"], "dK_dt": r["dK_dt"],
                     "total_knowledge": r["total_knowledge"]}
                    for r in reversed(rows)
                ]
            except Exception:
                pass  # Table may not exist yet

            conn.close()
        except Exception:
            pass  # Non-fatal

    def _add(self, memory_type, content, tags=None, source="", importance=0.5,
             verified=False, role_code=""):
        eid = f"K{self._next_id:04d}"
        self._next_id += 1
        import time
        self._store[eid] = {
            "id": eid, "type": memory_type, "content": content,
            "tags": tags or [], "source": source,
            "importance": importance, "verified": verified,
            "access_count": 0, "created_at": time.time(),
            "role_code": role_code,  # F21: Track which role produced this knowledge
        }

    def search(self, query, top_k=5):
        """
        Search using Knowledge Resonance Formula.
        Returns list of (content, score, explanation).
        """
        import math
        import time

        # Guard against None or non-string query
        if query is None or not isinstance(query, str):
            query = str(query or "")

        query_lower = query.lower()
        query_tokens = set(query_lower.split())
        results = []

        for entry in self._store.values():
            content_lower = entry["content"].lower()
            content_tokens = set(content_lower.split())
            tag_tokens = set(t.lower() for t in entry["tags"])
            all_tokens = content_tokens | tag_tokens

            # K_sim: keyword similarity (token overlap + substring matching for CJK)
            overlap = query_tokens & all_tokens
            k_sim = len(overlap) / max(len(query_tokens), 1) if query_tokens else 0

            # CJK substring boost: check if query substrings appear in content or tags
            cjk_hits = 0
            all_text = content_lower + " " + " ".join(t.lower() for t in entry["tags"])
            for qt in query_tokens:
                if len(qt) >= 2 and qt not in overlap:
                    if qt in all_text:
                        cjk_hits += 1
            # Also check if full query (without spaces) appears as substring
            query_joined = query_lower.replace(" ", "")
            if len(query_joined) >= 2 and query_joined in all_text.replace(" ", ""):
                cjk_hits += 2
            if cjk_hits > 0:
                k_sim = min(1.0, k_sim + cjk_hits * 0.25)

            # C_comp: complementarity (novel info)
            novel = content_tokens - query_tokens
            c_comp = min(1.0, len(novel) / max(len(content_tokens), 1))

            # I_freq: access frequency
            i_freq = min(1.0, entry["access_count"] / 50)

            # E_div: entropy divergence (unverified penalty)
            e_div = 0.0 if entry["verified"] else 0.3

            # R = w1*K_sim + w2*C_comp + w3*I_freq - w4*E_div
            r_score = (self.W_SIM * k_sim + self.W_COMP * c_comp +
                       self.W_FREQ * i_freq - self.W_DIV * e_div)

            # Freshness modifier
            age_hours = (time.time() - entry["created_at"]) / 3600
            freshness = math.exp(-0.01 * age_hours)
            r_score *= (0.7 + 0.3 * freshness) * (0.5 + 0.5 * entry["importance"])

            if r_score > 0.03:
                entry["access_count"] += 1
                explanation = (f"R={r_score:.3f} [sim={k_sim:.2f} comp={c_comp:.2f} "
                               f"freq={i_freq:.2f} div={e_div:.2f}] ({entry['type']})")
                results.append((entry["content"], r_score, explanation))

        results.sort(key=lambda x: x[1], reverse=True)
        top_results = results[:top_k]

        # Track average R-value and trigger calibration if needed
        if top_results:
            avg_r = sum(r[1] for r in top_results) / len(top_results)
            self._recent_r_values.append(avg_r)
            if len(self._recent_r_values) > 20:
                self._recent_r_values.pop(0)

        self._search_count += 1
        if self._search_count % self.CALIBRATION_INTERVAL == 0:
            self._calibrate_weights()

        return top_results

    def deposit(self, user_input, response, role_code, family):
        """Deposit interaction as episodic knowledge (sedimentation)."""
        summary = f"[{role_code}] Q: {user_input[:60]} → A: {response[:80]}"
        self._add("episodic", summary, [family, role_code, "interaction"],
                  source="engine", importance=0.4, role_code=role_code)

        # 跨路徑知識共享 — 每 5 次沉澱自動寫入 knowledge_checkpoint.db
        self._deposits_since_save = getattr(self, '_deposits_since_save', 0) + 1
        if self._deposits_since_save >= 5:
            self._save_checkpoint()
            self._deposits_since_save = 0

    def _save_checkpoint(self):
        """Save knowledge to shared checkpoint DB for cross-path state sharing."""
        try:
            import sqlite3
            import tempfile
            # Use writable path (prefer project root, fallback to temp)
            _root = Path(__file__).parent
            _test = _root / ".write_test"
            try:
                _test.touch()
                _test.unlink(missing_ok=True)
                db_path = _root / "knowledge_checkpoint.db"
            except (OSError, IOError, PermissionError):
                _fallback = Path(tempfile.gettempdir()) / "qspectrum_data"
                _fallback.mkdir(parents=True, exist_ok=True)
                db_path = _fallback / "knowledge_checkpoint.db"
            conn = sqlite3.connect(str(db_path), timeout=10)
            conn.execute("""CREATE TABLE IF NOT EXISTS engine_knowledge (
                entry_id TEXT PRIMARY KEY, memory_type TEXT, content TEXT,
                source TEXT, tags TEXT, importance REAL, created_at REAL,
                role_code TEXT DEFAULT '')""")
            for eid, entry in self._store.items():
                conn.execute(
                    "INSERT OR REPLACE INTO engine_knowledge VALUES (?,?,?,?,?,?,?,?)",
                    (eid, entry["type"], entry["content"], entry["source"],
                     json.dumps(entry["tags"]), entry["importance"], entry["created_at"],
                     entry.get("role_code", ""))
                )

            # Persist F7 calibrated weights so they survive restarts
            conn.execute("""CREATE TABLE IF NOT EXISTS calibration_state (
                key TEXT PRIMARY KEY, value REAL)""")
            for k, v in [("W_SIM", self.W_SIM), ("W_COMP", self.W_COMP),
                         ("W_FREQ", self.W_FREQ), ("W_DIV", self.W_DIV)]:
                conn.execute("INSERT OR REPLACE INTO calibration_state VALUES (?,?)", (k, v))

            # Persist F19 growth snapshots for F20 historical rate calculation
            conn.execute("""CREATE TABLE IF NOT EXISTS growth_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT, experience INT, spread REAL, dK_dt REAL, total_knowledge INT)""")
            snapshots = getattr(self, '_growth_snapshots', [])
            if snapshots:
                # Save only the latest 20 snapshots (avoid unbounded growth)
                for s in snapshots[-20:]:
                    conn.execute(
                        "INSERT INTO growth_snapshots (timestamp, experience, spread, dK_dt, total_knowledge) VALUES (?,?,?,?,?)",
                        (s["timestamp"], s["E"], s["S"], s["dK_dt"], s["total_knowledge"]))

            conn.commit()
            conn.close()
        except Exception:
            pass  # Non-fatal — knowledge persistence is best-effort

    def _calibrate_weights(self):
        """
        Formula 7: Dynamic Weight Adjustment
        w_{i,t} = w_{i,t-1} + λ·(R_{t-1} - R_target)·e^{-k·t}·g_i

        Adjusts weights based on recent R-values:
        - If avg R > R_target: system is overconfident, reduce weights slightly
        - If avg R < R_target: system lacks sensitivity, increase weights
        - Uses exponential decay to converge over time
        - Normalizes to sum to 1.0 after adjustment
        """
        import math
        if len(self._recent_r_values) < 2:
            return

        # Calculate average R from recent searches
        avg_r = sum(self._recent_r_values) / len(self._recent_r_values)
        r_error = avg_r - self.R_TARGET
        time_decay = math.exp(-self.K_DECAY * self._search_count)

        # Weight adjustment factors per component
        # Heuristic: SIM and COMP are primary, FREQ is secondary, DIV is penalty
        adjustment_factors = {
            "sim": 0.35,   # g_i factors (component influence)
            "comp": 0.25,
            "freq": 0.25,
            "div": 0.15,
        }

        # Calculate deltas for each weight
        old_weights = {
            "sim": self.W_SIM,
            "comp": self.W_COMP,
            "freq": self.W_FREQ,
            "div": self.W_DIV,
        }

        new_weights = {}
        max_delta = 0.0

        for component, old_w in old_weights.items():
            delta_w = self.LAMBDA * r_error * time_decay * adjustment_factors[component]
            new_w = old_w + delta_w
            # Clamp weights to [0.05, 0.50] to maintain stability
            new_w = max(0.05, min(0.50, new_w))
            new_weights[component] = new_w
            max_delta = max(max_delta, abs(delta_w))

        # Check convergence: if |Δw| < 0.001, weights have stabilized
        if max_delta < 0.001:
            # Silently converged, no log needed for sync version
            return

        # Normalize weights to sum to 1.0
        total = sum(new_weights.values())
        if total > 0:
            for component in new_weights:
                new_weights[component] /= total

        # Apply new weights
        self.W_SIM = new_weights["sim"]
        self.W_COMP = new_weights["comp"]
        self.W_FREQ = new_weights["freq"]
        self.W_DIV = new_weights["div"]

        # Optional: print calibration info for debugging
        # print(f"[KnowledgeResonance] Formula 7 calibration: R={avg_r:.3f} "
        #       f"(target={self.R_TARGET}) | W_SIM={self.W_SIM:.3f} W_COMP={self.W_COMP:.3f} "
        #       f"W_FREQ={self.W_FREQ:.3f} W_DIV={self.W_DIV:.3f}")

    @property
    def total_entries(self):
        return len(self._store)

    # ═══════════════════════════════════════════════════════════
    # Formula 19: Knowledge Growth Rate
    # dK/dt = η · E^(1/3) · S^(0.7)
    # η = learning efficiency, E = experience, S = knowledge spread
    # ═══════════════════════════════════════════════════════════

    ETA = 0.08          # Learning efficiency coefficient
    GROWTH_HISTORY = []  # Track growth snapshots for F20 integration

    def knowledge_growth_rate(self, experience: int = None, spread: float = None) -> dict:
        """
        F19: Compute instantaneous knowledge growth rate.

        dK/dt = η · E^(1/3) · S^(0.7)

        Where:
            η (ETA) = learning efficiency coefficient (0.08 default)
            E = accumulated experience (interaction count or deposit count)
            S = knowledge spread/diversity (unique categories / total possible)

        Returns dict with rate value and component breakdown.
        """
        import math

        # E = experience: default to total knowledge entries
        E = experience if experience is not None else len(self._store)
        E = max(1, E)  # Avoid zero

        # S = spread: ratio of unique memory types active vs total (5 types)
        if spread is not None:
            S = spread
        else:
            active_types = set()
            for entry in self._store.values():
                active_types.add(entry.get("type", "episodic"))
            S = len(active_types) / 5.0  # 5 memory types: episodic, semantic, procedural, emotional, somatic
            S = max(0.01, S)  # Avoid zero

        # dK/dt = η · E^(1/3) · S^(0.7)
        dK_dt = self.ETA * math.pow(E, 1.0 / 3.0) * math.pow(S, 0.7)

        # Track for F20 integration
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "E": E,
            "S": round(S, 4),
            "dK_dt": round(dK_dt, 6),
            "total_knowledge": len(self._store),
        }
        if not hasattr(self, '_growth_snapshots'):
            self._growth_snapshots = []
        self._growth_snapshots.append(snapshot)
        # Keep last 100 snapshots
        if len(self._growth_snapshots) > 100:
            self._growth_snapshots = self._growth_snapshots[-100:]

        return {
            "formula": "F19: dK/dt = η·E^(1/3)·S^(0.7)",
            "eta": self.ETA,
            "experience": E,
            "spread": round(S, 4),
            "growth_rate": round(dK_dt, 6),
            "interpretation": self._interpret_growth(dK_dt),
        }

    def _interpret_growth(self, rate: float) -> str:
        """Interpret the growth rate for human-readable output."""
        if rate < 0.01:
            return "stagnant — system needs more diverse inputs"
        elif rate < 0.05:
            return "slow growth — expanding experience will accelerate"
        elif rate < 0.15:
            return "healthy growth — knowledge accumulating steadily"
        elif rate < 0.30:
            return "rapid growth — high learning efficiency"
        else:
            return "exponential phase — maximize knowledge crystallization"

    # ═══════════════════════════════════════════════════════════
    # Formula 20: Knowledge Volume Prediction
    # K(t) = K₀ + Σᵢ η · E(tᵢ)^(1/3) · S(tᵢ)^(0.7) · Δt
    # Explicit time evolution of knowledge volume
    # ═══════════════════════════════════════════════════════════

    def predict_knowledge_volume(self, future_steps: int = 10,
                                  projected_experience_growth: float = 1.0) -> dict:
        """
        F20: Predict future knowledge volume using discrete integration.

        K(t) = K₀ + Σᵢ η · E(tᵢ)^(1/3) · S(tᵢ)^(0.7) · Δt

        Args:
            future_steps: Number of future time steps to predict
            projected_experience_growth: Expected new experiences per step

        Returns dict with current volume, predicted trajectory, and growth metrics.
        """
        import math

        K_0 = len(self._store)  # Current knowledge volume

        # Current state
        active_types = set()
        for entry in self._store.values():
            active_types.add(entry.get("type", "episodic"))
        S_current = max(0.01, len(active_types) / 5.0)
        E_current = max(1, K_0)

        # Compute historical average growth if snapshots exist
        snapshots = getattr(self, '_growth_snapshots', [])
        avg_historical_rate = 0.0
        if snapshots:
            rates = [s["dK_dt"] for s in snapshots]
            avg_historical_rate = sum(rates) / len(rates)

        # Discrete integration: K(t+Δt) = K(t) + dK/dt · Δt
        trajectory = []
        K_t = float(K_0)
        E_t = float(E_current)
        S_t = S_current

        for step in range(1, future_steps + 1):
            # Project experience growth
            E_t += projected_experience_growth
            # Spread slowly converges toward 1.0 as more types activate
            S_t = min(1.0, S_t + 0.02 * (1.0 - S_t))

            # F19: dK/dt at this projected step
            dK_dt = self.ETA * math.pow(E_t, 1.0 / 3.0) * math.pow(S_t, 0.7)

            # Integrate
            K_t += dK_dt

            trajectory.append({
                "step": step,
                "K": round(K_t, 2),
                "dK_dt": round(dK_dt, 6),
                "E": round(E_t, 1),
                "S": round(S_t, 4),
            })

        # Compute time-to-double
        if avg_historical_rate > 0 and K_0 > 0:
            time_to_double = K_0 / avg_historical_rate
        else:
            time_to_double = None

        return {
            "formula": "F20: K(t) = K₀ + Σ η·E(tᵢ)^(1/3)·S(tᵢ)^(0.7)·Δt",
            "current_volume": K_0,
            "predicted_volume_final": round(trajectory[-1]["K"], 2) if trajectory else K_0,
            "growth_trajectory": trajectory,
            "avg_historical_rate": round(avg_historical_rate, 6),
            "time_to_double": round(time_to_double, 1) if time_to_double else None,
            "health": self._assess_knowledge_health(K_0, avg_historical_rate, S_current),
        }

    def _assess_knowledge_health(self, volume: int, rate: float, spread: float) -> str:
        """Assess overall knowledge system health."""
        score = 0
        if volume >= 10:
            score += 1
        if volume >= 50:
            score += 1
        if rate > 0.05:
            score += 1
        if rate > 0.15:
            score += 1
        if spread >= 0.6:
            score += 1
        labels = ["critical", "developing", "stable", "healthy", "thriving", "optimal"]
        return labels[min(score, len(labels) - 1)]

    # ═══════════════════════════════════════════════════════════
    # Formula 21 support: Knowledge-based routing factors
    # Provides knowledge context scores for F21 argmax decision
    # ═══════════════════════════════════════════════════════════

    def get_role_knowledge_affinity(self, role_code: str) -> float:
        """
        Compute how much knowledge is associated with a given role.
        Used by F21 argmax decision to factor in knowledge depth.
        Returns a 0.0-1.0 score.
        """
        if not self._store:
            return 0.0
        role_entries = sum(1 for e in self._store.values()
                          if e.get("role_code") == role_code)
        return min(1.0, role_entries / max(1, len(self._store) * 0.3))


class PromptBuilder:
    """Build structured prompts from role definitions in DB + Knowledge Resonance."""

    SYSTEM_TEMPLATE = """你是 Q-SpecTrum 系統中的 {role_name}。

## 你的身份
- 角色代碼: {role_code}
- 家族: {family_display}
- 核心能力: {capabilities}

## 你的激活卡
{activation_card}

## 行為準則
1. 你是 {family_display} 家族的成員，按照家族職責行事
2. 回答時使用你的專業能力，不要超出職責範圍
3. 如果問題不在你的能力範圍，建議轉交給更合適的角色
4. 保持專業但友善的語氣
5. 重要決策要解釋推理過程

## 知識上下文
{knowledge_context}
"""

    FAMILY_DISPLAY = {
        "trum": "Trum（戰略層）",
        "spec": "Spec（架構層）",
        "qcm": "QCM（執行層）",
    }

    def __init__(self, db: QSpectrumDB, knowledge: KnowledgeResonance = None):
        self.db = db
        self.knowledge = knowledge

    def build_system_prompt(self, role_code: str, knowledge_context: str = "") -> str:
        """Build a complete system prompt for the given role."""
        role = self.db.get_role(role_code)
        if not role:
            return "你是 Q-SpecTrum AI 助手。"

        caps = role.get("capabilities_list", [])
        caps_str = "、".join(caps) if caps else role.get("capabilities", "通用助手")

        card = role.get("activation_card", "")
        if not card or len(card) < 50:
            card = f"作為 {role['role_name']}，你負責 {caps_str}。"

        # Truncate very long cards (ROLE-T03 is 6784 chars)
        if len(card) > 2000:
            card = card[:2000] + "\n\n[... 完整激活卡已截斷，核心職責如上 ...]"

        return self.SYSTEM_TEMPLATE.format(
            role_name=role["role_name"],
            role_code=role_code,
            family_display=self.FAMILY_DISPLAY.get(role.get("family", "qcm"), "QCM"),
            capabilities=caps_str,
            activation_card=card,
            knowledge_context=knowledge_context or "（本次無額外知識上下文）",
        )

    def build_knowledge_context(self, user_input: str) -> str:
        """
        Build knowledge context using BOTH:
        1. Knowledge Resonance Formula (R-formula search over memory)
        2. DB documents table (file-based knowledge)
        """
        parts = []

        # Source 1: Knowledge Resonance search
        if self.knowledge:
            results = self.knowledge.search(user_input, top_k=3)
            if results:
                resonance_lines = []
                for content, score, explanation in results:
                    resonance_lines.append(f"- [{score:.2f}] {content[:120]}")
                parts.append("知識共振結果 (R-Formula):\n" + "\n".join(resonance_lines))

        # Source 2: DB documents table
        try:
            keywords = [w for w in user_input.split() if len(w) > 1][:5]
            if keywords:
                doc_results = []
                for kw in keywords:
                    rows = self.db.query(
                        "SELECT title, file_path FROM documents WHERE title LIKE ? LIMIT 3",
                        (f"%{kw}%",)
                    )
                    for r in rows:
                        doc_results.append(f"- {dict(r)['title']} ({dict(r)['file_path']})")
                if doc_results:
                    parts.append("相關文檔:\n" + "\n".join(doc_results[:5]))
        except Exception:
            pass

        return "\n\n".join(parts) if parts else ""


# ═══════════════════════════════════════════════════════════
# 4. LLM PROVIDER — Mock + Real API support
# ═══════════════════════════════════════════════════════════

class LLMProvider:
    """Base class for LLM providers."""
    def generate(self, system_prompt: str, user_message: str, **kwargs) -> str:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """
    Smart Mock LLM v2.0 — delegates to SmartMockEngine for contextual,
    intent-aware, role-specific responses that make Q-SpecTrum useful without API keys.

    智能 Mock LLM v2.0 — 基于意图分类和角色特性生成有差异化的回复。
    """

    def __init__(self, db: QSpectrumDB = None):
        self.db = db
        # Import and initialize SmartMockEngine
        try:
            from smart_mock_llm import SmartMockEngine
            self._engine = SmartMockEngine(db=db)
        except ImportError:
            # Fallback: try relative import from same directory
            try:
                import importlib.util
                _spec = importlib.util.spec_from_file_location(
                    "smart_mock_llm",
                    Path(__file__).parent / "smart_mock_llm.py"
                )
                _mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                self._engine = _mod.SmartMockEngine(db=db)
            except Exception:
                self._engine = None

    def generate(self, system_prompt: str, user_message: str, **kwargs) -> str:
        """Smart Mock LLM v2.0 — intent-aware, role-specific responses.

        智能 Mock v2.0 — 意图分类 + 角色人格 + 知识库集成。
        NOTE: This is OFFLINE mode. Set OPENAI_API_KEY or ANTHROPIC_API_KEY for real AI.
        """
        if self._engine is not None:
            return self._engine.generate(system_prompt, user_message, **kwargs)

        # Ultra-fallback if SmartMockEngine failed to load
        role_name = kwargs.get("role_name", "AI 助手")
        msg = user_message.strip()[:100]
        return (
            f"**{role_name}**\n\n"
            f"收到: 「{msg}」\n\n"
            f"[Offline Mode — 设置 API Key 获取真实AI回复 / Set API Key for real AI]"
        )


class OpenAIProvider(LLMProvider):
    """Real OpenAI API provider (zero-dependency: uses urllib if SDK missing).
    Also compatible with any OpenAI-compatible API via OPENAI_BASE_URL.
    """
    def __init__(self, api_key=None, model=None, base_url=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL",
                         "https://api.openai.com/v1")).rstrip("/")
        if not self.api_key:
            raise ValueError("OpenAI API key required (set OPENAI_API_KEY)")

    def generate(self, system_prompt: str, user_message: str, **kwargs) -> str:
        # Try SDK first
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=4000, temperature=0.7,
            )
            return response.choices[0].message.content
        except ImportError:
            pass  # SDK not installed, fall through
        except Exception as e:
            return f"[OpenAI SDK Error: {e}]"
        # Zero-dependency fallback via urllib
        try:
            import urllib.request
            data = json.dumps({
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 4000, "temperature": 0.7,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions", data=data,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {self.api_key}"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[OpenAI Error: {e}]"


class AnthropicProvider(LLMProvider):
    """Real Anthropic Claude API provider (zero-dependency urllib fallback)."""
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        if not self.api_key:
            raise ValueError("Anthropic API key required (set ANTHROPIC_API_KEY)")

    def generate(self, system_prompt: str, user_message: str, **kwargs) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model, max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        except ImportError:
            pass
        except Exception as e:
            return f"[Anthropic SDK Error: {e}]"
        # Zero-dependency fallback
        try:
            import urllib.request
            data = json.dumps({
                "model": self.model, "max_tokens": 4000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages", data=data,
                headers={"Content-Type": "application/json",
                         "x-api-key": self.api_key,
                         "anthropic-version": "2023-06-01"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                return result["content"][0]["text"]
        except Exception as e:
            return f"[Anthropic Error: {e}]"


class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider (OpenAI-compatible, zero-dependency)."""
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        if not self.api_key:
            raise ValueError("DeepSeek API key required (set DEEPSEEK_API_KEY)")

    def generate(self, system_prompt: str, user_message: str, **kwargs) -> str:
        try:
            import urllib.request
            data = json.dumps({
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 4000, "temperature": 0.7,
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions", data=data,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {self.api_key}"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[DeepSeek Error: {e}]"


class OpenRouterProvider(LLMProvider):
    """OpenRouter — access 100+ models via single API key (zero-dependency)."""
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.model = model or os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
        if not self.api_key:
            raise ValueError("OpenRouter API key required (set OPENROUTER_API_KEY)")

    def generate(self, system_prompt: str, user_message: str, **kwargs) -> str:
        try:
            import urllib.request
            data = json.dumps({
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 4000, "temperature": 0.7,
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions", data=data,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {self.api_key}",
                         "HTTP-Referer": "https://q-spectrum.dev",
                         "X-Title": "Q-SpecTrum"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[OpenRouter Error: {e}]"


class OllamaProvider(LLMProvider):
    """Local Ollama provider (zero-dependency)."""
    def __init__(self, model=None, base_url=None):
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3")
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL",
                         "http://localhost:11434")).rstrip("/")

    def generate(self, system_prompt: str, user_message: str, **kwargs) -> str:
        try:
            import urllib.request
            data = json.dumps({
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/chat", data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                return result["message"]["content"]
        except Exception as e:
            return f"[Ollama Error: {e}]"


def create_llm_provider(provider_name=None, db=None):
    """
    Factory: create the right LLM provider based on config.

    Supported providers:
      mock       — Smart Mock (default, always works, no API key)
      openai     — OpenAI (needs OPENAI_API_KEY)
      anthropic  — Anthropic Claude (needs ANTHROPIC_API_KEY)
      deepseek   — DeepSeek (needs DEEPSEEK_API_KEY)
      openrouter — OpenRouter 100+ models (needs OPENROUTER_API_KEY)
      ollama     — Local Ollama (needs ollama running)

    All providers use zero-dependency urllib fallback — NO pip install required.

    Priority when provider_name is None or "auto":
      1. Check QSPECTRUM_LLM env var
      2. Auto-detect: Ollama → OpenAI → Anthropic → DeepSeek → OpenRouter → Mock
    """
    name = (provider_name or os.environ.get("QSPECTRUM_LLM", "auto")).lower()

    if name == "openai":
        return OpenAIProvider(), f"OpenAI ({os.environ.get('OPENAI_MODEL', 'gpt-4o')})"
    elif name == "anthropic":
        return AnthropicProvider(), f"Anthropic ({os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4')})"
    elif name == "deepseek":
        return DeepSeekProvider(), f"DeepSeek ({os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')})"
    elif name == "openrouter":
        return OpenRouterProvider(), f"OpenRouter ({os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4')})"
    elif name == "ollama":
        model = os.environ.get("OLLAMA_MODEL", "llama3")
        return OllamaProvider(), f"Ollama ({model})"
    elif name == "mock":
        return MockLLMProvider(db=db), "Mock (context-aware)"
    else:
        # Auto-detect best available provider
        # 1. Check Ollama (free, local, no API key)
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    return OllamaProvider(), f"Ollama ({os.environ.get('OLLAMA_MODEL', 'llama3')}) [auto]"
        except Exception:
            pass
        # 2. Check OpenAI key
        if os.environ.get("OPENAI_API_KEY", "").startswith("sk-"):
            return OpenAIProvider(), "OpenAI [auto]"
        # 3. Check Anthropic key
        if os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-ant-"):
            return AnthropicProvider(), "Anthropic Claude [auto]"
        # 4. Check DeepSeek key
        if os.environ.get("DEEPSEEK_API_KEY", ""):
            return DeepSeekProvider(), "DeepSeek [auto]"
        # 5. Check OpenRouter key
        if os.environ.get("OPENROUTER_API_KEY", ""):
            return OpenRouterProvider(), "OpenRouter [auto]"
        # 6. Fallback to smart mock (always works)
        return MockLLMProvider(db=db), "Mock (context-aware)"


# ═══════════════════════════════════════════════════════════
# 5. PROTOCOL BRIDGE — Connect to Platform scripts
# ═══════════════════════════════════════════════════════════

class ProtocolBridge:
    """Bridge to Platform/scripts/ engines (when available)."""

    def __init__(self):
        self._workflow_engine = None
        self._protocol_executor = None
        self._agent_runtime = None
        self._load_engines()

    def _load_engines(self):
        scripts_dir = Path(__file__).parent / "AI项目管理" / "Platform" / "scripts"
        if not scripts_dir.exists():
            return

        sys.path.insert(0, str(scripts_dir))
        try:
            from workflow_engine import WorkflowEngine
            self._workflow_engine = WorkflowEngine()
        except Exception:
            pass
        try:
            from protocol_executor import ProtocolExecutor
            db_path = str(scripts_dir.parent / "db" / "platform.db")
            self._protocol_executor = ProtocolExecutor(db_path)
        except Exception:
            pass

    def list_workflows(self):
        if self._workflow_engine:
            try:
                return self._workflow_engine.list_workflows()
            except Exception:
                # Handle SQLite threading issues gracefully
                return self._list_workflows_safe()
        return []

    def _list_workflows_safe(self):
        """Thread-safe fallback: open a new connection."""
        import sqlite3
        scripts_dir = Path(__file__).parent / "AI项目管理" / "Platform" / "db" / "platform.db"
        try:
            conn = sqlite3.connect(f"file:{scripts_dir.resolve()}?immutable=1",
                                   uri=True, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM workflow_definitions").fetchall()
            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            return []

    def run_workflow(self, wf_code):
        if self._workflow_engine:
            return self._workflow_engine.run_workflow(wf_code)
        return {"error": "Workflow engine not available"}

    def trigger_protocol(self, proto_code):
        if self._protocol_executor:
            return self._protocol_executor.trigger_protocol(proto_code)
        return {"error": "Protocol executor not available"}

    def list_protocols(self):
        if self._protocol_executor:
            try:
                return self._protocol_executor.list_protocols()
            except Exception:
                return self._list_protocols_safe()
        return []

    def _list_protocols_safe(self):
        """Thread-safe fallback."""
        import sqlite3
        db_path = Path(__file__).parent / "AI项目管理" / "Platform" / "db" / "platform.db"
        try:
            conn = sqlite3.connect(f"file:{db_path.resolve()}?immutable=1",
                                   uri=True, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM collaboration_protocols").fetchall()
            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            return []


# ═══════════════════════════════════════════════════════════
# 6. Q-SPECTRUM ENGINE — The unified pipeline
# ═══════════════════════════════════════════════════════════

class QSpectrumEngine:
    """
    The unified Q-SpecTrum engine that connects everything.
    This is what makes Q-SpecTrum REAL, not just a framework.
    """

    def __init__(self, llm_provider=None):
        # Initialize components
        self.db = QSpectrumDB()
        self.secretary = Secretary(self.db)
        self.knowledge = KnowledgeResonance(self.db)
        self.prompt_builder = PromptBuilder(self.db, knowledge=self.knowledge)
        self.protocol_bridge = ProtocolBridge()
        # Knowledge Graph + Vector Store — via brain_core GraphEngine
        if _HAS_BRAIN_CORE:
            _ge = GraphEngine()
            self.graph = _ge.graph
            self.vector_store = _ge.vector_store
        else:
            self.graph = None
            try:
                from knowledge_graph import KnowledgeGraph
                self.graph = KnowledgeGraph()
            except Exception:
                pass
            self.vector_store = None
            try:
                from vector_store import VectorStore
                self.vector_store = VectorStore()
            except Exception:
                pass

        if llm_provider:
            # Handle both tuple (from create_llm_provider) and direct provider instance
            if isinstance(llm_provider, tuple):
                self.llm, self.llm_name = llm_provider
            else:
                self.llm = llm_provider
                self.llm_name = type(llm_provider).__name__
        else:
            self.llm, self.llm_name = create_llm_provider(db=self.db)

        # DeerFlow integration bridge (lazy load via deerflow_bridge.py)
        self.deerflow = None
        try:
            from deerflow_bridge import DeerFlowBridge
            bridge = DeerFlowBridge()
            if bridge.status().get("installed"):
                self.deerflow = bridge
        except Exception:
            pass

        # Ghost Channel — the nervous system (QCM core thesis)
        # "幽灵通道 = 0 → 整个系统价值 = 0"
        self.ghost_channel = None
        try:
            from ghost_channel_adapter import GhostChannelAdapter
            self.ghost_channel = GhostChannelAdapter()
        except Exception:
            pass

        # src/ Bridge — connects advanced theoretical components
        # Sandbox (F13-15), CostFunction (F22), Flywheel (F16-18),
        # DeadlockDetector (F12), KnowledgeLayer TF-IDF
        self.src_bridge = None
        try:
            from src_bridge import SrcBridge
            self.src_bridge = SrcBridge()
        except Exception:
            pass

        # Skill Executor — can execute DeerFlow + Q-SpecTrum skills
        self.skill_executor = None
        try:
            from skill_executor import SkillExecutor
            self.skill_executor = SkillExecutor()
        except Exception:
            pass

        # Real skill executors (process data without LLM)
        self.real_skills = None
        try:
            from real_skills import RealSkillExecutor
            self.real_skills = RealSkillExecutor(project_root=str(Path(__file__).parent))
        except Exception:
            pass

        # DeerFlow Real Skills (local execution of DeerFlow skills)
        self.deerflow_real_skills = None
        try:
            from deerflow_real_skills import DeerFlowRealSkills
            self.deerflow_real_skills = DeerFlowRealSkills(
                project_root=str(Path(__file__).parent))
        except Exception:
            pass

        # Closed-Loop Architecture — 閉環管道
        # Resource Collection → Execution → Result Persistence → Feedback → Routing Tuning
        self.closed_loop = None
        try:
            import tempfile as _tmpmod

            from closed_loop import ClosedLoopManager
            # Determine writable path for user_resources.db
            _cl_root = Path(__file__).parent
            _cl_db_path = str(_cl_root / "user_resources.db")
            try:
                _tc2 = sqlite3.connect(_cl_db_path, timeout=10, check_same_thread=False)
                _tc2.execute("CREATE TABLE IF NOT EXISTS _t(x)")
                _tc2.commit()
                _tc2.close()
            except Exception:
                _tmpdir = Path(_tmpmod.gettempdir()) / "qspectrum_data"
                _tmpdir.mkdir(parents=True, exist_ok=True)
                _cl_db_path = str(_tmpdir / "user_resources.db")
            self.closed_loop = ClosedLoopManager(
                resource_db_path=_cl_db_path,
            )
        except Exception:
            pass

        # Wire closed-loop feedback → Secretary routing
        if self.closed_loop:
            self.secretary._feedback_fn = self.closed_loop.get_role_affinity

        # Wire F21 dependencies → Secretary argmax decision
        self.secretary._knowledge = self.knowledge
        if self.src_bridge:
            self.secretary._cost_bridge = self.src_bridge.cost

        # Simulation Flywheel — 沙盘推演飞轮
        # Multi-dimensional war-game reasoning before execution
        self.simulation_flywheel = None
        try:
            from src.engine.simulation_flywheel import SimulationFlywheel
            self.simulation_flywheel = SimulationFlywheel()
        except Exception:
            pass

        # ── Closed-Loop Core Components (closed_loop_core.py) ──
        # These extend the basic closed_loop.py with deeper capabilities:
        # KnowledgePipeline: auto task→knowledge→evolution sedimentation
        # ProjectOrchestrator: multi-project management + result aggregation
        # ComponentRegistry: hot-swap port for pluggable components (Point #15)
        # UserGrowthEngine: S1→S5 progressive capability unlocking
        self.knowledge_pipeline = None
        self.project_orchestrator = None
        self.component_registry = None
        self.user_growth = None
        self.negotiation_engine = None

        try:
            from closed_loop_core import (
                ComponentRegistry,
                KnowledgePipeline,
                ProjectOrchestrator,
                UserGrowthEngine,
            )

            # Determine writable DB directory — via brain_core
            _writable_dir = detect_writable_dir() if _HAS_BRAIN_CORE else Path(__file__).parent
            self._writable_dir = _writable_dir

            # Knowledge Pipeline — auto-sedimentation from every task result
            self.knowledge_pipeline = KnowledgePipeline(
                db_path=str(_writable_dir / "knowledge_pipeline.db"))

            # Project Orchestrator — multi-project "AI one-person company" (Point #11)
            self.project_orchestrator = ProjectOrchestrator(
                db_path=str(_writable_dir / "projects.db"))

            # Component Registry — hot-swap port (Point #15)
            self.component_registry = ComponentRegistry()
            # Register all existing engine components for hot-swap visibility
            if self.ghost_channel:
                self.component_registry.register(
                    "protocol", "ghost_channel", self.ghost_channel, "1.0")
            if self.deerflow:
                self.component_registry.register(
                    "skill_executor", "deerflow", self.deerflow, "1.0")
            if self.src_bridge:
                self.component_registry.register(
                    "formula_bridge", "src_bridge", self.src_bridge, "1.0")
            if self.closed_loop:
                self.component_registry.register(
                    "closed_loop", "manager", self.closed_loop, "1.0")
            self.component_registry.register(
                "llm_provider", self.llm_name, self.llm, "1.0")
            self.component_registry.register(
                "knowledge_store", "resonance", self.knowledge, "1.0")
            self.component_registry.register(
                "router", "secretary", self.secretary, "1.0")

            # Negotiation Engine — multi-role collaboration (Points #3, #8)
            self.negotiation_engine = None
            if _HAS_NEGOTIATION:
                self.negotiation_engine = NegotiationEngine(
                    llm_provider=self.llm,
                    ghost_channel=self.ghost_channel,
                    knowledge=self.knowledge,
                )
                self.component_registry.register(
                    "negotiation", "engine", self.negotiation_engine, "1.0")

            # User Growth Engine — S1→S5 progressive unlocking
            self.user_growth = UserGrowthEngine()

        except Exception as e:
            import logging
            logging.getLogger("q-spectrum").warning(
                f"Closed-loop core components partially loaded: {e}")

        # Ghost Channel Gate — tier-based soft-lock
        self.ghost_gate = None
        try:
            from ghost_channel_gate import GhostChannelGate
            self.ghost_gate = GhostChannelGate(str(Path(__file__).parent))
        except Exception:
            pass

        # ── 5-Layer Closed-Loop Architecture ──
        # Layer 1: Resource Layer (Raw DB → Vector Search → API)
        # Layer 4: Result Layer (Capture → Aggregate → Loop Close)
        # Layer 5: Decision Layer (Multi-LLM Window Mgmt + Routing Tuning)
        self.resource_layer = None
        self.result_layer = None
        self.decision_layer = None

        try:
            from resource_layer import ResourceAPI
            self.resource_layer = ResourceAPI()
        except Exception:
            pass

        try:
            from result_layer import ResultLayer
            self.result_layer = ResultLayer()
        except Exception:
            pass

        try:
            from decision_layer import DecisionEngine
            self.decision_layer = DecisionEngine()
            # Wire decision layer → secretary routing boost
            if self.decision_layer:
                old_feedback = self.secretary._feedback_fn
                de = self.decision_layer
                def _combined_feedback(role_code):
                    base = old_feedback(role_code) if old_feedback else 0.0
                    boost = de.get_routing_boost(role_code)
                    return base + boost
                self.secretary._feedback_fn = _combined_feedback
        except Exception:
            pass

        # Wire layers together for loop closing:
        # Result Layer → Resource Layer (reingest results as resources)
        # Result Layer → Decision Layer (feed quality scores)
        if self.result_layer:
            self.result_layer.wire(
                resource_api=self.resource_layer,
                decision_engine=self.decision_layer,
            )

        # Register new layers in Component Registry
        if self.component_registry:
            if self.resource_layer:
                self.component_registry.register(
                    "resource_layer", "resource_api", self.resource_layer, "1.0")
            if self.result_layer:
                self.component_registry.register(
                    "result_layer", "result_capture", self.result_layer, "1.0")
            if self.decision_layer:
                self.component_registry.register(
                    "decision_layer", "decision_engine", self.decision_layer, "1.0")

        # ── Project Memory Isolation (Point #19) ──
        # Multi-project chatroom switching with memory isolation
        self.project_memory = None
        self.chatroom_controller = None
        if _HAS_PROJECT_MEMORY:
            try:
                _pm_db = str(self._writable_dir / "project_memory.db") if hasattr(self, '_writable_dir') else None
                self.project_memory = ProjectMemoryManager(db_path=_pm_db)
                self.chatroom_controller = ChatroomSessionController(self.project_memory)
                if self.component_registry:
                    self.component_registry.register(
                        "memory_manager", "project_memory", self.project_memory, "1.0")
                    self.component_registry.register(
                        "session_controller", "chatroom", self.chatroom_controller, "1.0")
            except Exception as e:
                import logging
                logging.getLogger("q-spectrum").warning(
                    f"Project memory initialization: {e}")

        # ── YAML Role Loader (Point #15) ──
        self.role_loader = None
        if _HAS_ROLE_CONFIG:
            try:
                self.role_loader = YAMLRoleLoader(str(Path(__file__).parent))
                yaml_roles = self.role_loader.scan_and_load()
                # Register YAML roles into the DB layer for unified access
                for code, role_cfg in yaml_roles.items():
                    self.db._custom_roles[code] = role_cfg.to_db_dict()
                if yaml_roles and self.component_registry:
                    self.component_registry.register(
                        "role_loader", "yaml", self.role_loader, "1.0")
                pass  # YAML roles loaded successfully
            except Exception:
                pass  # YAML role loader not critical

        # ── Global Search Engine (Point #18) ──
        self.global_search = None
        if _HAS_GLOBAL_SEARCH:
            try:
                self.global_search = GlobalSearchEngine(
                    project_memory=self.project_memory,
                    knowledge_pipeline=self.knowledge_pipeline,
                    db=self.db,
                    deerflow=self.deerflow,
                    skill_executor=self.skill_executor,
                    resource_layer=self.resource_layer,
                )
                if self.component_registry:
                    self.component_registry.register(
                        "search_engine", "global_search", self.global_search, "1.0")
            except Exception as e:
                import logging
                logging.getLogger("q-spectrum").warning(f"Global search init: {e}")

        # ── Contact Channel (Point #20) ──
        self.contact_channel = None
        if _HAS_CONTACT:
            try:
                _cc_db = str(self._writable_dir / "contact_channel.db") if hasattr(self, '_writable_dir') else None
                self.contact_channel = ContactChannel(db_path=_cc_db)
                if self.component_registry:
                    self.component_registry.register(
                        "contact", "channel", self.contact_channel, "1.0")
            except Exception:
                pass

        # ── Task Manager (Point #10) ──
        self.task_manager = None
        if _HAS_TASK_MANAGER:
            try:
                _tm_db = str(self._writable_dir / "task_manager.db") if hasattr(self, '_writable_dir') else None
                self.task_manager = TaskManager(db_path=_tm_db)
                if self.component_registry:
                    self.component_registry.register(
                        "task_manager", "main", self.task_manager, "1.0")
            except Exception:
                pass

        # ── Scenario Engine + AI Companion (Point #7, #8) ──
        self.scenario_engine = None
        if _HAS_SCENARIO_ENGINE:
            try:
                self.scenario_engine = ScenarioEngineIntegration()
                if self.component_registry:
                    self.component_registry.register(
                        "scenario", "engine", self.scenario_engine, "1.0")
            except Exception:
                pass

        # ── Dual-Loop Brain Architecture (Phase 1-2: Inner Loop + Hybrid Router) ──
        # Inner Loop: UniversalKnowledgeOrchestrator (multi-source knowledge retrieval)
        # Hybrid Router: HybridModeRouter (auto-switch between orchestrator/peer modes)
        # Outer Loop components (peer_collaboration, skill_orchestrator, knowledge_crystallizer) pending.
        self.knowledge_orchestrator = None
        if _HAS_KNOWLEDGE_ORCHESTRATOR:
            try:
                self.knowledge_orchestrator = UniversalKnowledgeOrchestrator(engine=self)
                if self.component_registry:
                    self.component_registry.register(
                        "dual_loop", "knowledge_orchestrator", self.knowledge_orchestrator, "1.0")
            except Exception as e:
                import logging
                logging.getLogger("q-spectrum").warning(
                    f"Knowledge Orchestrator init failed: {e}")

        self.hybrid_router = None
        if _HAS_HYBRID_ROUTER:
            try:
                self.hybrid_router = HybridModeRouter()
                if self.component_registry:
                    self.component_registry.register(
                        "dual_loop", "hybrid_router", self.hybrid_router, "1.0")
            except Exception as e:
                import logging
                logging.getLogger("q-spectrum").warning(
                    f"Hybrid Router init failed: {e}")

        self.peer_collaboration = None
        if _HAS_PEER_COLLABORATION:
            try:
                self.peer_collaboration = PeerCollaborationEngine(engine=self)
                if self.component_registry:
                    self.component_registry.register(
                        "dual_loop", "peer_collaboration", self.peer_collaboration, "1.0")
            except Exception as e:
                import logging
                logging.getLogger("q-spectrum").warning(
                    f"Peer Collaboration init failed: {e}")

        self.skill_orchestrator = None
        if _HAS_SKILL_ORCHESTRATOR:
            try:
                self.skill_orchestrator = SkillOrchestrator(engine=self)
                if self.component_registry:
                    self.component_registry.register(
                        "dual_loop", "skill_orchestrator", self.skill_orchestrator, "1.0")
            except Exception as e:
                import logging
                logging.getLogger("q-spectrum").warning(
                    f"Skill Orchestrator init failed: {e}")

        self.knowledge_crystallizer = None
        if _HAS_KNOWLEDGE_CRYSTALLIZER:
            try:
                self.knowledge_crystallizer = KnowledgeCrystallizer(engine=self)
                if self.component_registry:
                    self.component_registry.register(
                        "dual_loop", "knowledge_crystallizer", self.knowledge_crystallizer, "1.0")
            except Exception as e:
                import logging
                logging.getLogger("q-spectrum").warning(
                    f"Knowledge Crystallizer init failed: {e}")

        # Session state
        self.conversation_history = []
        self.interaction_count = 0
        self._last_role = None  # Track for Ghost Channel transitions

    def _retrieve_knowledge(self, user_input: str, context: dict = None) -> str:
        """
        Retrieve knowledge context with fallback chain.

        Fallback order (Dual-Loop ready):
          1. knowledge_orchestrator (Dual-Loop Inner Loop — with hybrid_router mode selection)
          2. prompt_builder.build_knowledge_context (existing behavior)
          3. Raw DB search (last resort)
          4. Empty string (graceful degradation)

        This method is the extraction point for Step 2 of process().
        It prepares the integration hook for UniversalKnowledgeOrchestrator.
        """
        # Fallback 1: Dual-Loop knowledge_orchestrator (with hybrid_router mode)
        if self.knowledge_orchestrator is not None:
            try:
                mode = "orchestrator"
                if self.hybrid_router:
                    mode = self.hybrid_router.select_mode(user_input, context)
                result = self.knowledge_orchestrator.retrieve(user_input, context, mode=mode)
                if result:
                    return result
            except Exception:
                pass  # Fall through to next fallback

        # Fallback 2: Existing prompt_builder (current behavior)
        try:
            ctx = self.prompt_builder.build_knowledge_context(user_input)
            if ctx:
                return ctx
        except Exception:
            pass  # Fall through to next fallback

        # Fallback 3: Raw DB search (last resort)
        try:
            if self.db:
                keywords = [w for w in user_input.split() if len(w) > 1][:3]
                if keywords:
                    parts = []
                    for kw in keywords:
                        rows = self.db.query(
                            "SELECT title FROM documents WHERE title LIKE ? LIMIT 2",
                            (f"%{kw}%",)
                        )
                        for r in rows:
                            parts.append(f"- {dict(r)['title']}")
                    if parts:
                        return "相關文檔 (fallback):\n" + "\n".join(parts[:5])
        except Exception:
            pass

        # Fallback 4: Graceful degradation
        return ""

    def process(self, user_input: str, context: dict = None) -> dict:
        """
        THE core pipeline. Process a user message through the full Q-SpecTrum chain.

        Returns a complete result dict with routing info, response, and metadata.
        """
        context = context or {}
        start_time = datetime.now()
        self.interaction_count += 1

        # Step -1: Project Memory — inject project/chatroom context (Point #19)
        if self.chatroom_controller:
            context = self.chatroom_controller.pre_process(user_input, context)

        # Step 0: Ghost Channel Gate — soft-lock enforcement
        gate_status = None
        allowed_roles = None
        if self.ghost_gate:
            gate_status = self.ghost_gate.check()
            if not gate_status.valid:
                # Soft-lock: still respond but with degraded notice
                return {
                    "status": "degraded",
                    "response": (
                        f"⚠️ Ghost Channel 激活状态: {gate_status.reason}\n\n"
                        f"系统仍在基础模式运行。基础AI伙伴(QCM-001)可用。\n"
                        f"如需完整功能（多角色协商、DeerFlow技能、沙盘推演），"
                        f"请联系开发者获取激活密钥。\n\n"
                        f"💡 提示: 设置环境变量 GHOST_CHANNEL_KEY=GC-PRO-xxxx 或将密钥写入 .ghost_channel_key 文件"
                    ),
                    "routing": {"family": "qcm", "role_code": "ROLE-Q07", "role_name": "AI Companion", "confidence": 0.5, "reasoning": "Gate degraded mode"},
                    "ghost_channel": {"gate_status": "locked", "reason": gate_status.reason},
                    "metadata": {"llm_provider": self.llm_name, "elapsed_seconds": 0, "interaction_number": self.interaction_count, "timestamp": datetime.now().isoformat()},
                }
            # Determine allowed roles based on tier
            if gate_status.tier == "trial":
                # Trial: allow ALL 15 roles from every family
                # This ensures correct routing regardless of tier
                allowed_roles = None  # No restriction — all roles available
            elif gate_status.tier == "pro":
                allowed_roles = None  # All roles except TRUM custom
            # enterprise = all roles (allowed_roles stays None = no restriction)

        # Step 1: Secretary routes the request (or use forced role from context)
        force_role = context.get("force_role")
        if force_role and force_role in self.secretary.roles:
            role_data = self.secretary.roles[force_role]
            routing = {
                "family": role_data.get("family", "qcm"),
                "role_code": force_role,
                "role_name": role_data["role_name"],
                "confidence": 1.0,
                "radar": {},
                "reasoning": f"Force-routed to {force_role} via context",
            }
        else:
            routing = self.secretary.route(user_input, context)

        # Step 1.2: Tier-based role filtering (soft-lock)
        tier_notice = ""
        if allowed_roles is not None and routing["role_code"] not in allowed_roles:
            original_role = routing["role_name"]
            # Downgrade to QCM-001
            tier_notice = (
                f"\n\n💎 **升级提示**: 此请求最适合由 {original_role} 处理，"
                f"当前 {gate_status.tier.upper() if gate_status else 'UNKNOWN'} 版本仅支持基础角色。"
                f"升级到 PRO 版可解锁全部15个AI角色。"
            )
            routing["role_code"] = "ROLE-Q07"
            routing["role_name"] = "AI Companion"
            routing["family"] = "qcm"
            routing["tier_downgraded"] = True
            routing["original_role"] = original_role

        # Step 1.5: Ghost Channel sync — nervous system fires on role transition
        gc_sync = None
        if self.ghost_channel:
            from_role = self._last_role or "USER"
            gc_sync = self.ghost_channel.sync_role_transition(
                from_role=from_role,
                to_role=routing["role_code"],
                context=context,
                user_input=user_input,
            )
            self._last_role = routing["role_code"]

        # Step 1.3: Check if this request needs multi-role negotiation
        negotiation_result = None
        response_override = None
        if self.negotiation_engine and self.ghost_gate and self.ghost_gate.tier != "trial":
            neg_check = self.negotiation_engine.should_negotiate(user_input, routing)
            if neg_check:
                try:
                    neg_result = self.negotiation_engine.run_negotiation(
                        topic=user_input,
                        participants=neg_check["participants"],
                        mode=neg_check["mode"],
                        max_rounds=3,
                        context=context,
                    )
                    negotiation_result = neg_result.to_dict()
                    # Override response with negotiation conclusion
                    response_override = neg_result.conclusion
                    if neg_result.turns:
                        response_override = "## 🎯 多角色协商结果\n\n"
                        for turn in neg_result.turns:
                            response_override += f"**{turn.role_name}** ({turn.family.upper()}, 第{turn.round_num}轮):\n{turn.content}\n\n---\n\n"
                        response_override += f"\n{neg_result.conclusion}"
                except Exception as e:
                    import logging
                    logging.getLogger("q-spectrum").warning(f"Negotiation failed: {e}")

        # Step 1.8: Sandbox validation (F13-15) — three-layer defense
        # ACTIVE: If validation fails, inject warning into response
        sandbox_result = None
        sandbox_blocked = False
        if self.src_bridge and self.src_bridge.sandbox.available:
            sandbox_result = self.src_bridge.sandbox.validate_request(
                user_input, routing, context)
            # If sandbox reports invalid at Meso/Macro level, flag for response warning
            if sandbox_result and not sandbox_result.get("valid", True):
                sandbox_blocked = True
                sandbox_level = sandbox_result.get("level", "unknown")
                sandbox_findings = sandbox_result.get("findings", [])
                # At Macro level (critical), consider blocking execution
                if sandbox_level == "macro" and sandbox_result.get("score", 1.0) < 0.3:
                    # Hard block: return early with sandbox rejection
                    return {
                        "status": "blocked",
                        "response": (
                            f"⚠️ **沙箱安全拦截 (F13-15)**\n\n"
                            f"此请求未通过 {sandbox_level} 层沙箱验证 "
                            f"(得分: {sandbox_result.get('score', 0):.2f})。\n"
                            f"发现问题: {'; '.join(str(f) for f in sandbox_findings[:3])}\n\n"
                            f"请修改请求后重试。"
                        ),
                        "routing": routing,
                        "sandbox": sandbox_result,
                        "metadata": {"blocked_by": "sandbox_macro", "timestamp": datetime.now().isoformat()},
                    }

        # Step 1.9: Decision cost evaluation (F22)
        # ACTIVE: High cost triggers re-routing to lower-cost alternative
        cost_result = None
        cost_routing_adjusted = False
        if self.src_bridge and self.src_bridge.cost.available:
            cost_result = self.src_bridge.cost.evaluate(
                user_input, routing, context)

            if cost_result and cost_result.get("cost") is not None:
                cost_value = cost_result.get("cost", 0.0)
                if cost_value > 0.8 and cost_result.get("recommendation") == "OPTIMIZE":
                    cost_routing_adjusted = True
                    if "metadata" not in routing:
                        routing["metadata"] = {}
                    routing["metadata"]["cost_adjusted"] = True
                    routing["metadata"]["original_cost"] = cost_value
                    # Try to find a lower-cost role in the same family
                    try:
                        family_roles = self.db.get_roles_by_family(routing["family"])
                        original_role = routing["role_code"]
                        for alt_code in family_roles:
                            if alt_code == original_role:
                                continue
                            alt_cost = self.src_bridge.cost.estimate_role_cost(alt_code)
                            if alt_cost is not None and alt_cost < cost_value * 0.7:
                                routing["metadata"]["rerouted_from"] = original_role
                                routing["role_code"] = alt_code
                                routing["role_name"] = family_roles[alt_code].get("role_name", alt_code)
                                routing["metadata"]["reroute_reason"] = f"cost {cost_value:.2f}→{alt_cost:.2f}"
                                break
                    except Exception:
                        pass

        # Step 1.95: Deadlock check (F12) — detect routing loops
        # ACTIVE: If deadlock detected, only reroute the narrow anti-pattern
        # (same role selected many turns in a row), never overwrite a strong
        # argmax choice.
        deadlock_result = None
        if self.src_bridge and self.src_bridge.deadlock.available:
            deadlock_result = self.src_bridge.deadlock.check(routing)
            if deadlock_result and deadlock_result.get("detected", False):
                # S066 FIX: The previous policy wholesale-rerouted every
                # deadlock-flagged QCM turn to Q07 (then, after the first
                # S066 patch, to Q03). Both sink roles corrupted correct
                # argmax routing for P16–P23 in the 23-persona flywheel.
                #
                # New policy: trust the argmax. Only intervene if the
                # argmax itself produced one of the known "sink" defaults
                # (Q07 AI Companion without emotional anchor) — in which
                # case we redirect to Q03 Creator. Otherwise we annotate
                # the routing with the deadlock score but leave the role
                # untouched.
                current = routing.get("role_code")
                text_lower = (user_input or "").lower()
                emotional_anchors = (
                    "压力", "壓力", "焦虑", "焦慮", "难受", "難受",
                    "崩溃", "崩潰", "chat", "emotional", "stress",
                    "anxious", "anxiety", "lonely", "孤独", "孤獨",
                    "想哭", "痛苦", "沮丧", "沮喪", "委屈",
                    "聊聊", "聊聊天", "陪我", "陪陪",
                )
                has_emotion = any(ea in text_lower for ea in emotional_anchors)
                needs_reroute = (
                    current == "ROLE-Q07" and not has_emotion
                )
                if "metadata" not in routing:
                    routing["metadata"] = {}
                routing["metadata"]["deadlock_detected"] = True
                routing["metadata"]["deadlock_score"] = deadlock_result.get("score", 0)
                if needs_reroute:
                    routing["metadata"]["deadlock_rerouted_from"] = current
                    routing["metadata"]["deadlock_reason"] = (
                        "Q07 sink without emotional anchor → Q03 (S066 policy)"
                    )
                    routing["role_code"] = "ROLE-Q03"
                    fb_role = self.db.get_role("ROLE-Q03")
                    if fb_role:
                        routing["role_name"] = fb_role.get("role_name", "ROLE-Q03")
                else:
                    routing["metadata"]["deadlock_reason"] = (
                        "trusting argmax (S066 policy — no wholesale reroute)"
                    )

        # Step 1.97: Simulation Flywheel — 沙盘推演 (war-game before execution)
        simulation_result = None
        if self.simulation_flywheel:
            try:
                sim = self.simulation_flywheel.simulate(user_input, context)
                simulation_result = {
                    "primary_role": sim.primary_path.primary_role,
                    "confidence": round(sim.confidence, 3),
                    "scores": sim.primary_scores.to_dict(),
                    "alternatives": [
                        {"role": alt.primary_role, "rationale": alt.rationale_en[:80]}
                        for alt in sim.alternative_paths
                    ],
                    "reasoning": sim.reasoning_en[:200],
                    "warnings": sim.warnings,
                }
            except Exception:
                pass

        # Step 2: Build knowledge context (extracted to _retrieve_knowledge with fallback chain)
        knowledge_ctx = self._retrieve_knowledge(user_input, context)

        # Step 3: Build system prompt from role's activation card + DB data
        system_prompt = self.prompt_builder.build_system_prompt(
            routing["role_code"],
            knowledge_context=knowledge_ctx,
        )

        # Step 3.5: Real Skill auto-invocation — if message matches a real skill, execute it
        real_skill_result = None
        if self.real_skills:
            _skill_map = {
                "file-analyzer": ["分析文件", "分析项目", "文件结构", "项目结构", "analyze file", "file structure", "project structure", "file analyzer"],
                "code-reviewer": ["代码审查", "代码分析", "代码检查", "review code", "analyze code", "code review", "检查代码", "code quality", "review the code", "find issues"],
                "data-processor": ["处理数据", "分析数据", "CSV", "JSON", "data process", "parse data"],
                "project-planner": ["项目规划", "项目计划", "规划项目", "project plan", "create plan", "创建计划", "制定计划", "规划一个", "开发项目"],
                "system-reporter": ["系统状态", "系统报告", "数据库状态", "system status", "system report", "db status", "多少表"],
            }
            _input_lower = user_input.lower()
            for _skill_key, _triggers in _skill_map.items():
                if any(t in _input_lower for t in _triggers):
                    try:
                        real_skill_result = self.real_skills.execute(_skill_key, user_input)
                        if real_skill_result.get("status") == "ok":
                            break
                    except Exception:
                        real_skill_result = None

        # Step 3.7: Dual-Loop Peer Collaboration (Phase 4 — Outer Loop integration)
        # When hybrid_router selects 'peer' mode, trigger multi-round collaboration
        peer_collab_result = None
        peer_mode_active = False
        if self.hybrid_router and self.peer_collaboration:
            try:
                selected_mode = self.hybrid_router.select_mode(user_input, context)
                if selected_mode == "peer":
                    peer_mode_active = True
                    # Pre-retrieve relevant skills
                    skill_context = {}
                    if self.skill_orchestrator:
                        skill_context = self.skill_orchestrator.orchestrate_for_collaboration(
                            user_input, {"routing": routing, "knowledge_ctx": knowledge_ctx})

                    # Run collaboration
                    peer_collab_result = self.peer_collaboration.collaborate(
                        user_input=user_input,
                        role_code=routing["role_code"],
                        family=routing["family"],
                        context=context,
                    )

                    # Crystallize knowledge from collaboration
                    if self.knowledge_crystallizer and peer_collab_result.status == "completed":
                        decisions = self.knowledge_crystallizer.crystallize(peer_collab_result)
                        if decisions:
                            peer_collab_result.knowledge_deposited = len(decisions)
            except Exception as e:
                import logging
                logging.getLogger("q-spectrum").warning(f"Peer collaboration failed: {e}")
                peer_mode_active = False

        # Step 4: Call LLM with the assembled prompt (skip if peer collaboration active)
        # S069 FIX: pass session_id through so Mock's multi-turn continuation
        # preamble stays scoped to the caller's session, not leaked globally.
        if peer_mode_active and peer_collab_result and peer_collab_result.final_response:
            response_text = peer_collab_result.final_response
        else:
            response_text = self.llm.generate(
                system_prompt=system_prompt,
                user_message=user_input,
                role_name=routing["role_name"],
                role_code=routing["role_code"],
                family=routing["family"],
                session_id=(context or {}).get("session_id"),
            )

        # Step 4.5: Merge real skill output with LLM response
        if real_skill_result and real_skill_result.get("status") == "ok":
            skill_output = real_skill_result.get("response", "")
            skill_name = real_skill_result.get("skill", "")
            response_text = (
                f"{response_text}\n\n"
                f"---\n"
                f"📊 **{skill_name} 执行结果 / Skill Output**:\n\n"
                f"{skill_output}"
            )

        # Step 5: Check DeerFlow dispatch recommendation
        deerflow_info = None
        if self.deerflow:
            df_check = self.deerflow.can_handle(user_input, role_code=routing["role_code"])
            if df_check["should_use"]:
                deerflow_info = {
                    "recommended": True,
                    "skill": df_check["skill"],
                    "confidence": df_check["confidence"],
                    "prompt": self.deerflow.build_prompt(user_input, {
                        "role_name": routing["role_name"],
                        "role_code": routing["role_code"],
                        "family": routing["family"],
                        "capabilities": routing.get("reasoning", ""),
                    }),
                }
                # Try to execute via SkillExecutor if available
                skill_executed = False
                exec_threshold = getattr(self.deerflow, 'EXECUTION_THRESHOLD', 0.7)

                # Tier 1: SkillExecutor (LLM-driven skill execution)
                if self.skill_executor and df_check["confidence"] >= exec_threshold:
                    try:
                        exec_result = self.skill_executor.execute(
                            df_check["skill"], user_input)
                        if exec_result.get("status") == "ok":
                            skill_executed = True
                            deerflow_info["executed"] = True
                            deerflow_info["execution_method"] = "skill_executor"
                            deerflow_info["skill_output"] = exec_result.get(
                                "response", "")[:500]
                            deerflow_info["skills_used"] = [df_check["skill"]]
                            response_text += (
                                f"\n\n🔧 **DeerFlow `{df_check['skill']}` 執行結果**:\n"
                                f"{exec_result.get('response', '')[:300]}"
                            )
                    except Exception:
                        pass  # Fall through to Tier 2

                # Tier 1.5: DeerFlow Real Skills (local execution without LLM/API)
                if not skill_executed and self.deerflow_real_skills:
                    if self.deerflow_real_skills.can_execute(df_check["skill"]):
                        try:
                            df_real = self.deerflow_real_skills.execute(
                                df_check["skill"], user_input,
                                {"role": routing.get("role_code", ""),
                                 "family": routing.get("family", "")})
                            if df_real.get("status") == "ok":
                                skill_executed = True
                                deerflow_info["executed"] = True
                                deerflow_info["execution_method"] = "deerflow_real"
                                deerflow_info["skill_output"] = df_real.get(
                                    "response", "")[:800]
                                deerflow_info["skills_used"] = [df_check["skill"]]
                                response_text += (
                                    f"\n\n🔧 **DeerFlow `{df_check['skill']}` 执行结果**:\n"
                                    f"{df_real.get('response', '')[:600]}"
                                )
                        except Exception:
                            pass

                # Tier 1.75: DeerFlow dispatch (native execution via LangGraph API)
                if not skill_executed and self.deerflow:
                    try:
                        dispatch_result = self.deerflow.dispatch(
                            user_input,
                            skill_id=df_check["skill"],
                            context={
                                "role_name": routing.get("role_name", ""),
                                "role_code": routing.get("role_code", ""),
                                "family": routing.get("family", ""),
                            })
                        if dispatch_result.get("response") or dispatch_result.get("output"):
                            skill_executed = True
                            deerflow_info["executed"] = True
                            deerflow_info["execution_method"] = "deerflow_dispatch"
                            deerflow_info["dispatch_method"] = dispatch_result.get("method", "unknown")
                            output_text = dispatch_result.get("response", "") or dispatch_result.get("output", "")
                            deerflow_info["skill_output"] = output_text[:800]
                            deerflow_info["skills_used"] = [df_check["skill"]]
                            deerflow_info["task_id"] = dispatch_result.get("task_id", "")
                            response_text += (
                                f"\n\n🔧 **DeerFlow `{df_check['skill']}` 执行结果** (via {dispatch_result.get('method', 'api')}):\n"
                                f"{output_text[:400]}"
                            )
                    except Exception:
                        pass  # Fall through to Tier 2

                # Tier 2: DeerFlow simulation (structured mock output)
                if not skill_executed and df_check["confidence"] >= 0.5:
                    try:
                        sim_result = self.deerflow.simulate_skill_execution(
                            user_input, df_check["skill"],
                            context={"role": routing.get("role_code", "")})
                        if sim_result.get("response"):
                            skill_executed = True
                            deerflow_info["executed"] = True
                            deerflow_info["execution_method"] = "simulation"
                            deerflow_info["simulated"] = True
                            deerflow_info["skill_output"] = sim_result["response"][:500]
                            deerflow_info["skills_used"] = [df_check["skill"]]
                            response_text += (
                                f"\n\n🔬 **DeerFlow `{df_check['skill']}` 模拟执行**:\n"
                                f"{sim_result['response'][:400]}"
                            )
                    except Exception:
                        pass  # Fall through to Tier 3

                # Tier 3: Manual recommendation hint
                if not skill_executed:
                    response_text += (
                        f"\n\n💡 **DeerFlow 建議**: 此任務可交由 DeerFlow "
                        f"`{df_check['skill']}` 技能執行 "
                        f"(置信度 {df_check['confidence']:.0%})。"
                        f"\n   啟動: `python deerflow_bridge.py "
                        f"--prompt \"{user_input[:30]}...\"`"
                    )

        # Append tier upgrade notice if role was downgraded
        if tier_notice:
            response_text += tier_notice

        # Append sandbox warning if validation found issues (non-blocking)
        if sandbox_blocked and sandbox_result:
            findings = sandbox_result.get("findings", [])
            if findings:
                response_text += (
                    f"\n\n---\n⚠️ **沙箱验证提示 (F13-15)**: "
                    f"检测到 {len(findings)} 个潜在问题: "
                    f"{'; '.join(str(f) for f in findings[:2])}。"
                    f"建议审查后再执行。"
                )

        # Step 6: Build result
        elapsed = (datetime.now() - start_time).total_seconds()

        result = {
            "status": "completed",
            "response": response_text,
            "routing": routing,
            "deerflow": deerflow_info,
            "ghost_channel": {
                "synced": gc_sync is not None and gc_sync.success if gc_sync else False,
                "changes": gc_sync.changes if gc_sync else 0,
                "latency_ms": gc_sync.latency_ms if gc_sync else 0,
                "delta_hash": gc_sync.delta_hash if gc_sync else None,
                "bandwidth_reduction": gc_sync.bandwidth_reduction if gc_sync else 0,
            } if gc_sync else None,
            "metadata": {
                "llm_provider": self.llm_name,
                "elapsed_seconds": round(elapsed, 3),
                "interaction_number": self.interaction_count,
                "system_prompt_length": len(system_prompt),
                "knowledge_context": knowledge_ctx or None,
                "timestamp": datetime.now().isoformat(),
            },
        }

        # Add gate status to result
        if self.ghost_gate:
            result["gate"] = self.ghost_gate.get_status()
            self.ghost_gate.record_usage()

        # Add Dual-Loop peer collaboration result
        if peer_collab_result:
            result["peer_collaboration"] = peer_collab_result.to_dict()
            result["metadata"]["dual_loop_mode"] = "peer" if peer_mode_active else "orchestrator"
            result["metadata"]["collaboration_turns"] = len(peer_collab_result.turns)
            result["metadata"]["knowledge_crystallized"] = peer_collab_result.knowledge_deposited

        # Step 7: Knowledge sedimentation — deposit interaction as episodic memory
        self.knowledge.deposit(user_input, response_text,
                               routing["role_code"], routing["family"])

        # Step 7.2: Knowledge Evolution metrics (F19-F20)
        knowledge_evolution = None
        try:
            growth = self.knowledge.knowledge_growth_rate(
                experience=self.interaction_count)
            prediction = self.knowledge.predict_knowledge_volume(future_steps=5)
            knowledge_evolution = {
                "growth_rate": growth["growth_rate"],
                "interpretation": growth["interpretation"],
                "current_volume": prediction["current_volume"],
                "predicted_5step": prediction["predicted_volume_final"],
                "health": prediction["health"],
            }

            # ACTIVE: If knowledge is stagnant or critical, append hint to response
            health = prediction.get("health", "")
            if health in ("critical", "stagnant") or growth["growth_rate"] < 0.01:
                response_text += (
                    "\n\n---\n💡 **知识系统提示 (F19-20)**: "
                    "当前知识增长率较低，建议尝试不同类型的任务以激活更多知识维度 "
                    "(如：调研、创作、分析、规划等不同场景)。"
                )
                result["response"] = response_text
        except Exception:
            pass

        # Step 7.5: Flywheel recording (F16-18) — feed inner/outer loops
        flywheel_result = None
        if self.src_bridge and self.src_bridge.flywheel.available:
            flywheel_result = self.src_bridge.flywheel.record_outcome(
                user_input, routing, response_text, elapsed)

        # Inject src/ bridge data into result
        if sandbox_result:
            result["sandbox"] = sandbox_result
        if cost_result:
            result["cost"] = cost_result
        if deadlock_result:
            result["deadlock"] = deadlock_result
        if flywheel_result:
            result["flywheel"] = flywheel_result
        if negotiation_result:
            result["negotiation"] = negotiation_result
            # If negotiation produced a better response, use it
            if response_override:
                result["response"] = response_override
        if simulation_result:
            result["simulation"] = simulation_result
        if knowledge_evolution:
            result["knowledge_evolution"] = knowledge_evolution

        # Step 8: Closed-Loop — Result Persistence + Feedback + Resource Collection
        closed_loop_result = None
        if self.closed_loop:
            try:
                gc_synced = gc_sync is not None and gc_sync.success if gc_sync else False
                closed_loop_result = self.closed_loop.on_interaction_complete(
                    interaction_id=f"INT-{self.interaction_count}",
                    role_code=routing["role_code"],
                    family=routing["family"],
                    request_text=user_input,
                    response_text=response_text,
                    routing_info=routing,
                    execution_time_ms=elapsed * 1000,
                    deerflow_skill=(deerflow_info or {}).get("skill"),
                    ghost_channel_synced=gc_synced,
                )
                result["closed_loop"] = closed_loop_result
            except Exception:
                pass

        # Step 8.5: Knowledge Pipeline — auto-sedimentation (closed_loop_core)
        # Every task result → knowledge deposit → cross-link → evolution
        kp_deposit = None
        if self.knowledge_pipeline:
            try:
                gc_token = None
                active_project = (self.project_orchestrator.active_project
                                  if self.project_orchestrator else "default")
                kp_deposit = self.knowledge_pipeline.deposit(
                    result, gc_token=gc_token, project_id=active_project)
                result["knowledge_deposit"] = kp_deposit

                # Log evolution metrics for Flywheel tracking
                self.knowledge_pipeline.log_evolution(
                    flywheel_iterations=self.interaction_count)
            except Exception:
                pass

        # Step 8.7: Project Orchestrator — record interaction for multi-project tracking
        if self.project_orchestrator:
            try:
                active_project = self.project_orchestrator.active_project
                result["metadata"]["user_input"] = user_input
                self.project_orchestrator.record_interaction(active_project, result)

                # Record result for aggregation feedback loop
                if kp_deposit:
                    self.project_orchestrator.record_result(
                        active_project,
                        result_type=kp_deposit.get("knowledge_type", "episodic"),
                        summary=response_text[:200],
                        knowledge_deposit_id=kp_deposit.get("deposit_id", ""),
                        quality_score=kp_deposit.get("relevance", 0.5),
                    )
            except Exception:
                pass

        # Step 8.9: User Growth — check stage progression
        growth_info = None
        if self.user_growth:
            try:
                kp_total = (self.knowledge_pipeline._total_deposits
                            if self.knowledge_pipeline else 0)
                po_projects = (len(self.project_orchestrator._projects)
                               if self.project_orchestrator else 0)
                growth_info = self.user_growth.check_progression(
                    interaction_count=self.interaction_count,
                    knowledge_deposits=kp_total,
                    projects_created=po_projects,
                )
                result["user_growth"] = growth_info
            except Exception:
                pass

        # Step 9: 5-Layer Closed-Loop — Result Layer capture + Resource ingest + Loop close
        # Layer 4: Result Layer captures the execution result
        result_layer_info = None
        if self.result_layer:
            try:
                result["metadata"]["user_input"] = user_input
                result["metadata"]["project_id"] = (
                    self.project_orchestrator.active_project
                    if self.project_orchestrator else "default")
                result_layer_info = self.result_layer.on_interaction_complete(result)
                result["result_layer"] = {
                    "result_id": result_layer_info.get("result_id"),
                    "loop_closed": result_layer_info.get("loop_closed"),
                }
            except Exception:
                pass

        # Layer 5: Decision Tuning — auto-record feedback to close the loop
        # This wires quality signals back to Secretary routing weights
        if self.closed_loop and hasattr(self.closed_loop, 'feedback'):
            try:
                # Compute auto quality score from multiple signals
                auto_quality = 0.5  # baseline
                if kp_deposit:
                    auto_quality = kp_deposit.get("relevance", 0.5)
                if result.get("deerflow_dispatched"):
                    auto_quality = max(auto_quality, 0.7)  # DeerFlow dispatch = higher quality
                if routing.get("confidence", 0) > 0.8:
                    auto_quality += 0.1  # High confidence routing boost

                self.closed_loop.feedback.record_feedback(
                    interaction_id=result.get("metadata", {}).get("interaction_id",
                                    f"auto-{self.interaction_count}"),
                    role_code=routing.get("role_code", ""),
                    query_text=user_input[:500],
                    quality_score=min(1.0, auto_quality),
                    was_correct_route=routing.get("confidence", 0) > 0.5,
                )
                result["feedback_loop"] = {
                    "auto_recorded": True,
                    "quality_score": round(min(1.0, auto_quality), 3),
                    "role_affinities": self.closed_loop.feedback.get_all_affinities(),
                }
            except Exception:
                pass

        # Layer 5b: Decision Engine — feed quality to RoutingTuner for EMA weight updates
        if self.decision_layer:
            try:
                auto_quality = result.get("feedback_loop", {}).get("quality_score", 0.5)
                elapsed_ms = result.get("metadata", {}).get("elapsed_seconds", 0) * 1000
                self.decision_layer.on_result(
                    role_code=routing.get("role_code", ""),
                    family=routing.get("family", ""),
                    quality_score=auto_quality,
                    response_time_ms=elapsed_ms,
                    llm_window_used=self.llm_name,
                    was_correct=routing.get("confidence", 0) > 0.5,
                )
            except Exception:
                pass

        # Layer 5c: Simulation Flywheel learning — feed actual outcome back
        if self.simulation_flywheel and simulation_result:
            try:
                auto_quality = result.get("feedback_loop", {}).get("quality_score", 0.5)
                elapsed_ms = result.get("metadata", {}).get("elapsed_seconds", 0) * 1000
                # Re-run simulate to get the SimulationResult object for learn()
                sim_obj = self.simulation_flywheel.simulate(user_input, context)
                actual_outcome = {
                    "quality_score": auto_quality,
                    "execution_time_ms": elapsed_ms,
                    "success": True,
                    "role_used": routing.get("role_code", ""),
                }
                self.simulation_flywheel.learn(sim_obj, actual_outcome)
            except Exception:
                pass

        # Layer 1: Resource Layer — ingest user input as searchable resource
        if self.resource_layer:
            try:
                active_project = (self.project_orchestrator.active_project
                                  if self.project_orchestrator else "default")
                self.resource_layer.collect(
                    type_="text",
                    content=user_input,
                    title=f"User query #{self.interaction_count}",
                    tags=[routing.get("family", ""), routing.get("role_code", ""), "user_input"],
                    project_id=active_project,
                    source="chatroom",
                )
            except Exception:
                pass

        # Step 10: Record in conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": start_time.isoformat(),
        })
        self.conversation_history.append({
            "role": routing["role_code"],
            "role_name": routing["role_name"],
            "content": response_text,
            "timestamp": datetime.now().isoformat(),
        })

        # Step Final: Project Memory — store result in project memory (Point #19)
        if self.chatroom_controller:
            try:
                self.chatroom_controller.post_process(user_input, result)
            except Exception:
                pass  # Non-critical — don't break pipeline

        # Step Final+1: Task Manager — auto-track as task (Point #10)
        if self.task_manager:
            try:
                pid = context.get("project_id", "default") if context else "default"
                self.task_manager.create_from_engine_result(user_input, result, project_id=pid)
            except Exception:
                pass

        # Step Final+2: Contact Channel — detect support intent (Point #20)
        if self.contact_channel:
            try:
                intent = self.contact_channel.detect_support_intent(user_input)
                if intent:
                    result["support_intent"] = intent
            except Exception:
                pass

        # Step Final+3: Scenario Engine — AI Companion post-processing
        if self.scenario_engine:
            try:
                lang = "zh" if any('\u4e00' <= c <= '\u9fff' for c in user_input[:50]) else "en"
                companion_additions = self.scenario_engine.on_engine_result(
                    user_input, result, lang=lang)
                if companion_additions:
                    result["companion"] = companion_additions
            except Exception:
                pass

        return result

    def _safe_status(self, component):
        """Get status from a component, catching disk I/O and other errors."""
        if component is None:
            return None
        try:
            return component.status()
        except Exception as e:
            return {"error": str(e), "status": "unavailable"}

    def get_system_status(self) -> dict:
        """Get current system status."""
        roles = self.db.get_all_roles()
        protocols = self.db.get_all_protocols()
        workflows = self.protocol_bridge.list_workflows()

        # Ghost Channel status
        gc_status = None
        if self.ghost_channel:
            gc_status = self.ghost_channel.get_status()

        # DeerFlow status
        df_status = None
        if self.deerflow:
            df_status = {
                "installed": True,
                "running": self.deerflow._check_api_health(),
                "skills_count": 6,  # Real executors (deerflow_real_skills.py)
                "routing_registry": len(self.deerflow.SKILL_REGISTRY),  # Keyword-match table
                "queue": self.deerflow.get_queue_status() if hasattr(self.deerflow, 'get_queue_status') else {"queued": 0},
            }

        return {
            "engine": "QSpectrumEngine v3.0",
            "llm_provider": self.llm_name,
            "knowledge_entries": self.knowledge.total_entries,
            "roles_loaded": len(roles),
            "roles_by_family": {
                "trum": len([r for r in roles.values() if r.get("family") == "trum"]),
                "spec": len([r for r in roles.values() if r.get("family") == "spec"]),
                "qcm": len([r for r in roles.values() if r.get("family") == "qcm"]),
            },
            "protocols": len(protocols),
            "workflows": len(workflows),
            "interactions": self.interaction_count,
            "conversation_length": len(self.conversation_history),
            "ghost_channel": gc_status,
            "deerflow": df_status,
            "src_bridge": self.src_bridge.status() if self.src_bridge else None,
            "skill_executor": {
                "skills": len(self.skill_executor._skill_cache),  # Use cache directly, avoid blocking discovery
            } if self.skill_executor else None,
            "closed_loop": self._safe_status(self.closed_loop),
            "knowledge_pipeline": self.knowledge_pipeline.get_status() if self.knowledge_pipeline else None,
            "project_orchestrator": {
                "projects": self.project_orchestrator.list_projects(),
                "active": self.project_orchestrator.active_project,
                "aggregation": self.project_orchestrator.aggregate_results(),
            } if self.project_orchestrator else None,
            "component_registry": self.component_registry.get_status() if self.component_registry else None,
            "user_growth": self.user_growth.get_status() if self.user_growth else None,
            "ghost_gate": self.ghost_gate.get_status() if self.ghost_gate else None,
            "negotiation_engine": self.negotiation_engine.get_status() if self.negotiation_engine else None,
            # 5-Layer Closed-Loop Architecture
            "resource_layer": self._safe_status(self.resource_layer),
            "result_layer": self._safe_status(self.result_layer),
            "decision_layer": self._safe_status(self.decision_layer),
            # Scenario Engine + AI Companion
            "scenario_engine": self.scenario_engine.get_status() if self.scenario_engine else None,
            # Simulation Flywheel — 沙盘推演飞轮
            "simulation_flywheel": self.simulation_flywheel.get_flywheel_status() if self.simulation_flywheel else None,
            # Knowledge Graph (Phase 2.1)
            "knowledge_graph": self.graph.stats() if self.graph else None,
            # Vector Store (Phase 2.2)
            "vector_store": self.vector_store.stats() if self.vector_store else None,
        }

    def search_knowledge(self, query: str) -> list:
        """Search the knowledge resonance store. (MCP-facing)"""
        return self.knowledge.search(query) if self.knowledge else []

    def handle_message(self, message: str) -> str:
        """Process a chat message and return response text. (MCP-facing)"""
        result = self.process(message)
        return result.get("response", "")

    def close(self):
        self.db.close()
        if self.graph:
            self.graph.close()


# ═══════════════════════════════════════════════════════════
# 7. CLI INTERFACE
# ═══════════════════════════════════════════════════════════

def print_banner():
    print("=" * 60)
    print("  Q-SpecTrum Unified Engine v1.0")
    print("  AI-Driven Project Management System")
    print("=" * 60)


def run_demo(engine):
    """Run demonstration scenarios."""
    print_banner()
    status = engine.get_system_status()
    print(f"\n  LLM: {status['llm_provider']}")
    print(f"  Roles: {status['roles_loaded']} ({status['roles_by_family']})")
    print(f"  Protocols: {status['protocols']}")
    print(f"  Workflows: {status['workflows']}")

    scenarios = [
        ("幫我分析項目時間線，找出瓶頸", "Standard QCM task → Analyst"),
        ("設計一個微服務遷移的架構方案", "Architecture task → Chief Architect"),
        ("研究 AI 在項目管理中的最佳實踐", "Research task → Researcher"),
        ("寫一份項目啟動報告", "Content creation → Creator"),
        ("評估系統安全風險", "Risk assessment → Risk Auditor"),
        ("平台戰略規劃需要跨族協調", "Platform task → Trum family"),
        ("數據庫 schema 需要重構", "Architecture task → Spec family"),
        ("你好，我想了解系統怎麼使用", "General help → AI Companion"),
    ]

    for i, (query, description) in enumerate(scenarios, 1):
        print(f"\n{'─' * 60}")
        print(f"  Scenario {i}: {description}")
        print(f"  User: \"{query}\"")

        result = engine.process(query)
        r = result["routing"]

        print(f"\n  Secretary → {r['family'].upper()} / {r['role_code']} ({r['role_name']})")
        print(f"  Confidence: {r['confidence']:.2f} | Reason: {r['reasoning']}")
        print(f"\n  {result['response'][:300]}")
        if len(result['response']) > 300:
            print(f"  ... ({len(result['response'])} chars total)")
        print(f"\n  [{result['metadata']['elapsed_seconds']}s | {result['metadata']['llm_provider']}]")

    print(f"\n{'═' * 60}")
    print(f"  Demo complete. {engine.interaction_count} interactions processed.")
    print(f"{'═' * 60}")


def run_interactive(engine):
    """Interactive chat mode."""
    print_banner()
    status = engine.get_system_status()
    print(f"\n  LLM: {status['llm_provider']} | Roles: {status['roles_loaded']}")
    print("\n  Commands: /status /roles /workflows /protocols /quit")
    print("  Just type your message to start.\n")

    while True:
        try:
            user_input = input("[You] > ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "/q"):
            break

        if user_input.lower() == "/status":
            s = engine.get_system_status()
            for k, v in s.items():
                print(f"  {k}: {v}")
            continue

        if user_input.lower() == "/roles":
            for code, role in engine.db.get_all_roles().items():
                print(f"  {code} | {role['role_name']} | {role.get('family','')} | {role.get('capabilities','')[:60]}")
            continue

        if user_input.lower() == "/workflows":
            wfs = engine.protocol_bridge.list_workflows()
            if wfs:
                for wf in wfs:
                    print(f"  {wf.get('workflow_code','')} | {wf.get('workflow_name','')}")
            else:
                print("  (No workflows loaded)")
            continue

        if user_input.lower() == "/protocols":
            protos = engine.protocol_bridge.list_protocols()
            if protos:
                for p in protos:
                    print(f"  {p.get('protocol_code','')} | {p.get('source_role','')} → {p.get('target_role','')}")
            else:
                print("  (No protocols loaded)")
            continue

        # Process through the full pipeline
        result = engine.process(user_input)
        r = result["routing"]

        print(f"\n  [Secretary → {r['family'].upper()}/{r['role_code']}] {r['role_name']} (confidence: {r['confidence']:.2f})")
        print(f"\n{result['response']}")
        print(f"\n  [{result['metadata']['elapsed_seconds']}s | {result['metadata']['llm_provider']}]")
        print()


def run_single_query(engine, query):
    """Process a single query and print result."""
    result = engine.process(query)
    r = result["routing"]
    print(f"[{r['role_code']}] {r['role_name']} ({r['family']}, confidence: {r['confidence']:.2f})")
    print()
    print(result["response"])


def main():
    provider_name = None

    # Parse args
    if "--provider" in sys.argv:
        idx = sys.argv.index("--provider")
        if idx + 1 < len(sys.argv):
            provider_name = sys.argv[idx + 1]

    engine = QSpectrumEngine(
        llm_provider=create_llm_provider(provider_name)[0] if provider_name else None
    )

    try:
        if "--demo" in sys.argv:
            run_demo(engine)
        elif "--query" in sys.argv:
            idx = sys.argv.index("--query")
            if idx + 1 < len(sys.argv):
                run_single_query(engine, sys.argv[idx + 1])
            else:
                print("Usage: --query \"your question\"")
        else:
            run_interactive(engine)
    finally:
        engine.close()


if __name__ == "__main__":
    main()
