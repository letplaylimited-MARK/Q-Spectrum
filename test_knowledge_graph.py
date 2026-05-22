#!/usr/bin/env python3
"""Test knowledge_graph.py — 21 operators + 19 edges."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from knowledge_graph import EDGE_LABELS, OP_FAMILIES, KnowledgeGraph

errors = []
def check(desc, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
    if not ok:
        errors.append(f"{desc}: {detail}")

db_path = tempfile.mktemp(suffix=".db")
kg = KnowledgeGraph(db_path)

# 1. Default seeding
s = kg.stats()
check("21 operators seeded", s["nodes"] == 21, f"got {s['nodes']}")
check("21 operator type", s["operators"] == 21, f"got {s['operators']}")
check("Node types includes operator", s["node_types"].get("operator", 0) == 21)
check("4 operator families", len(OP_FAMILIES) == 4)
check("19 edge labels", len(EDGE_LABELS) == 19)

# 2. Custom nodes
n1 = kg.add_knowledge_node("doc_001", "Q-SpecTrum Arch", "document", {"path": "docs/arch.md"})
n2 = kg.add_concept_node("Knowledge Graph Pattern")
check("Custom node created", n1 == "doc_001")
check("Concept node created", n2.startswith("concept_"))

# 3. Edges
kg.add_edge("op_P01", "op_D01", "SEQ")
kg.add_edge("op_D01", "op_E01", "SEQ")
kg.add_edge("op_E01", "op_V01", "SEQ")
kg.add_edge("op_P01", n1, "ref")
kg.add_edge(n1, n2, "causal")
s2 = kg.stats()
check("Edges created", s2["edges"] == 5, f"got {s2['edges']}")

# 4. Invalid edge label should raise
try:
    kg.add_edge("op_P01", "op_D01", "INVALID_LABEL")
    check("Invalid label rejected", False, "should have raised")
except ValueError:
    check("Invalid label rejected", True)

# 5. Trace
path = kg.trace("op_P01")
check("Trace from P01 returns nodes", len(path) > 0)
check("Trace includes D01 and E01", "op_D01" in path and "op_E01" in path)

# 6. Shortest path
p = kg.path("op_P01", "op_V01")
check("Path P01→V01 exists", p is not None)
check("Path P01→V01 length", len(p) == 4, f"got {p}")
check("Path correct order", p == ["op_P01", "op_D01", "op_E01", "op_V01"])

# 7. Subgraph
sg = kg.subgraph(["op_P01", "op_D01", "op_E01", n1])
check("Subgraph nodes", len(sg["nodes"]) == 4, f"got {len(sg['nodes'])}")
check("Subgraph edges", len(sg["edges"]) == 3, f"got {len(sg['edges'])}")

# 8. Neighbors
nb = kg.neighbors("op_D01", "in")
check("Neighbors (in) of D01", "op_P01" in nb)
nb2 = kg.neighbors("op_D01", "out")
check("Neighbors (out) of D01", "op_E01" in nb2)

# 9. Query filter
q1 = kg.query(op_code="P01")
check("Query by op_code P01", len(q1) == 1)
q2 = kg.query(node_type="document")
check("Query by node_type document", len(q2) == 1)
q3 = kg.query(node_type="concept")
check("Query by node_type concept", len(q3) == 1)

# 10. Connect chain
chain_ids = [f"chain_{i}" for i in range(5)]
for cid in chain_ids:
    kg.add_knowledge_node(cid, f"Chain Node {cid}")
kg.connect_chain(chain_ids, "SEQ")
s3 = kg.stats()
check("Chain edges created", s3["edges"] == 9, f"got {s3['edges']}")  # 5 new + 5 previous
p2 = kg.path(chain_ids[0], chain_ids[-1])
check("Chain path length", len(p2) == 5)

kg.close()
os.unlink(db_path)

print(f"\n{'='*50}")
if errors:
    print(f"  FAILED: {len(errors)} checks")
    for e in errors:
        print(f"    - {e}")
    sys.exit(1)
else:
    print("  ALL CHECKS PASSED — Knowledge Graph is operational")
    print(f"{'='*50}")
