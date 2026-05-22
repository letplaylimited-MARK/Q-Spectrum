#!/usr/bin/env python3
"""
verify-health: Run the full integration verification
Usage: python verify-health.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.resolve()
VERIFY_SCRIPT = ROOT / "verify-integration.py"

if not VERIFY_SCRIPT.exists():
    print(f"Error: {VERIFY_SCRIPT} not found")
    sys.exit(1)

result = subprocess.run(
    [sys.executable, str(VERIFY_SCRIPT)],
    capture_output=True, text=True, cwd=str(ROOT)
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)
sys.exit(result.returncode)
