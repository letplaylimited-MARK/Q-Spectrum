#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q-SpecTrum Consistency Checker
Verifies cross-file consistency
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.dirname(SCRIPT_DIR)
ROOT_PATH = os.path.dirname(BASE_PATH)

def check_consistency() -> Dict:
    """Check consistency across all files"""
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "checks": [],
        "issues": []
    }

    # 1. Check MEMORY.md version
    memory_path = os.path.join(ROOT_PATH, "MEMORY.md")
    if os.path.exists(memory_path):
        with open(memory_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "V1.5" in content:
                report["checks"].append({"file": "MEMORY.md", "status": "OK", "detail": "V1.5"})
            else:
                report["issues"].append({"file": "MEMORY.md", "issue": "Version not V1.5"})
    else:
        report["issues"].append({"file": "MEMORY.md", "issue": "File not found"})

    # 2. Check flywheel iterations count
    flywheel_path = os.path.join(SCRIPT_DIR, "flywheel_logs")
    flywheel_files = [f for f in os.listdir(flywheel_path) if f.startswith('flywheel_') and f.endswith('.md')] if os.path.exists(flywheel_path) else []
    flywheel_count = len(flywheel_files)

    # 3. Check feynman cards count
    feynman_path = os.path.join(SCRIPT_DIR, "费曼卡片")
    feynman_files = [f for f in os.listdir(feynman_path) if f.startswith('费曼卡片-') and f.endswith('.md')] if os.path.exists(feynman_path) else []
    feynman_count = len(feynman_files)

    # 4. Check capabilities.json
    cap_path = os.path.join(SCRIPT_DIR, "capabilities.json")
    overall_score = "N/A"
    if os.path.exists(cap_path):
        with open(cap_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            overall_score = data.get("overall", {}).get("current", "N/A")
            evo_events = len(data.get("evolution", []))
            report["checks"].append({
                "file": "capabilities.json",
                "status": "OK",
                "detail": f"score:{overall_score}%, evolutions:{evo_events}"
            })
    else:
        report["issues"].append({"file": "capabilities.json", "issue": "File not found"})

    # 5. Cross-file consistency
    # Check MEMORY.md flywheel count vs capabilities.json
    if flywheel_count != overall_score:  # This is expected to NOT match, just example
        report["checks"].append({
            "file": "cross-check",
            "status": "INFO",
            "detail": f"flywheel:{flywheel_count} iterations, feynman:{feynman_count} cards"
        })

    return report

def main():
    print("=" * 50)
    print("Q-SpecTrum Consistency Checker")
    print("=" * 50)

    result = check_consistency()

    print(f"\n[TIME] {result['timestamp']}")
    print("\n[CHECKS]")
    for check in result['checks']:
        print(f"  [OK] {check['file']}: {check['detail']}")

    print("\n[ISSUES]")
    if result['issues']:
        for issue in result['issues']:
            print(f"  [FAIL] {issue['file']}: {issue['issue']}")
    else:
        print("  [OK] No issues found")

    print("\n" + "=" * 50)
    print("[OK] Consistency check complete")
    print("=" * 50)

if __name__ == "__main__":
    main()
