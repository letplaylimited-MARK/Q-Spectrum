"""
DeerFlow Integration Bridge for Q-SpecTrum  v2.0
===================================================
Connects Q-SpecTrum's Secretary/Engine pipeline to DeerFlow's
super-agent execution layer (ByteDance, LangGraph-based).

Architecture:
  Q-SpecTrum Engine               DeerFlow
  ┌──────────────┐    Bridge     ┌──────────────┐
  │ Secretary    │──▶ can_handle │ Skill Registry│
  │ Router       │    ◀──────── │ + LangGraph   │
  │              │   dispatch   │ + Tools       │
  │ KnowledgeRes │◀── deposit   │ + Sandbox     │
  └──────────────┘              └──────────────┘

Called from qspectrum_engine.py (already wired at lines 1117-1184):
  from deerflow_bridge import DeerFlowBridge
  bridge = DeerFlowBridge()
  bridge.status()                # → dict with installed/running/issues
  bridge.can_handle(text, role)  # → {"should_use": True, "skill": ..., ...}
  bridge.build_prompt(text, ctx) # → structured prompt string

Standalone CLI:
  python deerflow_bridge.py --status
  python deerflow_bridge.py --skills
  python deerflow_bridge.py --match "帮我分析销售数据"
  python deerflow_bridge.py --skills-by-role
  python deerflow_bridge.py --prompt "生成一个PPT关于Q1营收"
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DeerFlowBridge:
    """
    Integration bridge between Q-SpecTrum (15-role AI project management)
    and DeerFlow (super-agent harness, 6 executable skills + routing registry).

    Zero mandatory dependencies beyond Python stdlib.
    Graceful degradation: Q-SpecTrum core never fails due to DeerFlow.
    """

    # ─── DeerFlow skill routing registry ─────────────────────
    # 17 entries for keyword routing; only 6 have real Python executors
    # in deerflow_real_skills.py (deep-research, data-analysis, consulting-analysis,
    # github-deep-research, chart-visualization, find-skills).
    # Non-executable skills fall back to DeerFlowEnhancedSimulator.
    SKILL_REGISTRY: Dict[str, dict] = {
        "deep-research": {
            "description": "深度研究: 多轮搜索、信息交叉验证、结构化报告",
            "category": "research",
            "keywords_zh": ["深度研究", "调研", "文献综述", "行业分析", "竞品分析",
                            "市场调研", "背景调查", "技术调研", "可行性研究", "研究"],
            "keywords_en": ["deep research", "literature review", "industry analysis",
                            "competitive analysis", "market research", "feasibility study",
                            "research report", "investigate", "research"],
            "roles": ["ROLE-Q02", "ROLE-Q04"],
            "output": "text", "sandbox": False,
        },
        "data-analysis": {
            "description": "数据分析: Python 数据处理、统计分析、图表生成",
            "category": "analysis",
            "keywords_zh": ["数据分析", "統計", "指标", "KPI", "趋势分析", "销售分析",
                            "数据处理", "Excel分析", "CSV", "分析数据", "数据清洗",
                            "分析销售", "分析报表", "分析結果"],
            "keywords_en": ["data analysis", "statistics", "metrics", "KPI", "trend",
                            "sales analysis", "data processing", "analyze data",
                            "data cleaning", "analytics"],
            "roles": ["ROLE-Q04"],
            "output": "file", "sandbox": True,
        },
        "chart-visualization": {
            "description": "图表可视化: 交互式图表、Dashboard、数据展示",
            "category": "analysis",
            "keywords_zh": ["图表", "可视化", "Dashboard", "仪表盘", "柱状图", "折线图",
                            "饼图", "散点图", "热力图", "生成图表"],
            "keywords_en": ["chart", "visualization", "dashboard", "bar chart", "line chart",
                            "pie chart", "scatter", "heatmap", "graph", "plot"],
            "roles": ["ROLE-Q04", "ROLE-Q05"],
            "output": "file", "sandbox": True,
        },
        "ppt-generation": {
            "description": "PPT生成: 专业演示文稿自动创建",
            "category": "creation",
            "keywords_zh": ["PPT", "演示文稿", "幻灯片", "简报", "汇报", "路演",
                            "投资报告", "做PPT", "生成PPT", "做简报"],
            "keywords_en": ["PPT", "presentation", "slides", "slide deck", "pitch deck",
                            "keynote", "powerpoint"],
            "roles": ["ROLE-Q03"],
            "output": "presentation", "sandbox": True,
        },
        "image-generation": {
            "description": "图片生成: AI 绘图、Logo设计、插图创作",
            "category": "creation",
            "keywords_zh": ["生成图片", "画图", "画", "设计图", "Logo", "插图", "封面",
                            "海报", "配图", "图像生成", "AI绘画", "图片", "架构图", "张图", "一张图"],
            "keywords_en": ["generate image", "draw", "logo", "illustration",
                            "cover", "poster", "image generation", "AI art"],
            "roles": ["ROLE-Q03", "ROLE-Q05"],
            "output": "image", "sandbox": False,
        },
        "video-generation": {
            "description": "视频生成: AI 视频创作和编辑",
            "category": "creation",
            "keywords_zh": ["视频", "动画", "短视频", "视频生成", "剪辑", "影片"],
            "keywords_en": ["video", "animation", "short video", "video generation",
                            "edit video", "movie"],
            "roles": ["ROLE-Q03"],
            "output": "video", "sandbox": True,
        },
        "podcast-generation": {
            "description": "播客生成: 自动音频内容创作",
            "category": "creation",
            "keywords_zh": ["播客", "音频", "语音", "配音", "Podcast", "录音"],
            "keywords_en": ["podcast", "audio", "voice", "narration", "recording"],
            "roles": ["ROLE-Q03"],
            "output": "audio", "sandbox": True,
        },
        "consulting-analysis": {
            "description": "咨询分析: 商业分析、战略咨询、决策支持",
            "category": "analysis",
            "keywords_zh": ["咨询", "商业分析", "战略分析", "SWOT", "决策",
                            "商业模式", "业务分析", "投资分析", "评估"],
            "keywords_en": ["consulting", "business analysis", "strategic analysis",
                            "SWOT", "decision", "business model", "investment analysis"],
            "roles": ["ROLE-Q04", "ROLE-T03"],
            "output": "text", "sandbox": False,
        },
        "github-deep-research": {
            "description": "GitHub深度研究: 开源项目分析、代码审查、技术评估",
            "category": "research",
            "keywords_zh": ["GitHub", "开源", "代码审查", "项目分析", "技术评估",
                            "仓库", "代码库", "Star", "Issue", "PR分析"],
            "keywords_en": ["GitHub", "open source", "code review", "project analysis",
                            "tech evaluation", "repository", "pull request"],
            "roles": ["ROLE-Q02", "ROLE-Q01"],
            "output": "text", "sandbox": False,
        },
        "frontend-design": {
            "description": "前端设计: UI组件设计、页面布局、React/Vue组件",
            "category": "creation",
            "keywords_zh": ["前端", "UI", "页面", "组件", "布局", "React", "Vue",
                            "CSS", "响应式", "界面设计", "网页设计"],
            "keywords_en": ["frontend", "UI", "page", "component", "layout", "React",
                            "Vue", "CSS", "responsive", "interface design", "web design"],
            "roles": ["ROLE-Q05", "ROLE-Q01"],
            "output": "file", "sandbox": True,
        },
        "web-design-guidelines": {
            "description": "Web设计规范: 设计系统、样式指南、品牌规范",
            "category": "creation",
            "keywords_zh": ["设计规范", "设计系统", "样式指南", "品牌", "设计标准",
                            "组件库", "Design Token"],
            "keywords_en": ["design guidelines", "design system", "style guide",
                            "brand", "component library", "design standard"],
            "roles": ["ROLE-Q05", "Spec-R001"],
            "output": "text", "sandbox": False,
        },
        "bootstrap": {
            "description": "项目初始化: 快速搭建项目脚手架和基础结构",
            "category": "ops",
            "keywords_zh": ["初始化", "搭建", "脚手架", "新项目", "创建项目",
                            "项目模板", "启动项目"],
            "keywords_en": ["bootstrap", "scaffold", "init", "new project",
                            "create project", "project template", "start project"],
            "roles": ["ROLE-Q01", "ROLE-T03"],
            "output": "file", "sandbox": True,
        },
        "skill-creator": {
            "description": "技能创建: 创建、测试、优化 DeerFlow 技能",
            "category": "meta",
            "keywords_zh": ["创建技能", "新技能", "技能开发", "Skill开发", "技能模板"],
            "keywords_en": ["create skill", "new skill", "skill development",
                            "skill template", "build skill"],
            "roles": ["ROLE-Q01"],
            "output": "file", "sandbox": True,
        },
        "find-skills": {
            "description": "技能搜索: 发现和推荐适合任务的技能",
            "category": "meta",
            "keywords_zh": ["找技能", "技能推荐", "有什么技能", "技能列表", "能力清单"],
            "keywords_en": ["find skills", "skill recommendation", "what skills",
                            "skill list", "capabilities"],
            "roles": ["ROLE-Q07"],
            "output": "text", "sandbox": False,
        },
        "claude-to-deerflow": {
            "description": "Claude对接: 将 Claude 分析结果转化为 DeerFlow 可执行工作流",
            "category": "meta",
            "keywords_zh": ["Claude对接", "对接DeerFlow", "转化工作流", "自动化"],
            "keywords_en": ["claude to deerflow", "connect deerflow", "automate workflow"],
            "roles": ["ROLE-Q01"],
            "output": "text", "sandbox": False,
        },
        "surprise-me": {
            "description": "随机创意: 基于上下文生成创意建议或惊喜内容",
            "category": "creation",
            "keywords_zh": ["给我惊喜", "随机", "灵感", "创意", "有趣"],
            "keywords_en": ["surprise me", "random", "inspiration", "creative"],
            "roles": ["ROLE-Q03", "ROLE-Q07"],
            "output": "text", "sandbox": False,
        },
        "vercel-deploy-claimable": {
            "description": "Vercel部署: 一键部署前端项目到 Vercel",
            "category": "ops",
            "keywords_zh": ["部署", "上线", "发布", "Vercel", "托管"],
            "keywords_en": ["deploy", "publish", "release", "Vercel", "hosting"],
            "roles": ["ROLE-Q01"],
            "output": "text", "sandbox": True,
        },
    }

    # Category → fallback keywords (for broad matching)
    _CATEGORY_KEYWORDS = {
        "research": ["研究", "调研", "research", "investigate", "分析报告"],
        "analysis": ["分析", "数据", "analysis", "data", "chart", "图表", "统计"],
        "creation": ["创建", "生成", "create", "generate", "写", "画", "设计", "PPT"],
        "ops": ["部署", "初始化", "deploy", "init", "bootstrap"],
        "meta": ["技能", "skill"],
    }

    # Confidence threshold for recommending DeerFlow
    MIN_CONFIDENCE = 0.35

    # DeerFlow API default endpoint
    DEFAULT_API_URL = "http://localhost:8001"

    def __init__(self, root_dir: Optional[str] = None):
        self.root = Path(root_dir) if root_dir else Path(__file__).parent
        self._api_url = os.environ.get("DEERFLOW_API_URL", self.DEFAULT_API_URL)

        # Find DeerFlow directory (try multiple locations)
        self.deerflow_dir: Optional[Path] = None
        candidates = [
            self.root / "DeerFlow",
            self.root.parent / "Q-SpecTrum" / "DeerFlow",
            self.root / "AI项目管理" / "Systems" / "ai-skill-system" / "repos" / "deer-flow",
        ]
        for c in candidates:
            if c.exists() and (c / "config.yaml").exists():
                self.deerflow_dir = c
                break
            nested = c / "DeerFlow"
            if nested.exists() and (nested / "backend").exists():
                self.deerflow_dir = c
                break

    # ─── 1. STATUS ────────────────────────────────────────

    def status(self) -> Dict:
        """Check DeerFlow installation, configuration, and runtime state."""
        result = {
            "installed": self.deerflow_dir is not None,
            "root_path": str(self.deerflow_dir) if self.deerflow_dir else None,
            "config_exists": False,
            "env_exists": False,
            "api_key_set": False,
            "model_configured": None,
            "running": False,
            "skills_count": 6,  # Real executors in deerflow_real_skills.py
            "routing_registry": len(self.SKILL_REGISTRY),  # Full keyword routing table
            "available_on_disk": 0,
            "issues": [],
        }

        if not self.deerflow_dir:
            result["issues"].append("DeerFlow directory not found")
            return result

        # Config check
        config_path = self.deerflow_dir / "config.yaml"
        result["config_exists"] = config_path.exists()

        # .env and API key check
        env_path = self.deerflow_dir / ".env"
        result["env_exists"] = env_path.exists()
        if env_path.exists():
            try:
                env_text = env_path.read_text(encoding="utf-8", errors="ignore")
                for line in env_text.split("\n"):
                    line = line.strip()
                    for prefix in ["VOLCENGINE_API_KEY=", "OPENAI_API_KEY=", "ANTHROPIC_API_KEY="]:
                        if line.startswith(prefix):
                            val = line.split("=", 1)[1]
                            if val and "your-" not in val and len(val) > 5:
                                result["api_key_set"] = True
                                break
            except Exception:
                pass

        # Model config check
        if config_path.exists():
            try:
                text = config_path.read_text(encoding="utf-8", errors="ignore")
                for line in text.split("\n"):
                    s = line.strip()
                    if s.startswith("- name:") and not s.startswith("#"):
                        result["model_configured"] = s.split(":", 1)[1].strip()
                        break
            except Exception:
                pass

        # Skills on disk
        skills_dir = self.deerflow_dir / "DeerFlow" / "skills" / "public"
        if skills_dir.exists():
            result["available_on_disk"] = len([d for d in skills_dir.iterdir() if d.is_dir()])

        # Runtime check
        result["running"] = self._check_api_health()

        # Issue detection
        if not result["api_key_set"]:
            result["issues"].append("No valid LLM API key in .env")
        if not result["model_configured"]:
            result["issues"].append("No model configured in config.yaml")
        if not result["running"]:
            result["issues"].append("DeerFlow API not running (start with: cd DeerFlow && make dev)")

        return result

    def get_status(self) -> Dict:
        """
        Alias for status() - returns DeerFlow availability and skill count.
        Used by GhostChannelGate to determine activation level.
        """
        st = self.status()
        return {
            "active": st.get("installed", False) and st.get("running", False),
            "capabilities_count": st.get("available_on_disk", len(self.SKILL_REGISTRY)),
            "installed": st.get("installed", False),
            "skills_count": st.get("skills_count", 0),
            "available_on_disk": st.get("available_on_disk", 0),
            "issues": st.get("issues", []),
        }

    def _check_api_health(self) -> bool:
        """Check if DeerFlow FastAPI server is running."""
        try:
            import urllib.request
            req = urllib.request.Request(f"{self._api_url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    # ─── 2. CAN_HANDLE ─────────────────────────────────────

    def can_handle(self, query: str, role_code: str = None) -> Dict:
        """
        Determine if DeerFlow should handle this task.

        Uses multi-signal scoring:
        1. Exact keyword match (ZH + EN)
        2. CJK substring matching (for compound words)
        3. Role affinity bonus
        4. Category context bonus

        Returns:
            {
                "should_use": bool,
                "skill": str | None,
                "confidence": float,
                "reason": str,
                "all_matches": [(skill, score), ...],
            }
        """
        text = query.lower()
        matches: List[Tuple[str, float]] = []

        for skill_id, info in self.SKILL_REGISTRY.items():
            score = 0.0

            # Signal 1: Keyword match (ZH + EN)
            zh_hits = sum(1 for kw in info["keywords_zh"] if kw.lower() in text)
            en_hits = sum(1 for kw in info["keywords_en"] if kw.lower() in text)
            total_hits = zh_hits + en_hits
            if total_hits > 0:
                score += min(1.0, total_hits * 0.25)

            # Signal 2: CJK substring matching (character-level)
            # e.g. "分析销售" should match "data-analysis" via "分析"
            if score < 0.3:
                for kw in info["keywords_zh"]:
                    if len(kw) >= 2 and kw.lower() in text:
                        score += 0.2
                        break

            # Signal 3: Role affinity bonus
            if role_code and role_code in info.get("roles", []):
                score += 0.15

            # Signal 4: Category context
            cat_kws = self._CATEGORY_KEYWORDS.get(info["category"], [])
            cat_hits = sum(1 for kw in cat_kws if kw in text)
            if cat_hits > 0:
                score += min(0.15, cat_hits * 0.05)

            # Normalize
            score = min(1.0, score)

            if score > 0.05:
                matches.append((skill_id, round(score, 3)))

        matches.sort(key=lambda x: x[1], reverse=True)

        if matches and matches[0][1] >= self.MIN_CONFIDENCE:
            best_skill, best_score = matches[0]
            return {
                "should_use": True,
                "skill": best_skill,
                "confidence": best_score,
                "reason": f"Matched '{best_skill}' (conf={best_score:.2f})",
                "all_matches": matches[:5],
            }
        return {
            "should_use": False,
            "skill": matches[0][0] if matches else None,
            "confidence": matches[0][1] if matches else 0.0,
            "reason": "Below confidence threshold" if matches else "No keyword match",
            "all_matches": matches[:3],
        }

    # ─── 3. BUILD_PROMPT ───────────────────────────────────

    def build_prompt(self, query: str, role_context: Optional[Dict] = None) -> str:
        """
        Build a DeerFlow-optimized execution prompt.

        Includes Q-SpecTrum context so DeerFlow understands the request origin.
        """
        role_context = role_context or {}
        match = self.can_handle(query, role_context.get("role_code"))
        skill_id = match.get("skill", "deep-research")
        skill_info = self.SKILL_REGISTRY.get(skill_id, {})

        parts = [
            "# DeerFlow 执行请求",
            "",
            "## 用户请求",
            query,
            "",
            "## Q-SpecTrum 上下文",
        ]
        if role_context.get("role_name"):
            parts.append(f"- 角色: {role_context['role_name']} ({role_context.get('role_code', '')})")
        if role_context.get("family"):
            parts.append(f"- 家族: {role_context['family']}")
        if role_context.get("capabilities"):
            parts.append(f"- 能力: {role_context['capabilities']}")
        parts.extend([
            "- 项目: 15 AI 角色 / 40 表 / 85 行 SQLite / 3 家族",
            "",
            f"## 推荐技能: {skill_id}",
            f"- 描述: {skill_info.get('description', '')}",
            f"- 输出: {skill_info.get('output', 'text')}",
        ])
        if skill_info.get("sandbox"):
            parts.append("- 需要沙盒: 是")

        parts.extend([
            "",
            "## 要求",
            "- 执行结果将反馈到 Q-SpecTrum 知识共振引擎进行沉淀",
            "- 输出需结构化，便于角色后续处理",
        ])

        return "\n".join(parts)

    # ─── 4. DISPATCH ───────────────────────────────────────

    # Task queue for offline execution
    _task_queue: List[Dict] = []

    # Configurable confidence threshold (default 0.35 for routing, 0.7 for auto-exec)
    ROUTING_THRESHOLD = 0.35
    EXECUTION_THRESHOLD = 0.7

    def execute(self, skill_name: str, params: Dict = None) -> Dict:
        """
        Execute a skill with given parameters.
        Simple method that routes to dispatch() internally.

        Args:
            skill_name: Name of the DeerFlow skill to execute (e.g., 'deep-research')
            params: Parameters dict with 'query' and optional 'context' keys

        Returns:
            Execution result dict with status, response, and artifacts
        """
        if params is None:
            params = {}
        query = params.get("query", skill_name)
        context = params.get("context", {})
        return self.dispatch(query, skill_id=skill_name, context=context)

    def dispatch(self, query: str, skill_id: str = None,
                 context: Dict = None) -> Dict:
        """
        Dispatch a task to DeerFlow for execution.

        Three execution modes:
        1. LIVE: DeerFlow API running → execute via LangGraph stream API
        2. QUEUED: DeerFlow offline → queue task for later execution
        3. MANUAL: No DeerFlow installed → return manual instructions
        """
        if not skill_id:
            match = self.can_handle(query)
            skill_id = match.get("skill", "deep-research")

        prompt = self.build_prompt(query, context)
        task_descriptor = {
            "id": f"df-{int(time.time())}-{hash(query) % 10000:04d}",
            "query": query,
            "skill": skill_id,
            "prompt": prompt,
            "context": context or {},
            "status": "pending",
            "created_at": time.time(),
        }

        # Mode 1: LIVE execution via LangGraph API
        if self._check_api_health():
            result = self._execute_langgraph(task_descriptor)
            if result["success"]:
                return {
                    "dispatched": True,
                    "method": "langgraph_stream",
                    "task_id": task_descriptor["id"],
                    "skill": skill_id,
                    "response": result.get("output", ""),
                    "execution_time_ms": result.get("elapsed_ms", 0),
                    "artifacts": result.get("artifacts", []),
                }

        # Mode 2: QUEUED for later
        if self.deerflow_dir:
            task_descriptor["status"] = "queued"
            self._task_queue.append(task_descriptor)
            return {
                "dispatched": False,
                "method": "queued",
                "task_id": task_descriptor["id"],
                "skill": skill_id,
                "queue_position": len(self._task_queue),
                "response": None,
                "instructions": (
                    f"任務已加入執行佇列 (#{len(self._task_queue)})。\n"
                    f"啟動 DeerFlow 後將自動執行: cd DeerFlow && make dev"
                ),
            }

        # Mode 3: ENHANCED MANUAL — produce real simulated output
        # instead of just installation instructions
        try:
            from scenario_engine import DeerFlowEnhancedSimulator
            sim = DeerFlowEnhancedSimulator()
            lang = "zh" if any('\u4e00' <= c <= '\u9fff' for c in query[:30]) else "en"
            sim_result = sim.simulate(query, skill_id, context, lang=lang)
            sim_result["install_hint"] = (
                "Connect DeerFlow for live execution: "
                "git clone https://github.com/nicepkg/DeerFlow && cd DeerFlow && make install && make dev"
            )
            return sim_result
        except ImportError:
            pass

        # Fallback: original manual instructions
        return {
            "dispatched": False,
            "method": "manual",
            "task_id": task_descriptor["id"],
            "skill": skill_id,
            "response": None,
            "instructions": (
                f"DeerFlow 未安裝。請先安裝:\n"
                f"  1. git clone https://github.com/nicepkg/DeerFlow\n"
                f"  2. cd DeerFlow && make install\n"
                f"  3. make dev\n"
                f"  推薦技能: {skill_id}"
            ),
        }

    def _execute_langgraph(self, task: Dict) -> Dict:
        """Execute task via LangGraph stream API (correct endpoint)."""
        import urllib.request
        start = time.time()
        try:
            # LangGraph dev server uses /runs/stream for streaming
            # and /runs/wait for synchronous execution
            payload = {
                "assistant_id": "agent",
                "input": {
                    "messages": [
                        {"role": "user", "content": task["prompt"]}
                    ]
                },
                "config": {
                    "configurable": {
                        "skill": task["skill"],
                        "thread_id": task["id"],
                    }
                },
                "stream_mode": "values",
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self._api_url}/runs/wait",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read())
                elapsed = (time.time() - start) * 1000

                # Extract output from LangGraph response
                messages = result.get("messages", [])
                output = ""
                artifacts = []
                for msg in messages:
                    if msg.get("role") == "assistant" or msg.get("type") == "ai":
                        content = msg.get("content", "")
                        if isinstance(content, str):
                            output += content + "\n"
                        elif isinstance(content, list):
                            for part in content:
                                if isinstance(part, dict):
                                    if part.get("type") == "text":
                                        output += part.get("text", "") + "\n"
                                    elif part.get("type") in ("image", "file"):
                                        artifacts.append(part)

                return {
                    "success": True,
                    "output": output.strip(),
                    "artifacts": artifacts,
                    "elapsed_ms": round(elapsed, 1),
                    "raw": result,
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_ms": round((time.time() - start) * 1000, 1),
            }

    def process_queue(self) -> List[Dict]:
        """Process all queued tasks (call when DeerFlow comes online)."""
        if not self._check_api_health():
            return []

        results = []
        while self._task_queue:
            task = self._task_queue.pop(0)
            task["status"] = "executing"
            result = self._execute_langgraph(task)
            task["status"] = "completed" if result["success"] else "failed"
            task["result"] = result
            results.append(task)
        return results

    def get_queue_status(self) -> Dict:
        """Get current task queue status."""
        return {
            "queued": len(self._task_queue),
            "tasks": [
                {"id": t["id"], "skill": t["skill"], "status": t["status"],
                 "query": t["query"][:60]}
                for t in self._task_queue
            ],
        }

    def simulate_skill_execution(self, query: str, skill_id: str,
                                  context: Dict = None) -> Dict:
        """
        Smart offline simulation when DeerFlow is not running.
        Tries enhanced simulator first (from scenario_engine), falls back to basic.
        Generates structured mock responses based on skill type,
        allowing the system to demonstrate full pipeline flow.
        """
        # Try enhanced simulator first (richer output)
        try:
            from scenario_engine import DeerFlowEnhancedSimulator
            lang = "zh" if any('\u4e00' <= c <= '\u9fff' for c in query[:30]) else "en"
            return DeerFlowEnhancedSimulator().simulate(query, skill_id, context, lang=lang)
        except ImportError:
            pass

        skill_info = self.SKILL_REGISTRY.get(skill_id, {})
        category = skill_info.get("category", "research")
        desc = skill_info.get("description", skill_id)
        start = time.time()

        # Category-specific mock responses (fallback)
        mock_outputs = {
            "research": (
                f"## Research Report: {query[:80]}\n\n"
                f"### Executive Summary\n"
                f"Based on multi-source analysis using DeerFlow '{skill_id}' skill, "
                f"key findings include:\n\n"
                f"1. **Primary Insight**: The query domain shows significant activity with "
                f"emerging patterns that warrant deeper investigation.\n"
                f"2. **Market Context**: Current trends align with industry projections, "
                f"with 3 notable exceptions requiring attention.\n"
                f"3. **Recommended Actions**: Prioritize data validation, stakeholder "
                f"alignment, and iterative review cycles.\n\n"
                f"### Methodology\n"
                f"- Sources analyzed: 12 primary, 8 secondary\n"
                f"- Confidence: 0.82 (high)\n"
                f"- Skill: {desc}\n\n"
                f"*[Simulated output — connect DeerFlow for live execution]*"
            ),
            "analysis": (
                f"## Analysis Results: {query[:80]}\n\n"
                f"### Data Summary\n"
                f"| Metric | Value | Trend |\n"
                f"|--------|-------|-------|\n"
                f"| Primary KPI | 87.3% | +5.2% |\n"
                f"| Secondary KPI | 42.1 | Stable |\n"
                f"| Risk Score | 0.23 | -12% |\n\n"
                f"### Key Findings\n"
                f"The analysis reveals 3 actionable insights with high confidence. "
                f"Recommend proceeding with Phase 1 optimizations.\n\n"
                f"*[Simulated — skill: {skill_id}]*"
            ),
            "creation": (
                f"## Generated Content: {query[:80]}\n\n"
                f"Content generation via '{skill_id}' skill completed.\n\n"
                f"### Output Specifications\n"
                f"- Format: {skill_info.get('output', 'text')}\n"
                f"- Quality: Production-ready draft\n"
                f"- Iterations: 1 (initial generation)\n\n"
                f"### Preview\n"
                f"[Content preview would appear here with live DeerFlow execution]\n\n"
                f"*[Simulated — connect DeerFlow for actual output]*"
            ),
        }

        output = mock_outputs.get(category, mock_outputs["research"])
        elapsed = (time.time() - start) * 1000

        return {
            "dispatched": True,
            "method": "simulation",
            "task_id": f"sim-{int(time.time())}-{hash(query) % 10000:04d}",
            "skill": skill_id,
            "response": output,
            "execution_time_ms": round(elapsed, 1),
            "artifacts": [],
            "simulated": True,
            "confidence": 0.65,
        }

    # ─── 5. SKILL LISTING ──────────────────────────────────

    def list_skills(self, category: str = None) -> List[Dict]:
        """List all DeerFlow skills, optionally filtered by category."""
        results = []
        for skill_id, info in sorted(self.SKILL_REGISTRY.items()):
            if category and info["category"] != category:
                continue
            results.append({
                "id": skill_id,
                "name": info.get("description", skill_id).split(":")[0].strip(),
                "description": info["description"],
                "category": info["category"],
                "output": info["output"],
                "sandbox": info.get("sandbox", False),
                "roles": info.get("roles", []),
            })
        return results

    # ─── 6. UNIFIED SKILL MAP ──────────────────────────────

    def get_unified_skill_map(self) -> Dict:
        """
        Map each Q-SpecTrum role to its complementary DeerFlow skills.
        """
        role_map: Dict[str, list] = {}
        for skill_id, info in self.SKILL_REGISTRY.items():
            for role in info.get("roles", []):
                if role not in role_map:
                    role_map[role] = []
                role_map[role].append({
                    "skill": skill_id,
                    "category": info["category"],
                    "output": info["output"],
                })

        categories = {}
        for info in self.SKILL_REGISTRY.values():
            cat = info["category"]
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "mapping": role_map,
            "total_skills": len(self.SKILL_REGISTRY),
            "categories": categories,
        }


# ═══════════════════════════════════════════════════════════
# CLI Interface
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    bridge = DeerFlowBridge()

    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        s = bridge.status()
        print("=" * 50)
        print("  DeerFlow Integration Status")
        print("=" * 50)
        for k, v in s.items():
            if k == "issues":
                if v:
                    for issue in v:
                        print(f"  ⚠️  {issue}")
            else:
                icon = "✅" if (isinstance(v, bool) and v) else ("❌" if isinstance(v, bool) else "  ")
                print(f"  {icon} {k}: {v}")
        print("=" * 50)

    elif len(sys.argv) > 1 and sys.argv[1] == "--skills":
        cat = None
        if len(sys.argv) > 2:
            cat = sys.argv[2]
        skills = bridge.list_skills(category=cat)
        print(f"\nDeerFlow Skills ({len(skills)}):\n")
        for s in skills:
            sb = " 🔧" if s["sandbox"] else ""
            print(f"  [{s['category']:8s}] {s['id']:30s} → {s['output']:12s}{sb}")
            print(f"            {s['description']}")
            print(f"            Roles: {', '.join(s['roles'])}")
            print()

    elif len(sys.argv) > 1 and sys.argv[1] == "--skills-by-role":
        m = bridge.get_unified_skill_map()
        print("\n  Q-SpecTrum Role → DeerFlow Skills\n")
        for role, skills in sorted(m["mapping"].items()):
            print(f"  {role}:")
            for s in skills:
                print(f"    → {s['skill']} ({s['category']}/{s['output']})")
            print()
        print(f"  Categories: {json.dumps(m['categories'])}")
        print(f"  Total: {m['total_skills']} skills")

    elif len(sys.argv) > 2 and sys.argv[1] == "--match":
        query = " ".join(sys.argv[2:])
        result = bridge.can_handle(query)
        print(f"\n  Query: \"{query}\"")
        print(f"  Should use DeerFlow: {'✅ Yes' if result['should_use'] else '❌ No'}")
        print(f"  Best skill: {result['skill']} (confidence: {result['confidence']:.2f})")
        print(f"  Reason: {result['reason']}")
        if result["all_matches"]:
            print("\n  All matches:")
            for skill, score in result["all_matches"]:
                print(f"    [{score:.2f}] {skill}")

    elif len(sys.argv) > 2 and sys.argv[1] == "--prompt":
        query = " ".join(sys.argv[2:])
        print(bridge.build_prompt(query))

    else:
        print("DeerFlow Integration Bridge v2.0 for Q-SpecTrum")
        print()
        print("Usage:")
        print("  python deerflow_bridge.py --status")
        print("  python deerflow_bridge.py --skills [category]")
        print("  python deerflow_bridge.py --skills-by-role")
        print('  python deerflow_bridge.py --match "帮我分析销售数据"')
        print('  python deerflow_bridge.py --prompt "生成PPT关于Q1营收"')
