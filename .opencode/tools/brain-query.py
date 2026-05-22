#!/usr/bin/env python3
"""
brain-query: Query the 智脑 SQLite knowledge base
Usage: python brain-query.py <sql_query>
Returns query results as JSON
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.resolve()
DB_PATH = ROOT / "AI项目管理/Platform/db/platform.db"

if len(sys.argv) < 2:
    print(json.dumps({"error": "Usage: brain-query.py <SQL_QUERY>"}))
    sys.exit(1)

query = sys.argv[1]
try:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(query)
    rows = [dict(row) for row in cursor.fetchall()]
    print(json.dumps({"rows": rows, "count": len(rows)}, ensure_ascii=False, indent=2))
    conn.close()
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
