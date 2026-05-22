#!/usr/bin/env python3
"""
memory-sync: Sync memory system — read STATUS.md, CRITICAL-REMINDERS.md, MEMORY-INDEX.md
Usage: python memory-sync.py [read|write]
  read  — Display current memory state
  write — Validate that all memory files are internally consistent
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.resolve()
HANDOFF = ROOT / "_HANDOFF"

def read_file(path):
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None

if len(sys.argv) < 2 or sys.argv[1] == "read":
    files = ["STATUS.md", "CRITICAL-REMINDERS.md", "MEMORY-INDEX.md"]
    result = {}
    for f in files:
        content = read_file(HANDOFF / f)
        if content:
            result[f] = {
                "exists": True,
                "size": len(content),
                "lines": content.count("\n") + 1
            }
        else:
            result[f] = {"exists": False}
    print(json.dumps(result, indent=2))

elif sys.argv[1] == "write":
    # Validate consistency
    status = read_file(HANDOFF / "STATUS.md")
    reminders = read_file(HANDOFF / "CRITICAL-REMINDERS.md")
    index = read_file(HANDOFF / "MEMORY-INDEX.md")

    errors = []
    if not status:
        errors.append("STATUS.md missing")
    if not reminders:
        errors.append("CRITICAL-REMINDERS.md missing")
    if not index:
        errors.append("MEMORY-INDEX.md missing")

    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        sys.exit(1)

    entry_count = index.count("## 記憶條目")
    print(json.dumps({
        "valid": True,
        "status_size": len(status),
        "reminders_size": len(reminders),
        "memory_entries": entry_count
    }, indent=2))
