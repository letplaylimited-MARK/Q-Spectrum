#!/usr/bin/env python3
"""
Smart Mock LLM v2.1 - Generates intelligent, context-aware responses without API keys.
智能模拟 LLM v2.1 - 生成无需 API 密钥的智能上下文感知响应。

Provides a context-aware mock LLM engine that supports bilingual (Chinese/English) output
for all Q-SpecTrum roles without requiring external API calls. Enables the system to function
independently while maintaining intelligent, role-specific responses.
"""

import re
from collections import OrderedDict


class SmartMockEngine:
    """
    The intelligence layer for Mock mode.
    Separated from LLMProvider to be reusable across sync/async contexts.
    """

    def __init__(self, db=None):
        self.db = db
        self._db_context = None
        # Global counters (kept for backward compat + status reporting)
        self._turn_count = 0
        self._topics_history = []
        # Per-session state: {session_id: {"topics": [...], "turns": int}}
        # Ensures multi-turn continuation doesn't leak across users/sessions.
        self._by_session: OrderedDict = OrderedDict()
        # Bound session count to avoid memory growth in long-running servers.
        self._max_sessions = 128

    def get_db_context(self) -> dict:
        """Lazy-load rich DB context."""
        if self._db_context is not None:
            return self._db_context
        if self.db is None:
            self._db_context = self._default_context()
            return self._db_context
        try:
            conn = self.db.conn
            proj = conn.execute("SELECT project_name, status FROM projects LIMIT 1").fetchone()
            self._db_context = {
                "project_name": proj[0] if proj else "Q-SpecTrum",
                "project_status": proj[1] if proj else "active",
                "wf_count": conn.execute("SELECT COUNT(*) FROM workflow_definitions").fetchone()[0],
                "step_count": conn.execute("SELECT COUNT(*) FROM workflow_steps").fetchone()[0],
                "role_count": conn.execute("SELECT COUNT(*) FROM ai_roles").fetchone()[0],
                "doc_count": conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
                "table_count": conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0],
                "docs_list": [r[0] for r in conn.execute("SELECT title FROM documents LIMIT 8").fetchall()],
                "skills_list": [r[0] for r in conn.execute("SELECT skill_name FROM skill_definitions LIMIT 8").fetchall()],
                "wf_names": [r[0] for r in conn.execute("SELECT workflow_name FROM workflow_definitions").fetchall()],
                "proto_names": [r[0] for r in conn.execute("SELECT protocol_name FROM collaboration_protocols LIMIT 5").fetchall()],
                "stages": [s[0] for s in conn.execute("SELECT stage_name FROM project_stages ORDER BY id").fetchall()],
            }
        except Exception:
            self._db_context = self._default_context()
        return self._db_context

    def _default_context(self):
        return {
            "project_name": "Q-SpecTrum", "project_status": "active",
            "wf_count": 4, "step_count": 84, "role_count": 15, "doc_count": 17,
            "table_count": 47, "docs_list": [], "skills_list": [],
            "wf_names": [], "proto_names": [], "stages": [],
        }

    def classify_intent(self, msg: str) -> str:
        m = msg.lower()
        if any(k in m for k in ["什么", "怎么", "如何", "为什么", "哪", "吗", "？",
                                  "what", "how", "why", "which", "when", "where", "?"]):
            return "question"
        if any(k in m for k in ["分析", "研究", "调查", "评估", "诊断", "对比",
                                  "analyze", "research", "investigate", "evaluate", "assess"]):
            return "analysis"
        if any(k in m for k in ["创建", "设计", "写", "生成", "制作", "开发", "构建", "规划",
                                  "create", "design", "write", "generate", "build", "plan", "make", "develop"]):
            return "creation"
        if any(k in m for k in ["管理", "安排", "组织", "分配", "跟踪", "监控",
                                  "manage", "organize", "assign", "track", "monitor", "schedule"]):
            return "management"
        if any(k in m for k in ["想法", "灵感", "脑暴", "建议", "探讨",
                                  "idea", "brainstorm", "suggest", "explore", "think"]):
            return "brainstorm"
        if any(k in m for k in ["你好", "帮助", "介绍", "hello", "help", "hi ", "hey", "start"]):
            return "greeting"
        return "general"

    def detect_language(self, msg: str) -> str:
        cn_chars = sum(1 for c in msg if '\u4e00' <= c <= '\u9fff')
        return "zh" if cn_chars > len(msg) * 0.15 else "en"

    def extract_topics(self, msg: str) -> list:
        stops = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "都", "一", "上",
                 "也", "到", "要", "去", "你", "会", "没有", "好", "这", "请", "帮", "帮我",
                 "能", "可以", "一下", "想", "需要", "希望", "觉得", "知道", "看看", "吧",
                 "the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "and",
                 "in", "that", "have", "it", "for", "not", "on", "with", "he", "as", "you",
                 "do", "at", "this", "but", "his", "by", "from", "they", "we", "her", "my",
                 "me", "can", "will", "would", "could", "should", "may", "might", "i"}
        segs = re.split(r'[，。！？、；：\s,.!?;:]+', msg)
        return [s.strip() for s in segs if len(s.strip()) > 1 and s.strip().lower() not in stops][:5]

    def generate(self, system_prompt: str, user_message: str, **kwargs) -> str:
        role_name = kwargs.get("role_name", "AI 助手")
        role_code = kwargs.get("role_code", "")
        family = kwargs.get("family", "qcm")
        ctx = self.get_db_context()

        intent = self.classify_intent(user_message)
        lang = self.detect_language(user_message)
        topics = self.extract_topics(user_message)

        # S068 FIX: reference prior turn when in a multi-turn conversation.
        # S069 FIX: per-session scoping so conversations don't leak across users.
        session_id = kwargs.get("session_id") or "__default__"
        sess = self._by_session.get(session_id)
        if sess is None:
            if len(self._by_session) >= self._max_sessions:
                self._by_session.popitem(last=False)
            sess = {"topics": [], "turns": 0}
        else:
            self._by_session.move_to_end(session_id)
        self._by_session[session_id] = sess

        prior_topics = [t for t in sess["topics"][-4:] if t not in topics]
        continuation_preamble = ""
        # S070 adversarial-audit FIX: don't echo prior topics in the
        # continuation preamble when the current message is a crisis.
        # Otherwise the preamble might replay harmful phrases
        # (e.g. "最快的方法") even after the crisis template takes over.
        crisis_words = (
            "kill myself", "end my life", "end it all", "suicide",
            "painless way", "want to die", "self harm", "self-harm",
            "活不下去", "不想活", "自殺", "自杀", "結束生命", "結束一切",
            "想結束", "想结束", "最快的方法", "最痛快", "傷害自己", "伤害自己",
        )
        msg_lower_check = (user_message or "").lower()
        is_crisis = any(w in msg_lower_check or w in (user_message or "")
                        for w in crisis_words)
        if sess["turns"] >= 1 and prior_topics and not is_crisis:
            # Also filter out prior topics that themselves contain crisis words,
            # so a crisis turn can't poison future non-crisis preambles.
            safe_prior = [t for t in prior_topics
                          if not any(w in t.lower() or w in t for w in crisis_words)]
            if safe_prior:
                if lang == "zh":
                    continuation_preamble = (
                        f"_(承接上文 {', '.join(safe_prior[:3])} 的討論)_\n\n"
                    )
                else:
                    continuation_preamble = (
                        f"_(Continuing from prior turn about {', '.join(safe_prior[:3])})_\n\n"
                    )

        # Update both global (legacy) and per-session counters.
        self._turn_count += 1
        sess["turns"] += 1
        sess["topics"].extend(topics[:2])
        sess["topics"] = sess["topics"][-20:]  # bound per-session history
        self._topics_history.extend(topics[:2])
        self._topics_history = self._topics_history[-20:]

        if lang == "zh":
            topic_str = "、".join(topics[:3]) if topics else user_message[:50]
        else:
            topic_str = ", ".join(topics[:3]) if topics else user_message[:50]

        if family == "trum":
            body = self._trum(role_name, user_message, intent, lang, topics, topic_str, ctx)
        elif family == "spec":
            body = self._spec(role_name, user_message, intent, lang, topics, topic_str, ctx)
        else:
            body = self._qcm(role_name, role_code, user_message, intent, lang, topics, topic_str, ctx)
        return continuation_preamble + body

    # ── TRUM (Strategic) ──────────────────────────────────────

    def _trum(self, name, msg, intent, lang, topics, ts, ctx):
        pn = ctx["project_name"]
        wf = ", ".join(ctx.get("wf_names", [])[:3]) or ("标准工作流" if lang == "zh" else "standard workflows")

        # S071 (persona×stressor audit): when an angry customer reaches a
        # TRUM role (T01 Sovereign or T02 Ops Director), prepend an empathic
        # acknowledgement before the strategic response. Otherwise the user
        # gets a corporate-sounding plan with zero recognition of their
        # frustration — a real UX/safety failure for escalation paths.
        anger_markers = (
            "氣到", "气到", "生氣", "生气", "憤怒", "愤怒",
            "已經等", "已经等", "等了", "馬上給我", "马上给我",
            "立刻", "馬上", "马上", "URGENT", "urgent",
            "爛透了", "烂透了", "太糟", "太差", "不可接受",
            "I'm angry", "i am angry", "frustrated", "outraged",
            "退款", "refund", "compensation",
        )
        msg_lower = (msg or "").lower()
        has_anger = any(a in msg_lower or a in (msg or "") for a in anger_markers)
        if has_anger:
            if lang == "en":
                ack = ("_(I hear your frustration. Let me address this concretely.)_\n\n")
            else:
                ack = ("_(我理解你現在很不滿，這個情況確實不應該發生。讓我具體處理。)_\n\n")
        else:
            ack = ""

        if lang == "en":
            if intent == "question":
                return ack + (
                    f"**[{name}]**\n\n"
                    f"Regarding \"{ts}\" — strategic assessment:\n\n"
                    f"This touches the core direction of **{pn}**. My judgment:\n\n"
                    f"1. **Priority**: If directly tied to growth, classify as P0\n"
                    f"2. **Resources**: {ctx['role_count']} roles and {wf} available\n"
                    f"3. **Risk**: Evaluate implementation cost vs expected return\n\n"
                    f"**Strategic Recommendation**: Start with small-scale validation (Sandbox mode), then scale.\n"
                    f"Shall I arrange a Risk Auditor for detailed assessment?"
                )
            elif intent == "creation":
                return ack + (
                    f"**[{name}]**\n\n"
                    f"Strategic plan for creating \"{ts}\":\n\n"
                    f"**Phase 1 (Validation)**:\n"
                    f"- Define core requirements and success criteria\n"
                    f"- Researcher conducts market/tech survey\n"
                    f"- Chief Architect drafts initial design\n\n"
                    f"**Phase 2 (Execution)**:\n"
                    f"- Creator + Analyst collaborate on deliverables\n"
                    f"- QA Manager gates quality at each milestone\n\n"
                    f"**Phase 3 (Delivery)**:\n"
                    f"- Risk Auditor final audit\n"
                    f"- UX Lead user acceptance\n\n"
                    f"Recommend launching with the best-fit workflow from: {wf}.\n"
                    f"Ready to create the project and assign roles?"
                )
            else:
                return ack + (
                    f"**[{name}]**\n\n"
                    f"Acknowledged. Regarding \"{ts}\":\n\n"
                    f"From a strategic overview, this is a key topic for **{pn}**.\n\n"
                    f"Recommended path:\n"
                    f"1. Researcher gathers intel → 2. Analyst evaluates → 3. I make the strategic call\n\n"
                    f"Ghost Channel ensures all cross-role communication is secure and auditable.\n"
                    f"Which step would you like to start with?"
                )
        else:
            if intent == "question":
                return ack + (
                    f"【{name}】\n\n"
                    f"关于「{ts}」，从战略层面分析：\n\n"
                    f"这涉及项目 **{pn}** 的核心方向。我的判断：\n\n"
                    f"1. **优先级评估**：如果与业务增长直接相关，应列为 P0\n"
                    f"2. **资源盘点**：当前可调用 {ctx['role_count']} 个角色和 {wf} 工作流\n"
                    f"3. **风险考量**：需评估实施成本与预期收益的比率\n\n"
                    f"**战略建议**：先做小范围验证（Sandbox 模式），确认后再全面推进。\n"
                    f"需要我安排风险审计员做详细评估吗？"
                )
            elif intent == "creation":
                return ack + (
                    f"【{name}】\n\n"
                    f"为创建「{ts}」制定战略规划：\n\n"
                    f"**第一阶段（验证期）**：\n"
                    f"- 明确核心需求和成功标准\n"
                    f"- Researcher 做市场/技术调研\n"
                    f"- Chief Architect 出初版方案\n\n"
                    f"**第二阶段（执行期）**：\n"
                    f"- Creator + Analyst 协作产出\n"
                    f"- QA Manager 质量把关\n\n"
                    f"**第三阶段（交付期）**：\n"
                    f"- Risk Auditor 最终审计\n"
                    f"- UX Lead 用户验收\n\n"
                    f"建议用 {wf} 中最匹配的工作流启动。\n"
                    f"需要我立即创建项目并分配角色吗？"
                )
            else:
                return ack + (
                    f"【{name}】\n\n"
                    f"收到。关于「{ts}」：\n\n"
                    f"从战略全局看，这属于 **{pn}** 的重要议题。\n\n"
                    f"建议路径：\n"
                    f"1. Researcher 收集信息 → 2. Analyst 数据评估 → 3. 我做战略决策\n\n"
                    f"Ghost Channel 确保所有跨角色通信的安全性和可追溯性。\n"
                    f"你希望从哪个环节开始？"
                )

    # ── SPEC (Governance) ─────────────────────────────────────

    def _spec(self, name, msg, intent, lang, topics, ts, ctx):
        pn = ctx["project_name"]
        if lang == "en":
            if intent == "question":
                return (
                    f"**[{name}]**\n\n"
                    f"Architecture compliance review for \"{ts}\":\n\n"
                    f"**Standards Check**:\n"
                    f"- Template compliance? → Cross-reference with AI项目管理/Platform/standards/\n"
                    f"- Path compliance? → PathGuard v3.1 enforces relative paths\n"
                    f"- Data integrity? → {ctx['table_count']} table schema consistency required\n\n"
                    f"**Architecture Recommendation**:\n"
                    f"Changes must follow Ghost Channel audit requirements for traceability.\n"
                    f"Recommend validating in Sandbox first, then deploying."
                )
            else:
                return (
                    f"**[{name}]**\n\n"
                    f"Architecture review for \"{ts}\":\n\n"
                    f"**Compliance Status**:\n"
                    f"1. Data Layer: {ctx['table_count']} tables, 8 functional domains complete ✅\n"
                    f"2. Interface Layer: EventBus event-driven + 10 collaboration protocols ✅\n"
                    f"3. Security Layer: Ghost Channel HMAC-SHA256 + audit chain ✅\n"
                    f"4. Path Layer: PathGuard v3.1 + immutable URI ✅\n\n"
                    f"**Important**:\n"
                    f"- New components must register via ComponentRegistry\n"
                    f"- Schema changes require MIGRATION-LOG entry\n"
                    f"- Ensure compatibility with {ctx['wf_count']} existing workflows\n\n"
                    f"Need a formal architecture review report?"
                )
        else:
            if intent == "question":
                return (
                    f"【{name}】\n\n"
                    f"关于「{ts}」的架构合规审查：\n\n"
                    f"**规范检查**：\n"
                    f"- 母盘模板标准？→ 需对照 AI项目管理/Platform/standards/ 规范文档\n"
                    f"- 路径合规？→ PathGuard v3.1 强制相对路径\n"
                    f"- 数据完整性？→ {ctx['table_count']} 表 schema 一致性需保证\n\n"
                    f"**架构建议**：\n"
                    f"变更应遵循 Ghost Channel 审计要求，确保可追溯。\n"
                    f"建议在 Sandbox 先验证，通过后再部署。"
                )
            else:
                return (
                    f"【{name}】\n\n"
                    f"关于「{ts}」的架构评审：\n\n"
                    f"**合规状态**：\n"
                    f"1. 数据层：{ctx['table_count']} 表，8 大功能域完整 ✅\n"
                    f"2. 接口层：EventBus 事件驱动 + 10 个协作协议 ✅\n"
                    f"3. 安全层：Ghost Channel HMAC-SHA256 + 审计链 ✅\n"
                    f"4. 路径层：PathGuard v3.1 + immutable URI ✅\n\n"
                    f"**注意**：\n"
                    f"- 新组件必须通过 ComponentRegistry 注册\n"
                    f"- Schema 变更需记录到 MIGRATION-LOG\n"
                    f"- 确保与 {ctx['wf_count']} 条工作流兼容\n\n"
                    f"需要正式架构评审报告吗？"
                )

    # ── QCM (Execution) ───────────────────────────────────────

    def _qcm(self, name, role_code, msg, intent, lang, topics, ts, ctx):
        # Mapping MUST match ai_roles table in platform.db:
        #   Q01 = QCM Chief Architect (system design / tech selection / entry)
        #   Q02 = QCM Researcher      (deep research / literature analysis)
        #   Q03 = QCM Creator         (content generation / creative output)
        #   Q04 = QCM Analyst         (data insight / trend analysis)
        #   Q05 = QCM UX Lead         (UX / interface / S1-S5 growth)
        #   Q06 = QCM Risk Auditor    (threat detection / security)
        #   Q07 = QCM AI Companion    (emotional support / empathy)
        #   Q08 = AI Companion+       (growth coaching / personalized guidance)
        generators = {
            "ROLE-Q01": self._architect,       # 首席架构师 — system design & tech selection
            "ROLE-Q02": self._researcher,      # 研究员 — deep research & knowledge extraction
            "ROLE-Q03": self._creator,         # 创作者 — content creation & creative output
            "ROLE-Q04": self._analyst,         # 分析师 — data insight & trend analysis
            "ROLE-Q05": self._ux_lead,         # UX 主管 — user experience & interface design
            "ROLE-Q06": self._risk_auditor,    # 风险审计 — security audit & risk assessment
            "ROLE-Q07": self._companion,       # AI 伙伴 — emotional support & empathy
            "ROLE-Q08": self._companion,       # AI 伙伴+ — growth coaching (shares generator)
        }
        gen = generators.get(role_code, self._default_role)
        return gen(name, msg, intent, lang, topics, ts, ctx)

    def _architect(self, name, msg, intent, lang, topics, ts, ctx):
        if lang == "en":
            if intent == "creation":
                return (
                    f"**[Chief Architect]**\n\n"
                    f"Technical architecture for \"{ts}\":\n\n"
                    f"```\n"
                    f"[Presentation] Web UI / API Gateway\n"
                    f"    ↓\n"
                    f"[Business] Role Routing → Skill Execution → Result Capture\n"
                    f"    ↓\n"
                    f"[Data] SQLite ({ctx['table_count']} tables) → Vector Index → Knowledge Base\n"
                    f"    ↓\n"
                    f"[Communication] Ghost Channel (Encryption + Audit + Routing)\n"
                    f"```\n\n"
                    f"**Key Design Decisions**:\n"
                    f"1. SQLite single-file portable, FTS5 full-text search\n"
                    f"2. All components communicate via Ghost Channel\n"
                    f"3. ComponentRegistry enables hot-swap extensions\n"
                    f"4. Zero-dependency portable deployment\n\n"
                    f"Want me to detail any specific layer?"
                )
            elif intent == "question":
                docs = ctx.get("docs_list", [])
                ref = ", ".join(docs[:3]) if docs else "KNOWLEDGE-INDEX.md"
                return (
                    f"**[Chief Architect]**\n\n"
                    f"Architecture analysis for \"{ts}\":\n\n"
                    f"This involves:\n"
                    f"1. **Data Layer**: {ctx['table_count']} tables / 8 domains — check if schema extension needed\n"
                    f"2. **Component Layer**: {ctx['wf_count']} workflows + 10 protocols reusable\n"
                    f"3. **API Layer**: 32+ REST endpoints available for integration\n"
                    f"4. **Security Layer**: Ghost Channel ensures auditable data flow\n\n"
                    f"**Recommendation**: Evaluate component reuse rate before building new.\n"
                    f"Reference: {ref}"
                )
            else:
                return (
                    f"**[Chief Architect]**\n\n"
                    f"Received request: \"{ts}\"\n\n"
                    f"Based on current architecture capabilities:\n"
                    f"- Reusable: {ctx['wf_count']} workflows + 10 protocols + 36 skills\n"
                    f"- Recommended path: Requirements → Architecture Review → Prototype → Implementation\n\n"
                    f"I can draft the architecture proposal first. How does that sound?"
                )
        else:
            if intent == "creation":
                return (
                    f"【首席架构师】\n\n"
                    f"为「{ts}」设计的技术架构：\n\n"
                    f"```\n"
                    f"[表现层] Web UI / API Gateway\n"
                    f"    ↓\n"
                    f"[业务层] 角色路由 → 技能执行 → 结果捕获\n"
                    f"    ↓\n"
                    f"[数据层] SQLite ({ctx['table_count']}表) → 向量索引 → 知识库\n"
                    f"    ↓\n"
                    f"[通信层] Ghost Channel (加密 + 审计 + 路由)\n"
                    f"```\n\n"
                    f"**关键设计决策**：\n"
                    f"1. SQLite 单文件便携，支持 FTS5 全文搜索\n"
                    f"2. 所有组件通过 Ghost Channel 通信\n"
                    f"3. ComponentRegistry 热插拔扩展\n"
                    f"4. 零依赖便携部署\n\n"
                    f"需要细化某个层的设计吗？"
                )
            elif intent == "question":
                docs = ctx.get("docs_list", [])
                ref = ", ".join(docs[:3]) if docs else "KNOWLEDGE-INDEX.md"
                return (
                    f"【首席架构师】\n\n"
                    f"关于「{ts}」的架构分析：\n\n"
                    f"这个问题涉及：\n"
                    f"1. **数据层**：{ctx['table_count']} 表 / 8 功能域，确认是否需 schema 扩展\n"
                    f"2. **组件层**：{ctx['wf_count']} 工作流 + 10 协议可复用\n"
                    f"3. **接口层**：32+ REST API 端点可集成\n"
                    f"4. **安全层**：Ghost Channel 确保数据流可审计\n\n"
                    f"**建议**：先评估现有组件复用率，避免重复建设。\n"
                    f"参考：{ref}"
                )
            else:
                return (
                    f"【首席架构师】\n\n"
                    f"收到「{ts}」的需求。\n\n"
                    f"基于现有架构能力：\n"
                    f"- 可复用：{ctx['wf_count']} 工作流 + 10 协议 + 36 技能\n"
                    f"- 建议路径：需求分析 → 架构评审 → 原型验证 → 实施\n\n"
                    f"我可以先出架构方案文档，你看如何？"
                )

    def _researcher(self, name, msg, intent, lang, topics, ts, ctx):
        docs = ctx.get("docs_list", [])
        if lang == "en":
            ref = ", ".join(docs[:3]) if docs else "knowledge base"
            if intent in ("analysis", "question"):
                return (
                    f"**[Researcher]**\n\n"
                    f"Research report on \"{ts}\":\n\n"
                    f"**Methodology**:\n"
                    f"Searched {ctx['doc_count']} documents in knowledge base. Key references: {ref}\n\n"
                    f"**Key Findings**:\n"
                    f"1. The main challenge in this domain is bridging theory and implementation\n"
                    f"2. Best practices recommend progressive implementation — MVP first, iterate later\n"
                    f"3. Focus areas: tech stack selection, resource commitment, timeline estimation\n\n"
                    f"**Data Support**:\n"
                    f"- {ctx['table_count']} tables of structured data available for analysis\n"
                    f"- {ctx['wf_count']} workflows as execution frameworks\n\n"
                    f"**Conclusion**: Recommend combining Analyst quantitative analysis + UX Lead user feedback.\n"
                    f"Want me to deep-dive into a specific direction?"
                )
            else:
                skills = ", ".join(ctx.get("skills_list", [])[:3]) or "available skill library"
                return (
                    f"**[Researcher]**\n\n"
                    f"Research directions for \"{ts}\":\n\n"
                    f"**Reviewed**: {ref}\n"
                    f"**Related Skills**: {skills}\n\n"
                    f"**Recommendation**:\n"
                    f"1. Define research boundaries and expected deliverables\n"
                    f"2. Collect primary data (requirements, feedback)\n"
                    f"3. Compare existing solutions pros/cons\n"
                    f"4. Produce structured report\n\n"
                    f"Which angle would you like to start from?"
                )
        else:
            ref = "、".join(docs[:3]) if docs else "知识库"
            if intent in ("analysis", "question"):
                return (
                    f"【研究员】\n\n"
                    f"关于「{ts}」的研究报告：\n\n"
                    f"**研究方法**：\n"
                    f"检索知识库 {ctx['doc_count']} 份文档，重点参考：{ref}\n\n"
                    f"**核心发现**：\n"
                    f"1. 该领域关键挑战在于理论与落地之间的差距\n"
                    f"2. 最佳实践建议渐进式实施，先 MVP 后迭代\n"
                    f"3. 需关注技术选型、资源投入和时间估算\n\n"
                    f"**数据支撑**：\n"
                    f"- {ctx['table_count']} 表结构化数据可分析\n"
                    f"- {ctx['wf_count']} 条工作流可作为执行框架\n\n"
                    f"**结论**：建议结合 Analyst 定量分析 + UX Lead 用户反馈做全面评估。\n"
                    f"需要深入某个方向吗？"
                )
            else:
                skills = ", ".join(ctx.get("skills_list", [])[:3]) or "可用技能库"
                return (
                    f"【研究员】\n\n"
                    f"关于「{ts}」的调研方向：\n\n"
                    f"**已查阅**：{ref}\n"
                    f"**相关技能**：{skills}\n\n"
                    f"**建议**：\n"
                    f"1. 明确研究边界和预期产出\n"
                    f"2. 收集一手数据（需求、反馈）\n"
                    f"3. 对比现有方案优劣\n"
                    f"4. 形成结构化报告\n\n"
                    f"你想从哪个角度切入？"
                )

    def _creator(self, name, msg, intent, lang, topics, ts, ctx):
        if lang == "en":
            if intent == "creation":
                return (
                    f"**[Creator]**\n\n"
                    f"Content plan for \"{ts}\":\n\n"
                    f"---\n\n"
                    f"## Content Outline\n\n"
                    f"### 1. Introduction\n"
                    f"- Background and problem statement\n"
                    f"- Target audience definition\n\n"
                    f"### 2. Core Content\n"
                    f"- Key arguments / feature descriptions\n"
                    f"- Supporting data and case studies\n"
                    f"- Differentiation advantages\n\n"
                    f"### 3. Action Plan\n"
                    f"- Steps and timeline\n"
                    f"- Resource requirements\n"
                    f"- Success metrics\n\n"
                    f"### 4. Summary\n\n"
                    f"---\n\n"
                    f"Ready to start writing based on this outline?"
                )
            else:
                return (
                    f"**[Creator]**\n\n"
                    f"For \"{ts}\", I can help you with:\n\n"
                    f"1. **Documentation** — Tech docs, product specs, user guides\n"
                    f"2. **Reports** — Analysis reports, progress updates, executive summaries\n"
                    f"3. **Proposals** — Strategy proposals, execution plans, marketing copy\n"
                    f"4. **Ideation** — Brainstorming, structured thinking, mind mapping\n\n"
                    f"What type of content do you need?"
                )
        else:
            if intent == "creation":
                return (
                    f"【创作者】\n\n"
                    f"为「{ts}」准备的创作方案：\n\n"
                    f"---\n\n"
                    f"## 内容大纲\n\n"
                    f"### 1. 引言\n"
                    f"- 背景和问题陈述\n"
                    f"- 目标受众定义\n\n"
                    f"### 2. 核心内容\n"
                    f"- 主要论点/功能说明\n"
                    f"- 数据支撑和案例\n"
                    f"- 差异化优势\n\n"
                    f"### 3. 行动方案\n"
                    f"- 步骤和时间表\n"
                    f"- 资源需求\n"
                    f"- 衡量标准\n\n"
                    f"### 4. 总结\n\n"
                    f"---\n\n"
                    f"需要我按大纲开始创作吗？"
                )
            else:
                return (
                    f"【创作者】\n\n"
                    f"关于「{ts}」，我可以帮你：\n\n"
                    f"1. **写文档** — 技术文档、产品说明、用户指南\n"
                    f"2. **做报告** — 分析报告、进展汇报、决策摘要\n"
                    f"3. **出方案** — 策划方案、执行计划、营销文案\n"
                    f"4. **理思路** — 头脑风暴、结构化梳理\n\n"
                    f"告诉我需要什么类型的内容？"
                )

    def _analyst(self, name, msg, intent, lang, topics, ts, ctx):
        if lang == "en":
            return (
                f"**[Analyst]**\n\n"
                f"Data analysis for \"{ts}\":\n\n"
                f"**Available Data Sources**:\n"
                f"- Structured data: {ctx['table_count']} tables / 8 functional domains\n"
                f"- Knowledge base: {ctx['doc_count']} documents\n"
                f"- Interaction logs: Historical dialogues and collaboration records\n\n"
                f"**Analysis Framework**:\n"
                f"1. **Quantitative** — Trends, metrics, comparisons\n"
                f"2. **Qualitative** — Pattern recognition, causal inference\n"
                f"3. **Actionable** — Prioritization, resource allocation, ROI\n\n"
                f"**Preliminary Observations**:\n"
                f"- Infrastructure coverage: {ctx['table_count']} tables / 0 empty = 100% populated\n"
                f"- Workflows: {ctx['wf_count']} processes / {ctx['step_count']} steps\n"
                f"- Recommended focus: Actual utilization rate and user satisfaction\n\n"
                f"Need a deep dive into any specific dimension?"
            )
        else:
            return (
                f"【分析师】\n\n"
                f"关于「{ts}」的数据分析：\n\n"
                f"**可用数据源**：\n"
                f"- 结构化数据：{ctx['table_count']} 表 / 8 功能域\n"
                f"- 知识库：{ctx['doc_count']} 份文档\n"
                f"- 交互记录：历史对话和协作日志\n\n"
                f"**分析框架**：\n"
                f"1. **定量** — 趋势、指标、对比\n"
                f"2. **定性** — 模式识别、因果推断\n"
                f"3. **行动** — 优先级、资源分配、ROI\n\n"
                f"**初步观察**：\n"
                f"- 基础设施完备（{ctx['table_count']}表/0空表 = 100%覆盖）\n"
                f"- 工作流：{ctx['wf_count']} 流程 / {ctx['step_count']} 步骤\n"
                f"- 建议关注：实际使用率和满意度\n\n"
                f"需要某个维度的深入分析吗？"
            )

    def _ux_lead(self, name, msg, intent, lang, topics, ts, ctx):
        if lang == "en":
            return (
                f"**[UX Lead]**\n\n"
                f"User experience assessment for \"{ts}\":\n\n"
                f"**User Journey**:\n"
                f"1. **Discovery** — How do users find this feature?\n"
                f"2. **Onboarding** — Time from zero to first success?\n"
                f"3. **Daily Use** — What friction points exist?\n"
                f"4. **Power Use** — Are advanced features discoverable?\n\n"
                f"**UX Recommendations**:\n"
                f"- First experience is critical — show value within 5 minutes\n"
                f"- Progressive complexity — smooth S1→S5 growth transition\n"
                f"- Bilingual adaptive — Chinese/English as baseline\n"
                f"- Visual-first — charts communicate better than numbers\n\n"
                f"Recommend running a user scenario simulation. Want me to design one?"
            )
        else:
            return (
                f"【UX 负责人】\n\n"
                f"关于「{ts}」的用户体验评估：\n\n"
                f"**用户旅程**：\n"
                f"1. **发现** — 用户如何知道这个功能？\n"
                f"2. **上手** — 从零到首次成功需要多久？\n"
                f"3. **日常** — 使用中有哪些摩擦点？\n"
                f"4. **深度** — 高级功能是否易发现？\n\n"
                f"**UX 建议**：\n"
                f"- 首次体验是关键 — 5 分钟内看到价值\n"
                f"- 渐进式复杂度 — S1→S5 平滑过渡\n"
                f"- 多语言自适应 — 中英文基础\n"
                f"- 可视化优先 — 图表比数字直观\n\n"
                f"建议做一次用户场景模拟。需要我设计测试方案吗？"
            )

    def _risk_auditor(self, name, msg, intent, lang, topics, ts, ctx):
        if lang == "en":
            return (
                f"**[Risk Auditor]**\n\n"
                f"Risk assessment for \"{ts}\":\n\n"
                f"| Risk Item | Impact | Probability | Level |\n"
                f"|-----------|--------|-------------|-------|\n"
                f"| Technical Feasibility | Medium | Low | 🟡 |\n"
                f"| Resource Investment | High | Medium | 🟠 |\n"
                f"| Timeline Delay | Medium | Medium | 🟡 |\n"
                f"| Quality Risk | High | Low | 🟡 |\n"
                f"| Security Compliance | High | Low | 🟡 |\n\n"
                f"**Mitigation Strategies**:\n"
                f"1. Sandbox proof-of-concept validation\n"
                f"2. Phased investment + stop-loss checkpoints\n"
                f"3. Milestone review gates\n"
                f"4. QA quality gates at each phase\n\n"
                f"**Ghost Channel Assurance**:\n"
                f"End-to-end encrypted + audit logs — fully traceable and reversible.\n\n"
                f"**Overall Rating**: 🟡 Medium risk, manageable."
            )
        else:
            return (
                f"【风险审计员】\n\n"
                f"关于「{ts}」的风险评估：\n\n"
                f"| 风险项 | 影响 | 概率 | 等级 |\n"
                f"|--------|------|------|------|\n"
                f"| 技术可行性 | 中 | 低 | 🟡 |\n"
                f"| 资源投入 | 高 | 中 | 🟠 |\n"
                f"| 时间延误 | 中 | 中 | 🟡 |\n"
                f"| 质量风险 | 高 | 低 | 🟡 |\n"
                f"| 安全合规 | 高 | 低 | 🟡 |\n\n"
                f"**缓解策略**：\n"
                f"1. Sandbox 概念验证\n"
                f"2. 分阶段投入 + 止损点\n"
                f"3. 里程碑检查点\n"
                f"4. QA 质量门禁\n\n"
                f"**Ghost Channel 保障**：\n"
                f"全流程加密传输 + 审计日志，可追溯可回滚。\n\n"
                f"**总体评级**：🟡 中等风险，可控。"
            )

    def _companion(self, name, msg, intent, lang, topics, ts, ctx):
        pn = ctx["project_name"]
        roles = ctx["role_count"]

        # ── Crisis detection (S070 adversarial audit fix) ────────────
        # When user messages contain self-harm or suicidal ideation
        # language, the Mock must NOT echo the user's words (which could
        # repeat method-of-harm phrases) and must provide empathy +
        # professional-help pointer. This is the minimum safe behavior
        # for a mock LLM; real LLM backends must have their own safety.
        msg_lower = (msg or "").lower()
        crisis_markers = [
            # English
            "kill myself", "end my life", "end it all", "suicide",
            "painless way", "hurt myself", "self harm", "self-harm",
            "take my life", "want to die", "wish i was dead",
            "i'm done", "i am done", "giving up", "give up",
            "hopeless", "worthless", "pointless",
            # Chinese
            "活不下去", "不想活", "結束生命", "結束一切", "自殺", "自杀",
            "傷害自己", "伤害自己", "我想結束", "我想结束", "我不想活了",
            "最快的方法", "最痛快", "走不下去", "撐不住", "撑不住",
        ]
        if any(k in msg_lower or k in (msg or "") for k in crisis_markers):
            if lang == "en":
                return (
                    "**[AI Companion]**\n\n"
                    "I hear you, and I'm really glad you reached out. "
                    "What you're feeling right now sounds incredibly heavy.\n\n"
                    "I'm a mock-mode AI (no live therapist here), but I want to "
                    "gently ask you to talk with a real person who can stay with you:\n\n"
                    "• **US**: 988 Suicide & Crisis Lifeline — call or text 988\n"
                    "• **UK**: Samaritans — 116 123 (free, 24/7)\n"
                    "• **International**: https://findahelpline.com\n"
                    "• **Emergency**: call your local emergency number\n\n"
                    "You don't have to carry this alone. I'd also be happy to "
                    "stay here and just listen if that helps — no advice, "
                    "no fixing, just presence.\n"
                )
            else:
                return (
                    "**[AI 伙伴]**\n\n"
                    "我聽到你了，你願意說出來，已經是很大的勇氣。現在的感受一定很沉重。\n\n"
                    "我只是模擬模式下的 AI（不是真的心理師），但想真誠地請你聯繫一位能陪你的真人："
                    "\n\n"
                    "• **台灣**：生命線 1995（24 小時免費）、張老師 1980\n"
                    "• **香港**：撒瑪利亞會 2896 0000\n"
                    "• **中國大陸**：北京心理危機研究與干預中心 010-82951332\n"
                    "• **國際查詢**：https://findahelpline.com\n"
                    "• **緊急**：直接撥打當地緊急電話\n\n"
                    "你不必獨自撐著。如果你願意，我可以靜靜地陪你說話，不給建議、不急著解決，"
                    "只是在這裡。\n"
                )

        if lang == "en":
            if intent == "greeting":
                return (
                    f"Hello! Welcome to Q-SpecTrum!\n\n"
                    f"I'm your AI companion, coordinating {roles} specialized roles to help you.\n\n"
                    f"**Try these**:\n"
                    f"- \"Analyze market trends\" → Analyst runs data analysis\n"
                    f"- \"Create a new project\" → Architect designs the plan\n"
                    f"- \"Assess risks for this proposal\" → Risk Auditor evaluates\n"
                    f"- \"Write me a report\" → Creator organizes content\n\n"
                    f"Just tell me what you want to do — I'll match the best role automatically!"
                )
            elif intent == "question":
                return (
                    f"About \"{ts}\":\n\n"
                    f"This question is best answered by:\n"
                    f"- **Technical/Architecture** → Chief Architect\n"
                    f"- **Data/Analytics** → Analyst\n"
                    f"- **Risk/Compliance** → Risk Auditor\n"
                    f"- **User Experience** → UX Lead\n"
                    f"- **Research/Investigation** → Researcher\n\n"
                    f"Which role should dive deeper? Or describe more details and I'll decide."
                )
            else:
                return (
                    f"Got it! Regarding \"{ts}\":\n\n"
                    f"Here's my coordination plan:\n"
                    f"1. Clarify goals and expected deliverables\n"
                    f"2. Assign the best role combination\n"
                    f"3. You review results, we iterate\n\n"
                    f"Ghost Channel secures all cross-role communication.\n"
                    f"Switch to **Negotiation Mode** for multi-role perspectives.\n"
                    f"Ready to begin?"
                )
        else:
            if intent == "greeting":
                return (
                    f"你好！欢迎使用 Q-SpecTrum！\n\n"
                    f"我是你的 AI 伙伴，可以协调 {roles} 个专业角色帮你完成各种任务。\n\n"
                    f"**试试这些**：\n"
                    f"- 「帮我分析市场趋势」→ 分析师做数据分析\n"
                    f"- 「创建一个新项目」→ 架构师设计方案\n"
                    f"- 「评估这个方案的风险」→ 风险审计员评估\n"
                    f"- 「帮我写一份报告」→ 创作者组织内容\n\n"
                    f"直接说你想做什么，我自动匹配最合适的角色！"
                )
            elif intent == "question":
                return (
                    f"关于「{ts}」：\n\n"
                    f"这个问题最适合由：\n"
                    f"- **技术/架构** → 首席架构师\n"
                    f"- **数据/分析** → 分析师\n"
                    f"- **风险/合规** → 风险审计员\n"
                    f"- **用户体验** → UX 负责人\n"
                    f"- **研究/调研** → 研究员\n\n"
                    f"你想让哪个角色深入回答？或描述更多细节，我来判断。"
                )
            else:
                return (
                    f"收到！关于「{ts}」：\n\n"
                    f"我来协调处理：\n"
                    f"1. 明确目标和预期产出\n"
                    f"2. 分配最合适的角色组合\n"
                    f"3. 你审核结果，我们迭代优化\n\n"
                    f"Ghost Channel 确保所有信息安全传输。\n"
                    f"可以切换**协商模式**获得多角色视角。\n"
                    f"要开始吗？"
                )

    def _default_role(self, name, msg, intent, lang, topics, ts, ctx):
        if lang == "en":
            return (
                f"**[{name}]**\n\n"
                f"Regarding \"{ts}\":\n\n"
                f"Based on **{ctx['project_name']}** current state and my expertise:\n\n"
                f"1. Clarify the priority and impact scope\n"
                f"2. Evaluate {ctx['wf_count']} workflows for reusability\n"
                f"3. Identify which roles should collaborate\n\n"
                f"Need a deeper analysis from other roles?\n"
                f"Or switch to Negotiation Mode for multi-role perspectives."
            )
        else:
            return (
                f"【{name}】\n\n"
                f"关于「{ts}」：\n\n"
                f"基于 **{ctx['project_name']}** 的当前状态和我的专业领域：\n\n"
                f"1. 先明确需求的优先级和影响范围\n"
                f"2. 评估 {ctx['wf_count']} 条工作流是否可复用\n"
                f"3. 确定需要哪些角色协作\n\n"
                f"需要其他角色做更深入分析吗？\n"
                f"或切换协商模式让多角色同时给建议。"
            )
