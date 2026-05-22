#!/usr/bin/env python3
"""
Knowledge Graph — 21 operators + 19 edge labels.
NetworkX in-memory + SQLite persistence layer.
"""
import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path

# ─── 24 智能算子 (Intelligent Operators) ───────────────────────
PERCEPTION_OPS = {
    "P01": "intent_parse",       # 意圖解析
    "P02": "code_understand",    # 程式碼理解
    "P03": "knowledge_retrieve", # 知識檢索
    "P04": "global_search",      # 全域搜索
    "P05": "web_research",       # 網路調研
}
DECISION_OPS = {
    "D01": "role_route",         # 角色路由
    "D02": "risk_assess",        # 風險評估
    "D03": "arch_review",        # 架構審查
    "D04": "task_decompose",     # 任務分解
    "D05": "resource_alloc",     # 資源分配
}
EXECUTION_OPS = {
    "E01": "file_edit",          # 檔案編輯
    "E02": "cmd_exec",           # 指令執行
    "E03": "sql_query",          # SQL 查詢
    "E04": "git_operate",        # Git 操作
    "E05": "knowledge_deposit",  # 知識沉澱
    "E06": "notify_send",        # 通知發送
    "E07": "workflow_schedule",  # 工作流調度
    "E08": "code_generate",      # 程式碼生成
}
EVALUATION_OPS = {
    "V01": "code_review",        # 代碼審查
    "V02": "loop_feedback",      # 閉環反饋
    "V03": "semantic_consist",   # 語義一致性
}

ALL_OPS = {}
for d in (PERCEPTION_OPS, DECISION_OPS, EXECUTION_OPS, EVALUATION_OPS):
    ALL_OPS.update(d)

OP_FAMILIES = {
    "perception": list(PERCEPTION_OPS.keys()),
    "decision": list(DECISION_OPS.keys()),
    "execution": list(EXECUTION_OPS.keys()),
    "evaluation": list(EVALUATION_OPS.keys()),
}

# ─── 19 邊標籤 (Edge Labels) ──────────────────────────────────
EDGE_LABELS = {
    # Control flow
    "SEQ": "sequential",
    "PAR": "parallel",
    "CON": "conditional",
    "LOOP": "loop",
    # Data flow
    "ctx": "context",
    "mem": "memory",
    "ref": "reference",
    "sig": "signal",
    # Permission
    "auth:admin": "admin_only",
    "auth:review": "review_required",
    "auth:exec": "executable",
    # Resource
    "dep": "depends_on",
    "lock": "mutex_lock",
    "pool": "resource_pool",
    # Semantic
    "causal": "causes",
    "implements": "implements",
    "delegates": "delegates_to",
    "triggers": "triggers",
    "belongs_to": "belongs_to",
}

class KnowledgeGraph:
    """Knowledge Graph: NetworkX in-memory + SQLite persistence."""

    def __init__(self, db_path=None):
        self._nx = None
        self._db_path = db_path or str(Path(__file__).parent / "knowledge_graph.db")
        self._conn = None
        self._lock = threading.Lock()
        self._ensure_networkx()
        self._ensure_db()
        self._load_from_db()

    def _ensure_networkx(self):
        try:
            import networkx as nx
            self._nx = nx
        except ImportError:
            raise ImportError("NetworkX is required: pip install networkx")

    def _ensure_db(self):
        self._conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id TEXT PRIMARY KEY,
                op_code TEXT,
                label TEXT,
                node_type TEXT DEFAULT 'operator',
                metadata TEXT DEFAULT '{}',
                created_at REAL,
                updated_at REAL
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS graph_edges (
                id TEXT PRIMARY KEY,
                source TEXT,
                target TEXT,
                label TEXT,
                weight REAL DEFAULT 1.0,
                metadata TEXT DEFAULT '{}',
                created_at REAL,
                FOREIGN KEY(source) REFERENCES graph_nodes(id),
                FOREIGN KEY(target) REFERENCES graph_nodes(id)
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target)
        """)
        self._conn.commit()
        self._seed_default_nodes()

    def _seed_default_nodes(self):
        count = self._conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
        if count > 0:
            return
        now = time.time()
        for code, label in ALL_OPS.items():
            family = "unknown"
            for fname, codes in OP_FAMILIES.items():
                if code in codes:
                    family = fname
                    break
            nid = f"op_{code}"
            self._conn.execute(
                "INSERT INTO graph_nodes (id, op_code, label, node_type, metadata, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                (nid, code, label, "operator", json.dumps({"family": family}), now, now)
            )
        self._conn.commit()
        self._nx_graph = None  # force reload

    def _load_from_db(self):
        self._nx_graph = self._nx.DiGraph()
        rows = self._conn.execute("SELECT * FROM graph_nodes").fetchall()
        for r in rows:
            meta = json.loads(r["metadata"]) if r["metadata"] else {}
            self._nx_graph.add_node(
                r["id"], op_code=r["op_code"], label=r["label"],
                node_type=r["node_type"], **meta
            )
        edges = self._conn.execute("SELECT * FROM graph_edges").fetchall()
        for e in edges:
            meta = json.loads(e["metadata"]) if e["metadata"] else {}
            self._nx_graph.add_edge(
                e["source"], e["target"],
                label=e["label"], weight=e["weight"], **meta
            )

    def _save(self):
        pass  # Already saved synchronously in mutation methods

    # ─── Node Operations ────────────────────────────────────────

    def add_knowledge_node(self, node_id, label, node_type="knowledge", metadata=None):
        now = time.time()
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        self._conn.execute(
            "INSERT OR REPLACE INTO graph_nodes (id, op_code, label, node_type, metadata, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (node_id, "", label, node_type, meta_str, now, now)
        )
        self._conn.commit()
        self._load_from_db()
        return node_id

    def add_concept_node(self, concept, metadata=None):
        nid = f"concept_{hashlib.md5(concept.encode()).hexdigest()[:12]}"
        return self.add_knowledge_node(nid, concept, "concept", metadata)

    # ─── Edge Operations ────────────────────────────────────────

    def add_edge(self, source, target, label="SEQ", weight=1.0, metadata=None):
        if label not in EDGE_LABELS:
            valid = list(EDGE_LABELS.keys())
            raise ValueError(f"Invalid edge label '{label}'. Valid: {valid}")
        now = time.time()
        eid = f"e_{hashlib.md5(f'{source}:{target}:{label}'.encode()).hexdigest()[:12]}"
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        self._conn.execute(
            "INSERT OR REPLACE INTO graph_edges (id, source, target, label, weight, metadata, created_at) VALUES (?,?,?,?,?,?,?)",
            (eid, source, target, label, weight, meta_str, now)
        )
        self._conn.commit()
        self._load_from_db()
        return eid

    def connect_chain(self, node_ids, label="SEQ"):
        """Connect a chain of nodes: n1→n2→n3→..."""
        eids = []
        for i in range(len(node_ids) - 1):
            eid = self.add_edge(node_ids[i], node_ids[i + 1], label)
            eids.append(eid)
        return eids

    # ─── Query Operations ───────────────────────────────────────

    def query(self, op_code=None, node_type=None, label=None, limit=50):
        """Query nodes; if op_code given, filter operators by code."""
        if self._nx_graph is None:
            return []
        nodes = list(self._nx_graph.nodes(data=True))
        results = []
        for nid, data in nodes:
            if op_code and data.get("op_code") != op_code:
                continue
            if node_type and data.get("node_type") != node_type:
                continue
            results.append({"id": nid, **data})
            if len(results) >= limit:
                break
        return results

    def trace(self, start_node, max_depth=10):
        """Trace forward from a node following edges."""
        if self._nx_graph is None or not self._nx_graph.has_node(start_node):
            return []
        visited = set()
        path = []

        def _dfs(node, depth):
            if depth > max_depth or node in visited:
                return
            visited.add(node)
            path.append(node)
            for _, succ, edata in self._nx_graph.out_edges(node, data=True):
                _dfs(succ, depth + 1)

        _dfs(start_node, 0)
        return path

    def path(self, source, target):
        """Find shortest path between two nodes."""
        try:
            p = self._nx.shortest_path(self._nx_graph, source, target)
            return p
        except (self._nx.NetworkXNoPath, self._nx.NodeNotFound):
            return None

    def subgraph(self, node_ids):
        """Extract subgraph containing the given nodes and their connections."""
        if self._nx_graph is None:
            return {"nodes": [], "edges": []}
        sg = self._nx_graph.subgraph(node_ids)
        nodes = [{"id": n, **d} for n, d in sg.nodes(data=True)]
        edges = [{"source": u, "target": v, **d} for u, v, d in sg.edges(data=True)]
        return {"nodes": nodes, "edges": edges}

    def neighbors(self, node_id, direction="both"):
        """Get neighbors of a node."""
        if self._nx_graph is None or not self._nx_graph.has_node(node_id):
            return []
        if direction == "in":
            return list(self._nx_graph.predecessors(node_id))
        elif direction == "out":
            return list(self._nx_graph.successors(node_id))
        else:
            return list(self._nx_graph.neighbors(node_id))

    # ─── Statistics ─────────────────────────────────────────────

    def stats(self):
        if self._nx_graph is None:
            return {"error": "graph not loaded"}
        with self._lock:
            node_types = {}
            edge_labels = {}
            for _, d in self._nx_graph.nodes(data=True):
                nt = d.get("node_type", "unknown")
                node_types[nt] = node_types.get(nt, 0) + 1
            for _, _, d in self._nx_graph.edges(data=True):
                el = d.get("label", "unknown")
                edge_labels[el] = edge_labels.get(el, 0) + 1
            return {
                "nodes": self._nx_graph.number_of_nodes(),
                "edges": self._nx_graph.number_of_edges(),
                "operators": sum(1 for _, d in self._nx_graph.nodes(data=True) if d.get("node_type") == "operator"),
                "node_types": node_types,
                "edge_labels": edge_labels,
            }

    def close(self):
        if self._conn:
            self._conn.close()
