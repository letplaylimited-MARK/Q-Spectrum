#!/usr/bin/env python3
"""
sandbox-drill: Run a structured 3-perspective sandbox drill
Usage: python sandbox-drill.py <task_description>
Outputs a structured sandbox record
"""
import sys
from datetime import datetime

TEMPLATE = """---
sandbox_drill:
  task: {task}
  timestamp: {timestamp}
  perspectives:
    - name: Q01 開發者
      view: "樂觀 — 如何最快達成目標"
      analysis: |
        (填寫方案)
      risks: []
    - name: Q06 審計員
      view: "悲觀 — 什麼情況下會失敗"
      analysis: |
        (填寫反方意見)
      failure_scenarios: []
    - name: T03 協調官
      view: "中立 — 現實限制下的最佳折衷"
      analysis: |
        (填寫整合意見)
      confidence: "中"
      rationale: ""
  decision: ""
  status: pending
"""

if len(sys.argv) < 2:
    task = input("Enter task description: ")
else:
    task = sys.argv[1]

result = TEMPLATE.format(task=task, timestamp=datetime.now().isoformat())
print(result)
