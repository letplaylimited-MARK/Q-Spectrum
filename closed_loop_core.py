"""
Q-SpecTrum Closed-Loop Core v1.0
===================================
Implements the critical closed-loop architecture:

  【Resource Layer】→ 【AI Chatroom】→ 【Execution Layer】→ 【Result Layer】
       ↑                                                        ↓
  【Resource Aggregation】← 【Decision Layer】← ← ← ← ← ← ← ←┘

Core Components:
  1. KnowledgePipeline    — Auto task→knowledge→evolution sedimentation
  2. ProjectOrchestrator   — Multi-project management + result aggregation
  3. ComponentRegistry     — Hot-swap port for pluggable components
  4. ResourceLayer         — DB intake + vector search + API interface
  5. UserGrowthEngine      — S1→S5 progressive capability unlocking

Theory: QCM papers define that the system must form a complete closed loop
where every task result feeds back into the knowledge base, driving the
Dual Flywheel (F16-18) and evolving the system's collective intelligence.
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("q-spectrum.closed-loop")

# ═══════════════════════════════════════════════════════════
# 2. KNOWLEDGE SEDIMENTATION PIPELINE
# ═══════════════════════════════════════════════════════════

class KnowledgePipeline:
    """
    Automatic knowledge sedimentation from task results.

    Theory requires: Every task → knowledge deposit → flywheel update → evolution

    Pipeline stages:
      1. CAPTURE: Extract key information from task result
      2. CLASSIFY: Determine knowledge type (episodic/semantic/procedural)
      3. DEPOSIT: Store in knowledge base with proper tagging
      4. CROSS-LINK: Connect to related knowledge entries
      5. EVOLVE: Feed to Flywheel for system optimization
    """

    def __init__(self, db_path: str = None):
        self._db_path = db_path or str(
            Path(__file__).parent / "knowledge_pipeline.db"
        )
        self._init_db()
        self._total_deposits = 0
        self._evolution_score = 0.0

    def _init_db(self):
        """Initialize knowledge pipeline database."""
        try:
            conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
        except Exception:
            import tempfile
            tmpdir = Path(tempfile.gettempdir()) / "qspectrum_data"
            tmpdir.mkdir(parents=True, exist_ok=True)
            self._db_path = str(tmpdir / "knowledge_pipeline.db")
            conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)

        # Use individual execute() calls to avoid disk I/O errors on FUSE
        _ddl = [
            """CREATE TABLE IF NOT EXISTS knowledge_deposits (
                deposit_id TEXT PRIMARY KEY,
                timestamp REAL,
                source_type TEXT,
                source_role TEXT,
                source_family TEXT,
                project_id TEXT DEFAULT 'default',
                knowledge_type TEXT,
                content TEXT,
                tags TEXT,
                relevance_score REAL,
                gc_token TEXT,
                gc_delta_hash TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS knowledge_links (
                link_id TEXT PRIMARY KEY,
                from_deposit TEXT,
                to_deposit TEXT,
                link_type TEXT,
                strength REAL
            )""",
            """CREATE TABLE IF NOT EXISTS evolution_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                total_deposits INTEGER,
                evolution_score REAL,
                flywheel_iterations INTEGER,
                knowledge_growth_rate REAL
            )""",
            "CREATE INDEX IF NOT EXISTS idx_deposits_project ON knowledge_deposits(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_deposits_type ON knowledge_deposits(knowledge_type)",
            "CREATE INDEX IF NOT EXISTS idx_deposits_role ON knowledge_deposits(source_role)",
        ]
        for stmt in _ddl:
            try:
                conn.execute(stmt)
            except Exception:
                pass
        conn.commit()

        # Count existing deposits
        self._total_deposits = conn.execute(
            "SELECT COUNT(*) FROM knowledge_deposits"
        ).fetchone()[0]
        conn.close()

    def deposit(self, task_result: dict, gc_token: str = None,
                project_id: str = "default") -> dict:
        """
        Stage 1-3: Capture, classify, and deposit knowledge from task result.
        """
        routing = task_result.get("routing", {})
        response = task_result.get("response", "")
        gc_info = task_result.get("ghost_channel", {})

        # Classify knowledge type
        knowledge_type = self._classify(response, routing)

        # Generate deposit ID
        self._total_deposits += 1
        deposit_id = f"KD-{self._total_deposits:06d}-{int(time.time()) % 100000}"

        # Extract tags from routing and content
        tags = [
            routing.get("family", ""),
            routing.get("role_code", ""),
            knowledge_type,
        ]

        # Calculate relevance based on response quality signals
        relevance = self._calculate_relevance(task_result)

        # Store
        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)
        conn.execute(
            """INSERT INTO knowledge_deposits
               (deposit_id, timestamp, source_type, source_role, source_family,
                project_id, knowledge_type, content, tags, relevance_score,
                gc_token, gc_delta_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (deposit_id, time.time(), "task_result",
             routing.get("role_code", ""), routing.get("family", ""),
             project_id, knowledge_type,
             response[:2000],  # Truncate for storage
             json.dumps(tags),
             relevance,
             gc_token or "",
             gc_info.get("delta_hash", "") if gc_info else "")
        )
        conn.commit()
        conn.close()

        return {
            "deposit_id": deposit_id,
            "knowledge_type": knowledge_type,
            "relevance": round(relevance, 4),
            "project_id": project_id,
            "total_deposits": self._total_deposits,
        }

    def cross_link(self, deposit_id: str, related_ids: List[str],
                   link_type: str = "semantic") -> int:
        """Stage 4: Cross-link related knowledge entries."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)
        linked = 0
        for related_id in related_ids:
            link_id = f"KL-{deposit_id}-{related_id}"
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO knowledge_links
                       (link_id, from_deposit, to_deposit, link_type, strength)
                       VALUES (?, ?, ?, ?, ?)""",
                    (link_id, deposit_id, related_id, link_type, 0.5)
                )
                linked += 1
            except Exception:
                pass
        conn.commit()
        conn.close()
        return linked

    def log_evolution(self, flywheel_iterations: int = 0) -> dict:
        """Stage 5: Log evolution metrics for Flywheel tracking."""
        # Calculate growth rate
        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)
        recent = conn.execute(
            """SELECT COUNT(*) FROM knowledge_deposits
               WHERE timestamp > ?""",
            (time.time() - 3600,)  # Last hour
        ).fetchone()[0]

        growth_rate = recent / max(self._total_deposits, 1)
        self._evolution_score = min(1.0, self._total_deposits / 100) * 0.5 + growth_rate * 0.5

        conn.execute(
            """INSERT INTO evolution_log
               (timestamp, total_deposits, evolution_score,
                flywheel_iterations, knowledge_growth_rate)
               VALUES (?, ?, ?, ?, ?)""",
            (time.time(), self._total_deposits, self._evolution_score,
             flywheel_iterations, growth_rate)
        )
        conn.commit()
        conn.close()

        return {
            "total_deposits": self._total_deposits,
            "evolution_score": round(self._evolution_score, 4),
            "growth_rate": round(growth_rate, 4),
            "flywheel_iterations": flywheel_iterations,
        }

    def get_project_knowledge(self, project_id: str, limit: int = 20) -> List[dict]:
        """Get knowledge deposits for a specific project."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)
        rows = conn.execute(
            """SELECT deposit_id, timestamp, source_role, knowledge_type,
                      content, relevance_score
               FROM knowledge_deposits
               WHERE project_id = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (project_id, limit)
        ).fetchall()
        conn.close()
        return [
            {"id": r[0], "time": r[1], "role": r[2], "type": r[3],
             "content": r[4][:200], "relevance": r[5]}
            for r in rows
        ]

    def get_status(self) -> dict:
        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)
        types = {}
        for row in conn.execute(
            "SELECT knowledge_type, COUNT(*) FROM knowledge_deposits GROUP BY knowledge_type"
        ):
            types[row[0]] = row[1]
        projects = conn.execute(
            "SELECT COUNT(DISTINCT project_id) FROM knowledge_deposits"
        ).fetchone()[0]
        links = conn.execute("SELECT COUNT(*) FROM knowledge_links").fetchone()[0]
        conn.close()

        return {
            "total_deposits": self._total_deposits,
            "knowledge_types": types,
            "projects": projects,
            "cross_links": links,
            "evolution_score": round(self._evolution_score, 4),
        }

    def _classify(self, response: str, routing: dict) -> str:
        """Classify knowledge type based on content and source."""
        family = routing.get("family", "")
        if family == "trum":
            return "strategic"
        elif family == "spec":
            return "procedural"

        # QCM family — classify by content signals
        text = response.lower()
        if any(k in text for k in ["分析", "数据", "指标", "趋势"]):
            return "analytical"
        elif any(k in text for k in ["设计", "架构", "方案"]):
            return "architectural"
        elif any(k in text for k in ["风险", "安全", "审计"]):
            return "risk_assessment"
        elif any(k in text for k in ["研究", "调研", "报告"]):
            return "research"
        else:
            return "episodic"

    def _calculate_relevance(self, task_result: dict) -> float:
        """Calculate relevance score based on multiple signals."""
        score = 0.3  # Base relevance

        response = task_result.get("response", "")
        routing = task_result.get("routing", {})

        # Length signal (longer = more substantive, up to a point)
        score += min(0.2, len(response) / 1000)

        # Confidence signal
        score += routing.get("confidence", 0) * 0.2

        # Ghost Channel verification
        gc = task_result.get("ghost_channel", {})
        if gc and gc.get("synced"):
            score += 0.15

        # Sandbox validation
        sb = task_result.get("sandbox", {})
        if sb and sb.get("valid"):
            score += 0.1

        # DeerFlow execution
        df = task_result.get("deerflow")
        if df and df.get("executed"):
            score += 0.15

        return min(1.0, score)


# ═══════════════════════════════════════════════════════════
# 3. MULTI-PROJECT ORCHESTRATOR
# ═══════════════════════════════════════════════════════════

@dataclass
class ProjectContext:
    """A managed project with its own knowledge space and state."""
    project_id: str
    name: str
    description: str = ""
    created_at: float = field(default_factory=time.time)
    status: str = "active"
    knowledge_count: int = 0
    interaction_count: int = 0
    roles_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProjectOrchestrator:
    """
    Multi-project management + result aggregation.

    Supports the user's vision of managing multiple projects
    as an "AI one-person company" (Point #11).

    Each project has its own:
    - Knowledge space (isolated deposits)
    - Interaction history
    - Role usage patterns
    - Result aggregation
    """

    def __init__(self, db_path: str = None):
        self._db_path = db_path or str(
            Path(__file__).parent / "projects.db"
        )
        self._projects: Dict[str, ProjectContext] = {}
        self._active_project: str = "default"
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)
            conn.execute("PRAGMA journal_mode=DELETE")
        except Exception:
            import tempfile
            tmpdir = Path(tempfile.gettempdir()) / "qspectrum_data"
            tmpdir.mkdir(parents=True, exist_ok=True)
            self._db_path = str(tmpdir / "projects.db")
            conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)

        # Use individual execute() calls to avoid disk I/O on FUSE
        _ddl = [
            """CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                created_at REAL,
                status TEXT DEFAULT 'active',
                metadata TEXT DEFAULT '{}'
            )""",
            """CREATE TABLE IF NOT EXISTS project_interactions (
                interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                timestamp REAL,
                user_input TEXT,
                role_code TEXT,
                family TEXT,
                response_length INTEGER,
                elapsed_ms REAL,
                gc_synced INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS project_results (
                result_id TEXT PRIMARY KEY,
                project_id TEXT,
                timestamp REAL,
                result_type TEXT,
                summary TEXT,
                knowledge_deposit_id TEXT,
                quality_score REAL
            )""",
        ]
        for stmt in _ddl:
            try:
                conn.execute(stmt)
            except Exception:
                pass

        # Ensure default project exists
        conn.execute(
            """INSERT OR IGNORE INTO projects
               (project_id, name, description, created_at)
               VALUES (?, ?, ?, ?)""",
            ("default", "Default Project", "Auto-created default project", time.time())
        )
        conn.commit()

        # Load existing projects
        for row in conn.execute("SELECT * FROM projects"):
            ctx = ProjectContext(
                project_id=row[0], name=row[1], description=row[2],
                created_at=row[3], status=row[4],
                metadata=json.loads(row[5]) if row[5] else {},
            )
            self._projects[row[0]] = ctx
        conn.close()

    def create_project(self, project_id: str, name: str,
                       description: str = "") -> ProjectContext:
        """Create a new project context."""
        ctx = ProjectContext(
            project_id=project_id, name=name, description=description,
        )
        self._projects[project_id] = ctx

        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)
        conn.execute(
            """INSERT OR REPLACE INTO projects
               (project_id, name, description, created_at, status)
               VALUES (?, ?, ?, ?, ?)""",
            (project_id, name, description, ctx.created_at, "active")
        )
        conn.commit()
        conn.close()

        logger.info(f"Project created: {project_id} ({name})")
        return ctx

    def switch_project(self, project_id: str) -> bool:
        """Switch active project context."""
        if project_id in self._projects:
            self._active_project = project_id
            return True
        return False

    def record_interaction(self, project_id: str, task_result: dict):
        """Record an interaction for a project."""
        routing = task_result.get("routing", {})
        gc = task_result.get("ghost_channel", {})

        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)
        conn.execute(
            """INSERT INTO project_interactions
               (project_id, timestamp, user_input, role_code, family,
                response_length, elapsed_ms, gc_synced)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (project_id, time.time(),
             task_result.get("metadata", {}).get("user_input", "")[:200],
             routing.get("role_code", ""),
             routing.get("family", ""),
             len(task_result.get("response", "")),
             task_result.get("metadata", {}).get("elapsed_seconds", 0) * 1000,
             1 if gc and gc.get("synced") else 0)
        )
        conn.commit()
        conn.close()

        # Update in-memory state
        if project_id in self._projects:
            self._projects[project_id].interaction_count += 1
            role = routing.get("role_code", "")
            if role and role not in self._projects[project_id].roles_used:
                self._projects[project_id].roles_used.append(role)

    def record_result(self, project_id: str, result_type: str,
                      summary: str, knowledge_deposit_id: str = "",
                      quality_score: float = 0.5) -> str:
        """Record a project result for aggregation."""
        result_id = f"PR-{project_id[:8]}-{int(time.time()) % 100000}"

        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)
        conn.execute(
            """INSERT INTO project_results
               (result_id, project_id, timestamp, result_type, summary,
                knowledge_deposit_id, quality_score)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (result_id, project_id, time.time(), result_type,
             summary[:500], knowledge_deposit_id, quality_score)
        )
        conn.commit()
        conn.close()
        return result_id

    def aggregate_results(self, project_id: str = None) -> dict:
        """Aggregate results across one or all projects (feedback loop)."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=10)

        if project_id:
            where = "WHERE project_id = ?"
            params = (project_id,)
        else:
            where = ""
            params = ()

        # Interaction stats
        interactions = conn.execute(
            f"SELECT COUNT(*) FROM project_interactions {where}", params
        ).fetchone()[0]

        # Result stats
        results = conn.execute(
            f"SELECT COUNT(*), AVG(quality_score) FROM project_results {where}",
            params
        ).fetchone()

        # Role distribution
        roles = {}
        for row in conn.execute(
            f"""SELECT role_code, COUNT(*) FROM project_interactions
                {where} GROUP BY role_code ORDER BY COUNT(*) DESC""",
            params
        ):
            roles[row[0]] = row[1]

        # Family distribution
        families = {}
        for row in conn.execute(
            f"""SELECT family, COUNT(*) FROM project_interactions
                {where} GROUP BY family""",
            params
        ):
            families[row[0]] = row[1]

        conn.close()

        return {
            "project_id": project_id or "all",
            "total_interactions": interactions,
            "total_results": results[0],
            "avg_quality": round(results[1] or 0, 4),
            "role_distribution": roles,
            "family_distribution": families,
            "projects_count": len(self._projects),
        }

    def list_projects(self) -> List[dict]:
        return [
            {
                "id": p.project_id,
                "name": p.name,
                "status": p.status,
                "interactions": p.interaction_count,
                "roles_used": len(p.roles_used),
                "created_at": p.created_at,
            }
            for p in self._projects.values()
        ]

    @property
    def active_project(self) -> str:
        return self._active_project


# ═══════════════════════════════════════════════════════════
# 4. COMPONENT REGISTRY (Hot-Swap Port — Point #15)
# ═══════════════════════════════════════════════════════════

class ComponentRegistry:
    """
    Pluggable component registry for hot-swapping system parts.

    This is the "端口和区域" (port and area) from Point #15.
    Components can be registered, replaced, and queried at runtime.

    Component types:
    - llm_provider: Language model backend
    - knowledge_store: Knowledge storage engine
    - vector_db: Vector database for embeddings
    - skill_executor: Skill execution engine
    - workflow_engine: Workflow orchestration
    - sandbox: Sandbox validation layer
    - protocol: Communication protocol
    """

    def __init__(self):
        self._components: Dict[str, Dict] = {}
        self._hooks: Dict[str, List] = {}  # event → [callback, ...]
        self._swap_history: List[dict] = []

    def register(self, component_type: str, name: str, instance: Any,
                 version: str = "1.0", metadata: dict = None) -> bool:
        """Register a component. Replaces existing if same type+name."""
        key = f"{component_type}:{name}"
        old = self._components.get(key)

        self._components[key] = {
            "type": component_type,
            "name": name,
            "instance": instance,
            "version": version,
            "registered_at": time.time(),
            "metadata": metadata or {},
        }

        if old:
            self._swap_history.append({
                "type": component_type,
                "name": name,
                "old_version": old.get("version"),
                "new_version": version,
                "time": time.time(),
            })
            logger.info(f"Component swapped: {key} v{old['version']} → v{version}")
        else:
            logger.info(f"Component registered: {key} v{version}")

        # Fire hooks
        for callback in self._hooks.get(f"on_register:{component_type}", []):
            try:
                callback(name, instance)
            except Exception:
                pass

        return True

    def get(self, component_type: str, name: str = None) -> Any:
        """Get a component instance. If name omitted, returns first of that type."""
        if name:
            key = f"{component_type}:{name}"
            entry = self._components.get(key)
            return entry["instance"] if entry else None

        # Find first matching type
        for key, entry in self._components.items():
            if entry["type"] == component_type:
                return entry["instance"]
        return None

    def list_components(self, component_type: str = None) -> List[dict]:
        """List all registered components."""
        result = []
        for key, entry in self._components.items():
            if component_type and entry["type"] != component_type:
                continue
            result.append({
                "type": entry["type"],
                "name": entry["name"],
                "version": entry["version"],
                "registered_at": entry["registered_at"],
                "class": type(entry["instance"]).__name__,
            })
        return result

    def on(self, event: str, callback):
        """Register a hook for component events."""
        self._hooks.setdefault(event, []).append(callback)

    def swap_history(self) -> List[dict]:
        return list(self._swap_history)

    def get_status(self) -> dict:
        types = {}
        for entry in self._components.values():
            t = entry["type"]
            types[t] = types.get(t, 0) + 1

        return {
            "total_components": len(self._components),
            "component_types": types,
            "swap_count": len(self._swap_history),
        }


# ═══════════════════════════════════════════════════════════
# 5. USER GROWTH ENGINE (S1-S5)
# ═══════════════════════════════════════════════════════════

class UserGrowthEngine:
    """
    Progressive capability unlocking (S1→S5).

    S1: Observer     — View roles, basic chat, learn system
    S2: Participant  — Full chat, role selection, basic workflows
    S3: Contributor  — Sandbox access, knowledge deposits, skill use
    S4: Architect    — Multi-project, workflow creation, DeerFlow
    S5: Master       — Full system access, component swap, governance
    """

    STAGES = {
        "S1": {
            "name": "Observer", "max_roles": 3, "can_sandbox": False,
            "can_workflow": False, "can_multi_project": False,
            "can_deerflow": False, "can_swap_components": False,
            "unlock_interactions": 0,
        },
        "S2": {
            "name": "Participant", "max_roles": 7, "can_sandbox": False,
            "can_workflow": True, "can_multi_project": False,
            "can_deerflow": False, "can_swap_components": False,
            "unlock_interactions": 10,
        },
        "S3": {
            "name": "Contributor", "max_roles": 10, "can_sandbox": True,
            "can_workflow": True, "can_multi_project": False,
            "can_deerflow": True, "can_swap_components": False,
            "unlock_interactions": 30,
        },
        "S4": {
            "name": "Architect", "max_roles": 15, "can_sandbox": True,
            "can_workflow": True, "can_multi_project": True,
            "can_deerflow": True, "can_swap_components": False,
            "unlock_interactions": 80,
        },
        "S5": {
            "name": "Master", "max_roles": 15, "can_sandbox": True,
            "can_workflow": True, "can_multi_project": True,
            "can_deerflow": True, "can_swap_components": True,
            "unlock_interactions": 200,
        },
    }

    def __init__(self):
        self._current_stage = "S1"
        self._interaction_count = 0
        self._knowledge_deposits = 0
        self._projects_created = 0
        self._history: List[dict] = []

    def check_progression(self, interaction_count: int = 0,
                          knowledge_deposits: int = 0,
                          projects_created: int = 0) -> dict:
        """Check and potentially advance user stage."""
        self._interaction_count = interaction_count
        self._knowledge_deposits = knowledge_deposits
        self._projects_created = projects_created

        old_stage = self._current_stage

        # Check each stage from S5 down
        for stage_id in reversed(list(self.STAGES.keys())):
            stage = self.STAGES[stage_id]
            if interaction_count >= stage["unlock_interactions"]:
                self._current_stage = stage_id
                break

        advanced = self._current_stage != old_stage
        if advanced:
            self._history.append({
                "from": old_stage, "to": self._current_stage,
                "time": time.time(),
                "interactions": interaction_count,
            })
            logger.info(
                f"User Growth: {old_stage} → {self._current_stage} "
                f"({self.STAGES[self._current_stage]['name']})"
            )

        current = self.STAGES[self._current_stage]
        next_stage = None
        stages = list(self.STAGES.keys())
        idx = stages.index(self._current_stage)
        if idx < len(stages) - 1:
            next_id = stages[idx + 1]
            next_info = self.STAGES[next_id]
            next_stage = {
                "stage": next_id,
                "name": next_info["name"],
                "interactions_needed": next_info["unlock_interactions"] - interaction_count,
            }

        return {
            "stage": self._current_stage,
            "name": current["name"],
            "capabilities": current,
            "advanced": advanced,
            "next": next_stage,
        }

    def can(self, capability: str) -> bool:
        """Check if current stage permits a capability."""
        current = self.STAGES.get(self._current_stage, {})
        return current.get(capability, False)

    @property
    def stage(self) -> str:
        return self._current_stage

    def get_status(self) -> dict:
        current = self.STAGES[self._current_stage]
        return {
            "stage": self._current_stage,
            "name": current["name"],
            "interactions": self._interaction_count,
            "capabilities": {k: v for k, v in current.items() if k.startswith("can_")},
            "max_roles": current["max_roles"],
            "history": self._history[-5:],
        }
