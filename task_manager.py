"""
Q-SpecTrum Task Manager v1.0
==============================
Implements Point #10: Visual task/workflow management with full pipeline tracking.

Every user interaction can spawn tasks. Tasks have:
  - Lifecycle: pending → in_progress → review → completed | failed
  - Assignment to AI roles
  - Dependency chains
  - DeerFlow skill associations
  - Result tracking with quality scores
  - Project scoping

Architecture:
  User Request → Task Creation → Role Assignment → Execution → Result → Review → Close
       ↓              ↓                ↓              ↓          ↓
   Task Board     Dependency       Skill Map       Progress    Archive
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("q-spectrum.task-manager")


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Task:
    """A managed task within Q-SpecTrum."""
    task_id: str
    title: str
    description: str = ""
    status: str = "pending"
    priority: str = "normal"
    project_id: str = "default"
    assigned_role: str = ""
    assigned_family: str = ""
    skills_used: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    quality_score: float = 0.0
    result_summary: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """
    Central task management system.

    Features:
    - Task CRUD with full lifecycle
    - Project-scoped task boards
    - Role assignment tracking
    - Dependency chain management
    - Analytics and statistics
    - Workflow pipeline visualization data
    """

    def __init__(self, db_path: str = None):
        self._db_path = db_path or str(
            Path(__file__).parent / "task_manager.db"
        )
        self._task_count = 0
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tm_tasks (
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'normal',
                project_id TEXT DEFAULT 'default',
                assigned_role TEXT DEFAULT '',
                assigned_family TEXT DEFAULT '',
                skills_used TEXT DEFAULT '[]',
                dependencies TEXT DEFAULT '[]',
                created_at REAL,
                started_at REAL DEFAULT 0,
                completed_at REAL DEFAULT 0,
                quality_score REAL DEFAULT 0,
                result_summary TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS tm_workflow_steps (
                step_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                task_id TEXT,
                step_order INTEGER,
                step_type TEXT DEFAULT 'task',
                config TEXT DEFAULT '{}',
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (task_id) REFERENCES tm_tasks(task_id)
            );

            CREATE INDEX IF NOT EXISTS idx_tm_tasks_project
                ON tm_tasks(project_id, status);
            CREATE INDEX IF NOT EXISTS idx_tm_tasks_role
                ON tm_tasks(assigned_role);
            CREATE INDEX IF NOT EXISTS idx_tm_tasks_status
                ON tm_tasks(status, priority);
        """)
        self._task_count = conn.execute("SELECT COUNT(*) FROM tm_tasks").fetchone()[0]
        conn.commit()
        conn.close()

    # ── Task CRUD ─────────────────────────────────────────

    def create_task(self, title: str, description: str = "",
                    priority: str = "normal", project_id: str = "default",
                    assigned_role: str = "", tags: List[str] = None,
                    dependencies: List[str] = None,
                    metadata: dict = None) -> Task:
        """Create a new task."""
        # Handle case where a dict is passed as title (ensure proper serialization)
        if isinstance(title, dict):
            task_data = title
            title = task_data.get('title', '')
            description = task_data.get('description', description)
            priority = task_data.get('priority', priority)
            project_id = task_data.get('project_id', project_id)
            assigned_role = task_data.get('assigned_role', assigned_role) or task_data.get('assignee', assigned_role)
            tags = task_data.get('tags', tags)
            dependencies = task_data.get('dependencies', dependencies)
            metadata = task_data.get('metadata', metadata)

        # Ensure string types for SQL binding
        title = str(title) if title else ""
        description = str(description) if description else ""
        priority = str(priority) if priority else "normal"
        project_id = str(project_id) if project_id else "default"
        assigned_role = str(assigned_role) if assigned_role else ""

        self._task_count += 1
        tid = f"T-{self._task_count:05d}-{int(time.time()) % 10000}"

        task = Task(
            task_id=tid,
            title=title,
            description=description,
            priority=priority,
            project_id=project_id,
            assigned_role=assigned_role,
            dependencies=dependencies or [],
            tags=tags or [],
            metadata=metadata or {},
        )

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            INSERT INTO tm_tasks
            (task_id, title, description, status, priority, project_id,
             assigned_role, skills_used, dependencies, created_at, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tid, title, description, "pending", priority, project_id,
              assigned_role, "[]", json.dumps(dependencies or []),
              task.created_at, json.dumps(tags or []), json.dumps(metadata or {})))
        conn.commit()
        conn.close()

        logger.info(f"Task created: {tid} ({title})")
        return task

    def update_status(self, task_id: str, status: str,
                      result_summary: str = "", quality_score: float = 0.0) -> bool:
        """Update task status with optional result info."""
        now = time.time()
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")

        updates = ["status = ?", "metadata = json_set(COALESCE(metadata,'{}'), '$.last_update', ?)"]
        params = [status, now]

        if status == "in_progress":
            updates.append("started_at = ?")
            params.append(now)
        elif status in ("completed", "failed"):
            updates.append("completed_at = ?")
            params.append(now)
            if result_summary:
                updates.append("result_summary = ?")
                params.append(result_summary)
            if quality_score > 0:
                updates.append("quality_score = ?")
                params.append(quality_score)

        params.append(task_id)
        conn.execute(
            f"UPDATE tm_tasks SET {', '.join(updates)} WHERE task_id = ?",
            params
        )
        affected = conn.execute("SELECT changes()").fetchone()[0]
        conn.commit()
        conn.close()
        return affected > 0

    def assign_role(self, task_id: str, role_code: str, family: str = "") -> bool:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "UPDATE tm_tasks SET assigned_role = ?, assigned_family = ? WHERE task_id = ?",
            (role_code, family, task_id)
        )
        affected = conn.execute("SELECT changes()").fetchone()[0]
        conn.commit()
        conn.close()
        return affected > 0

    def add_skill_used(self, task_id: str, skill_name: str) -> bool:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        row = conn.execute("SELECT skills_used FROM tm_tasks WHERE task_id = ?",
                           (task_id,)).fetchone()
        if not row:
            conn.close()
            return False
        skills = json.loads(row[0]) if row[0] else []
        if skill_name not in skills:
            skills.append(skill_name)
        conn.execute("UPDATE tm_tasks SET skills_used = ? WHERE task_id = ?",
                     (json.dumps(skills), task_id))
        conn.commit()
        conn.close()
        return True

    def get_task(self, task_id: str) -> Optional[dict]:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        row = conn.execute("SELECT * FROM tm_tasks WHERE task_id = ?",
                           (task_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return self._row_to_dict(row)

    def _row_to_dict(self, row) -> dict:
        return {
            "task_id": row[0], "title": row[1], "description": row[2],
            "status": row[3], "priority": row[4], "project_id": row[5],
            "assigned_role": row[6], "assigned_family": row[7],
            "skills_used": json.loads(row[8]) if row[8] else [],
            "dependencies": json.loads(row[9]) if row[9] else [],
            "created_at": row[10], "started_at": row[11],
            "completed_at": row[12], "quality_score": row[13],
            "result_summary": row[14],
            "tags": json.loads(row[15]) if row[15] else [],
            "metadata": json.loads(row[16]) if row[16] else {},
        }

    # ── Task Board (Project-scoped) ───────────────────────

    def get_board(self, project_id: str = None,
                  status: str = None, limit: int = 50) -> dict:
        """Get task board organized by status columns."""
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conditions = []
        params = []
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = conn.execute(
            f"SELECT * FROM tm_tasks {where} ORDER BY CASE priority "
            f"WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END, "
            f"created_at DESC LIMIT ?",
            params + [limit]
        ).fetchall()
        conn.close()

        # Organize into columns
        board = {
            "pending": [], "in_progress": [], "review": [],
            "completed": [], "failed": [], "blocked": [],
        }
        for row in rows:
            task = self._row_to_dict(row)
            col = task["status"]
            if col in board:
                board[col].append(task)

        return {
            "project_id": project_id or "all",
            "columns": board,
            "total": sum(len(v) for v in board.values()),
            "active": len(board["pending"]) + len(board["in_progress"]),
        }

    # ── Auto-Task from Engine Results ─────────────────────

    def create_from_engine_result(self, user_input: str, result: dict,
                                  project_id: str = "default") -> Task:
        """Automatically create and complete a task from an engine result."""
        routing = result.get("routing", {})
        response = result.get("response", "")

        task = self.create_task(
            title=user_input[:100],
            description=user_input,
            project_id=project_id,
            assigned_role=routing.get("role_code", ""),
            tags=[routing.get("family", "")],
            metadata={
                "auto_created": True,
                "confidence": routing.get("confidence", 0),
            },
        )

        # Auto-advance through lifecycle
        self.update_status(task.task_id, "in_progress")
        self.assign_role(task.task_id, routing.get("role_code", ""),
                         routing.get("family", ""))

        # DeerFlow skills
        df = result.get("deerflow")
        if df and df.get("executed"):
            for skill in df.get("skills_used", []):
                self.add_skill_used(task.task_id, skill)

        # Complete
        quality = result.get("metadata", {}).get("knowledge_relevance", 0.5)
        self.update_status(
            task.task_id, "completed",
            result_summary=response[:300],
            quality_score=quality,
        )

        return task

    # ── Analytics ─────────────────────────────────────────

    def get_analytics(self, project_id: str = None) -> dict:
        """Get task analytics and statistics."""
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        cond = "WHERE project_id = ?" if project_id else ""
        params = [project_id] if project_id else []

        total = conn.execute(f"SELECT COUNT(*) FROM tm_tasks {cond}", params).fetchone()[0]
        completed = conn.execute(
            f"SELECT COUNT(*) FROM tm_tasks {cond} {'AND' if cond else 'WHERE'} status = 'completed'",
            params
        ).fetchone()[0]
        avg_quality = conn.execute(
            f"SELECT AVG(quality_score) FROM tm_tasks {cond} {'AND' if cond else 'WHERE'} quality_score > 0",
            params
        ).fetchone()[0] or 0

        # Role distribution
        roles = {}
        for row in conn.execute(
            f"SELECT assigned_role, COUNT(*) FROM tm_tasks {cond} GROUP BY assigned_role",
            params
        ):
            if row[0]:
                roles[row[0]] = row[1]

        # Priority distribution
        priorities = {}
        for row in conn.execute(
            f"SELECT priority, COUNT(*) FROM tm_tasks {cond} GROUP BY priority",
            params
        ):
            priorities[row[0]] = row[1]

        conn.close()

        completion_rate = (completed / total * 100) if total > 0 else 0

        return {
            "total_tasks": total,
            "completed": completed,
            "completion_rate": round(completion_rate, 1),
            "avg_quality": round(avg_quality, 4),
            "role_distribution": roles,
            "priority_distribution": priorities,
        }

    # ── Status ────────────────────────────────────────────

    def get_status(self) -> dict:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        status_counts = {}
        for row in conn.execute("SELECT status, COUNT(*) FROM tm_tasks GROUP BY status"):
            status_counts[row[0]] = row[1]
        total = conn.execute("SELECT COUNT(*) FROM tm_tasks").fetchone()[0]
        conn.close()

        return {
            "total_tasks": total,
            "status_counts": status_counts,
            "task_count": self._task_count,
        }


# ═══════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════

def _self_test():
    import shutil
    import tempfile

    print("=" * 60)
    print("Task Manager — Self Test")
    print("=" * 60)

    tmp = tempfile.mkdtemp()
    tm = TaskManager(db_path=str(Path(tmp) / "test_tm.db"))

    # 1. Create tasks
    t1 = tm.create_task("Design ad campaign", priority="high", project_id="marketing",
                        assigned_role="ROLE-Q05", tags=["marketing", "ads"])
    t2 = tm.create_task("API security audit", priority="urgent", project_id="dev",
                        assigned_role="ROLE-Q06", tags=["security"])
    t3 = tm.create_task("Write blog post", project_id="marketing",
                        dependencies=[t1.task_id])
    assert t1.task_id.startswith("T-")
    print("  [1] Task creation: 3 tasks ✅")

    # 2. Status updates
    tm.update_status(t1.task_id, "in_progress")
    tm.update_status(t1.task_id, "completed", result_summary="Campaign designed", quality_score=0.85)
    task = tm.get_task(t1.task_id)
    assert task["status"] == "completed"
    assert task["quality_score"] == 0.85
    print("  [2] Status lifecycle: pending→in_progress→completed ✅")

    # 3. Skills tracking
    tm.add_skill_used(t2.task_id, "security_audit")
    tm.add_skill_used(t2.task_id, "vulnerability_scan")
    task2 = tm.get_task(t2.task_id)
    assert len(task2["skills_used"]) == 2
    print(f"  [3] Skills tracking: {task2['skills_used']} ✅")

    # 4. Board view
    board = tm.get_board(project_id="marketing")
    assert board["total"] >= 2
    print(f"  [4] Task board: {board['total']} tasks, {board['active']} active ✅")

    # 5. Auto-create from engine result
    mock_result = {
        "routing": {"role_code": "ROLE-Q01", "family": "qcm", "confidence": 0.9},
        "response": "Here is the analysis result...",
        "metadata": {"knowledge_relevance": 0.75},
    }
    auto_task = tm.create_from_engine_result("分析项目数据", mock_result, project_id="dev")
    assert auto_task.task_id.startswith("T-")
    auto = tm.get_task(auto_task.task_id)
    assert auto["status"] == "completed"
    print(f"  [5] Auto-create from engine: {auto_task.task_id} ✅")

    # 6. Analytics
    analytics = tm.get_analytics()
    assert analytics["total_tasks"] == 4
    assert analytics["completion_rate"] > 0
    print(f"  [6] Analytics: {analytics['total_tasks']} tasks, {analytics['completion_rate']}% complete ✅")

    # 7. Status
    status = tm.get_status()
    assert status["total_tasks"] == 4
    print(f"  [7] Status: {status['status_counts']} ✅")

    shutil.rmtree(tmp, ignore_errors=True)

    print("=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
    return True


if __name__ == "__main__":
    _self_test()
