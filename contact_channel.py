"""
Q-SpecTrum Contact Channel v1.0
=================================
Implements Point #20: Customer service, social media, and developer contact scenarios.

Architecture:
  ┌─────────────────────────────────────────────────┐
  │              Contact Channel Hub                 │
  │                                                  │
  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
  │  │  Ticket   │  │Notifica- │  │   Social     │  │
  │  │  System   │  │  tions   │  │   Configs    │  │
  │  └──────────┘  └──────────┘  └──────────────┘  │
  │                                                  │
  │  Types: bug | feature | support | feedback       │
  │         collaboration | developer_contact        │
  │                                                  │
  │  Channels: in_app | email | social | webhook     │
  └─────────────────────────────────────────────────┘

User scenarios:
  - Submit bug reports / feature requests
  - Contact developer for activation keys
  - Manage social media integration configs
  - Receive system notifications
  - Collaboration requests between projects
"""

import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("q-spectrum.contact")


# ═══════════════════════════════════════════════════════════
# 1. ENUMS & DATA MODELS
# ═══════════════════════════════════════════════════════════

class TicketType(str, Enum):
    BUG = "bug"
    FEATURE = "feature"
    SUPPORT = "support"
    FEEDBACK = "feedback"
    COLLABORATION = "collaboration"
    DEVELOPER_CONTACT = "developer_contact"
    ACTIVATION = "activation"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting_response"
    RESOLVED = "resolved"
    CLOSED = "closed"


class NotificationCategory(str, Enum):
    SYSTEM = "system"
    TICKET = "ticket"
    GROWTH = "growth"
    GHOST_CHANNEL = "ghost_channel"
    PROJECT = "project"
    ALERT = "alert"


@dataclass
class Ticket:
    """A support/feedback ticket."""
    ticket_id: str
    type: str
    subject: str
    description: str
    status: str = "open"
    priority: str = "normal"  # low | normal | high | urgent
    project_id: str = "default"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    responses: List[dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Notification:
    """A system notification."""
    notification_id: str
    category: str
    title: str
    message: str
    read: bool = False
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SocialConfig:
    """Social media / contact integration config."""
    platform: str       # wechat | weibo | twitter | email | telegram | discord | custom
    config_type: str    # contact | broadcast | webhook
    endpoint: str       # URL or identifier
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
# 2. CONTACT CHANNEL MANAGER
# ═══════════════════════════════════════════════════════════

class ContactChannel:
    """
    Unified contact, support, and notification system.

    Handles:
    - Ticket creation and lifecycle management
    - System notifications (growth milestones, GC alerts, etc.)
    - Social media / developer contact configurations
    - Auto-responses for common scenarios
    """

    # Pre-built auto-responses for common ticket types
    AUTO_RESPONSES = {
        "activation": {
            "message": (
                "感谢您对 Q-SpecTrum 的关注！\n\n"
                "**激活密钥获取方式:**\n"
                "1. TRIAL (免费体验): 系统自动生成，30天有效\n"
                "2. PRO 版本: 请联系开发者获取专属密钥\n"
                "3. ENTERPRISE: 定制方案，请提供项目需求\n\n"
                "开发者邮箱: developer@qspectrum.ai\n"
                "密钥格式: GC-{TIER}-{16位HASH}"
            ),
            "auto_resolve": False,
        },
        "bug": {
            "message": (
                "感谢您提交 Bug 报告！我们会尽快处理。\n\n"
                "请确保包含以下信息:\n"
                "- 复现步骤\n"
                "- 期望行为 vs 实际行为\n"
                "- 系统环境信息"
            ),
            "auto_resolve": False,
        },
        "support": {
            "message": (
                "收到您的支持请求。AI 伙伴会优先协助您解决问题。\n"
                "如果问题需要人工介入，将自动升级至开发者。"
            ),
            "auto_resolve": False,
        },
    }

    # Developer contact info (configurable)
    DEVELOPER_INFO = {
        "name": "Q-SpecTrum Developer",
        "email": "developer@qspectrum.ai",
        "wechat": "qspectrum_dev",
        "github": "github.com/qspectrum",
        "support_hours": "Mon-Fri 09:00-18:00 (UTC+8)",
    }

    def __init__(self, db_path: str = None):
        self._db_path = db_path or str(
            Path(__file__).parent / "contact_channel.db"
        )
        self._init_db()
        self._ticket_count = 0
        self._notification_count = 0
        self._social_configs: List[SocialConfig] = []
        self._load_counts()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cc_tickets (
                ticket_id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'normal',
                project_id TEXT DEFAULT 'default',
                created_at REAL,
                updated_at REAL,
                responses TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS cc_notifications (
                notification_id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                read INTEGER DEFAULT 0,
                created_at REAL,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS cc_social_configs (
                config_id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                config_type TEXT DEFAULT 'contact',
                endpoint TEXT,
                enabled INTEGER DEFAULT 1,
                metadata TEXT DEFAULT '{}'
            );

            CREATE INDEX IF NOT EXISTS idx_cc_tickets_status
                ON cc_tickets(status, type);
            CREATE INDEX IF NOT EXISTS idx_cc_notif_read
                ON cc_notifications(read, created_at);
        """)
        conn.commit()
        conn.close()

    def _load_counts(self):
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        self._ticket_count = conn.execute("SELECT COUNT(*) FROM cc_tickets").fetchone()[0]
        self._notification_count = conn.execute("SELECT COUNT(*) FROM cc_notifications").fetchone()[0]

        # Load social configs
        for row in conn.execute("SELECT * FROM cc_social_configs"):
            self._social_configs.append(SocialConfig(
                platform=row[1], config_type=row[2], endpoint=row[3],
                enabled=bool(row[4]),
                metadata=json.loads(row[5]) if row[5] else {},
            ))
        conn.close()

    # ── Tickets ──────────────────────────────────────────

    def create_ticket(self, type: str, subject: str, description: str = "",
                      priority: str = "normal", project_id: str = "default",
                      metadata: dict = None) -> Ticket:
        """Create a new support/feedback ticket."""
        self._ticket_count += 1
        tid = f"TK-{self._ticket_count:05d}-{int(time.time()) % 100000}"

        ticket = Ticket(
            ticket_id=tid,
            type=type,
            subject=subject,
            description=description,
            priority=priority,
            project_id=project_id,
            metadata=metadata or {},
        )

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("""
            INSERT INTO cc_tickets
            (ticket_id, type, subject, description, status, priority,
             project_id, created_at, updated_at, responses, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tid, type, subject, description, "open", priority,
              project_id, ticket.created_at, ticket.updated_at,
              "[]", json.dumps(metadata or {})))
        conn.commit()
        conn.close()

        # Auto-response if available
        auto = self.AUTO_RESPONSES.get(type)
        if auto:
            self.add_ticket_response(tid, "system", auto["message"])
            if auto.get("auto_resolve"):
                self.update_ticket_status(tid, "resolved")

        # Create notification
        self.create_notification(
            category="ticket",
            title=f"New {type} ticket: {subject}",
            message=f"Ticket {tid} created with priority {priority}",
            metadata={"ticket_id": tid},
        )

        logger.info(f"Ticket created: {tid} ({type}: {subject})")
        return ticket

    def add_ticket_response(self, ticket_id: str, responder: str,
                            message: str) -> bool:
        """Add a response to a ticket."""
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        row = conn.execute(
            "SELECT responses FROM cc_tickets WHERE ticket_id = ?",
            (ticket_id,)
        ).fetchone()
        if not row:
            conn.close()
            return False

        responses = json.loads(row[0]) if row[0] else []
        responses.append({
            "responder": responder,
            "message": message,
            "timestamp": time.time(),
        })

        conn.execute("""
            UPDATE cc_tickets SET responses = ?, updated_at = ?
            WHERE ticket_id = ?
        """, (json.dumps(responses), time.time(), ticket_id))
        conn.commit()
        conn.close()
        return True

    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("""
            UPDATE cc_tickets SET status = ?, updated_at = ?
            WHERE ticket_id = ?
        """, (status, time.time(), ticket_id))
        affected = conn.execute("SELECT changes()").fetchone()[0]
        conn.commit()
        conn.close()
        return affected > 0

    def get_ticket(self, ticket_id: str) -> Optional[dict]:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        row = conn.execute("SELECT * FROM cc_tickets WHERE ticket_id = ?",
                           (ticket_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return {
            "ticket_id": row[0], "type": row[1], "subject": row[2],
            "description": row[3], "status": row[4], "priority": row[5],
            "project_id": row[6], "created_at": row[7], "updated_at": row[8],
            "responses": json.loads(row[9]) if row[9] else [],
            "metadata": json.loads(row[10]) if row[10] else {},
        }

    def list_tickets(self, status: str = None, type: str = None,
                     project_id: str = None, limit: int = 50) -> List[dict]:
        """List tickets with optional filtering."""
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conditions = []
        params = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if type:
            conditions.append("type = ?")
            params.append(type)
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = conn.execute(
            f"SELECT * FROM cc_tickets {where} ORDER BY created_at DESC LIMIT ?",
            params + [limit]
        ).fetchall()
        conn.close()

        return [
            {
                "ticket_id": r[0], "type": r[1], "subject": r[2],
                "status": r[4], "priority": r[5], "project_id": r[6],
                "created_at": r[7], "response_count": len(json.loads(r[9]) if r[9] else []),
            }
            for r in rows
        ]

    # ── Notifications ─────────────────────────────────────

    def create_notification(self, category: str, title: str, message: str,
                            metadata: dict = None) -> str:
        """Create a system notification."""
        self._notification_count += 1
        nid = f"N-{self._notification_count:06d}"

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("""
            INSERT INTO cc_notifications
            (notification_id, category, title, message, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nid, category, title, message, time.time(), json.dumps(metadata or {})))
        conn.commit()
        conn.close()
        return nid

    def get_notifications(self, unread_only: bool = False,
                          category: str = None,
                          limit: int = 30) -> List[dict]:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conditions = []
        params = []
        if unread_only:
            conditions.append("read = 0")
        if category:
            conditions.append("category = ?")
            params.append(category)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = conn.execute(
            f"SELECT * FROM cc_notifications {where} ORDER BY created_at DESC LIMIT ?",
            params + [limit]
        ).fetchall()
        conn.close()

        return [
            {
                "id": r[0], "category": r[1], "title": r[2],
                "message": r[3], "read": bool(r[4]),
                "created_at": r[5],
                "metadata": json.loads(r[6]) if r[6] else {},
            }
            for r in rows
        ]

    def mark_read(self, notification_id: str) -> bool:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute(
            "UPDATE cc_notifications SET read = 1 WHERE notification_id = ?",
            (notification_id,)
        )
        conn.commit()
        conn.close()
        return True

    def mark_all_read(self) -> int:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("UPDATE cc_notifications SET read = 1 WHERE read = 0")
        count = conn.execute("SELECT changes()").fetchone()[0]
        conn.commit()
        conn.close()
        return count

    def unread_count(self) -> int:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        count = conn.execute(
            "SELECT COUNT(*) FROM cc_notifications WHERE read = 0"
        ).fetchone()[0]
        conn.close()
        return count

    # ── Social / Contact Configs ──────────────────────────

    def add_social_config(self, platform: str, endpoint: str,
                          config_type: str = "contact",
                          metadata: dict = None) -> str:
        cid = f"SC-{platform}-{hashlib.sha256(endpoint.encode()).hexdigest()[:8]}"

        config = SocialConfig(
            platform=platform, config_type=config_type,
            endpoint=endpoint, metadata=metadata or {},
        )

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("""
            INSERT OR REPLACE INTO cc_social_configs
            (config_id, platform, config_type, endpoint, enabled, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cid, platform, config_type, endpoint, 1, json.dumps(metadata or {})))
        conn.commit()
        conn.close()

        self._social_configs.append(config)
        return cid

    def get_social_configs(self) -> List[dict]:
        return [
            {
                "platform": c.platform,
                "type": c.config_type,
                "endpoint": c.endpoint,
                "enabled": c.enabled,
            }
            for c in self._social_configs
        ]

    def get_developer_info(self) -> dict:
        return dict(self.DEVELOPER_INFO)

    # ── AI-Assisted Support ───────────────────────────────

    def detect_support_intent(self, user_input: str) -> Optional[dict]:
        """
        Detect if user input contains a support/contact intent.
        Returns suggested ticket type and extracted info, or None.
        """
        text = user_input.lower()

        # Bug report signals
        bug_signals = ["bug", "错误", "崩溃", "crash", "报错", "异常", "不工作", "broken", "error"]
        if any(s in text for s in bug_signals):
            return {"type": "bug", "priority": "high", "signal": "bug_report"}

        # Feature request
        feature_signals = ["功能", "feature", "建议", "suggest", "希望能", "能不能", "想要"]
        if any(s in text for s in feature_signals):
            return {"type": "feature", "priority": "normal", "signal": "feature_request"}

        # Activation / key request
        key_signals = ["激活", "密钥", "activation", "key", "license", "升级", "pro版", "enterprise"]
        if any(s in text for s in key_signals):
            return {"type": "activation", "priority": "normal", "signal": "activation_request"}

        # Developer contact
        contact_signals = ["联系开发者", "contact developer", "联系客服", "customer service",
                           "人工", "客服", "support"]
        if any(s in text for s in contact_signals):
            return {"type": "developer_contact", "priority": "normal", "signal": "contact_request"}

        # Feedback
        feedback_signals = ["反馈", "feedback", "评价", "review", "体验"]
        if any(s in text for s in feedback_signals):
            return {"type": "feedback", "priority": "low", "signal": "feedback"}

        return None

    # ── Status ────────────────────────────────────────────

    def get_status(self) -> dict:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        open_tickets = conn.execute(
            "SELECT COUNT(*) FROM cc_tickets WHERE status IN ('open', 'in_progress')"
        ).fetchone()[0]
        total_tickets = conn.execute("SELECT COUNT(*) FROM cc_tickets").fetchone()[0]
        unread = conn.execute(
            "SELECT COUNT(*) FROM cc_notifications WHERE read = 0"
        ).fetchone()[0]

        # Type distribution
        types = {}
        for row in conn.execute("SELECT type, COUNT(*) FROM cc_tickets GROUP BY type"):
            types[row[0]] = row[1]

        conn.close()

        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "unread_notifications": unread,
            "ticket_types": types,
            "social_configs": len(self._social_configs),
            "developer_info": self.DEVELOPER_INFO,
        }


# ═══════════════════════════════════════════════════════════
# 3. SELF-TEST
# ═══════════════════════════════════════════════════════════

def _self_test():
    import shutil
    import tempfile

    print("=" * 60)
    print("Contact Channel — Self Test")
    print("=" * 60)

    tmp = tempfile.mkdtemp()
    cc = ContactChannel(db_path=str(Path(tmp) / "test_cc.db"))

    # 1. Create tickets
    t1 = cc.create_ticket("bug", "Login fails on Safari", "Cannot login using Safari browser", priority="high")
    t2 = cc.create_ticket("feature", "Dark mode support", "Add dark theme to chat UI")
    t3 = cc.create_ticket("activation", "Need PRO key", "I need a PRO activation key for my project")
    assert t1.ticket_id.startswith("TK-")
    print("  [1] Ticket creation: 3 tickets ✅")

    # 2. Ticket responses
    assert cc.add_ticket_response(t1.ticket_id, "ROLE-Q01", "We're investigating this issue")
    t1_data = cc.get_ticket(t1.ticket_id)
    assert len(t1_data["responses"]) >= 1  # System auto-response + manual
    print(f"  [2] Ticket responses: {len(t1_data['responses'])} responses ✅")

    # 3. Notifications
    notifs = cc.get_notifications()
    assert len(notifs) >= 3  # One per ticket creation
    unread = cc.unread_count()
    assert unread >= 3
    print(f"  [3] Notifications: {len(notifs)} total, {unread} unread ✅")

    # 4. Mark read
    cc.mark_read(notifs[0]["id"])
    assert cc.unread_count() == unread - 1
    print(f"  [4] Mark read: unread now {cc.unread_count()} ✅")

    # 5. List tickets
    open_tickets = cc.list_tickets(status="open")
    assert len(open_tickets) >= 2
    print(f"  [5] List tickets: {len(open_tickets)} open ✅")

    # 6. Intent detection
    d1 = cc.detect_support_intent("系统崩溃了，打不开")
    assert d1 and d1["type"] == "bug"
    d2 = cc.detect_support_intent("我需要激活密钥")
    assert d2 and d2["type"] == "activation"
    d3 = cc.detect_support_intent("联系客服")
    assert d3 and d3["type"] == "developer_contact"
    d4 = cc.detect_support_intent("今天天气不错")
    assert d4 is None
    print("  [6] Intent detection: 4/4 correct ✅")

    # 7. Social configs
    cc.add_social_config("wechat", "qspectrum_dev", "contact")
    cc.add_social_config("email", "dev@qspectrum.ai", "contact")
    configs = cc.get_social_configs()
    assert len(configs) == 2
    print(f"  [7] Social configs: {len(configs)} ✅")

    # 8. Status
    status = cc.get_status()
    assert status["total_tickets"] == 3
    print(f"  [8] Status: {status['total_tickets']} tickets, {status['unread_notifications']} unread ✅")

    shutil.rmtree(tmp, ignore_errors=True)

    print("=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
    return True


if __name__ == "__main__":
    _self_test()
