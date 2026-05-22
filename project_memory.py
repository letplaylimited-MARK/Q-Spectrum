"""
Q-SpecTrum Project Memory Isolation & Chatroom Switching v1.0
=============================================================
Implements Point #19: Multi-project memory isolation with chatroom switching.

Architecture:
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  │  Project-A   │   │  Project-B   │   │  Project-C   │
  │ ┌──────────┐ │   │ ┌──────────┐ │   │ ┌──────────┐ │
  │ │Chatroom-1│ │   │ │Chatroom-1│ │   │ │Chatroom-1│ │
  │ │Chatroom-2│ │   │ │Chatroom-2│ │   │              │
  │ └──────────┘ │   │ └──────────┘ │   │ └──────────┘ │
  │  Memory Pool │   │  Memory Pool │   │  Memory Pool │
  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
         │                  │                  │
         └──────────┬───────┴──────────────────┘
              Global Memory Index (cross-project search)

Each project owns:
  - Conversation history (per chatroom)
  - Knowledge deposits (isolated)
  - Role usage patterns
  - Context window state
  - Session metadata

Chatrooms within a project:
  - Default chatroom for general discussion
  - Focused chatrooms for specific topics/roles
  - Each chatroom maintains its own conversation history
  - All chatrooms share the project's knowledge pool
"""

import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("q-spectrum.project-memory")


# ═══════════════════════════════════════════════════════════
# 1. DATA MODELS
# ═══════════════════════════════════════════════════════════

@dataclass
class ChatMessage:
    """A single message in a chatroom conversation."""
    message_id: str
    chatroom_id: str
    project_id: str
    role: str  # "user" | role_code (e.g. "ROLE-Q01")
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Chatroom:
    """A chatroom within a project — isolated conversation space."""
    chatroom_id: str
    project_id: str
    name: str
    description: str = ""
    created_at: float = field(default_factory=time.time)
    status: str = "active"  # active | archived | paused
    mode: str = "discuss"   # discuss | sandbox | debate
    pinned_roles: List[str] = field(default_factory=list)
    message_count: int = 0
    last_activity: float = 0.0


@dataclass
class ProjectMemoryState:
    """Complete memory state for a project."""
    project_id: str
    name: str
    active_chatroom: str = "default"
    chatrooms: Dict[str, Chatroom] = field(default_factory=dict)
    context_summary: str = ""  # Rolling summary of project context
    role_affinity: Dict[str, float] = field(default_factory=dict)  # role → usage weight
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    total_messages: int = 0
    total_knowledge: int = 0


# ═══════════════════════════════════════════════════════════
# 2. PROJECT MEMORY MANAGER
# ═══════════════════════════════════════════════════════════

class ProjectMemoryManager:
    """
    Central memory manager for multi-project isolation.

    Responsibilities:
    - Create/switch projects with isolated memory
    - Manage chatrooms within each project
    - Store/retrieve conversation history per chatroom
    - Maintain per-project context summaries
    - Provide cross-project search capability
    - Handle project archival and memory cleanup
    """

    def __init__(self, db_path: str = None):
        self._db_path = db_path or str(
            Path(__file__).parent / "project_memory.db"
        )
        self._projects: Dict[str, ProjectMemoryState] = {}
        self._active_project: str = "default"
        self._active_chatroom: str = "default"
        self._init_db()
        self._load_projects()

    def _init_db(self):
        """Initialize the project memory database."""
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.executescript("""
            -- Projects table
            CREATE TABLE IF NOT EXISTS pm_projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                context_summary TEXT DEFAULT '',
                role_affinity TEXT DEFAULT '{}',
                tags TEXT DEFAULT '[]',
                created_at REAL,
                status TEXT DEFAULT 'active',
                total_messages INTEGER DEFAULT 0,
                total_knowledge INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            );

            -- Chatrooms within projects
            CREATE TABLE IF NOT EXISTS pm_chatrooms (
                chatroom_id TEXT,
                project_id TEXT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                mode TEXT DEFAULT 'discuss',
                pinned_roles TEXT DEFAULT '[]',
                created_at REAL,
                status TEXT DEFAULT 'active',
                message_count INTEGER DEFAULT 0,
                last_activity REAL DEFAULT 0,
                PRIMARY KEY (chatroom_id, project_id),
                FOREIGN KEY (project_id) REFERENCES pm_projects(project_id)
            );

            -- Conversation messages (per chatroom, per project)
            CREATE TABLE IF NOT EXISTS pm_messages (
                message_id TEXT PRIMARY KEY,
                chatroom_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (project_id) REFERENCES pm_projects(project_id)
            );

            -- Per-project knowledge snapshots (lightweight pointer to knowledge_pipeline)
            CREATE TABLE IF NOT EXISTS pm_knowledge_refs (
                ref_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                deposit_id TEXT NOT NULL,
                knowledge_type TEXT,
                summary TEXT,
                timestamp REAL,
                relevance REAL DEFAULT 0.5,
                FOREIGN KEY (project_id) REFERENCES pm_projects(project_id)
            );

            -- Context window snapshots (for resumption)
            CREATE TABLE IF NOT EXISTS pm_context_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                chatroom_id TEXT NOT NULL,
                snapshot_type TEXT DEFAULT 'auto',
                context_data TEXT NOT NULL,
                timestamp REAL,
                FOREIGN KEY (project_id) REFERENCES pm_projects(project_id)
            );

            -- Indexes for fast queries
            CREATE INDEX IF NOT EXISTS idx_pm_msg_project
                ON pm_messages(project_id, chatroom_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_pm_msg_role
                ON pm_messages(role, project_id);
            CREATE INDEX IF NOT EXISTS idx_pm_kr_project
                ON pm_knowledge_refs(project_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_pm_chatroom_project
                ON pm_chatrooms(project_id, status);
        """)

        # Ensure default project + default chatroom exist
        conn.execute("""
            INSERT OR IGNORE INTO pm_projects
            (project_id, name, description, created_at)
            VALUES (?, ?, ?, ?)
        """, ("default", "Default Project", "Auto-created default workspace", time.time()))

        conn.execute("""
            INSERT OR IGNORE INTO pm_chatrooms
            (chatroom_id, project_id, name, description, created_at, mode)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("default", "default", "General", "Default chatroom", time.time(), "discuss"))

        conn.commit()
        conn.close()

    def _load_projects(self):
        """Load all projects and chatrooms from database."""
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)

        # Load projects
        for row in conn.execute("SELECT * FROM pm_projects WHERE status != 'deleted'"):
            pid = row[0]
            state = ProjectMemoryState(
                project_id=pid,
                name=row[1],
                context_summary=row[3] or "",
                role_affinity=json.loads(row[4]) if row[4] else {},
                tags=json.loads(row[5]) if row[5] else [],
                created_at=row[6] or time.time(),
                total_messages=row[8] or 0,
                total_knowledge=row[9] or 0,
            )
            self._projects[pid] = state

        # Load chatrooms for each project
        for row in conn.execute("SELECT * FROM pm_chatrooms WHERE status != 'deleted'"):
            cid, pid = row[0], row[1]
            chatroom = Chatroom(
                chatroom_id=cid,
                project_id=pid,
                name=row[2],
                description=row[3] or "",
                mode=row[4] or "discuss",
                pinned_roles=json.loads(row[5]) if row[5] else [],
                created_at=row[6] or time.time(),
                status=row[7] or "active",
                message_count=row[8] or 0,
                last_activity=row[9] or 0.0,
            )
            if pid in self._projects:
                self._projects[pid].chatrooms[cid] = chatroom

        conn.close()
        logger.info(
            f"ProjectMemory loaded: {len(self._projects)} projects, "
            f"{sum(len(p.chatrooms) for p in self._projects.values())} chatrooms"
        )

    # ── Project Management ────────────────────────────────

    def create_project(self, project_id: str, name: str,
                       description: str = "", tags: List[str] = None) -> ProjectMemoryState:
        """Create a new project with its own memory space."""
        if project_id in self._projects:
            return self._projects[project_id]

        now = time.time()
        state = ProjectMemoryState(
            project_id=project_id,
            name=name,
            tags=tags or [],
            created_at=now,
        )

        # Create default chatroom for the project
        default_chatroom = Chatroom(
            chatroom_id="default",
            project_id=project_id,
            name="General",
            description=f"Default chatroom for {name}",
            created_at=now,
        )
        state.chatrooms["default"] = default_chatroom
        state.active_chatroom = "default"

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("""
            INSERT OR REPLACE INTO pm_projects
            (project_id, name, description, tags, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (project_id, name, description, json.dumps(tags or []), now))

        conn.execute("""
            INSERT OR REPLACE INTO pm_chatrooms
            (chatroom_id, project_id, name, description, created_at, mode)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("default", project_id, "General", f"Default chatroom for {name}", now, "discuss"))

        conn.commit()
        conn.close()

        self._projects[project_id] = state
        logger.info(f"Project created: {project_id} ({name})")
        return state

    def switch_project(self, project_id: str) -> Optional[ProjectMemoryState]:
        """Switch active project. Returns the new project state or None."""
        if project_id not in self._projects:
            return None

        # Save current context snapshot before switching
        self._save_context_snapshot()

        self._active_project = project_id
        state = self._projects[project_id]
        self._active_chatroom = state.active_chatroom

        logger.info(f"Switched to project: {project_id} ({state.name}), chatroom: {self._active_chatroom}")
        return state

    def get_project(self, project_id: str = None) -> Optional[ProjectMemoryState]:
        """Get a project state. If None, returns active project."""
        pid = project_id or self._active_project
        return self._projects.get(pid)

    def list_projects(self) -> List[dict]:
        """List all projects with summary info."""
        result = []
        for p in self._projects.values():
            result.append({
                "project_id": p.project_id,
                "name": p.name,
                "active": p.project_id == self._active_project,
                "chatroom_count": len(p.chatrooms),
                "active_chatroom": p.active_chatroom,
                "total_messages": p.total_messages,
                "total_knowledge": p.total_knowledge,
                "tags": p.tags,
                "created_at": p.created_at,
                "context_summary": p.context_summary[:200] if p.context_summary else "",
            })
        return sorted(result, key=lambda x: x["created_at"], reverse=True)

    def archive_project(self, project_id: str) -> bool:
        """Archive a project (soft delete — preserves data)."""
        if project_id not in self._projects or project_id == "default":
            return False

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute(
            "UPDATE pm_projects SET status = 'archived' WHERE project_id = ?",
            (project_id,)
        )
        conn.commit()
        conn.close()

        # If archiving active project, switch to default
        if self._active_project == project_id:
            self._active_project = "default"
            self._active_chatroom = "default"

        del self._projects[project_id]
        return True

    # ── Chatroom Management ───────────────────────────────

    def create_chatroom(self, name: str, project_id: str = None,
                        mode: str = "discuss", description: str = "",
                        pinned_roles: List[str] = None) -> Chatroom:
        """Create a new chatroom within a project."""
        pid = project_id or self._active_project
        project = self._projects.get(pid)
        if not project:
            raise ValueError(f"Project not found: {pid}")

        # Generate chatroom ID
        cid = f"cr-{hashlib.sha256(f'{pid}-{name}-{time.time()}'.encode()).hexdigest()[:12]}"

        chatroom = Chatroom(
            chatroom_id=cid,
            project_id=pid,
            name=name,
            description=description,
            mode=mode,
            pinned_roles=pinned_roles or [],
            created_at=time.time(),
        )

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("""
            INSERT INTO pm_chatrooms
            (chatroom_id, project_id, name, description, mode, pinned_roles, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cid, pid, name, description, mode,
              json.dumps(pinned_roles or []), chatroom.created_at))
        conn.commit()
        conn.close()

        project.chatrooms[cid] = chatroom
        logger.info(f"Chatroom created: {cid} ({name}) in project {pid}, mode={mode}")
        return chatroom

    def switch_chatroom(self, chatroom_id: str, project_id: str = None) -> Optional[Chatroom]:
        """Switch active chatroom within a project."""
        pid = project_id or self._active_project
        project = self._projects.get(pid)
        if not project or chatroom_id not in project.chatrooms:
            return None

        project.active_chatroom = chatroom_id
        self._active_chatroom = chatroom_id
        return project.chatrooms[chatroom_id]

    def list_chatrooms(self, project_id: str = None) -> List[dict]:
        """List all chatrooms for a project."""
        pid = project_id or self._active_project
        project = self._projects.get(pid)
        if not project:
            return []

        return [
            {
                "chatroom_id": c.chatroom_id,
                "name": c.name,
                "description": c.description,
                "mode": c.mode,
                "active": c.chatroom_id == project.active_chatroom,
                "pinned_roles": c.pinned_roles,
                "message_count": c.message_count,
                "last_activity": c.last_activity,
                "status": c.status,
            }
            for c in project.chatrooms.values()
            if c.status != "deleted"
        ]

    def archive_chatroom(self, chatroom_id: str, project_id: str = None) -> bool:
        """Archive a chatroom."""
        pid = project_id or self._active_project
        project = self._projects.get(pid)
        if not project or chatroom_id not in project.chatrooms:
            return False
        if chatroom_id == "default":
            return False  # Cannot archive default chatroom

        project.chatrooms[chatroom_id].status = "archived"
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute(
            "UPDATE pm_chatrooms SET status = 'archived' WHERE chatroom_id = ? AND project_id = ?",
            (chatroom_id, pid)
        )
        conn.commit()
        conn.close()

        if project.active_chatroom == chatroom_id:
            project.active_chatroom = "default"
            self._active_chatroom = "default"

        return True

    # ── Message Management ────────────────────────────────

    def add_message(self, role: str, content: str,
                    chatroom_id: str = None, project_id: str = None,
                    metadata: dict = None) -> ChatMessage:
        """Add a message to a chatroom's conversation history."""
        pid = project_id or self._active_project
        cid = chatroom_id or self._active_chatroom
        now = time.time()

        msg_id = f"msg-{hashlib.sha256(f'{pid}-{cid}-{now}-{role}'.encode()).hexdigest()[:16]}"

        msg = ChatMessage(
            message_id=msg_id,
            chatroom_id=cid,
            project_id=pid,
            role=role,
            content=content,
            timestamp=now,
            metadata=metadata or {},
        )

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("""
            INSERT INTO pm_messages
            (message_id, chatroom_id, project_id, role, content, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (msg_id, cid, pid, role, content, now, json.dumps(metadata or {})))

        # Update chatroom stats
        conn.execute("""
            UPDATE pm_chatrooms
            SET message_count = message_count + 1, last_activity = ?
            WHERE chatroom_id = ? AND project_id = ?
        """, (now, cid, pid))

        # Update project stats
        conn.execute("""
            UPDATE pm_projects
            SET total_messages = total_messages + 1
            WHERE project_id = ?
        """, (pid,))

        conn.commit()
        conn.close()

        # Update in-memory state
        project = self._projects.get(pid)
        if project:
            project.total_messages += 1
            chatroom = project.chatrooms.get(cid)
            if chatroom:
                chatroom.message_count += 1
                chatroom.last_activity = now

            # Update role affinity
            if role != "user":
                project.role_affinity[role] = project.role_affinity.get(role, 0) + 1.0

        return msg

    def get_history(self, chatroom_id: str = None, project_id: str = None,
                    limit: int = 50, offset: int = 0) -> List[dict]:
        """Get conversation history for a chatroom."""
        pid = project_id or self._active_project
        cid = chatroom_id or self._active_chatroom

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        rows = conn.execute("""
            SELECT message_id, role, content, timestamp, metadata
            FROM pm_messages
            WHERE chatroom_id = ? AND project_id = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (cid, pid, limit, offset)).fetchall()
        conn.close()

        return [
            {
                "id": r[0],
                "role": r[1],
                "content": r[2],
                "timestamp": r[3],
                "metadata": json.loads(r[4]) if r[4] else {},
            }
            for r in reversed(rows)  # Return in chronological order
        ]

    def get_context_window(self, chatroom_id: str = None,
                           project_id: str = None,
                           max_messages: int = 20) -> List[dict]:
        """
        Get the recent context window for LLM consumption.
        Returns messages formatted for system prompt injection.
        """
        history = self.get_history(chatroom_id, project_id, limit=max_messages)
        return [
            {"role": m["role"], "content": m["content"]}
            for m in history
        ]

    def search_messages(self, query: str, project_id: str = None,
                        limit: int = 20) -> List[dict]:
        """Search messages within a project (or cross-project if project_id is None)."""
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)

        if project_id:
            rows = conn.execute("""
                SELECT m.message_id, m.chatroom_id, m.project_id, m.role,
                       m.content, m.timestamp, c.name as chatroom_name
                FROM pm_messages m
                LEFT JOIN pm_chatrooms c ON m.chatroom_id = c.chatroom_id
                    AND m.project_id = c.project_id
                WHERE m.project_id = ? AND m.content LIKE ?
                ORDER BY m.timestamp DESC LIMIT ?
            """, (project_id, f"%{query}%", limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT m.message_id, m.chatroom_id, m.project_id, m.role,
                       m.content, m.timestamp, c.name as chatroom_name
                FROM pm_messages m
                LEFT JOIN pm_chatrooms c ON m.chatroom_id = c.chatroom_id
                    AND m.project_id = c.project_id
                WHERE m.content LIKE ?
                ORDER BY m.timestamp DESC LIMIT ?
            """, (f"%{query}%", limit)).fetchall()

        conn.close()

        return [
            {
                "id": r[0], "chatroom_id": r[1], "project_id": r[2],
                "role": r[3], "content": r[4][:300], "timestamp": r[5],
                "chatroom_name": r[6] or "Unknown",
            }
            for r in rows
        ]

    # ── Knowledge Isolation ───────────────────────────────

    def add_knowledge_ref(self, deposit_id: str, knowledge_type: str,
                          summary: str, relevance: float = 0.5,
                          project_id: str = None) -> str:
        """Link a knowledge deposit to a project for isolation tracking."""
        pid = project_id or self._active_project
        ref_id = f"kr-{pid[:8]}-{deposit_id}"

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("""
            INSERT OR REPLACE INTO pm_knowledge_refs
            (ref_id, project_id, deposit_id, knowledge_type, summary, timestamp, relevance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ref_id, pid, deposit_id, knowledge_type, summary[:500], time.time(), relevance))

        conn.execute("""
            UPDATE pm_projects SET total_knowledge = total_knowledge + 1
            WHERE project_id = ?
        """, (pid,))
        conn.commit()
        conn.close()

        project = self._projects.get(pid)
        if project:
            project.total_knowledge += 1

        return ref_id

    def get_project_knowledge(self, project_id: str = None,
                              knowledge_type: str = None,
                              limit: int = 30) -> List[dict]:
        """Get knowledge deposits specific to a project."""
        pid = project_id or self._active_project
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)

        if knowledge_type:
            rows = conn.execute("""
                SELECT ref_id, deposit_id, knowledge_type, summary, timestamp, relevance
                FROM pm_knowledge_refs
                WHERE project_id = ? AND knowledge_type = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (pid, knowledge_type, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT ref_id, deposit_id, knowledge_type, summary, timestamp, relevance
                FROM pm_knowledge_refs
                WHERE project_id = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (pid, limit)).fetchall()

        conn.close()
        return [
            {"ref_id": r[0], "deposit_id": r[1], "type": r[2],
             "summary": r[3], "timestamp": r[4], "relevance": r[5]}
            for r in rows
        ]

    # ── Context Snapshots ─────────────────────────────────

    def _save_context_snapshot(self):
        """Save current context before switching projects/chatrooms."""
        pid = self._active_project
        cid = self._active_chatroom

        # Get recent messages as context
        recent = self.get_history(cid, pid, limit=10)
        if not recent:
            return

        snapshot_id = f"snap-{pid}-{cid}-{int(time.time())}"
        context_data = json.dumps({
            "project_id": pid,
            "chatroom_id": cid,
            "messages": recent,
            "timestamp": time.time(),
        })

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("""
            INSERT OR REPLACE INTO pm_context_snapshots
            (snapshot_id, project_id, chatroom_id, snapshot_type, context_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (snapshot_id, pid, cid, "auto", context_data, time.time()))
        conn.commit()
        conn.close()

    def get_latest_snapshot(self, project_id: str = None,
                            chatroom_id: str = None) -> Optional[dict]:
        """Get the most recent context snapshot for resumption."""
        pid = project_id or self._active_project
        cid = chatroom_id or self._active_chatroom

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        row = conn.execute("""
            SELECT snapshot_id, context_data, timestamp
            FROM pm_context_snapshots
            WHERE project_id = ? AND chatroom_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (pid, cid)).fetchone()
        conn.close()

        if row:
            return {
                "snapshot_id": row[0],
                "data": json.loads(row[1]),
                "timestamp": row[2],
            }
        return None

    # ── Context Summary (Rolling) ─────────────────────────

    def update_context_summary(self, summary: str, project_id: str = None):
        """Update the rolling context summary for a project."""
        pid = project_id or self._active_project
        project = self._projects.get(pid)
        if project:
            project.context_summary = summary

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute(
            "UPDATE pm_projects SET context_summary = ? WHERE project_id = ?",
            (summary[:5000], pid)
        )
        conn.commit()
        conn.close()

    # ── Properties ────────────────────────────────────────

    @property
    def active_project_id(self) -> str:
        return self._active_project

    @property
    def active_chatroom_id(self) -> str:
        return self._active_chatroom

    @property
    def active_project(self) -> Optional[ProjectMemoryState]:
        return self._projects.get(self._active_project)

    # ── Status ────────────────────────────────────────────

    def get_status(self) -> dict:
        """Full memory system status."""
        total_chatrooms = sum(len(p.chatrooms) for p in self._projects.values())
        total_messages = sum(p.total_messages for p in self._projects.values())
        total_knowledge = sum(p.total_knowledge for p in self._projects.values())

        return {
            "active_project": self._active_project,
            "active_chatroom": self._active_chatroom,
            "projects_count": len(self._projects),
            "total_chatrooms": total_chatrooms,
            "total_messages": total_messages,
            "total_knowledge": total_knowledge,
            "projects": [
                {
                    "id": p.project_id,
                    "name": p.name,
                    "active": p.project_id == self._active_project,
                    "chatrooms": len(p.chatrooms),
                    "messages": p.total_messages,
                    "knowledge": p.total_knowledge,
                }
                for p in self._projects.values()
            ],
        }


# ═══════════════════════════════════════════════════════════
# 3. CHATROOM SESSION CONTROLLER
# ═══════════════════════════════════════════════════════════

class ChatroomSessionController:
    """
    High-level controller that bridges ProjectMemoryManager
    with the QSpectrumEngine.

    Handles:
    - Pre-process: inject project context into engine input
    - Post-process: store results in project memory
    - Project/chatroom switching with context preservation
    - Role affinity tracking per project
    """

    def __init__(self, memory_manager: ProjectMemoryManager):
        self.memory = memory_manager
        self._switch_history: List[dict] = []

    def pre_process(self, user_input: str, context: dict = None) -> dict:
        """
        Prepare context for engine processing.
        Injects project-specific context and chatroom history.
        """
        context = context or {}

        pid = self.memory.active_project_id
        cid = self.memory.active_chatroom_id

        # Inject project context
        context["project_id"] = pid
        context["chatroom_id"] = cid

        # Get recent history for this chatroom
        recent = self.memory.get_context_window(cid, pid, max_messages=10)
        if recent:
            context["chatroom_history"] = recent

        # Get project's role affinity for routing hints
        project = self.memory.active_project
        if project and project.role_affinity:
            context["role_affinity"] = project.role_affinity

        # Get project context summary
        if project and project.context_summary:
            context["project_context"] = project.context_summary

        # Store user message
        self.memory.add_message(
            role="user",
            content=user_input,
            chatroom_id=cid,
            project_id=pid,
        )

        return context

    def post_process(self, user_input: str, result: dict):
        """
        Store engine results in project memory.
        Called after engine.process() completes.
        """
        pid = self.memory.active_project_id
        cid = self.memory.active_chatroom_id

        routing = result.get("routing", {})
        response = result.get("response", "")
        role_code = routing.get("role_code", "ROLE-Q01")

        # Store AI response
        self.memory.add_message(
            role=role_code,
            content=response,
            chatroom_id=cid,
            project_id=pid,
            metadata={
                "family": routing.get("family", ""),
                "role_name": routing.get("role_name", ""),
                "confidence": routing.get("confidence", 0),
            },
        )

        # If knowledge was deposited, link it to project
        kp_info = result.get("knowledge_pipeline")
        if kp_info and kp_info.get("deposit_id"):
            self.memory.add_knowledge_ref(
                deposit_id=kp_info["deposit_id"],
                knowledge_type=kp_info.get("knowledge_type", "episodic"),
                summary=response[:200],
                relevance=kp_info.get("relevance", 0.5),
                project_id=pid,
            )

    def switch_project(self, project_id: str) -> dict:
        """Switch project with full context handoff."""
        old_pid = self.memory.active_project_id
        old_cid = self.memory.active_chatroom_id

        state = self.memory.switch_project(project_id)
        if not state:
            return {"success": False, "error": f"Project not found: {project_id}"}

        self._switch_history.append({
            "from_project": old_pid,
            "from_chatroom": old_cid,
            "to_project": project_id,
            "to_chatroom": state.active_chatroom,
            "timestamp": time.time(),
        })

        return {
            "success": True,
            "project": {
                "id": state.project_id,
                "name": state.name,
                "chatroom_count": len(state.chatrooms),
                "active_chatroom": state.active_chatroom,
                "total_messages": state.total_messages,
                "context_summary": state.context_summary[:300],
            },
            "recent_history": self.memory.get_history(
                state.active_chatroom, project_id, limit=5
            ),
        }

    def switch_chatroom(self, chatroom_id: str) -> dict:
        """Switch chatroom within current project."""
        old_cid = self.memory.active_chatroom_id

        chatroom = self.memory.switch_chatroom(chatroom_id)
        if not chatroom:
            return {"success": False, "error": f"Chatroom not found: {chatroom_id}"}

        self._switch_history.append({
            "from_chatroom": old_cid,
            "to_chatroom": chatroom_id,
            "project": self.memory.active_project_id,
            "timestamp": time.time(),
        })

        return {
            "success": True,
            "chatroom": {
                "id": chatroom.chatroom_id,
                "name": chatroom.name,
                "mode": chatroom.mode,
                "message_count": chatroom.message_count,
                "pinned_roles": chatroom.pinned_roles,
            },
            "recent_history": self.memory.get_history(
                chatroom_id, limit=10
            ),
        }

    def get_status(self) -> dict:
        """Combined status of memory + session controller."""
        mem_status = self.memory.get_status()
        mem_status["switch_history_count"] = len(self._switch_history)
        mem_status["recent_switches"] = self._switch_history[-5:]
        return mem_status


# ═══════════════════════════════════════════════════════════
# 4. SELF-TEST
# ═══════════════════════════════════════════════════════════

def _self_test():
    """Verify project memory isolation works correctly."""
    import tempfile
    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "test_pm.db")

    print("=" * 60)
    print("Project Memory Isolation — Self Test")
    print("=" * 60)

    # 1. Create manager
    mgr = ProjectMemoryManager(db_path=db_path)
    assert "default" in mgr._projects, "Default project should exist"
    print("  [1] Default project created ✅")

    # 2. Create projects
    p1 = mgr.create_project("proj-alpha", "Alpha Marketing", tags=["marketing", "ads"])
    p2 = mgr.create_project("proj-beta", "Beta Development", tags=["dev", "api"])
    assert len(mgr.list_projects()) == 3  # default + alpha + beta
    print("  [2] Multi-project creation ✅")

    # 3. Add messages to different projects
    mgr.switch_project("proj-alpha")
    mgr.add_message("user", "Design a new ad campaign")
    mgr.add_message("ROLE-Q05", "Here's my ad strategy...")
    mgr.add_message("user", "What about the budget?")

    mgr.switch_project("proj-beta")
    mgr.add_message("user", "Review the API architecture")
    mgr.add_message("ROLE-S01", "Here's my architecture review...")

    # 4. Verify isolation
    alpha_history = mgr.get_history(project_id="proj-alpha")
    beta_history = mgr.get_history(project_id="proj-beta")
    assert len(alpha_history) == 3, f"Alpha should have 3 messages, got {len(alpha_history)}"
    assert len(beta_history) == 2, f"Beta should have 2 messages, got {len(beta_history)}"
    assert "ad campaign" in alpha_history[0]["content"]
    assert "API architecture" in beta_history[0]["content"]
    print("  [3] Memory isolation verified ✅")

    # 5. Chatroom management
    cr = mgr.create_chatroom("Budget Discussion", project_id="proj-alpha", mode="debate")
    mgr.switch_project("proj-alpha")
    mgr.switch_chatroom(cr.chatroom_id)
    mgr.add_message("user", "Let's debate the budget allocation")
    mgr.add_message("ROLE-Q03", "I suggest 60% on digital...")

    budget_history = mgr.get_history(cr.chatroom_id, "proj-alpha")
    default_history = mgr.get_history("default", "proj-alpha")
    assert len(budget_history) == 2, f"Budget chatroom should have 2 messages, got {len(budget_history)}"
    assert len(default_history) == 3, "Default chatroom should still have 3 messages"
    print("  [4] Chatroom isolation verified ✅")

    # 6. Cross-project search
    results = mgr.search_messages("budget")
    assert len(results) >= 2, "Should find 'budget' in both chatrooms"
    print("  [5] Cross-project search ✅")

    # 7. Knowledge refs
    mgr.add_knowledge_ref("KD-000001", "strategic", "Ad campaign analysis", project_id="proj-alpha")
    mgr.add_knowledge_ref("KD-000002", "architectural", "API design patterns", project_id="proj-beta")
    alpha_k = mgr.get_project_knowledge("proj-alpha")
    beta_k = mgr.get_project_knowledge("proj-beta")
    assert len(alpha_k) == 1 and alpha_k[0]["type"] == "strategic"
    assert len(beta_k) == 1 and beta_k[0]["type"] == "architectural"
    print("  [6] Knowledge isolation per project ✅")

    # 8. Session controller
    ctrl = ChatroomSessionController(mgr)
    ctx = ctrl.pre_process("Test message")
    assert ctx["project_id"] == "proj-alpha"
    assert "chatroom_history" in ctx
    print("  [7] Session controller pre-process ✅")

    # 9. Project switching with context
    result = ctrl.switch_project("proj-beta")
    assert result["success"]
    assert result["project"]["name"] == "Beta Development"
    print("  [8] Project switching with context ✅")

    # 10. Status
    status = ctrl.get_status()
    assert status["projects_count"] == 3
    assert status["active_project"] == "proj-beta"
    print("  [9] Status reporting ✅")

    # Cleanup
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    print("=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
    return True


if __name__ == "__main__":
    _self_test()
