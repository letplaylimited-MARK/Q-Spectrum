"""
Q-SpecTrum Closed-Loop Architecture v1.0
==========================================
Implements the complete closed-loop pipeline:

  [Resource Layer]     → User uploads text/files/images/code/tools into DB
      ↓
  [AI Chatroom]        → User describes needs, AI roles collaborate
      ↓
  [Execution Layer]    → Q-SpecTrum 15-role pipeline processes
      ↓
  [Result Layer]       → Execution results persisted to DB
      ↓
  [Decision Tuning]    → Quality feedback tunes routing weights
      ↓
  [Resource Layer]     → Loop closes — enriched resources feed next cycle

Components:
  1. ComponentConfig    — Load/manage config.yaml, hot-reload
  2. ResourceCollector  — User data collection pipeline (text/file/image/code → DB)
  3. ResultPersistence  — Save execution results to DB for continuity
  4. FeedbackLoop       — Quality scores feed back to routing weights

Ghost Channel activation via ghost_channel_gate.GhostChannelGate (canonical).
Called from qspectrum_engine.py and api_server.py.
"""

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, List

# ═══════════════════════════════════════════════════════════
# 1. COMPONENT CONFIG — Load and manage system configuration
# ═══════════════════════════════════════════════════════════

class ComponentConfig:
    """
    Loads Q-SpecTrum configuration from YAML files.
    Priority: local.yaml > default.yaml > hardcoded defaults.
    """

    DEFAULTS = {
        "llm": {"provider": "mock", "model": "mock", "temperature": 0.7, "max_tokens": 4096},
        "database": {"path": "AI项目管理/Platform/db/platform.db", "backup_interval_minutes": 15},
        "secretary": {"radar_dimensions": 5, "default_qos": "assured", "default_governance": "medium"},
        "knowledge_resonance": {
            "weights": {"k_sim": 0.35, "c_comp": 0.25, "i_freq": 0.25, "e_div": 0.15},
            "threshold": {"high": 0.75, "medium": 0.50, "low": 0.50},
        },
        "growth": {"initial_stage": "S1", "auto_evaluate": True},
        "ghost_channel": {
            "encryption": "AES-256-GCM",
            "required": True,           # Ghost Channel is the activation grip
            "key_rotation_hours": 12,
            "delta_compression": True,
        },
        "closed_loop": {
            "result_persistence": True,  # Save execution results to DB
            "resource_collection": True, # Enable user resource collection
            "feedback_loop": True,       # Quality → routing feedback
            "auto_checkpoint": 5,        # Auto-save knowledge every N interactions
        },
        "logging": {"level": "INFO", "audit_trail": True},
    }

    def __init__(self, root_dir: str = None):
        self.root = Path(root_dir) if root_dir else Path(__file__).parent
        self._config = dict(self.DEFAULTS)
        self._load()

    def _load(self):
        """Load config from YAML files (local.yaml > default.yaml)."""
        for name in ["config/default.yaml", "config/local.yaml", "local.yaml"]:
            path = self.root / name
            if path.exists():
                try:
                    data = self._parse_yaml(path)
                    if data:
                        self._deep_merge(self._config, data)
                except Exception:
                    pass

        # Environment variable overrides
        env_provider = os.environ.get("QSPECTRUM_LLM")
        if env_provider:
            self._config["llm"]["provider"] = env_provider

    @staticmethod
    def _parse_yaml(path: Path) -> dict:
        """Minimal YAML parser (no external dependency)."""
        result = {}
        current_section = None
        current_subsection = None

        for line in path.read_text(encoding="utf-8").split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip())

            if ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                # Remove inline comments
                if "#" in value and not value.startswith('"'):
                    value = value.split("#")[0].strip().strip('"').strip("'")

                if indent == 0:
                    if not value:
                        current_section = key
                        current_subsection = None
                        result.setdefault(current_section, {})
                    else:
                        result[key] = _parse_value(value)
                elif indent <= 4 and current_section:
                    if not value:
                        current_subsection = key
                        result[current_section].setdefault(current_subsection, {})
                    else:
                        result[current_section][key] = _parse_value(value)
                elif indent > 4 and current_section and current_subsection:
                    result[current_section][current_subsection][key] = _parse_value(value)

        return result

    @staticmethod
    def _deep_merge(base: dict, override: dict):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                ComponentConfig._deep_merge(base[k], v)
            else:
                base[k] = v

    def get(self, section: str, key: str = None, default=None):
        """Get config value. e.g. config.get('llm', 'provider')"""
        sect = self._config.get(section, {})
        if key is None:
            return sect
        if isinstance(sect, dict):
            return sect.get(key, default)
        return default

    def get_all(self) -> dict:
        return dict(self._config)

    def status(self) -> dict:
        return {
            "config_loaded": True,
            "sections": list(self._config.keys()),
            "llm_provider": self._config.get("llm", {}).get("provider", "unknown"),
            "ghost_channel_required": self._config.get("ghost_channel", {}).get("required", True),
            "closed_loop_enabled": self._config.get("closed_loop", {}).get("result_persistence", False),
        }


def _parse_value(v: str):
    """Parse a YAML value string to Python type."""
    if not v or v == '""' or v == "''":
        return ""
    low = v.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low == "null" or low == "none":
        return None
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


# ═══════════════════════════════════════════════════════════
# 2. RESOURCE COLLECTOR — User data collection pipeline
# ═══════════════════════════════════════════════════════════

class ResourceCollector:
    """
    Collects user resources (text, files, images, code, tools, skills)
    into the database. This is the INPUT side of the closed loop.

    Addresses user vision point 16:
      "收集文字/资料/图片/视频/工具/技能/代码...等等数据库"
    """

    RESOURCE_TYPES = {
        "text": "用户文本输入",
        "file": "上传文件",
        "image": "图片资源",
        "video": "视频资源",
        "code": "代码片段",
        "tool": "工具/API",
        "skill": "技能定义",
        "document": "文档资料",
        "data": "数据集",
        "config": "配置信息",
    }

    def __init__(self, db_path: str = None):
        self._db_path = db_path
        self._conn = None
        self._ensure_tables()

    def _get_conn(self):
        # Thread-safe connection: check_same_thread=False allows the
        # API server's multi-threaded handler to share the connection.
        # SQLite itself serializes writes via its internal lock.
        if self._conn is None:
            db_path = self._db_path or str(
                Path(__file__).parent / "user_resources.db")
            try:
                # Clean stale journal files that cause disk I/O errors
                journal = db_path + "-journal"
                if Path(journal).exists():
                    try:
                        Path(journal).unlink()
                    except OSError:
                        pass
                self._conn = sqlite3.connect(db_path, check_same_thread=False, timeout=10)
                self._conn.execute("PRAGMA journal_mode=WAL")
            except Exception:
                # Fallback to temp dir if disk I/O fails
                import tempfile
                tmpdir = Path(tempfile.gettempdir()) / "qspectrum_data"
                tmpdir.mkdir(parents=True, exist_ok=True)
                fallback = str(tmpdir / "user_resources.db")
                self._conn = sqlite3.connect(fallback, check_same_thread=False, timeout=10)
        return self._conn

    def _ensure_tables(self):
        """Create resource collection tables if they don't exist."""
        conn = self._get_conn()
        # Use individual execute() calls instead of executescript()
        # to avoid disk I/O errors on FUSE-mounted filesystems.
        _ddl = [
            """CREATE TABLE IF NOT EXISTS user_resources (
                id TEXT PRIMARY KEY,
                resource_type TEXT NOT NULL,
                title TEXT,
                content TEXT,
                file_path TEXT,
                file_size INTEGER DEFAULT 0,
                mime_type TEXT,
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                project_id TEXT,
                interaction_id TEXT,
                created_at REAL,
                updated_at REAL
            )""",
            """CREATE TABLE IF NOT EXISTS execution_results (
                id TEXT PRIMARY KEY,
                interaction_id TEXT,
                role_code TEXT,
                family TEXT,
                request_text TEXT,
                response_text TEXT,
                artifacts TEXT DEFAULT '[]',
                routing_info TEXT DEFAULT '{}',
                quality_score REAL DEFAULT 0.0,
                user_rating INTEGER,
                execution_time_ms REAL,
                deerflow_skill TEXT,
                ghost_channel_synced INTEGER DEFAULT 0,
                knowledge_deposited INTEGER DEFAULT 0,
                created_at REAL
            )""",
            """CREATE TABLE IF NOT EXISTS routing_feedback (
                id TEXT PRIMARY KEY,
                interaction_id TEXT,
                role_code TEXT,
                query_text TEXT,
                quality_score REAL,
                user_rating INTEGER,
                was_correct_route INTEGER,
                suggested_role TEXT,
                created_at REAL
            )""",
            "CREATE INDEX IF NOT EXISTS idx_resources_type ON user_resources(resource_type)",
            "CREATE INDEX IF NOT EXISTS idx_resources_project ON user_resources(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_results_role ON execution_results(role_code)",
            "CREATE INDEX IF NOT EXISTS idx_results_created ON execution_results(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_role ON routing_feedback(role_code)",
        ]
        for stmt in _ddl:
            try:
                conn.execute(stmt)
            except Exception:
                pass
        conn.commit()

    def collect(self, resource_type: str, content: str,
                title: str = None, tags: list = None,
                file_path: str = None, file_size: int = 0,
                mime_type: str = None, project_id: str = None,
                interaction_id: str = None, metadata: dict = None) -> dict:
        """
        Collect a user resource into the database.

        Returns: {"id": "...", "resource_type": "...", "stored": True}
        """
        rid = f"RES-{uuid.uuid4().hex[:8]}"
        now = time.time()
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO user_resources
               (id, resource_type, title, content, file_path, file_size,
                mime_type, tags, metadata, project_id, interaction_id,
                created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rid, resource_type, title or "",
             content[:10000] if content else "",  # Limit content size
             file_path or "", file_size, mime_type or "",
             json.dumps(tags or []),
             json.dumps(metadata or {}),
             project_id or "", interaction_id or "",
             now, now))
        conn.commit()

        return {
            "id": rid,
            "resource_type": resource_type,
            "title": title,
            "stored": True,
            "created_at": now,
        }

    def search(self, query: str, resource_type: str = None,
               limit: int = 20, top_k: int = None) -> List[dict]:
        """Search collected resources."""
        if top_k is not None:
            limit = top_k  # alias for API compatibility
        conn = self._get_conn()
        sql = "SELECT id, resource_type, title, content, tags, created_at FROM user_resources"
        params = []

        conditions = []
        if resource_type:
            conditions.append("resource_type = ?")
            params.append(resource_type)
        if query:
            conditions.append("(title LIKE ? OR content LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        return [
            {"id": r[0], "type": r[1], "title": r[2],
             "content_preview": (r[3] or "")[:100],
             "tags": json.loads(r[4] or "[]"),
             "created_at": r[5]}
            for r in rows
        ]

    def get_stats(self) -> dict:
        """Get resource collection statistics."""
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM user_resources").fetchone()[0]
        by_type = {}
        for row in conn.execute(
                "SELECT resource_type, COUNT(*) FROM user_resources GROUP BY resource_type"):
            by_type[row[0]] = row[1]
        return {"total_resources": total, "by_type": by_type}


# ═══════════════════════════════════════════════════════════
# 3. RESULT PERSISTENCE — Save execution results
# ═══════════════════════════════════════════════════════════

class ResultPersistence:
    """
    Persists execution results to the database.
    This is the OUTPUT side of the closed loop.
    Results survive server restarts and can be queried/analyzed.
    """

    def __init__(self, collector: ResourceCollector):
        self._collector = collector

    def save_result(self, interaction_id: str, role_code: str,
                    family: str, request_text: str, response_text: str,
                    routing_info: dict = None, execution_time_ms: float = 0,
                    deerflow_skill: str = None, ghost_channel_synced: bool = False,
                    knowledge_deposited: bool = True, artifacts: list = None) -> dict:
        """Save an execution result to the database."""
        rid = f"EXEC-{uuid.uuid4().hex[:8]}"
        now = time.time()
        conn = self._collector._get_conn()

        # Calculate a basic quality score based on response characteristics
        quality_score = self._estimate_quality(response_text, routing_info or {})

        conn.execute(
            """INSERT INTO execution_results
               (id, interaction_id, role_code, family, request_text, response_text,
                artifacts, routing_info, quality_score, execution_time_ms,
                deerflow_skill, ghost_channel_synced, knowledge_deposited, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rid, interaction_id, role_code, family,
             request_text[:2000], response_text[:5000],
             json.dumps(artifacts or []),
             json.dumps(routing_info or {}),
             quality_score, execution_time_ms,
             deerflow_skill or "",
             1 if ghost_channel_synced else 0,
             1 if knowledge_deposited else 0,
             now))
        conn.commit()

        return {
            "result_id": rid,
            "quality_score": round(quality_score, 3),
            "saved": True,
        }

    def _estimate_quality(self, response: str, routing: dict) -> float:
        """Estimate quality based on response characteristics."""
        score = 0.0
        if len(response) > 50:
            score += 0.3
        if len(response) > 200:
            score += 0.2
        if routing.get("confidence", 0) > 0.5:
            score += 0.2
        if routing.get("role_code", "").startswith("ROLE-Q"):
            score += 0.1  # Specialized QCM role
        if "**" in response or "##" in response:
            score += 0.1  # Structured output
        if "DeerFlow" in response:
            score += 0.1  # DeerFlow integration triggered
        return min(1.0, score)

    def get_history(self, limit: int = 50, role_code: str = None) -> List[dict]:
        """Get execution history from database."""
        conn = self._collector._get_conn()
        sql = """SELECT id, interaction_id, role_code, family,
                        request_text, quality_score, execution_time_ms,
                        deerflow_skill, created_at
                 FROM execution_results"""
        params = []
        if role_code:
            sql += " WHERE role_code = ?"
            params.append(role_code)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        return [
            {"id": r[0], "interaction_id": r[1], "role_code": r[2],
             "family": r[3], "request_preview": (r[4] or "")[:60],
             "quality_score": r[5], "execution_time_ms": r[6],
             "deerflow_skill": r[7], "created_at": r[8]}
            for r in rows
        ]

    def get_stats(self) -> dict:
        """Get result persistence statistics."""
        conn = self._collector._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM execution_results").fetchone()[0]
        avg_quality = conn.execute(
            "SELECT AVG(quality_score) FROM execution_results").fetchone()[0] or 0
        by_role = {}
        for row in conn.execute(
                "SELECT role_code, COUNT(*), AVG(quality_score) "
                "FROM execution_results GROUP BY role_code"):
            by_role[row[0]] = {"count": row[1], "avg_quality": round(row[2] or 0, 3)}
        return {
            "total_results": total,
            "avg_quality": round(avg_quality, 3),
            "by_role": by_role,
        }


# ═══════════════════════════════════════════════════════════
# 4. FEEDBACK LOOP — Quality → Routing Weight Tuning
# ═══════════════════════════════════════════════════════════

class FeedbackLoop:
    """
    Connects execution quality back to routing decisions.
    Implements the DECISION TUNING stage of the closed loop.

    When a role produces good results → increase affinity for similar queries.
    When a role produces bad results → decrease affinity, try alternatives.
    """

    def __init__(self, collector: ResourceCollector):
        self._collector = collector
        self._role_affinity: Dict[str, float] = {}  # role_code → affinity boost
        self._load_affinity()

    def _load_affinity(self):
        """Load affinity weights from feedback history."""
        try:
            conn = self._collector._get_conn()
            for row in conn.execute(
                    """SELECT role_code, AVG(quality_score), COUNT(*)
                       FROM routing_feedback
                       GROUP BY role_code"""):
                role, avg_q, count = row
                # Affinity = (avg_quality - 0.5) * log(count+1) * 0.1
                import math
                self._role_affinity[role] = (avg_q - 0.5) * math.log(count + 1) * 0.1
        except Exception:
            pass

    def record_feedback(self, interaction_id: str, role_code: str,
                        query_text: str, quality_score: float,
                        user_rating: int = None,
                        was_correct_route: bool = True,
                        suggested_role: str = None) -> dict:
        """Record feedback for a routing decision."""
        fid = f"FB-{uuid.uuid4().hex[:8]}"
        now = time.time()
        conn = self._collector._get_conn()

        conn.execute(
            """INSERT INTO routing_feedback
               (id, interaction_id, role_code, query_text, quality_score,
                user_rating, was_correct_route, suggested_role, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (fid, interaction_id, role_code,
             query_text[:500], quality_score,
             user_rating, 1 if was_correct_route else 0,
             suggested_role or "", now))
        conn.commit()

        # Update affinity
        self._load_affinity()

        return {"feedback_id": fid, "recorded": True}

    def get_role_affinity(self, role_code: str) -> float:
        """Get affinity boost for a role (used by Secretary for routing)."""
        return self._role_affinity.get(role_code, 0.0)

    def get_all_affinities(self) -> Dict[str, float]:
        """Get all role affinities."""
        return dict(self._role_affinity)

    def get_stats(self) -> dict:
        """Get feedback loop statistics."""
        conn = self._collector._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM routing_feedback").fetchone()[0]
        return {
            "total_feedback": total,
            "role_affinities": {k: round(v, 3) for k, v in self._role_affinity.items()},
        }


from ghost_channel_gate import GhostChannelGate

# ─── Feature gate mapping ───────────────────────────────────
# Maps canonical Ghost Channel tier → closed-loop feature availability
_GC_FEATURES: dict = {
    "open": {   # Gate is open (any valid tier)
        "result_persistence": True,
        "feedback_loop": True,
        "resource_collection": True,
    },
    "closed": { # Gate is locked or no key
        "result_persistence": False,
        "feedback_loop": False,
        "resource_collection": True,
    },
}

def _gate_feature_enabled(gate: GhostChannelGate, feature: str) -> bool:
    """Check if a closed-loop feature is allowed by the Ghost Channel gate."""
    mapping = _GC_FEATURES["open" if gate.is_open else "closed"]
    return mapping.get(feature, False)


# ═══════════════════════════════════════════════════════════
# 6. CLOSED LOOP MANAGER — Unifies all components
# ═══════════════════════════════════════════════════════════

class ClosedLoopManager:
    """
    The unified manager for the closed-loop architecture.
    Instantiated once by QSpectrumEngine, provides all loop services.
    """

    def __init__(self, resource_db_path: str = None):
        self.config = ComponentConfig()
        self.gate = GhostChannelGate()

        # Resource DB — separate from platform.db to avoid immutable conflict
        db_path = resource_db_path or str(Path(__file__).parent / "user_resources.db")
        self.resources = ResourceCollector(db_path=db_path)
        self.results = ResultPersistence(self.resources)
        self.feedback = FeedbackLoop(self.resources)

    def on_interaction_complete(self, interaction_id: str, role_code: str,
                                 family: str, request_text: str,
                                 response_text: str, routing_info: dict = None,
                                 execution_time_ms: float = 0,
                                 deerflow_skill: str = None,
                                 ghost_channel_synced: bool = False) -> dict:
        """
        Called after each interaction completes.
        Saves result + records feedback + updates affinity.
        """
        result = {}

        # 1. Save execution result
        if _gate_feature_enabled(self.gate, "result_persistence"):
            result["persistence"] = self.results.save_result(
                interaction_id=interaction_id,
                role_code=role_code,
                family=family,
                request_text=request_text,
                response_text=response_text,
                routing_info=routing_info,
                execution_time_ms=execution_time_ms,
                deerflow_skill=deerflow_skill,
                ghost_channel_synced=ghost_channel_synced,
            )

        # 2. Auto-feedback (quality estimation)
        if _gate_feature_enabled(self.gate, "feedback_loop"):
            quality = result.get("persistence", {}).get("quality_score", 0.5)
            self.feedback.record_feedback(
                interaction_id=interaction_id,
                role_code=role_code,
                query_text=request_text,
                quality_score=quality,
            )
            result["feedback"] = {"quality_score": quality, "recorded": True}

        # 3. Auto-collect user input as resource
        if _gate_feature_enabled(self.gate, "resource_collection"):
            self.resources.collect(
                resource_type="text",
                content=request_text,
                title=f"User query → {role_code}",
                tags=[family, role_code, "interaction"],
                interaction_id=interaction_id,
            )

        return result

    def collect_user_resource(self, resource_type: str, content: str,
                               **kwargs) -> dict:
        """Collect a user resource (file, image, code, etc.)."""
        if not _gate_feature_enabled(self.gate, "resource_collection"):
            return {"error": "Resource collection not enabled (upgrade Ghost Channel)"}
        return self.resources.collect(resource_type=resource_type,
                                       content=content, **kwargs)

    def get_role_affinity(self, role_code: str) -> float:
        """Get routing affinity boost for a role."""
        if not _gate_feature_enabled(self.gate, "feedback_loop"):
            return 0.0
        return self.feedback.get_role_affinity(role_code)

    def status(self) -> dict:
        """Complete closed-loop status."""
        return {
            "closed_loop": "active",
            "config": self.config.status(),
            "activation": self.gate.get_status(),
            "resources": self.resources.get_stats(),
            "results": self.results.get_stats(),
            "feedback": self.feedback.get_stats(),
        }


# ═══════════════════════════════════════════════════════════
# 7. CLOSED LOOP SYSTEM — Standalone convenience class
# ═══════════════════════════════════════════════════════════

class ClosedLoopSystem(ClosedLoopManager):
    """
    Convenience alias for ClosedLoopManager.
    Allows standalone initialization: cl = ClosedLoopSystem()
    """
    pass


# ═══════════════════════════════════════════════════════════
# CLI Interface
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("  Q-SpecTrum Closed-Loop Architecture v1.0")
    print("=" * 60)

    manager = ClosedLoopManager()
    status = manager.status()

    print(f"\n  Gate Open: {status['activation'].get('gate_open', False)}")
    print(f"  Tier: {status['activation'].get('tier', 'none')}")
    print(f"  Resources: {status['resources']['total_resources']} collected")
    print(f"  Results: {status['results']['total_results']} persisted")
    print(f"  Feedback: {status['feedback']['total_feedback']} entries")

    # Test collection
    if "--test" in sys.argv:
        print("\n  Running closed-loop test...")

        # Collect a resource
        r = manager.collect_user_resource(
            "text", "测试用户输入: 帮我分析竞品市场",
            title="Test resource",
            tags=["test", "market_analysis"])
        print(f"  Resource: {r}")

        # Simulate interaction completion
        loop_result = manager.on_interaction_complete(
            interaction_id="TEST-001",
            role_code="ROLE-Q04",
            family="qcm",
            request_text="帮我分析竞品市场",
            response_text="分析结果: 竞品A市场份额25%, 竞品B份额18%...",
            routing_info={"confidence": 0.8, "role_code": "ROLE-Q04"},
            execution_time_ms=150.0,
            ghost_channel_synced=True,
        )
        print(f"  Loop result: {loop_result}")

        # Check stats
        print(f"\n  Resources: {manager.resources.get_stats()}")
        print(f"  Results: {manager.results.get_stats()}")
        print(f"  Affinities: {manager.feedback.get_all_affinities()}")

    print("\n" + "=" * 60)
