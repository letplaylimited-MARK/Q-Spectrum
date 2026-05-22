#!/usr/bin/env python3
"""Test vector_store.py — ChromaDB-backed semantic search."""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

errors = []
def check(desc, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
    if not ok:
        errors.append(f"{desc}: {detail}")

tmp_dir = tempfile.mkdtemp()
persist_dir = os.path.join(tmp_dir, "chroma_test")

from vector_store import VectorStore

vs = VectorStore(persist_dir=persist_dir)

# 1. Seeding
c = vs.count()
check("VectorStore seeded from BRAIN-KB", c > 0, f"got {c} entries")
check("BRAIN-KB entries seeded", c >= 5, f"got {c} entries")

# 2. Search
results = vs.search("MCP tools", top_k=3)
check("Semantic search returns results", len(results) > 0, f"got {len(results)}")
if results:
    check("Results have text field", bool(results[0].get("text")), f"got {results[0]}")
    check("Results have metadata", bool(results[0].get("metadata")))

# 3. Add custom entry
vs.add_entry("test_001", "Custom test knowledge entry for Q-SpecTrum verification", {"section": "test"})
check("After add, count increased", vs.count() == c + 1, f"got {vs.count()}")

# 4. Stats
s = vs.stats()
check("Stats has total_entries", s.get("total_entries", 0) > 0)

# Cleanup
shutil.rmtree(tmp_dir, ignore_errors=True)

print(f"\n{'='*50}")
if errors:
    print(f"  FAILED: {len(errors)} checks")
    for e in errors:
        print(f"    - {e}")
    sys.exit(1)
else:
    print("  ALL CHECKS PASSED — Vector Store is operational")
    print(f"{'='*50}")
