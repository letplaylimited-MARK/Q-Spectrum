#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q-SpecTrum Session Start Self-Check Engine
Runs on every session start
"""

import json
import os
import sys
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Path: script is in QCM/, go up 2 levels to root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.dirname(SCRIPT_DIR)
ROOT_PATH = os.path.dirname(BASE_PATH)

def scan_system_status():
    """Scan system status"""
    status = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "checks": {}
    }

    # 1. Check MEMORY.md (root)
    memory_path = os.path.join(ROOT_PATH, "MEMORY.md")
    if os.path.exists(memory_path):
        with open(memory_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 提取版本号
            if "V1." in content:
                version = content.split("V1.")[1].split(")")[0] if "V1." in content else "未知"
                status["checks"]["memory"] = {"status": "OK", "version": f"V1.{version}"}
            else:
                status["checks"]["memory"] = {"status": "OK", "version": "unknown"}
    else:
        status["checks"]["memory"] = {"status": "MISSING"}

    # 2. Check flywheel logs (in QCM/ folder)
    flywheel_path = os.path.join(SCRIPT_DIR, "flywheel_logs")
    if os.path.exists(flywheel_path):
        files = [f for f in os.listdir(flywheel_path) if f.endswith('.md')]
        status["checks"]["flywheel"] = {"status": "OK", "iterations": len(files)}
    else:
        status["checks"]["flywheel"] = {"status": "NOT_FOUND"}

    # 3. Check feynman cards (in QCM/ folder)
    feynman_path = os.path.join(SCRIPT_DIR, "费曼卡片")
    if os.path.exists(feynman_path):
        files = [f for f in os.listdir(feynman_path) if f.endswith('.md')]
        status["checks"]["feynman"] = {"status": "OK", "cards": len(files)}
    else:
        status["checks"]["feynman"] = {"status": "NOT_FOUND"}

    # 4. Check capabilities.json (in QCM/ folder)
    cap_path = os.path.join(SCRIPT_DIR, "capabilities.json")
    if os.path.exists(cap_path):
        with open(cap_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            status["checks"]["capabilities"] = {
                "status": "OK",
                "overall": data.get("overall", {}).get("current", 0)
            }
    else:
        status["checks"]["capabilities"] = {"status": "NOT_FOUND"}

    # 5. Check knowledge graph (in QCM/ folder)
    kg_path = os.path.join(SCRIPT_DIR, "knowledge_graph.md")
    if os.path.exists(kg_path):
        status["checks"]["knowledge_graph"] = {"status": "OK"}
    else:
        status["checks"]["knowledge_graph"] = {"status": "NOT_FOUND"}

    return status

def run_self_check():
    """运行自检"""
    print("=" * 50)
    print("Q-SpecTrum Session Start Self-Check")
    print("=" * 50)

    status = scan_system_status()

    print(f"\n[TIME] {status['timestamp']}")
    print("\n[SYSTEM CHECK RESULTS]")

    all_ok = True
    for check_name, result in status["checks"].items():
        icon = "[OK]" if result["status"] == "OK" else "[FAIL]"
        info = ""
        if "version" in result:
            info = f" (v{result['version']})"
        elif "iterations" in result:
            info = f" ({result['iterations']} iterations)"
        elif "cards" in result:
            info = f" ({result['cards']} cards)"
        elif "overall" in result:
            info = f" (score: {result['overall']}%)"

        print(f"  {icon} {check_name}: {result['status']}{info}")

        if result["status"] != "OK":
            all_ok = False

    print("\n" + "=" * 50)
    if all_ok:
        print("[OK] System ready!")
    else:
        print("[WARN] Some issues detected")
    print("=" * 50)

    return status

if __name__ == "__main__":
    run_self_check()
