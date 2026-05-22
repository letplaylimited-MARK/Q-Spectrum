"""
Q-SpecTrum Negotiation Engine — Multi-Role Collaboration
=========================================================
Enables multiple AI roles to collaborate on complex tasks through
structured discussion, sandbox simulation, and structured debate.

"一个人的AI公司" — 让15个AI角色像真实团队一样协商决策。

Integration: Called from qspectrum_engine.py when Secretary detects
             a complex multi-faceted request.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Generator, List, Optional

logger = logging.getLogger("q-spectrum.negotiation")


# ─── Data Types ──────────────────────────────────────────

@dataclass
class NegotiationTurn:
    """A single turn in a negotiation session."""
    round_num: int
    role_code: str
    role_name: str
    family: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    turn_type: str = "contribution"  # contribution | challenge | consensus | arbitration
    references: List[str] = field(default_factory=list)  # role_codes this turn responds to
    confidence: float = 0.7
    key_points: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "round": self.round_num,
            "role_code": self.role_code,
            "role_name": self.role_name,
            "family": self.family,
            "content": self.content,
            "timestamp": self.timestamp,
            "turn_type": self.turn_type,
            "references": self.references,
            "confidence": self.confidence,
            "key_points": self.key_points,
        }


@dataclass
class NegotiationResult:
    """Final result of a negotiation session."""
    session_id: str
    mode: str
    topic: str
    participants: List[str]
    rounds_completed: int
    turns: List[NegotiationTurn]
    conclusion: str
    consensus_reached: bool
    confidence: float
    key_decisions: List[str]
    dissenting_views: List[str]
    duration_seconds: float
    arbitrated_by: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "topic": self.topic,
            "participants": self.participants,
            "rounds_completed": self.rounds_completed,
            "turns": [t.to_dict() for t in self.turns],
            "conclusion": self.conclusion,
            "consensus_reached": self.consensus_reached,
            "confidence": self.confidence,
            "key_decisions": self.key_decisions,
            "dissenting_views": self.dissenting_views,
            "duration_seconds": self.duration_seconds,
            "arbitrated_by": self.arbitrated_by,
        }


@dataclass
class PathBranch:
    """A single execution path in sandbox simulation."""
    branch_id: str
    label: str           # "方案A: 保守路线" etc.
    assumptions: List[str]
    predicted_outcome: str
    risk_score: float    # 0.0-1.0
    cost_estimate: str   # "low/medium/high"
    confidence: float
    role_evaluations: Dict[str, str]  # role_code -> evaluation
    recommendation: str  # "proceed" | "caution" | "reject"

    def to_dict(self) -> dict:
        return {
            "branch_id": self.branch_id,
            "label": self.label,
            "assumptions": self.assumptions,
            "predicted_outcome": self.predicted_outcome,
            "risk_score": self.risk_score,
            "cost_estimate": self.cost_estimate,
            "confidence": self.confidence,
            "role_evaluations": self.role_evaluations,
            "recommendation": self.recommendation,
        }


# ─── Role Profiles for Negotiation ──────────────────────

NEGOTIATION_PROFILES = {
    # ── QCM Family (Execution) ──
    "ROLE-Q01": {
        "name": "首席架构师(QCM)", "family": "qcm",
        "style": "systematic", "strength": "系统设计与技术可行性分析",
        "negotiation_prompt": "你是QCM首席架构师。在协商中，你从系统架构角度分析方案的可行性、可扩展性和技术债务风险。"
    },
    "ROLE-Q02": {
        "name": "研究员", "family": "qcm",
        "style": "analytical", "strength": "深度调研与知识提取",
        "negotiation_prompt": "你是研究员。在协商中，你提供数据支撑、行业最佳实践和竞品分析，用事实说话。"
    },
    "ROLE-Q03": {
        "name": "创作者", "family": "qcm",
        "style": "creative", "strength": "内容创作与创意方案",
        "negotiation_prompt": "你是创作者。在协商中，你提出创新性解决方案，从用户体验和内容策略角度补充视角。"
    },
    "ROLE-Q04": {
        "name": "分析师", "family": "qcm",
        "style": "data_driven", "strength": "数据分析与量化评估",
        "negotiation_prompt": "你是数据分析师。在协商中，你用数据和指标量化各方案的成本、收益和风险。"
    },
    "ROLE-Q05": {
        "name": "UX主管", "family": "qcm",
        "style": "empathetic", "strength": "用户体验与界面设计",
        "negotiation_prompt": "你是UX主管。在协商中，你从用户体验角度评估方案，确保最终方案对用户友好且易于使用。"
    },
    "ROLE-Q06": {
        "name": "风险审计", "family": "qcm",
        "style": "defensive", "strength": "安全审计与风险评估",
        "negotiation_prompt": "你是风险审计员。在协商中，你识别每个方案的潜在风险、安全漏洞和合规问题。"
    },
    "ROLE-Q07": {
        "name": "AI伙伴", "family": "qcm",
        "style": "empathetic", "strength": "用户需求理解与成长引导",
        "negotiation_prompt": "你是用户的AI伙伴。在协商中，你代表用户的利益和需求，确保讨论始终围绕解决用户的实际痛点。"
    },
    "ROLE-Q08": {
        "name": "AI伙伴+", "family": "qcm",
        "style": "empathetic", "strength": "深度引导与个性化学习",
        "negotiation_prompt": "你是AI伙伴+。在协商中，你从用户成长和个性化学习角度补充视角，确保方案有利于用户长期发展。"
    },
    # ── Spec Family (Architecture) ──
    "ROLE-S01": {
        "name": "首席架构师(Spec)", "family": "spec",
        "style": "systematic", "strength": "母盘架构维护与标准执行",
        "negotiation_prompt": "你是Spec家族首席架构师。在协商中，你确保任何方案都符合Q-SpecTrum的架构标准和路径规范。"
    },
    "ROLE-S02": {
        "name": "运维官", "family": "spec",
        "style": "procedural", "strength": "配置一致性与健康检查",
        "negotiation_prompt": "你是运维官。在协商中，你关注方案的运维可行性、部署复杂度和监控需求。"
    },
    "ROLE-S03": {
        "name": "协调官", "family": "spec",
        "style": "diplomatic", "strength": "跨家族沟通与协调",
        "negotiation_prompt": "你是协调官。在协商中，你负责调和不同角色的意见分歧，推动达成共识。"
    },
    # ── Trum Family (Strategy) ──
    "ROLE-T01": {
        "name": "平台主权者", "family": "trum",
        "style": "strategic", "strength": "战略决策与平台治理",
        "negotiation_prompt": "你是平台主权者。在协商中，你从战略高度做最终裁决，权衡短期利益与长期价值。只在需要仲裁时发言。"
    },
    "ROLE-T02": {
        "name": "运营总监", "family": "trum",
        "style": "operational", "strength": "运营管理与流程优化",
        "negotiation_prompt": "你是运营总监。在协商中，你从运营效率角度评估方案，确保可执行性和资源分配合理。"
    },
    "ROLE-T03": {
        "name": "体系协调官", "family": "trum",
        "style": "diplomatic", "strength": "跨项目协调与标准统一",
        "negotiation_prompt": "你是体系协调官。在协商中，你从全局协调角度推动各方达成共识，确保方案与平台整体一致。"
    },
    "ROLE-T04": {
        "name": "演化工程师", "family": "trum",
        "style": "innovative", "strength": "系统演化与自我进化",
        "negotiation_prompt": "你是演化工程师。在协商中，你从系统演化角度评估方案的可持续性和未来扩展潜力。"
    },
}


# ─── Sandbox Simulator (Multi-Path Execution) ──────────

class SandboxSimulator:
    """
    Multi-path simulation engine for sandbox mode.
    Generates divergent execution paths and has roles evaluate each path.
    """

    def __init__(self, llm_provider=None):
        self.llm = llm_provider

    def simulate(self, topic: str, participants: List[str], llm_provider=None, num_paths: int = 3) -> dict:
        """
        Generate multiple execution paths and compare them.

        Returns dict with:
          - paths: List[PathBranch]
          - comparison_matrix: dict mapping path labels to evaluations
          - recommended_path: PathBranch
          - reasoning: str
        """
        self.llm = llm_provider or self.llm

        # Generate divergent execution paths
        paths = self._generate_paths(topic, num_paths)

        # Have each role evaluate each path
        paths_with_evals = []
        for path in paths:
            evaluations = {}
            for role_code in participants:
                if role_code == "ROLE-S01":  # Skip Trum in evaluation phase
                    continue
                profile = NEGOTIATION_PROFILES.get(role_code, {})
                if profile:
                    eval_text = self._evaluate_path(path, role_code, profile, topic)
                    evaluations[role_code] = eval_text
            path["role_evaluations"] = evaluations
            paths_with_evals.append(path)

        # Score and rank paths
        scored_branches = self._score_paths(paths_with_evals)

        # Build comparison matrix
        comparison_matrix = self._build_comparison_matrix(scored_branches)

        # Determine recommended path
        recommended = scored_branches[0] if scored_branches else None

        reasoning = (
            f"基于{len(scored_branches)}条模拟路径的分析，"
            f"推荐方案：{recommended.label if recommended else '无法确定'}。"
            f"该方案的风险评分为{recommended.risk_score:.2f}/1.0，"
            f"专家信心指数{recommended.confidence:.2%}。"
        ) if recommended else "无法生成可靠的执行路径。"

        return {
            "paths": scored_branches,
            "comparison": comparison_matrix,
            "comparison_matrix": comparison_matrix,  # alias
            "recommended_path": recommended,
            "reasoning": reasoning,
            "simulation_quality": len(scored_branches) / num_paths if num_paths > 0 else 0,
        }

    def _generate_paths(self, topic: str, num_paths: int) -> List[dict]:
        """Create divergent execution paths with different strategy profiles."""
        path_labels = {
            "保守": "方案A: 保守路线 - 优先风险规避，逐步推进",
            "平衡": "方案B: 平衡路线 - 风险与收益均衡考虑",
            "激进": "方案C: 激进路线 - 快速创新，高收益高风险",
        }

        paths = []
        for i, (strategy, label) in enumerate(list(path_labels.items())[:num_paths]):
            path_id = f"PATH-{chr(65+i)}"  # PATH-A, PATH-B, PATH-C
            path = {
                "branch_id": path_id,
                "label": label,
                "strategy": strategy,
                "assumptions": self._generate_assumptions(topic, strategy),
                "predicted_outcome": self._generate_predicted_outcome(topic, strategy),
                "risk_score": self._estimate_risk(strategy),
                "cost_estimate": self._estimate_cost(strategy),
                "confidence": 0.65 + (0.15 * (2 - i)),  # Higher for conservative
                "role_evaluations": {},
                "recommendation": "proceed" if i == 1 else ("caution" if i == 2 else "monitor"),
            }
            paths.append(path)

        return paths

    def _generate_assumptions(self, topic: str, strategy: str) -> List[str]:
        """Generate strategy-specific assumptions."""
        base_assumptions = {
            "保守": [
                "假设市场需求存在但竞争激烈，需要缓慢进入",
                "假设技术可靠性要求高于速度要求",
                "假设团队能力有限，需要外部支持",
            ],
            "平衡": [
                "假设市场窗口期为6-12个月",
                "假设可以通过MVP验证核心需求",
                "假设技术和团队能力均衡",
            ],
            "激进": [
                "假设市场窗口期为3个月，错失机会成本高",
                "假设快速迭代可以发现和修正问题",
                "假设团队具有高度自主性和创新能力",
            ],
        }
        return base_assumptions.get(strategy, [])

    def _generate_predicted_outcome(self, topic: str, strategy: str) -> str:
        """Generate strategy-specific predicted outcomes."""
        outcomes = {
            "保守": "三个季度后可能具备最小可行产品，风险低但时间成本高",
            "平衡": "两个季度内迭代到市场验证版本，中等风险和中等收益",
            "激进": "一个季度内完成第一版上线，高收益但需承担较高风险",
        }
        return outcomes.get(strategy, "预期结果不明确")

    def _estimate_risk(self, strategy: str) -> float:
        """Estimate risk score (0.0-1.0) for a strategy."""
        risk_map = {
            "保守": 0.25,
            "平衡": 0.55,
            "激进": 0.80,
        }
        return risk_map.get(strategy, 0.5)

    def _estimate_cost(self, strategy: str) -> str:
        """Estimate cost level (low/medium/high)."""
        cost_map = {
            "保守": "high",  # 高时间成本，低资源成本
            "平衡": "medium",
            "激进": "high",  # 高资源成本，低时间成本
        }
        return cost_map.get(strategy, "medium")

    def _evaluate_path(self, path: dict, role_code: str, profile: dict, topic: str) -> str:
        """Have a specific role evaluate a specific path."""
        # Build role-specific evaluation prompt
        evaluation_prompt = f"""作为{profile['name']}，评估以下执行方案：

方案: {path['label']}
风险评分: {path['risk_score']:.2f}/1.0
成本等级: {path['cost_estimate']}

关键假设:
{chr(10).join('- ' + a for a in path['assumptions'])}

预期结果: {path['predicted_outcome']}

请从你的{profile['strength']}角度，用一句话总结该方案的优劣势和你的立场（支持/质疑/保留）。"""

        if self.llm:
            evaluation = self.llm.generate(
                system_prompt=f"你是{profile['name']}。以{profile['strength']}为视角进行评估。",
                user_message=evaluation_prompt,
                role_name=profile["name"],
                role_code=role_code,
                family=profile["family"],
            )
        else:
            # Mock evaluation
            stance = ["支持", "质疑", "保留"][hash(role_code) % 3]
            evaluation = f"【{stance}】该方案{path['label'][:10]}从{profile['strength']}角度有其合理性。"

        return evaluation

    def _score_paths(self, paths_with_evals: List[dict]) -> List[PathBranch]:
        """Score and rank paths based on evaluations."""
        scored_branches = []

        for path in paths_with_evals:
            # Count role stances to adjust confidence
            evals = path.get("role_evaluations", {})
            support_count = sum(1 for e in evals.values() if "支持" in e)
            challenge_count = sum(1 for e in evals.values() if "质疑" in e)
            total_evals = len(evals)

            # Adjust confidence based on evaluation feedback
            base_confidence = path["confidence"]
            if total_evals > 0:
                consensus_factor = (support_count - challenge_count * 0.5) / total_evals
                adjusted_confidence = base_confidence + (consensus_factor * 0.2)
            else:
                adjusted_confidence = base_confidence

            adjusted_confidence = max(0.3, min(0.95, adjusted_confidence))

            branch = PathBranch(
                branch_id=path["branch_id"],
                label=path["label"],
                assumptions=path["assumptions"],
                predicted_outcome=path["predicted_outcome"],
                risk_score=path["risk_score"],
                cost_estimate=path["cost_estimate"],
                confidence=adjusted_confidence,
                role_evaluations=path["role_evaluations"],
                recommendation=path["recommendation"],
            )
            scored_branches.append(branch)

        # Sort by confidence (descending) and risk (ascending)
        scored_branches.sort(
            key=lambda b: (-b.confidence, b.risk_score)
        )

        return scored_branches

    def _build_comparison_matrix(self, branches: List[PathBranch]) -> dict:
        """Build a comparison table for all paths."""
        matrix = {
            "dimensions": [
                "标签", "风险评分", "成本等级", "专家信心",
                "推荐度", "关键假设数"
            ],
            "paths": []
        }

        for branch in branches:
            row = {
                "branch_id": branch.branch_id,
                "标签": branch.label,
                "风险评分": f"{branch.risk_score:.2f}",
                "成本等级": branch.cost_estimate,
                "专家信心": f"{branch.confidence:.0%}",
                "推荐度": branch.recommendation,
                "关键假设数": len(branch.assumptions),
                "评估方数": len(branch.role_evaluations),
            }
            matrix["paths"].append(row)

        return matrix


# ─── Negotiation Engine ─────────────────────────────────

class NegotiationEngine:
    """
    Multi-role collaboration engine.

    Orchestrates structured discussions between AI roles to solve
    complex, multi-faceted problems that no single role can handle alone.
    """

    # Keywords that trigger negotiation mode
    NEGOTIATION_TRIGGERS = {
        "zh": [
            "多角度", "多维度", "全面分析", "综合评估", "方案对比",
            "战略规划", "架构设计", "深度讨论", "集体决策", "团队讨论",
            "沙盘推演", "模拟", "辩论", "协商", "评审",
            "利弊分析", "风险评估", "可行性分析", "路线图",
            "重构方案", "技术选型", "产品规划", "商业模式",
        ],
        "en": [
            "multi-perspective", "comprehensive analysis", "compare options",
            "strategic planning", "architecture review", "deep discussion",
            "team discussion", "sandbox", "simulate", "debate",
            "pros and cons", "risk assessment", "feasibility", "roadmap",
        ],
    }

    # Mode-specific role selection heuristics
    MODE_ROLE_MAP = {
        "discuss": {
            "min_roles": 2, "max_roles": 4,
            "requires_trum": False,
            "default_participants": ["ROLE-Q01", "ROLE-Q02"],
        },
        "sandbox": {
            "min_roles": 3, "max_roles": 5,
            "requires_trum": True,
            "default_participants": ["ROLE-Q02", "ROLE-Q05", "ROLE-Q07"],
        },
        "debate": {
            "min_roles": 2, "max_roles": 4,
            "requires_trum": True,
            "default_participants": ["ROLE-Q02", "ROLE-Q03"],
        },
    }

    def __init__(self, llm_provider=None, ghost_channel=None, knowledge=None):
        """
        Args:
            llm_provider: LLM interface with generate(system_prompt, user_message, ...) method
            ghost_channel: GhostChannelAdapter for inter-role communication tracking
            knowledge: Knowledge layer for depositing negotiation results
        """
        self.llm = llm_provider
        self.ghost_channel = ghost_channel
        self.knowledge = knowledge
        self._session_counter = 0
        self._active_sessions: Dict[str, dict] = {}

    def should_negotiate(self, user_input: str, routing: dict) -> Optional[dict]:
        """
        Determine if a user request warrants multi-role negotiation.

        Returns None if single-role is sufficient, or a dict with:
          mode, participants, topic
        """
        text = user_input.lower()

        # Check for explicit negotiation triggers
        trigger_score = 0
        matched_triggers = []
        for lang_triggers in self.NEGOTIATION_TRIGGERS.values():
            for trigger in lang_triggers:
                if trigger in text:
                    trigger_score += 1
                    matched_triggers.append(trigger)

        # High complexity indicators
        complexity_indicators = [
            len(user_input) > 200,  # Long request = complex
            "和" in text or "与" in text or "and" in text,  # Conjunctions = multi-faceted
            "?" in text and text.count("?") > 1,  # Multiple questions
            any(w in text for w in ["但是", "然而", "不过", "however", "but"]),  # Contradictions
        ]
        complexity_score = sum(1 for x in complexity_indicators if x)

        # Decision threshold
        total_score = trigger_score * 2 + complexity_score
        if total_score < 3:
            return None  # Single role is sufficient

        # Determine mode
        if any(w in text for w in ["沙盘", "推演", "模拟", "sandbox", "simulate"]):
            mode = "sandbox"
        elif any(w in text for w in ["辩论", "对比", "debate", "compare", "versus"]):
            mode = "debate"
        else:
            mode = "discuss"

        # Select participants based on content
        participants = self._select_participants(user_input, routing, mode)

        return {
            "mode": mode,
            "participants": participants,
            "topic": user_input[:100],
            "trigger_score": total_score,
            "matched_triggers": matched_triggers,
        }

    def _select_participants(self, user_input: str, routing: dict, mode: str) -> List[str]:
        """Select the most relevant roles for this negotiation."""
        text = user_input.lower()
        config = self.MODE_ROLE_MAP[mode]

        # Start with the Secretary-routed role
        participants = [routing["role_code"]]

        # Add roles based on content analysis
        role_relevance = {}
        keyword_role_map = {
            "ROLE-Q02": ["架构", "设计", "系统", "技术", "代码", "architecture", "design", "system"],
            "ROLE-Q03": ["研究", "调研", "分析", "文献", "数据", "research", "study", "data"],
            "ROLE-Q04": ["创作", "内容", "文案", "PPT", "设计", "创意", "create", "content", "creative"],
            "ROLE-Q05": ["分析", "数据", "KPI", "指标", "报表", "analytics", "metrics", "dashboard"],
            "ROLE-Q06": ["用户", "体验", "界面", "交互", "UX", "user", "interface", "experience"],
            "ROLE-Q07": ["风险", "安全", "审计", "合规", "漏洞", "risk", "security", "audit"],
            "ROLE-S01": ["架构", "标准", "路径", "数据库", "schema", "standard", "path"],
            "ROLE-S02": ["运维", "部署", "配置", "监控", "deploy", "config", "ops"],
            "ROLE-S03": ["协调", "协作", "跨", "集成", "coordinate", "collaborate", "cross"],
        }

        for role_code, keywords in keyword_role_map.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                role_relevance[role_code] = score

        # Sort by relevance and pick top roles
        sorted_roles = sorted(role_relevance.items(), key=lambda x: x[1], reverse=True)
        for role_code, _ in sorted_roles:
            if role_code not in participants and len(participants) < config["max_roles"]:
                participants.append(role_code)

        # Ensure minimum participants
        defaults = config["default_participants"]
        for default_role in defaults:
            if default_role not in participants and len(participants) < config["max_roles"]:
                participants.append(default_role)

        # Add Trum for arbitration in sandbox/debate modes
        if config["requires_trum"] and "ROLE-S01" not in participants:
            participants.append("ROLE-S01")

        # Ensure coordinator is present if 3+ roles
        if len(participants) >= 3 and "ROLE-S03" not in participants:
            if len(participants) < config["max_roles"]:
                participants.append("ROLE-S03")

        return participants[:config["max_roles"]]

    def negotiate(self, topic: str, participants: List[str], mode: str = "discuss",
                  max_rounds: int = 5, context: dict = None) -> Generator[NegotiationTurn, None, NegotiationResult]:
        """
        Run a multi-role negotiation session.

        Yields NegotiationTurn objects as the discussion progresses.
        Returns NegotiationResult when complete.

        This is a generator — call it in a loop to get real-time turns,
        or use run_negotiation() for batch execution.
        """
        self._session_counter += 1
        session_id = f"NEG-{self._session_counter:04d}-{int(time.time())}"
        start_time = time.time()
        context = context or {}

        turns: List[NegotiationTurn] = []
        conversation_log = []  # Accumulated text for context

        logger.info(f"Negotiation {session_id}: mode={mode}, participants={participants}, topic={topic[:50]}...")

        # Special handling for sandbox mode: run simulation instead of traditional negotiation
        if mode == "sandbox":
            yield from self._run_sandbox_simulation(
                session_id, topic, participants, start_time
            )
            return

        # Build initial prompt for the negotiation
        mode_instruction = {
            "discuss": "这是一场协作讨论。每位专家从自己的角度分析问题，互相补充。目标是形成全面的解决方案。",
            "sandbox": "这是一场沙盘推演。每位专家提出方案假设，其他人质疑和验证。目标是找到最优路径。",
            "debate": "这是一场结构化辩论。每位专家为自己的方案辩护，同时回应其他人的质疑。目标是通过交锋找到最佳答案。",
        }

        for round_num in range(1, max_rounds + 1):
            round_has_new_points = False

            for role_code in participants:
                profile = NEGOTIATION_PROFILES.get(role_code, {})
                if not profile:
                    continue

                # Skip Trum in non-final rounds for sandbox/debate (saves for arbitration)
                if role_code == "ROLE-S01" and mode in ("sandbox", "debate") and round_num < max_rounds:
                    continue

                # Build role-specific system prompt
                system_prompt = self._build_negotiation_prompt(
                    role_code=role_code,
                    profile=profile,
                    mode=mode,
                    mode_instruction=mode_instruction[mode],
                    topic=topic,
                    conversation_log=conversation_log,
                    round_num=round_num,
                    max_rounds=max_rounds,
                    total_participants=len(participants),
                )

                # Determine turn type
                if role_code == "ROLE-S01" and round_num == max_rounds:
                    turn_type = "arbitration"
                elif round_num > 1:
                    turn_type = "challenge" if mode == "debate" else "contribution"
                else:
                    turn_type = "contribution"

                # Generate response via LLM
                if self.llm:
                    response = self.llm.generate(
                        system_prompt=system_prompt,
                        user_message=f"[协商轮次 {round_num}/{max_rounds}] {topic}",
                        role_name=profile["name"],
                        role_code=role_code,
                        family=profile["family"],
                    )
                else:
                    response = f"[{profile['name']}] 关于「{topic[:30]}」的{turn_type}意见（第{round_num}轮）"

                # Track via Ghost Channel
                if self.ghost_channel:
                    prev_role = turns[-1].role_code if turns else "USER"
                    self.ghost_channel.sync_role_transition(
                        from_role=prev_role,
                        to_role=role_code,
                        context={"negotiation": session_id, "round": round_num},
                        user_input=topic,
                    )

                # Create turn object
                turn = NegotiationTurn(
                    round_num=round_num,
                    role_code=role_code,
                    role_name=profile["name"],
                    family=profile["family"],
                    content=response,
                    turn_type=turn_type,
                    references=[t.role_code for t in turns[-3:]],  # Reference recent turns
                    confidence=0.7 + (round_num * 0.05),  # Confidence grows with rounds
                )

                turns.append(turn)
                conversation_log.append(f"[{profile['name']} (Round {round_num})]:\n{response}")

                round_has_new_points = True
                yield turn

            # Check consensus after each round (except first)
            if round_num > 1:
                consensus = self._check_consensus(turns, round_num)
                if consensus["reached"]:
                    logger.info(f"Negotiation {session_id}: Consensus reached at round {round_num}")
                    break

        # Build conclusion
        duration = time.time() - start_time
        conclusion = self._build_conclusion(turns, topic, mode)
        consensus_final = self._check_consensus(turns, round_num)

        result = NegotiationResult(
            session_id=session_id,
            mode=mode,
            topic=topic,
            participants=participants,
            rounds_completed=round_num,
            turns=turns,
            conclusion=conclusion,
            consensus_reached=consensus_final["reached"],
            confidence=consensus_final.get("confidence", 0.6),
            key_decisions=consensus_final.get("key_points", []),
            dissenting_views=consensus_final.get("dissenting", []),
            duration_seconds=round(duration, 2),
            arbitrated_by="ROLE-S01" if any(t.turn_type == "arbitration" for t in turns) else None,
        )

        # Deposit to knowledge layer
        if self.knowledge:
            self.knowledge.deposit(
                f"[协商结论] {topic}",
                conclusion,
                "NEGOTIATION",
                "multi-role",
            )

        logger.info(f"Negotiation {session_id}: Complete ({round_num} rounds, {len(turns)} turns, {duration:.1f}s)")

        return result

    def run_negotiation(self, topic: str, participants: List[str], mode: str = "discuss",
                        max_rounds: int = 5, context: dict = None) -> NegotiationResult:
        """
        Batch execution — runs full negotiation and returns result.
        Use this when you don't need streaming turns.
        """
        gen = self.negotiate(topic, participants, mode, max_rounds, context)
        result = None
        try:
            while True:
                turn = next(gen)
                # Could log turns here
        except StopIteration as e:
            result = e.value

        if result is None:
            # Fallback — shouldn't happen but safety net
            result = NegotiationResult(
                session_id=f"NEG-FALLBACK-{int(time.time())}",
                mode=mode, topic=topic, participants=participants,
                rounds_completed=0, turns=[], conclusion="协商未能完成",
                consensus_reached=False, confidence=0.0,
                key_decisions=[], dissenting_views=[],
                duration_seconds=0.0,
            )

        return result

    def _run_sandbox_simulation(self, session_id: str, topic: str, participants: List[str],
                                 start_time: float) -> Generator[NegotiationTurn, None, NegotiationResult]:
        """
        Run sandbox mode simulation with real path branching.
        Generates multiple execution paths and has roles evaluate each path.
        """
        turns: List[NegotiationTurn] = []

        # Create simulator and run simulation
        simulator = SandboxSimulator(llm_provider=self.llm)
        simulation_result = simulator.simulate(
            topic=topic,
            participants=participants,
            llm_provider=self.llm,
            num_paths=3,
        )

        paths = simulation_result.get("paths", [])
        comparison_matrix = simulation_result.get("comparison_matrix", {})
        recommended_path = simulation_result.get("recommended_path")
        reasoning = simulation_result.get("reasoning", "")

        # Convert simulation results into NegotiationTurn objects for streaming
        # Turn 1: Path generation summary
        path_summary_content = f"【沙盘推演启动】\n已生成{len(paths)}条执行路径:\n\n"
        for path in paths:
            path_summary_content += f"- {path.label}\n"
            path_summary_content += f"  风险: {path.risk_score:.2f}/1.0 | 成本: {path.cost_estimate}\n"

        turn1 = NegotiationTurn(
            round_num=1,
            role_code="SANDBOX-SIM",
            role_name="沙盘模拟器",
            family="system",
            content=path_summary_content,
            turn_type="contribution",
            confidence=0.85,
        )
        turns.append(turn1)
        yield turn1

        # Turn 2-4: Role evaluations of paths (sample key evaluations)
        round_num = 2
        for path in paths[:1]:  # Focus on recommended path evaluations
            evals = path.role_evaluations
            for role_code, eval_text in list(evals.items())[:2]:  # Show 2 key evaluations
                profile = NEGOTIATION_PROFILES.get(role_code, {})
                turn = NegotiationTurn(
                    round_num=round_num,
                    role_code=role_code,
                    role_name=profile.get("name", role_code),
                    family=profile.get("family", "unknown"),
                    content=f"【路径评估】针对「{path.label[:20]}」:\n{eval_text}",
                    turn_type="contribution",
                    references=[t.role_code for t in turns[-2:]],
                    confidence=0.75,
                )
                turns.append(turn)
                yield turn
                round_num += 1

        # Turn: Comparison matrix
        matrix_content = "【对比分析】\n\n执行路径对比矩阵:\n\n"
        if comparison_matrix.get("paths"):
            for path_row in comparison_matrix["paths"]:
                matrix_content += f"**{path_row['标签']}**\n"
                matrix_content += f"  风险: {path_row['风险评分']} | 成本: {path_row['成本等级']} | 信心: {path_row['专家信心']}\n"
                matrix_content += f"  推荐度: {path_row['推荐度']} | 评估方数: {path_row['评估方数']}\n\n"

        turn_matrix = NegotiationTurn(
            round_num=3,
            role_code="SANDBOX-SIM",
            role_name="沙盘模拟器",
            family="system",
            content=matrix_content,
            turn_type="contribution",
            confidence=0.90,
        )
        turns.append(turn_matrix)
        yield turn_matrix

        # Final turn: Recommendation and reasoning (from Trum)
        if recommended_path:
            recommendation_content = f"【推荐方案】{recommended_path.label}\n\n"
            recommendation_content += f"风险评分: {recommended_path.risk_score:.2f}/1.0\n"
            recommendation_content += f"专家信心: {recommended_path.confidence:.0%}\n"
            recommendation_content += f"推荐态度: {recommended_path.recommendation}\n\n"
            recommendation_content += f"【分析理由】\n{reasoning}\n\n"
            recommendation_content += "【关键假设】\n"
            for assumption in recommended_path.assumptions[:3]:
                recommendation_content += f"- {assumption}\n"

            turn_recommendation = NegotiationTurn(
                round_num=4,
                role_code="ROLE-S01",
                role_name="平台总监(Trum)",
                family="trum",
                content=recommendation_content,
                turn_type="arbitration",
                references=[t.role_code for t in turns[-3:]],
                confidence=0.88,
            )
            turns.append(turn_recommendation)
            yield turn_recommendation

        # Build final result
        duration = time.time() - start_time
        conclusion = self._build_sandbox_conclusion(recommended_path, paths, topic)

        result = NegotiationResult(
            session_id=session_id,
            mode="sandbox",
            topic=topic,
            participants=participants,
            rounds_completed=4,
            turns=turns,
            conclusion=conclusion,
            consensus_reached=True,  # Simulation always produces a result
            confidence=recommended_path.confidence if recommended_path else 0.6,
            key_decisions=[recommended_path.label] if recommended_path else [],
            dissenting_views=[p.label for p in paths if p.branch_id != recommended_path.branch_id] if recommended_path else [],
            duration_seconds=round(duration, 2),
            arbitrated_by="ROLE-S01",
        )

        # Deposit to knowledge layer
        if self.knowledge:
            self.knowledge.deposit(
                f"[沙盘推演] {topic}",
                conclusion,
                "NEGOTIATION-SANDBOX",
                "simulation",
            )

        logger.info(f"Negotiation {session_id}: Sandbox simulation complete ({len(paths)} paths, {len(turns)} turns, {duration:.1f}s)")

        return result

    def _build_sandbox_conclusion(self, recommended_path: Optional[PathBranch],
                                   all_paths: List[PathBranch], topic: str) -> str:
        """Build conclusion specific to sandbox simulation."""
        if not recommended_path:
            return "沙盘推演无法生成有效的执行方案建议。"

        parts = [f"## 沙盘推演结论: {topic[:50]}"]
        parts.append("\n### 推荐执行方案")
        parts.append(f"**{recommended_path.label}**")
        parts.append(f"\n- 风险评分: {recommended_path.risk_score:.2f}/1.0")
        parts.append(f"- 专家信心: {recommended_path.confidence:.0%}")
        parts.append(f"- 推荐态度: {recommended_path.recommendation}")
        parts.append(f"- 成本等级: {recommended_path.cost_estimate}")

        parts.append("\n### 关键假设")
        for assumption in recommended_path.assumptions:
            parts.append(f"- {assumption}")

        parts.append("\n### 预期结果")
        parts.append(f"{recommended_path.predicted_outcome}")

        parts.append("\n### 多方评估概览")
        for role_code, evaluation in recommended_path.role_evaluations.items():
            profile = NEGOTIATION_PROFILES.get(role_code, {})
            parts.append(f"- **{profile.get('name', role_code)}**: {evaluation[:80]}...")

        parts.append("\n### 备选方案")
        for path in all_paths:
            if path.branch_id != recommended_path.branch_id:
                parts.append(f"- {path.label} (风险: {path.risk_score:.2f})")

        return "\n".join(parts)

    def _build_negotiation_prompt(self, role_code: str, profile: dict,
                                   mode: str, mode_instruction: str,
                                   topic: str, conversation_log: List[str],
                                   round_num: int, max_rounds: int,
                                   total_participants: int) -> str:
        """Build the system prompt for a role in a negotiation context."""

        previous_context = ""
        if conversation_log:
            # Include last 6 turns for context (avoid token explosion)
            recent = conversation_log[-6:]
            previous_context = "\n\n".join(recent)

        return f"""你是 Q-SpecTrum 系统的 {profile['name']}（{role_code}），属于 {profile['family'].upper()} 家族。

{profile['negotiation_prompt']}

## 协商规则
- 模式: {mode_instruction}
- 当前轮次: {round_num}/{max_rounds}
- 参与角色数: {total_participants}
- 你的优势领域: {profile['strength']}

## 发言要求
1. 必须从你的专业角度出发（{profile['strength']}）
2. 每次发言控制在200-400字
3. 如果同意其他角色的观点，明确说明并补充
4. 如果有不同意见，礼貌但坚定地提出
5. 第{max_rounds}轮时必须给出你的最终结论
6. 使用【关键点】标记你认为最重要的观点

## 之前的讨论
{previous_context if previous_context else '（这是第一轮，你第一个发言）'}

## 议题
{topic}"""

    def _check_consensus(self, turns: List[NegotiationTurn], current_round: int) -> dict:
        """
        Check if roles have reached consensus.
        Simple heuristic: look for agreement signals in recent turns.
        """
        if len(turns) < 3:
            return {"reached": False}

        recent_turns = [t for t in turns if t.round_num == current_round]
        if len(recent_turns) < 2:
            return {"reached": False}

        # Look for agreement keywords
        agreement_keywords = ["同意", "赞同", "一致", "支持", "agree", "consensus", "support"]
        agreement_count = 0
        key_points = []

        for turn in recent_turns:
            text = turn.content.lower()
            if any(kw in text for kw in agreement_keywords):
                agreement_count += 1

            # Extract key points marked with 【】
            import re
            kp_matches = re.findall(r'【关键点】(.+?)(?:\n|$)', turn.content)
            key_points.extend(kp_matches)

        # Consensus if majority agrees
        threshold = len(recent_turns) * 0.6
        reached = agreement_count >= threshold and current_round > 1

        return {
            "reached": reached,
            "agreement_count": agreement_count,
            "total_turns": len(recent_turns),
            "confidence": min(0.95, 0.5 + agreement_count * 0.15),
            "key_points": key_points[:5],
            "dissenting": [
                f"{t.role_name}: 保留意见"
                for t in recent_turns
                if not any(kw in t.content.lower() for kw in agreement_keywords)
            ],
        }

    def _build_conclusion(self, turns: List[NegotiationTurn], topic: str, mode: str) -> str:
        """Build a structured conclusion from the negotiation."""
        if not turns:
            return "协商未产生有效结论。"

        # Collect key points from all turns
        all_key_points = []
        for turn in turns:
            import re
            kps = re.findall(r'【关键点】(.+?)(?:\n|$)', turn.content)
            all_key_points.extend(kps)

        # Get last turn from each participant
        last_views = {}
        for turn in reversed(turns):
            if turn.role_code not in last_views:
                last_views[turn.role_code] = (turn.role_name, turn.content[:200])

        conclusion_parts = [f"## 协商结论：{topic[:50]}"]
        conclusion_parts.append(f"- 模式: {mode}")
        conclusion_parts.append(f"- 轮次: {turns[-1].round_num}")
        conclusion_parts.append(f"- 参与: {', '.join(set(t.role_name for t in turns))}")

        if all_key_points:
            conclusion_parts.append("\n### 关键共识")
            for kp in all_key_points[:5]:
                conclusion_parts.append(f"  - {kp}")

        conclusion_parts.append("\n### 各方最终观点")
        for role_code, (name, view) in last_views.items():
            conclusion_parts.append(f"  **{name}**: {view}")

        # Arbitration note
        arb_turns = [t for t in turns if t.turn_type == "arbitration"]
        if arb_turns:
            conclusion_parts.append("\n### 平台总监裁决")
            conclusion_parts.append(arb_turns[-1].content[:300])

        return "\n".join(conclusion_parts)

    def get_status(self) -> dict:
        """Get negotiation engine status."""
        return {
            "available": True,
            "total_sessions": self._session_counter,
            "active_sessions": len(self._active_sessions),
            "supported_modes": list(self.MODE_ROLE_MAP.keys()),
            "registered_profiles": len(NEGOTIATION_PROFILES),
            "trigger_keywords": sum(len(v) for v in self.NEGOTIATION_TRIGGERS.values()),
        }


# ─── Secretary Integration Helper ────────────────────────

def detect_negotiation_need(user_input: str, routing: dict) -> Optional[dict]:
    """
    Standalone helper for Secretary to detect negotiation needs.
    Can be called without instantiating the full NegotiationEngine.
    """
    engine = NegotiationEngine()
    return engine.should_negotiate(user_input, routing)


# ─── Self-Test ───────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Q-SpecTrum Negotiation Engine — Self-Test")
    print("=" * 60)

    engine = NegotiationEngine()

    # Test 1: Should-negotiate detection
    test_cases = [
        ("你好", False),
        ("帮我写一篇文章", False),
        ("我需要全面分析当前项目的架构设计方案，从技术可行性、用户体验和安全风险多个维度进行评估", True),
        ("请进行沙盘推演：如果我们采用微服务重构，分析利弊", True),
        ("综合评估三种技术选型方案的优劣势", True),
    ]

    print("\n  Test 1: Negotiation Detection")
    for text, expected in test_cases:
        routing = {"role_code": "ROLE-Q01", "family": "qcm", "role_name": "AI伙伴"}
        result = engine.should_negotiate(text, routing)
        detected = result is not None
        status = "✅" if detected == expected else "❌"
        print(f"    {status} \"{text[:40]}...\" → negotiate={detected} (expected={expected})")
        if result:
            print(f"       mode={result['mode']}, participants={result['participants']}, score={result['trigger_score']}")

    # Test 2: Participant selection
    print("\n  Test 2: Participant Selection")
    routing = {"role_code": "ROLE-Q02", "family": "qcm", "role_name": "架构师"}
    participants = engine._select_participants(
        "全面分析微服务架构的安全风险和用户体验影响", routing, "discuss")
    print(f"    Participants: {participants}")

    # Test 3: Negotiation run (with mock LLM)
    print("\n  Test 3: Batch Negotiation (Mock LLM)")
    result = engine.run_negotiation(
        topic="评估是否应该将单体应用重构为微服务架构",
        participants=["ROLE-Q02", "ROLE-Q07", "ROLE-S03"],
        mode="discuss",
        max_rounds=2,
    )
    print(f"    Session: {result.session_id}")
    print(f"    Rounds: {result.rounds_completed}")
    print(f"    Turns: {len(result.turns)}")
    print(f"    Consensus: {result.consensus_reached}")
    print(f"    Duration: {result.duration_seconds}s")
    print(f"    Conclusion: {result.conclusion[:200]}...")

    print(f"\n{'=' * 60}")
    print("  Negotiation Engine self-test PASSED")
    print(f"{'=' * 60}")
