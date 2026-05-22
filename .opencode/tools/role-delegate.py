#!/usr/bin/env python3
"""
role-delegate: Load the instructions for a given role
Usage: python role-delegate.py <ROLE_CODE>
Returns the role's instructions and capabilities
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.resolve()
DB_PATH = ROOT / "AI项目管理/Platform/db/platform.db"
AGENTS_DIR = ROOT / ".opencode/agents"

if len(sys.argv) < 2:
    print(json.dumps({"error": "Usage: role-delegate.py <ROLE_CODE (e.g. ROLE-T01)>"}))
    sys.exit(1)

role_code = sys.argv[1].upper()
agent_file = AGENTS_DIR / f"{role_code.replace('-', '-')}*.yaml"

try:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM ai_roles WHERE role_code = ?", (role_code,))
    row = cursor.fetchone()
    conn.close()

    if row:
        result = dict(row)
        result["capabilities_list"] = json.loads(result.get("capabilities", "[]"))
        # Find agent definition file
        agent_files = list(AGENTS_DIR.glob(f"{role_code.replace('-', '-')}*.yaml"))
        agent_files += list(AGENTS_DIR.glob(f"{role_code}*.yaml"))
        result["agent_file"] = str(agent_files[0]) if agent_files else None
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": f"Role {role_code} not found"}))
        sys.exit(1)
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
