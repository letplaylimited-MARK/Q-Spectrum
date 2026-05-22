"""McpRouter — auto-discovers and routes MCP tools through CapabilityRegistry."""

from typing import Dict, List

# Module-level tool defs (shared with qspectrum_mcp_server for backward compat)
_TOOL_DEFS = [
            {"name": "get_status", "description": "Get Q-SpecTrum engine system status",
             "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_roles", "description": "List all AI roles by family",
             "inputSchema": {"type": "object", "properties": {
                 "family": {"type": "string", "description": "Filter by family: trum, spec, qcm"}}}},
            {"name": "get_role", "description": "Get details for a specific role",
             "inputSchema": {"type": "object", "properties": {
                 "role_code": {"type": "string", "description": "e.g. ROLE-T01"}},
              "required": ["role_code"]}},
            {"name": "query_knowledge", "description": "Search knowledge base",
             "inputSchema": {"type": "object", "properties": {
                 "query": {"type": "string", "description": "Search query"}},
              "required": ["query"]}},
            {"name": "execute_chat", "description": "Send a message to the engine chat",
             "inputSchema": {"type": "object", "properties": {
                 "message": {"type": "string", "description": "User message"}},
              "required": ["message"]}},
            {"name": "get_history", "description": "Get conversation history",
             "inputSchema": {"type": "object", "properties": {
                 "limit": {"type": "integer", "description": "Max messages"}}}},
            {"name": "get_protocols", "description": "Get collaboration protocols",
             "inputSchema": {"type": "object", "properties": {}}},
            {"name": "query_database", "description": "Execute read-only SQL query on platform.db",
             "inputSchema": {"type": "object", "properties": {
                 "sql": {"type": "string", "description": "SELECT SQL query"}},
              "required": ["sql"]}},
            {"name": "graph_query", "description": "Query knowledge graph: filter by op_code, node_type, or label",
             "inputSchema": {"type": "object", "properties": {
                 "op_code": {"type": "string", "description": "Operator code filter (e.g. P01, D01, E01, V01)"},
                 "node_type": {"type": "string", "description": "Node type filter: operator, knowledge, concept"}}}},
            {"name": "graph_trace", "description": "Trace forward from a graph node following edges",
             "inputSchema": {"type": "object", "properties": {
                 "node_id": {"type": "string", "description": "Starting node ID (e.g. op_P01)"},
                 "max_depth": {"type": "integer", "description": "Max traversal depth (default 10)"}},
              "required": ["node_id"]}},
            {"name": "graph_connect", "description": "Add an edge between two graph nodes",
             "inputSchema": {"type": "object", "properties": {
                 "source": {"type": "string", "description": "Source node ID"},
                 "target": {"type": "string", "description": "Target node ID"},
                 "label": {"type": "string", "description": "Edge label: SEQ/PAR/CON/LOOP/ctx/mem/ref/sig/dep/causal/triggers/belongs_to"},
                 "weight": {"type": "number", "description": "Edge weight (default 1.0)"}},
              "required": ["source", "target"]}},
            {"name": "graph_path", "description": "Find shortest path between two graph nodes",
             "inputSchema": {"type": "object", "properties": {
                 "source": {"type": "string", "description": "Source node ID"},
                 "target": {"type": "string", "description": "Target node ID"}},
              "required": ["source", "target"]}},
            {"name": "graph_stats", "description": "Get knowledge graph statistics",
             "inputSchema": {"type": "object", "properties": {}}},
            {"name": "vector_search", "description": "Semantic search over BRAIN-KB vector store",
             "inputSchema": {"type": "object", "properties": {
                 "query": {"type": "string", "description": "Search query"},
                 "top_k": {"type": "integer", "description": "Max results (default 5)"}},
              "required": ["query"]}},
            {"name": "vector_stats", "description": "Get vector store statistics",
             "inputSchema": {"type": "object", "properties": {}}},
            {"name": "search_all", "description": "Unified search across graph + vector store + knowledge resonance",
             "inputSchema": {"type": "object", "properties": {
                 "query": {"type": "string", "description": "Search query"}},
              "required": ["query"]}},
            {"name": "knowledge_stats", "description": "Get KnowledgeResonance statistics",
             "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_workflows", "description": "List available engine workflows",
             "inputSchema": {"type": "object", "properties": {}}},
        ]


class McpRouter:
    """Bridges engine capabilities to MCP tool calls via CapabilityRegistry."""

    def __init__(self, engine, provider_name: str = "mock"):
        self.engine = engine
        self.provider_name = provider_name
        self._status = engine.get_system_status()
        self._cap_registry = None
        self._tool_defs = list(_TOOL_DEFS)
        self._register_handlers()

    # ── Tool Handlers ──

    def _handle_get_status(self, **kw):
        return {"status": "ok", "engine": self._status.get("engine"),
                "roles": self._status.get("roles_loaded"), "provider": self.provider_name}

    def _handle_get_roles(self, family=None, **kw):
        db = getattr(self.engine, 'db', None)
        if not db:
            return {"error": "DB not available"}
        if family:
            roles = db.get_roles_by_family(family)
        else:
            roles = db.get_all_roles()
        if isinstance(roles, dict):
            roles = list(roles.values())
        return {"roles": roles, "count": len(roles)}

    def _handle_get_role(self, role_code=None, **kw):
        db = getattr(self.engine, 'db', None)
        if not db:
            return {"error": "DB not available"}
        role = db.get_role(role_code)
        if not role:
            return {"error": f"Role {role_code} not found"}
        return {"role": role}

    def _handle_query_knowledge(self, query=None, **kw):
        try:
            return {"results": self.engine.search_knowledge(query)}
        except Exception as e:
            return {"error": str(e)}

    def _handle_execute_chat(self, message=None, **kw):
        try:
            return {"response": self.engine.handle_message(message)}
        except Exception as e:
            return {"error": str(e)}

    def _handle_get_history(self, limit=10, **kw):
        try:
            history = getattr(self.engine, 'session_history', [])
            return {"history": history[-int(limit):]}
        except Exception as e:
            return {"error": str(e)}

    def _handle_get_protocols(self, **kw):
        db = getattr(self.engine, 'db', None)
        if not db:
            return {"error": "DB not available"}
        return {"protocols": db.get_all_protocols()}

    def _handle_query_database(self, sql=None, **kw):
        if not sql or not isinstance(sql, str):
            return {"error": "SQL query required (non-empty string)"}
        sql_stripped = sql.strip().rstrip(";").strip()
        sql_upper = sql_stripped.upper()
        # Only allow single SELECT — reject multi-statement, comments, and DML
        if not sql_upper.startswith("SELECT"):
            return {"error": "Only SELECT queries are allowed"}
        if "--" in sql_stripped or "/*" in sql_stripped:
            return {"error": "SQL comments are not permitted"}
        if ";" in sql_stripped:
            return {"error": "Only a single SELECT statement is allowed (no semicolons)"}
        blocked = ("DROP ", "DELETE ", "INSERT ", "UPDATE ", "ALTER ", "CREATE ",
                   "EXEC ", "EXECUTE ", "GRANT ", "REVOKE ", "ATTACH ")
        for kw_frag in blocked:
            if kw_frag in sql_upper:
                return {"error": f"Prohibited keyword detected: {kw_frag.strip()}"}
        db = getattr(self.engine, 'db', None)
        if not db:
            return {"error": "DB not available"}
        try:
            results = db.query(sql_stripped)
            if results and hasattr(results[0], 'keys'):
                results = [dict(r) for r in results]
            return {"results": results, "count": len(results) if results else 0}
        except Exception as e:
            return {"error": str(e)}

    def _handle_graph_query(self, op_code=None, node_type=None, **kw):
        kg = getattr(self.engine, 'graph', None)
        if not kg:
            return {"error": "Knowledge Graph not available"}
        results = kg.query(op_code=op_code or "", node_type=node_type or "")
        return {"results": results, "count": len(results)}

    def _handle_graph_trace(self, node_id=None, max_depth=10, **kw):
        kg = getattr(self.engine, 'graph', None)
        if not kg:
            return {"error": "Knowledge Graph not available"}
        path = kg.trace(node_id, max_depth=int(max_depth))
        return {"trace_path": path, "length": len(path)}

    def _handle_graph_connect(self, source=None, target=None, label="SEQ", weight=1.0, **kw):
        kg = getattr(self.engine, 'graph', None)
        if not kg:
            return {"error": "Knowledge Graph not available"}
        try:
            eid = kg.add_edge(source, target, label, float(weight))
            return {"edge_id": eid, "source": source, "target": target, "label": label}
        except ValueError as e:
            return {"error": str(e)}

    def _handle_graph_path(self, source=None, target=None, **kw):
        kg = getattr(self.engine, 'graph', None)
        if not kg:
            return {"error": "Knowledge Graph not available"}
        path = kg.path(source, target)
        if path is None:
            return {"error": "No path found"}
        return {"path": path, "length": len(path)}

    def _handle_graph_stats(self, **kw):
        kg = getattr(self.engine, 'graph', None)
        if not kg:
            return {"error": "Knowledge Graph not available"}
        return kg.stats()

    def _handle_vector_search(self, query=None, top_k=5, **kw):
        vs = getattr(self.engine, 'vector_store', None)
        if not vs:
            return {"error": "Vector Store not available"}
        results = vs.search(query, top_k=int(top_k))
        return {"results": results, "count": len(results)}

    def _handle_vector_stats(self, **kw):
        vs = getattr(self.engine, 'vector_store', None)
        if not vs:
            return {"error": "Vector Store not available"}
        return vs.stats()

    def _handle_search_all(self, query=None, **kw):
        results = {}
        kg = getattr(self.engine, 'graph', None)
        if kg:
            results["graph"] = kg.query(label=query)
        vs = getattr(self.engine, 'vector_store', None)
        if vs:
            results["vector"] = vs.search(query, top_k=3)
        kr = getattr(self.engine, 'knowledge', None)
        if kr:
            try:
                results["knowledge"] = kr.search(query, top_k=3)
            except Exception:
                results["knowledge"] = []
        return results

    def _handle_knowledge_stats(self, **kw):
        kr = getattr(self.engine, 'knowledge', None)
        if not kr:
            return {"error": "KnowledgeResonance not available"}
        total = None
        try:
            total = kr.total_entries if hasattr(kr, 'total_entries') else None
        except Exception:
            pass
        growth = None
        try:
            growth = kr.knowledge_growth_rate() if hasattr(kr, 'knowledge_growth_rate') else None
        except Exception:
            pass
        return {"total_entries": total, "growth_rate": growth}

    def _handle_get_workflows(self, **kw):
        pb = getattr(self.engine, 'protocol_bridge', None)
        if not pb:
            return {"error": "ProtocolBridge not available"}
        return {"workflows": pb.list_workflows() or [], "protocols": pb.list_protocols() or []}

    # ── Registration ──

    def _register_handlers(self):
        self._handler_map = {
            "get_status": self._handle_get_status,
            "get_roles": self._handle_get_roles,
            "get_role": self._handle_get_role,
            "query_knowledge": self._handle_query_knowledge,
            "execute_chat": self._handle_execute_chat,
            "get_history": self._handle_get_history,
            "get_protocols": self._handle_get_protocols,
            "query_database": self._handle_query_database,
            "graph_query": self._handle_graph_query,
            "graph_trace": self._handle_graph_trace,
            "graph_connect": self._handle_graph_connect,
            "graph_path": self._handle_graph_path,
            "graph_stats": self._handle_graph_stats,
            "vector_search": self._handle_vector_search,
            "vector_stats": self._handle_vector_stats,
            "search_all": self._handle_search_all,
            "knowledge_stats": self._handle_knowledge_stats,
            "get_workflows": self._handle_get_workflows,
        }

    def bind_to(self, cap_registry):
        """Register all tools into a CapabilityRegistry for MCP Auto-Bridge."""
        self._cap_registry = cap_registry
        for td in self._tool_defs:
            name = td["name"]
            handler = self._handler_map[name]
            cap_registry.register(name, td["description"], handler)

    # ── Public API ──

    def list_tools(self) -> List[Dict]:
        return list(self._tool_defs)

    def call_tool(self, name: str, args: Dict = None) -> Dict:
        handler = self._handler_map.get(name)
        if not handler:
            return {"error": f"Tool not found: {name}"}
        try:
            return handler(**(args or {}))
        except Exception as e:
            return {"error": str(e)}

    @property
    def tool_count(self) -> int:
        return len(self._tool_defs)
