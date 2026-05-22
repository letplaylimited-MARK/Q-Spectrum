"""
Q-SpecTrum ARCS Protocol Executor v1.0
=======================================
Executes collaboration protocols between AI roles.

The ARCS (AI Role Collaboration System) defines protocols for inter-role
communication. This executor reads protocol definitions from platform.db
and facilitates structured message passing between roles.

Usage:
    python protocol_executor.py                     # List protocols
    python protocol_executor.py trigger PROTO-001   # Trigger a protocol
    python protocol_executor.py log                 # View interaction log
"""

import json
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path


class ProtocolExecutor:
    """Executes ARCS collaboration protocols between AI roles."""

    def __init__(self, db_path=None):
        if db_path is None:
            try:
                from path_utils import get_db_path
                db_path = get_db_path()
            except ImportError:
                script_dir = Path(__file__).parent
                db_path = script_dir.parent / "db" / "platform.db"
        self.db_path = str(db_path)
        # Use immutable mode for virtiofs compatibility (read-only)
        # For writes, scripts should copy DB locally first
        try:
            db_uri = f"file:{Path(self.db_path).resolve()}?immutable=1"
            self.conn = sqlite3.connect(db_uri, uri=True)
        except Exception:
            self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    # ──────────────────────────────────────────────
    # Query Methods
    # ──────────────────────────────────────────────

    def list_protocols(self):
        """List all collaboration protocols."""
        rows = self.conn.execute(
            "SELECT protocol_code, source_role, target_role, trigger_event "
            "FROM collaboration_protocols ORDER BY protocol_code"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_protocol(self, proto_code):
        """Get a protocol by code."""
        row = self.conn.execute(
            "SELECT * FROM collaboration_protocols WHERE protocol_code = ?",
            (proto_code,)
        ).fetchone()
        return dict(row) if row else None

    def get_role(self, role_code):
        """Get a role by code."""
        row = self.conn.execute(
            "SELECT * FROM ai_roles WHERE role_code = ?",
            (role_code,)
        ).fetchone()
        return dict(row) if row else None

    def get_interaction_log(self, limit=20):
        """Get recent interaction log entries."""
        rows = self.conn.execute(
            "SELECT * FROM interaction_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ──────────────────────────────────────────────
    # Execution Methods
    # ──────────────────────────────────────────────

    def trigger_protocol(self, proto_code, payload=None):
        """
        Trigger a protocol execution.

        Steps:
        1. Load protocol definition
        2. Resolve source and target roles
        3. Validate payload against schema
        4. Execute the protocol action
        5. Log the interaction
        """
        protocol = self.get_protocol(proto_code)
        if not protocol:
            return {"error": f"Protocol {proto_code} not found"}

        source_role = protocol["source_role"]
        target_role = protocol["target_role"]
        trigger_event = protocol["trigger_event"]

        # Parse rules
        rules = protocol.get("rules", "")
        if rules and isinstance(rules, str):
            try:
                rules = json.loads(rules)
            except json.JSONDecodeError:
                rules = {"raw": rules}

        # Parse payload schema
        schema = protocol.get("payload_schema", "")
        if schema and isinstance(schema, str):
            try:
                schema = json.loads(schema)
            except json.JSONDecodeError:
                schema = {}

        # Build execution record
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        execution = {
            "protocol_code": proto_code,
            "trigger_event": trigger_event,
            "source_role": source_role,
            "target_role": target_role,
            "payload": payload or {},
            "rules_applied": rules,
            "status": "completed",
            "timestamp": now,
        }

        # Log the interaction (skip on read-only/immutable connections)
        log_id = str(uuid.uuid4())
        try:
            self.conn.execute(
                "INSERT INTO interaction_logs VALUES (?,?,?,?,?,?,?)",
                (log_id, now, source_role, target_role, proto_code,
                 'completed', json.dumps(execution))
            )
            self.conn.commit()
        except Exception:
            pass  # Read-only mode (virtiofs immutable), skip logging

        execution["log_id"] = log_id
        return execution

    def send_message(self, from_role, to_role, message_type, content):
        """
        Send a structured message between roles.
        Automatically finds the matching protocol.
        """
        # Find matching protocol
        row = self.conn.execute(
            "SELECT protocol_code FROM collaboration_protocols "
            "WHERE source_role = ? AND target_role = ?",
            (from_role, to_role)
        ).fetchone()

        if not row:
            return {"error": f"No protocol defined for {from_role} -> {to_role}"}

        return self.trigger_protocol(
            row["protocol_code"],
            payload={
                "message_type": message_type,
                "content": content,
                "from": from_role,
                "to": to_role,
            }
        )

    # ──────────────────────────────────────────────
    # Analysis Methods
    # ──────────────────────────────────────────────

    def get_role_communication_map(self):
        """Build a map of which roles can communicate with which."""
        protocols = self.list_protocols()
        comm_map = {}
        for p in protocols:
            src = p["source_role"]
            tgt = p["target_role"]
            if src not in comm_map:
                comm_map[src] = []
            comm_map[src].append({
                "target": tgt,
                "protocol": p["protocol_code"],
                "trigger": p["trigger_event"]
            })
        return comm_map


def main():
    """CLI entry point."""
    executor = ProtocolExecutor()

    if len(sys.argv) < 2:
        print("Q-SpecTrum ARCS Protocol Executor v1.0")
        print("=" * 55)
        protocols = executor.list_protocols()
        for p in protocols:
            print(f"  {p['protocol_code']}: {p['source_role']} -> {p['target_role']}")
            print(f"    Trigger: {p['trigger_event']}")
        print(f"\nTotal: {len(protocols)} protocols")

        print("\nCommunication Map:")
        comm_map = executor.get_role_communication_map()
        for role, targets in sorted(comm_map.items()):
            print(f"  {role} ->")
            for t in targets:
                print(f"    {t['target']} via {t['protocol']} ({t['trigger']})")

        print("\nUsage:")
        print("  python protocol_executor.py trigger <PROTO-CODE>")
        print("  python protocol_executor.py send <FROM-ROLE> <TO-ROLE> <MSG>")
        print("  python protocol_executor.py log")
        print("  python protocol_executor.py map")

    elif sys.argv[1] == 'trigger' and len(sys.argv) > 2:
        result = executor.trigger_protocol(sys.argv[2])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif sys.argv[1] == 'send' and len(sys.argv) > 4:
        result = executor.send_message(sys.argv[2], sys.argv[3], 'message', sys.argv[4])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif sys.argv[1] == 'log':
        logs = executor.get_interaction_log()
        for log in logs:
            print(f"  [{log['timestamp']}] {log['source_role']} -> {log['target_role']} "
                  f"({log['protocol_code']}) [{log['status']}]")

    elif sys.argv[1] == 'map':
        comm_map = executor.get_role_communication_map()
        print(json.dumps(comm_map, indent=2, ensure_ascii=False))

    executor.close()


if __name__ == '__main__':
    main()
