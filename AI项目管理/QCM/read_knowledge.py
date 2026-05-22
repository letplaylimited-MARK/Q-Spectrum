#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q-SpecTrum Knowledge Reader
Reads and displays knowledge graph, feynman cards, and memory
"""

import json
import os
import re
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.dirname(SCRIPT_DIR)
ROOT_PATH = os.path.dirname(BASE_PATH)

def read_knowledge_graph():
    """Read knowledge graph - 增强版"""
    kg_path = os.path.join(SCRIPT_DIR, "knowledge_graph.md")
    if not os.path.exists(kg_path):
        return {"status": "NOT_FOUND", "content": None}

    try:
        with open(kg_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

    version = "V1.1"
    nodes = 35
    edges = 58

    lines = content.split('\n')
    for i, line in enumerate(lines[:20]):
        if '**版本**' in line or 'Version' in line:
            match = re.search(r'V(\d+\.\d+)', line)
            if match:
                version = f"V{match.group(1)}"
        if '核心概念' in line:
            match = re.search(r'(\d+)个', line)
            if match:
                nodes = int(match.group(1))
        if '连接数' in line or '边' in line:
            match = re.search(r'(\d+)条', line)
            if match:
                edges = int(match.group(1))

    return {
        "status": "OK",
        "version": version,
        "nodes": nodes,
        "edges": edges,
        "path": kg_path
    }

def read_feynman_cards():
    """Read all feynman cards - 增强版"""
    feynman_path = os.path.join(SCRIPT_DIR, "费曼卡片")
    if not os.path.exists(feynman_path):
        return {"status": "NOT_FOUND", "cards": []}

    try:
        files = sorted([f for f in os.listdir(feynman_path) if f.endswith('.md')])
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

    cards = []
    for f in files:
        match = re.search(r'费曼卡片-(\d+)-(.+)\.md', f)
        if match:
            num = int(match.group(1))
            title = match.group(2).strip()
            cards.append({
                "num": num,
                "file": f,
                "title": title
            })

    return {
        "status": "OK",
        "count": len(cards),
        "cards": sorted(cards, key=lambda x: x['num']),
        "path": feynman_path
    }

def read_feynman_card_content(card_num):
    """Read specific feynman card content"""
    feynman_path = os.path.join(SCRIPT_DIR, "费曼卡片")
    card_file = os.path.join(feynman_path, f"费曼卡片-{card_num:03d}-*.md")

    files = [f for f in os.listdir(feynman_path) if f.startswith(f"费曼卡片-{card_num:03d}-")]
    if not files:
        return {"status": "NOT_FOUND", "card": card_num}

    try:
        with open(os.path.join(feynman_path, files[0]), 'r', encoding='utf-8') as f:
            content = f.read()
        return {"status": "OK", "content": content, "file": files[0]}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

def read_memory():
    """Read MEMORY.md - 增强版"""
    memory_path = os.path.join(ROOT_PATH, "MEMORY.md")
    if not os.path.exists(memory_path):
        return {"status": "NOT_FOUND", "path": None}

    try:
        with open(memory_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

    version = "V1.5"
    lines = content.split('\n')

    for line in lines[:10]:
        if '**最后更新**' in line:
            match = re.search(r'V(\d+\.\d+)', line)
            if match:
                version = f"V{match.group(1)}"

    flywheel_path = os.path.join(SCRIPT_DIR, "flywheel_logs")
    flywheel_count = 0
    if os.path.exists(flywheel_path):
        flywheel_count = len([f for f in os.listdir(flywheel_path) if f.startswith('flywheel_') and f.endswith('.md')])

    feynman_path = os.path.join(SCRIPT_DIR, "费曼卡片")
    feynman_count = 0
    if os.path.exists(feynman_path):
        feynman_count = len([f for f in os.listdir(feynman_path) if f.endswith('.md')])

    return {
        "status": "OK",
        "version": version,
        "flywheel_count": flywheel_count,
        "feynman_count": feynman_count,
        "path": memory_path
    }

def read_capabilities():
    """Read capabilities.json - 增强版"""
    cap_path = os.path.join(SCRIPT_DIR, "capabilities.json")
    if not os.path.exists(cap_path):
        return {"status": "NOT_FOUND", "content": None}

    try:
        with open(cap_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

    return {
        "status": "OK",
        "version": data.get("version", "Unknown"),
        "score": data.get("overall", {}).get("current", 0),
        "target": data.get("overall", {}).get("target", 0),
        "dimensions": len(data.get("dimensions", [])),
        "path": cap_path
    }

def get_all_knowledge():
    """Get all knowledge - 统一入口"""
    return {
        "knowledge_graph": read_knowledge_graph(),
        "feynman_cards": read_feynman_cards(),
        "memory": read_memory(),
        "capabilities": read_capabilities()
    }

def main():
    print("=" * 60)
    print("Q-SpecTrum Knowledge Reader")
    print("=" * 60)

    kb = get_all_knowledge()

    kg = kb["knowledge_graph"]
    print("\n[1] KNOWLEDGE GRAPH")
    print(f"    Status: {kg['status']}")
    if kg['status'] == 'OK':
        print(f"    Version: {kg['version']}")
        print(f"    Nodes: {kg['nodes']}")
        print(f"    Edges: {kg['edges']}")

    fc = kb["feynman_cards"]
    print("\n[2] FEYNMAN CARDS")
    print(f"    Status: {fc['status']}")
    if fc['status'] == 'OK':
        print(f"    Count: {fc['count']}")
        for card in fc['cards'][:3]:
            print(f"    - #{card['num']} {card['title']}")
        if fc['count'] > 3:
            print(f"    ... and {fc['count'] - 3} more")

    mem = kb["memory"]
    print("\n[3] MEMORY")
    print(f"    Status: {mem['status']}")
    if mem['status'] == 'OK':
        print(f"    Version: {mem['version']}")
        print(f"    Flywheel: {mem['flywheel_count']}")
        print(f"    Feynman: {mem['feynman_count']}")

    cap = kb["capabilities"]
    print("\n[4] CAPABILITIES")
    print(f"    Status: {cap['status']}")
    if cap['status'] == 'OK':
        print(f"    Score: {cap['score']}% / {cap['target']}%")
        print(f"    Dimensions: {cap['dimensions']}")

    print("\n" + "=" * 60)
    print("[OK] Knowledge reading complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
