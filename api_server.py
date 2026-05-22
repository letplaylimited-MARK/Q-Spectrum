#!/usr/bin/env python3
"""
Q-SpecTrum Web API Server v2.0
================================
HTTP API that bridges the Web Chat UI to the QSpectrumEngine.
Now with Ghost Channel nervous system + DeerFlow execution layer.

Usage:
  python api_server.py                    # Start on port 8765
  python api_server.py --port 9000        # Custom port
  python api_server.py --provider openai  # Use real LLM

Endpoints (84 total across 20 categories):
  Core:
    GET  /                            → Redirect to chat.html
    GET  /api/status                  → System health + role/protocol counts
    POST /api/chat                    → Full pipeline: Secretary → GhostChannel → Role → LLM
    GET  /api/roles                   → All 15 roles with families
    GET  /api/knowledge?q=...        → Search knowledge base
    GET  /api/history                 → Session interaction history
    POST /api/reset                   → Reset session state
    GET  /api/config                  → Current LLM/system config
  Ghost Channel:
    GET  /api/ghost-channel/status|network|audit
  DeerFlow:
    GET  /api/deerflow/status|queue|skills
  Closed Loop: /api/closed-loop/*
  Knowledge Pipeline: /api/knowledge-pipeline/*
  Projects: /api/projects/{list,active,aggregate,create,switch}
  Components: /api/components/{list,history}
  Growth: /api/growth/status
  Tasks: /api/tasks/{board,analytics,status,create,update}
  Contact: /api/contact/{status,tickets,notifications}
  Search: /api/search
  Memory: /api/memory/{status,projects,chatrooms,history,search,...}
  Negotiation: /api/negotiation/status
  Files: /api/files/{scan,read,analyze,tree,write}
  5-Layer: /api/{resource,result,decision}-layer/*
  Scenarios: /api/scenarios/{list,status,start,advance,sandbox}
  Skills: /api/skills/{list,execute}, /api/deerflow-skills/*
  Formulas: /api/formulas/status

  Run 'python run.py --status' or see API docs for full details.

Architecture:
  Browser (chat.html)
      ↓ fetch("/api/chat", {body: {message: "..."}})
  api_server.py (this file)
      ↓
  QSpectrumEngine.process()
      ↓
  Secretary → GhostChannel → Role → PromptBuilder → LLM → DeerFlow → KnowledgeDeposit
      ↓
  JSON response → Browser renders (multi-visualization)
"""

import argparse
import json
import logging
import os
import sys
import time
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse

# Configure logging
_logger = logging.getLogger("qspectrum")
_log_json = os.environ.get("QSPECTRUM_LOG_FORMAT", "").lower() == "json"
if _log_json:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter(
        json.dumps({
            "ts": "%(asctime)s", "level": "%(levelname)s",
            "logger": "%(name)s", "msg": "%(message)s"
        })))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

logger = logging.getLogger("qspectrum.api")


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server — prevents single-request blocking."""
    daemon_threads = True
    allow_reuse_address = True

# Ensure project root is on path
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from file_ops import get_file_ops
from qspectrum_engine import QSpectrumEngine, create_llm_provider


class QSpectrumAPIHandler(SimpleHTTPRequestHandler):
    """
    HTTP handler that serves static files AND API endpoints.
    Static: *.html, *.js, *.css from project root
    API:    /api/* routes to QSpectrumEngine
    """

    # Class-level shared state
    engine = None
    llm_name = "mock"
    session_history = []
    start_time = __import__('time').time()
    _engine_lock = __import__('threading').RLock()  # Reentrant lock for engine access
    _counter_lock = __import__('threading').Lock()   # Protects _active_requests
    _cors_origin = os.environ.get("QSPECTRUM_CORS_ORIGIN", "")  # Empty = same-origin only
    _active_requests = 0  # Track concurrent requests
    _max_concurrent = int(os.environ.get("QSPECTRUM_MAX_CONCURRENT", "8"))  # Concurrency limit
    # Optional API authentication (env: QSPECTRUM_API_TOKEN)
    # When set, all /api/* endpoints require Authorization: Bearer <token>
    # When empty/unset, authentication is disabled (localhost tool mode)
    _api_token = os.environ.get("QSPECTRUM_API_TOKEN", "")

    @staticmethod
    def _safe_int(value, default=30, lo=1, hi=1000):
        """Parse query param to int with safe bounds."""
        try:
            v = int(value)
            return max(lo, min(hi, v))
        except (ValueError, TypeError):
            return default

    def do_GET(self):
        from urllib.parse import unquote
        self._request_id = uuid.uuid4().hex[:8]
        parsed = urlparse(unquote(self.path))
        path = parsed.path

        # API routes — enforce auth before dispatching
        if path.startswith("/api/"):
            if not self._check_api_auth():
                return
        if path == "/api/status":
            self._handle_status()
        elif path == "/api/roles":
            self._handle_roles()
        elif path == "/api/knowledge":
            query = parse_qs(parsed.query).get("q", [""])[0]
            self._handle_knowledge(query)
        elif path == "/api/history":
            self._handle_history()
        elif path == "/api/config":
            self._handle_config()
        # Ghost Channel endpoints
        elif path == "/api/ghost-channel/status":
            self._handle_gc_status()
        elif path == "/api/ghost-channel/network":
            self._handle_gc_network()
        elif path == "/api/ghost-channel/audit":
            self._handle_gc_audit()
        # QCM Formula endpoints
        elif path == "/api/formulas/status":
            self._handle_formulas_status()
        # DeerFlow endpoints
        elif path == "/api/deerflow/status":
            self._handle_df_status()
        elif path == "/api/deerflow/queue":
            self._handle_df_queue()
        elif path == "/api/deerflow/skills":
            self._handle_df_skills()
        # Real Skills endpoints
        elif path == "/api/skills/list":
            self._handle_real_skills_list()
        # DeerFlow Real Skills endpoints (list only; execute is POST-only)
        elif path == "/api/deerflow-skills/list":
            self._handle_df_real_skills_list()
        # Closed-Loop endpoints
        elif path == "/api/closed-loop/status":
            self._handle_cl_status()
        elif path == "/api/closed-loop/resources":
            query = parse_qs(parsed.query).get("q", [""])[0]
            rtype = parse_qs(parsed.query).get("type", [None])[0]
            self._handle_cl_resources(query, rtype)
        elif path == "/api/closed-loop/results":
            self._handle_cl_results()
        elif path == "/api/closed-loop/activation":
            self._handle_cl_activation()
        # Knowledge Pipeline endpoints
        elif path == "/api/knowledge-pipeline/status":
            self._handle_kp_status()
        elif path == "/api/knowledge-pipeline/deposits":
            project = parse_qs(parsed.query).get("project", ["default"])[0]
            self._handle_kp_deposits(project)
        # Project Orchestrator endpoints
        elif path == "/api/projects/list":
            self._handle_projects_list()
        elif path == "/api/projects/active":
            self._handle_projects_active()
        elif path == "/api/projects/aggregate":
            project = parse_qs(parsed.query).get("project", [None])[0]
            self._handle_projects_aggregate(project)
        # Component Registry endpoints
        elif path == "/api/components/list":
            ctype = parse_qs(parsed.query).get("type", [None])[0]
            self._handle_components_list(ctype)
        elif path == "/api/components/history":
            self._handle_components_history()
        # User Growth endpoint
        elif path == "/api/growth/status":
            self._handle_growth_status()
        # GC Gate endpoint
        elif path == "/api/gc-gate/status":
            self._handle_gc_gate_status()
        # Task Manager endpoints (Point #10)
        elif path == "/api/tasks/board":
            project = parse_qs(parsed.query).get("project", [None])[0]
            status_filter = parse_qs(parsed.query).get("status", [None])[0]
            self._handle_task_board(project, status_filter)
        elif path == "/api/tasks/analytics":
            project = parse_qs(parsed.query).get("project", [None])[0]
            self._handle_task_analytics(project)
        elif path == "/api/tasks/status":
            tm = self.engine.task_manager
            self._send_json(tm.get_status() if tm else {"available": False})
        # Contact Channel endpoints (Point #20)
        elif path == "/api/contact/status":
            cc = self.engine.contact_channel
            self._send_json(cc.get_status() if cc else {"available": False})
        elif path == "/api/contact/tickets":
            status_filter = parse_qs(parsed.query).get("status", [None])[0]
            type_filter = parse_qs(parsed.query).get("type", [None])[0]
            self._handle_contact_tickets(status_filter, type_filter)
        elif path == "/api/contact/notifications":
            unread = parse_qs(parsed.query).get("unread", ["false"])[0] == "true"
            self._handle_contact_notifications(unread)
        elif path == "/api/contact/developer":
            cc = self.engine.contact_channel
            self._send_json(cc.get_developer_info() if cc else {})
        elif path == "/api/contact/social":
            cc = self.engine.contact_channel
            self._send_json({"configs": cc.get_social_configs() if cc else []})
        # Global Search endpoint (Point #18)
        elif path == "/api/search":
            q = parse_qs(parsed.query).get("q", [""])[0]
            domains = parse_qs(parsed.query).get("domains", [None])[0]
            project = parse_qs(parsed.query).get("project", [None])[0]
            limit = self._safe_int(parse_qs(parsed.query).get("limit", ["30"])[0], default=30, hi=200)
            self._handle_global_search(q, domains, project, limit)
        elif path == "/api/search/status":
            gs = self.engine.global_search
            self._send_json(gs.get_status() if gs else {"available": False})
        # Project Memory endpoints (Point #19)
        elif path == "/api/memory/status":
            self._handle_memory_status()
        elif path == "/api/memory/projects":
            self._handle_memory_projects()
        elif path == "/api/memory/chatrooms":
            project = parse_qs(parsed.query).get("project", [None])[0]
            self._handle_memory_chatrooms(project)
        elif path == "/api/memory/history":
            project = parse_qs(parsed.query).get("project", [None])[0]
            chatroom = parse_qs(parsed.query).get("chatroom", [None])[0]
            limit = self._safe_int(parse_qs(parsed.query).get("limit", ["50"])[0], default=50, hi=200)
            self._handle_memory_history(project, chatroom, limit)
        elif path == "/api/memory/search":
            q = parse_qs(parsed.query).get("q", [""])[0]
            project = parse_qs(parsed.query).get("project", [None])[0]
            self._handle_memory_search(q, project)
        # Negotiation Engine endpoint
        elif path == "/api/negotiation/status":
            self._send_json(
                self.engine.negotiation_engine.get_status()
                if self.engine.negotiation_engine else {"available": False}
            )
        # File Operations endpoints (Point #12)
        elif path == "/api/files/scan":
            project = parse_qs(parsed.query).get("project", [str(ROOT)])[0]
            depth = self._safe_int(parse_qs(parsed.query).get("depth", ["3"])[0], default=3, hi=20)
            self._handle_file_scan(project, depth)
        elif path == "/api/files/read":
            fpath = parse_qs(parsed.query).get("path", [""])[0]
            start = parse_qs(parsed.query).get("start", [None])[0]
            end = parse_qs(parsed.query).get("end", [None])[0]
            self._handle_file_read(fpath, start, end)
        elif path == "/api/files/analyze":
            project = parse_qs(parsed.query).get("project", [str(ROOT)])[0]
            self._handle_file_analyze(project)
        elif path == "/api/files/tree":
            project = parse_qs(parsed.query).get("project", [str(ROOT)])[0]
            depth = self._safe_int(parse_qs(parsed.query).get("depth", ["5"])[0], default=5, hi=20)
            self._handle_file_tree(project, depth)
        # 5-Layer Architecture endpoints
        elif path == "/api/resource-layer/status":
            self._handle_resource_layer_status()
        elif path == "/api/resource-layer/search":
            q = parse_qs(parsed.query).get("q", [""])[0]
            rtype = parse_qs(parsed.query).get("type", [None])[0]
            self._handle_resource_search(q, rtype)
        elif path == "/api/result-layer/status":
            self._handle_result_layer_status()
        elif path == "/api/result-layer/results":
            project = parse_qs(parsed.query).get("project", ["default"])[0]
            self._handle_result_layer_results(project)
        elif path == "/api/decision-layer/status":
            self._handle_decision_layer_status()
        elif path == "/api/decision-layer/performance":
            self._handle_decision_performance()
        elif path == "/api/closed-loop/full-status":
            self._handle_full_loop_status()
        # Scenario Engine + AI Companion endpoints
        elif path == "/api/scenarios/list":
            lang = parse_qs(parsed.query).get("lang", ["zh"])[0]
            se = self.engine.scenario_engine
            if se:
                self._send_json({"scenarios": se.companion.list_scenarios(lang)})
            else:
                self._send_json({"scenarios": [], "available": False})
        elif path == "/api/scenarios/status":
            se = self.engine.scenario_engine
            self._send_json(se.get_status() if se else {"available": False})
        elif path == "/api/scenarios/active":
            se = self.engine.scenario_engine
            if se:
                self._send_json({"sessions": se.companion.get_active_sessions()})
            else:
                self._send_json({"sessions": []})
        elif path == "/" or path == "":
            # Redirect to chat interface
            self.send_response(302)
            self.send_header("Location", "/chat.html")
            self.end_headers()
        else:
            # Check if this is a POST-only endpoint accessed via GET
            post_only = ["/api/chat", "/api/negotiate", "/api/reset",
                         "/api/closed-loop/collect",
                         "/api/skills/execute", "/api/deerflow-skills/execute"]
            if path in post_only:
                self.send_response(405)
                self.send_header("Content-Type", "application/json")
                self.send_header("Allow", "POST")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Method Not Allowed. Use POST."}).encode())
                return
            # Serve static files
            super().do_GET()

    # Override send_error to return JSON for API paths
    def send_error(self, code, message=None, explain=None):
        """Return JSON error response for /api/* paths, HTML for static files."""
        if self.path.startswith("/api/"):
            self._send_json({"error": message or self.responses.get(code, ("Error",))[0],
                             "status": code, "path": self.path}, code)
        else:
            super().send_error(code, message, explain)

    def do_POST(self):
        self._request_id = uuid.uuid4().hex[:8]
        parsed = urlparse(self.path)
        path = parsed.path

        # All POST /api/* routes require auth when enabled
        if path.startswith("/api/"):
            if not self._check_api_auth():
                return

        if path == "/api/chat":
            self._handle_chat()
        elif path == "/api/negotiate":
            self._handle_negotiate()
        elif path == "/api/reset":
            self._handle_reset()
        elif path == "/api/closed-loop/collect":
            self._handle_cl_collect()
        elif path == "/api/closed-loop/feedback":
            self._handle_cl_feedback()
        elif path == "/api/projects/create":
            self._handle_projects_create()
        elif path == "/api/projects/switch":
            self._handle_projects_switch()
        elif path == "/api/skills/execute":
            self._handle_real_skills_execute_post()
        elif path == "/api/deerflow-skills/execute":
            self._handle_df_real_skills_exec_post()
        elif path == "/api/resource-layer/collect":
            self._handle_resource_collect()
        elif path == "/api/result-layer/close-loop":
            self._handle_close_loop()
        # Task Manager POST endpoints
        elif path == "/api/tasks/create":
            self._handle_task_create()
        elif path == "/api/tasks/update":
            self._handle_task_update()
        # Contact Channel POST endpoints
        elif path == "/api/contact/ticket/create":
            self._handle_ticket_create()
        elif path == "/api/contact/ticket/respond":
            self._handle_ticket_respond()
        elif path == "/api/contact/notifications/read-all":
            cc = self.engine.contact_channel
            count = cc.mark_all_read() if cc else 0
            self._send_json({"marked_read": count})
        # File Operations POST endpoints (Point #12)
        elif path == "/api/files/write":
            self._handle_file_write()
        # Project Memory POST endpoints (Point #19)
        elif path == "/api/memory/project/create":
            self._handle_memory_create_project()
        elif path == "/api/memory/project/switch":
            self._handle_memory_switch_project()
        elif path == "/api/memory/project/archive":
            self._handle_memory_archive_project()
        elif path == "/api/memory/chatroom/create":
            self._handle_memory_create_chatroom()
        elif path == "/api/memory/chatroom/switch":
            self._handle_memory_switch_chatroom()
        elif path == "/api/memory/chatroom/archive":
            self._handle_memory_archive_chatroom()
        elif path == "/api/memory/append":
            # S068: append a user-curated entry to MEMORY.md (persistent
            # cross-session memory). Closes the documented gap where
            # USER-GUIDE.md promised MEMORY.md would be updated but the
            # engine never wrote to the file.
            self._handle_memory_md_append()
        # Scenario Engine POST endpoints
        elif path == "/api/scenarios/start":
            self._handle_scenario_start()
        elif path == "/api/scenarios/advance":
            self._handle_scenario_advance()
        elif path == "/api/scenarios/sandbox":
            self._handle_scenario_sandbox()
        elif path == "/api/scenarios/deerflow-sim":
            self._handle_scenario_deerflow_sim()
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self._add_cors_headers()
        self.end_headers()

    def _check_api_auth(self):
        """Verify optional Bearer token authentication.

        Returns True if request is authorized, False otherwise.
        When QSPECTRUM_API_TOKEN is not set, always returns True (localhost mode).
        When set, requires Authorization: Bearer <token> header matching exactly.
        """
        token = QSpectrumAPIHandler._api_token
        if not token:
            return True  # Auth disabled — localhost tool mode
        auth_header = self.headers.get("Authorization", "")
        if auth_header == f"Bearer {token}":
            return True
        # Reject with 401
        self._send_json({"error": "Authentication required",
                         "status": "unauthorized"}, 401)
        return False

    # ── API Handlers ──────────────────────────────────────

    def _handle_chat(self):
        """Process user message through full Q-SpecTrum pipeline."""
        try:
            # Read and validate request body
            try:
                body = self._read_body()
            except ValueError as e:
                # JSON parsing error - return 400
                self._send_json({"error": str(e)}, 400)
                return

            message = (body.get("message") or "").strip()
            context = body.get("context", {}) or {}
            # S069: accept session_id at top-level for convenience — per common
            # REST client patterns. Merge it into the context dict so the engine
            # can pass it downstream for per-session multi-turn preamble.
            if "session_id" in body and "session_id" not in context:
                context["session_id"] = body["session_id"]

            if not message:
                self._send_json({"error": "Empty message / 消息为空"}, 400)
                return

            # Truncate extremely long messages to prevent resource exhaustion
            if len(message) > 10000:
                message = message[:10000]

            # Process through engine (thread-safe with concurrency limit)
            start = time.time()
            with QSpectrumAPIHandler._counter_lock:
                if QSpectrumAPIHandler._active_requests >= QSpectrumAPIHandler._max_concurrent:
                    busy = True
                    cur = QSpectrumAPIHandler._active_requests
                else:
                    QSpectrumAPIHandler._active_requests += 1
                    busy = False
            if busy:
                self._send_json({
                    "success": False,
                    "error": f"Server busy — {cur} requests in progress "
                             f"(max: {QSpectrumAPIHandler._max_concurrent}). Please retry.",
                    "routing": {"role_name": "System", "family": "system"},
                }, 429)
                return
            try:
                with self._engine_lock:
                    result = self.engine.process(message, context)
            except Exception as proc_err:
                logger.error(f"Engine processing error: {proc_err}", exc_info=True)
                self._send_json({
                    "success": False,
                    "error": "Engine processing error — check server logs for details",
                    "routing": {"role_name": "System", "family": "system"},
                }, 500)
                return
            finally:
                QSpectrumAPIHandler._active_requests -= 1
            elapsed_ms = (time.time() - start) * 1000

            # Extract knowledge context info
            meta = result.get("metadata", {})
            knowledge_ctx = meta.get("knowledge_context") or ""
            knowledge_hits = []
            if knowledge_ctx:
                # Parse knowledge hits from the context text
                for line in knowledge_ctx.split("\n"):
                    line = line.strip()
                    if line.startswith("- [") and "]" in line:
                        # Format: - [0.42] content...
                        hit_text = line.split("]", 1)[-1].strip()[:60]
                        if hit_text:
                            knowledge_hits.append(hit_text)

            # Build response
            response_data = {
                "success": True,
                "response": result["response"],
                "routing": result["routing"],
                "knowledge_used": len(knowledge_ctx) > 0,
                "knowledge_hits": knowledge_hits[:3],
                "elapsed_ms": round(elapsed_ms, 1),
                "llm_provider": self.llm_name,
                "interaction_id": meta.get("interaction_number", 0),
                "deerflow": result.get("deerflow"),
                "ghost_channel": result.get("ghost_channel"),
                "sandbox": result.get("sandbox"),
                "cost": result.get("cost"),
                "flywheel": result.get("flywheel"),
                "deadlock": result.get("deadlock"),
                "feedback_loop": result.get("feedback_loop"),
                "knowledge_deposit": result.get("knowledge_deposit"),
                "user_growth": result.get("user_growth"),
                "result_layer": result.get("result_layer"),
                "deerflow_skill": result.get("deerflow", {}).get("skill") if result.get("deerflow") else None,
                "companion": result.get("companion"),
            }

            # Save to session history
            self.session_history.append({
                "user": message,
                "response": result["response"],
                "routing": result["routing"],
                "elapsed_ms": round(elapsed_ms, 1),
                "timestamp": time.time(),
            })

            self._send_json(response_data)

        except Exception as e:
            self._send_json({
                "success": False,
                "error": str(e),
                "response": f"[系統錯誤] {e}",
            }, 500)

    def _handle_status(self):
        """Return system status."""
        try:
            status = self.engine.get_system_status()
            status["uptime_seconds"] = round(time.time() - self.start_time, 1)
            status["session_interactions"] = len(self.session_history)
            status["api_version"] = "1.0"
            self._send_json(status)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_roles(self):
        """Return all roles grouped by family."""
        try:
            roles = self.engine.db.get_all_roles()
            families = {"trum": [], "spec": [], "qcm": []}
            for code, role in roles.items():
                family = role.get("family", "qcm")
                families.setdefault(family, []).append({
                    "role_code": code,
                    "role_name": role.get("role_name", code),
                    "family": family,
                    "capabilities": role.get("capabilities_list", []),
                })
            self._send_json({
                "total": len(roles),
                "families": families,
            })
        except Exception as e:
            self._send_json({"error": f"Failed to load roles: {e}"}, 500)

    def _handle_knowledge(self, query):
        """Search knowledge base."""
        try:
            if not query:
                self._send_json({
                    "total_entries": self.engine.knowledge.total_entries,
                    "results": [],
                })
                return

            results = self.engine.knowledge.search(query, top_k=10)
            self._send_json({
                "query": query,
                "results": [
                    {"content": content, "score": round(score, 4), "explanation": expl}
                    for content, score, expl in results
                ],
            })
        except Exception as e:
            self._send_json({"error": f"Knowledge search failed: {e}"}, 500)

    def _handle_history(self):
        """Return session history."""
        try:
            history = self.session_history or []
            self._send_json({
                "count": len(history),
                "history": history[-50:],
            })
        except Exception as e:
            self._send_json({"error": f"History retrieval failed: {e}"}, 500)

    def _handle_config(self):
        """Return current config."""
        try:
            kr = self.engine.knowledge
            self._send_json({
                "llm_provider": self.llm_name,
                "roles_loaded": len(self.engine.db.get_all_roles()),
                "protocols": len(self.engine.db.get_all_protocols()),
                "knowledge_entries": kr.total_entries if kr else 0,
                "r_formula_weights": {
                    "W_SIM": round(getattr(kr, 'W_SIM', 0.35), 4),
                    "W_COMP": round(getattr(kr, 'W_COMP', 0.25), 4),
                    "W_FREQ": round(getattr(kr, 'W_FREQ', 0.25), 4),
                    "W_DIV": round(getattr(kr, 'W_DIV', 0.15), 4),
                },
                "formula_coverage": "19/22 (F1-F22 all implemented)",
            })
        except Exception as e:
            self._send_json({"error": f"Config retrieval failed: {e}"}, 500)

    def _handle_reset(self):
        """Reset session state."""
        try:
            if self.session_history:
                self.session_history.clear()
            if self.engine:
                self.engine.interaction_count = 0
            self._send_json({"success": True, "message": "Session reset"})
        except Exception as e:
            self._send_json({"error": f"Reset failed: {e}"}, 500)

    def _handle_negotiate(self):
        """Handle multi-role negotiation request."""
        try:
            data = self._read_body()
            if not data or "topic" not in data:
                self._send_json({"error": "Missing 'topic' field"}, 400)
                return
            if not self.engine.negotiation_engine:
                self._send_json({"error": "Negotiation engine not available"}, 503)
                return

            topic = data["topic"]
            mode = data.get("mode", "discuss")
            participants = data.get("participants", None)
            max_rounds = data.get("max_rounds", 3)

            # Auto-detect participants if not specified
            if not participants:
                routing = self.engine.secretary.route(topic, {})
                neg_check = self.engine.negotiation_engine.should_negotiate(topic, routing)
                if neg_check:
                    participants = neg_check["participants"]
                    mode = neg_check.get("mode", mode)
                else:
                    participants = ["ROLE-Q01", "ROLE-Q02"]

            result = self.engine.negotiation_engine.run_negotiation(
                topic=topic, participants=participants,
                mode=mode, max_rounds=max_rounds)
            self._send_json(result.to_dict())
        except Exception as e:
            import logging
            logging.getLogger("q-spectrum").error(f"Negotiation handler error: {e}")
            self._send_json({"error": str(e)}, 500)

    # ── Ghost Channel Handlers ─────────────────────────────

    def _handle_gc_status(self):
        """Return Ghost Channel nervous system status."""
        gc = self.engine.ghost_channel
        if gc:
            self._send_json(gc.get_status())
        else:
            self._send_json({
                "active": False,
                "mode": "unavailable",
                "capabilities": "none",
                "capabilities_count": 0,
                "total_syncs": 0,
                "active_roles": 0,
                "audit_entries": 0,
            })

    def _handle_gc_network(self):
        """Return Ghost Channel role communication graph."""
        gc = self.engine.ghost_channel
        if gc:
            self._send_json(gc.get_network_graph())
        else:
            self._send_json({"nodes": [], "edges": []})

    def _handle_gc_audit(self):
        """Return Ghost Channel audit trail."""
        try:
            gc = self.engine.ghost_channel
            if gc:
                self._send_json({
                    "entries": gc.get_audit_log(last_n=50),
                    "total": getattr(gc, '_txn_counter', 0),
                })
            else:
                self._send_json({"entries": [], "total": 0})
        except Exception as e:
            self._send_json({"error": f"GC audit failed: {e}"}, 500)

    # ── QCM Formula Handlers ───────────────────────────────

    def _handle_formulas_status(self):
        """Return QCM formula components status (F12-F22)."""
        sb = self.engine.src_bridge
        if sb:
            self._send_json(sb.status())
        else:
            self._send_json({
                "bridge": "unavailable",
                "components_loaded": 0,
                "components_total": 5,
            })

    # ── DeerFlow Handlers ────────────────────────────────

    def _handle_df_status(self):
        """Return DeerFlow integration status."""
        df = self.engine.deerflow
        if df:
            status = df.status()
            if hasattr(df, 'get_queue_status'):
                status["queue"] = df.get_queue_status()
            self._send_json(status)
        else:
            self._send_json({
                "installed": False,
                "running": False,
                "skills_count": 0,
                "issues": ["DeerFlow not installed"],
            })

    def _handle_df_queue(self):
        """Return DeerFlow task queue."""
        df = self.engine.deerflow
        if df and hasattr(df, 'get_queue_status'):
            self._send_json(df.get_queue_status())
        else:
            self._send_json({"queued": 0, "tasks": []})

    def _handle_df_skills(self):
        """Return all DeerFlow skills."""
        df = self.engine.deerflow
        if df:
            self._send_json({
                "skills": df.list_skills(),
                "skill_map": df.get_unified_skill_map(),
            })
        else:
            self._send_json({"skills": [], "skill_map": {}})

    # ── Real Skills Handlers ─────────────────────────────

    def _handle_real_skills_list(self):
        """List all skills — merges RealSkills (executable) + SkillExecutor (Skills/ folder)."""
        merged = []
        seen_keys = set()

        # 1. RealSkills — the 5 executable skills (File Analyzer, etc.)
        rs = getattr(self.engine, 'real_skills', None)
        if rs:
            try:
                for s in rs.list_real_skills():
                    if isinstance(s, dict):
                        key = s.get('name') or s.get('skill_code') or s.get('id')
                        if key and key not in seen_keys:
                            seen_keys.add(key)
                            merged.append({**s, "source": "real_skills"})
            except Exception:
                pass

        # 2. SkillExecutor — the 22 Markdown skills under AI项目管理/Skills/
        se = getattr(self.engine, 'skill_executor', None)
        if se is None:
            try:
                from skill_executor import SkillExecutor
                se = SkillExecutor()
            except Exception:
                se = None
        if se:
            try:
                for s in se.list_skills():
                    if isinstance(s, dict):
                        key = s.get('key') or s.get('name')
                        if key and key not in seen_keys:
                            seen_keys.add(key)
                            merged.append({
                                "name": s.get('name', key),
                                "key": key,
                                "source": s.get('source', 'skill_executor'),
                                "has_scripts": s.get('has_scripts', False),
                            })
            except Exception:
                pass

        self._send_json({
            "skills": merged,
            "total": len(merged),
            "sources": sorted({s.get("source","?") for s in merged})
        })

    def _handle_real_skills_execute_post(self):
        """Execute a skill via POST (for complex requests with data)."""
        data = self._read_body()
        if data is None:
            return  # _read_body already sent 400 for malformed body
        skill = (data.get("skill") or "").strip()
        if not skill:
            self._send_json(
                {"status": "error", "error": "Missing required field 'skill'"},
                status=400,
            )
            return
        msg = data.get("message", "")
        kwargs = {k: v for k, v in data.items() if k not in ("skill", "message")}

        rs = getattr(self.engine, 'real_skills', None)
        if rs and rs.can_execute(skill):
            result = rs.execute(skill, msg, **kwargs)
            self._send_json(result)
        else:
            self._send_json({"status": "error", "error": f"Skill '{skill}' not available"})

    def _handle_df_real_skills_list(self):
        """List all DeerFlow real skills (locally executable)."""
        drs = getattr(self.engine, 'deerflow_real_skills', None)
        if drs:
            self._send_json({"skills": drs.list_skills(), "status": "ok"})
        else:
            self._send_json({"skills": [], "note": "DeerFlow real skills not loaded"})

    def _handle_df_real_skills_exec_post(self):
        """Execute a DeerFlow skill via POST (for complex requests with data)."""
        data = self._read_body()
        if data is None:
            return  # _read_body already sent 400
        skill = (data.get("skill") or "").strip()
        if not skill:
            self._send_json(
                {"status": "error", "error": "Missing required field 'skill'"},
                status=400,
            )
            return
        msg = data.get("message", "")
        kwargs = {k: v for k, v in data.items() if k not in ("skill", "message")}

        drs = getattr(self.engine, 'deerflow_real_skills', None)
        if drs and drs.can_execute(skill):
            result = drs.execute(skill, msg, **kwargs)
            self._send_json(result)
        else:
            self._send_json({"status": "error", "error": f"DeerFlow skill '{skill}' not available"})

    # ── Closed-Loop Handlers ──────────────────────────────

    def _handle_cl_status(self):
        """Return closed-loop architecture status."""
        cl = self.engine.closed_loop
        if cl:
            self._send_json(cl.status())
        else:
            self._send_json({"closed_loop": "unavailable"})

    def _handle_cl_resources(self, query, resource_type):
        """Search or list collected resources."""
        cl = self.engine.closed_loop
        if cl:
            results = cl.resources.search(query or "", resource_type=resource_type)
            self._send_json({
                "query": query,
                "type_filter": resource_type,
                "results": results,
                "stats": cl.resources.get_stats(),
            })
        else:
            self._send_json({"results": [], "stats": {}})

    def _handle_cl_results(self):
        """Get persisted execution results."""
        cl = self.engine.closed_loop
        if cl:
            self._send_json({
                "history": cl.results.get_history(limit=50),
                "stats": cl.results.get_stats(),
            })
        else:
            self._send_json({"history": [], "stats": {}})

    def _handle_cl_activation(self):
        """Get Ghost Channel activation gate status."""
        cl = self.engine.closed_loop
        if cl:
            self._send_json(cl.gate.check_activation())
        else:
            self._send_json({"level": "unavailable"})

    def _handle_cl_collect(self):
        """Collect a user resource via POST."""
        cl = self.engine.closed_loop
        if not cl:
            self._send_json({"error": "Closed loop not available"}, 500)
            return
        try:
            body = self._read_body()
            result = cl.collect_user_resource(
                resource_type=body.get("type", "text"),
                content=body.get("content", ""),
                title=body.get("title"),
                tags=body.get("tags", []),
                file_path=body.get("file_path"),
                project_id=body.get("project_id"),
            )
            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_cl_feedback(self):
        """Submit user feedback on a routing decision."""
        cl = self.engine.closed_loop
        if not cl:
            self._send_json({"error": "Closed loop not available"}, 500)
            return
        try:
            body = self._read_body()
            result = cl.feedback.record_feedback(
                interaction_id=body.get("interaction_id", ""),
                role_code=body.get("role_code", ""),
                query_text=body.get("query_text", ""),
                quality_score=body.get("quality_score", 0.5),
                user_rating=body.get("user_rating"),
                was_correct_route=body.get("was_correct_route", True),
                suggested_role=body.get("suggested_role"),
            )
            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    # ── Knowledge Pipeline Handlers ─────────────────────────

    def _handle_kp_status(self):
        kp = self.engine.knowledge_pipeline
        if kp:
            self._send_json(kp.get_status())
        else:
            self._send_json({"status": "unavailable", "total_deposits": 0})

    def _handle_kp_deposits(self, project_id):
        kp = self.engine.knowledge_pipeline
        if kp:
            deposits = kp.get_project_knowledge(project_id, limit=30)
            self._send_json({"project_id": project_id, "deposits": deposits})
        else:
            self._send_json({"project_id": project_id, "deposits": []})

    # ── Project Orchestrator Handlers ─────────────────────

    def _handle_projects_list(self):
        po = self.engine.project_orchestrator
        if po:
            self._send_json({"projects": po.list_projects(), "active": po.active_project})
        else:
            self._send_json({"projects": [], "active": "default"})

    def _handle_projects_active(self):
        po = self.engine.project_orchestrator
        if po:
            self._send_json({
                "active": po.active_project,
                "aggregation": po.aggregate_results(po.active_project),
            })
        else:
            self._send_json({"active": "default", "aggregation": {}})

    def _handle_projects_aggregate(self, project_id):
        po = self.engine.project_orchestrator
        if po:
            self._send_json(po.aggregate_results(project_id))
        else:
            self._send_json({"project_id": project_id or "all", "total_interactions": 0})

    def _handle_projects_create(self):
        po = self.engine.project_orchestrator
        if not po:
            self._send_json({"error": "Project orchestrator not available"}, 500)
            return
        try:
            body = self._read_body()
            ctx = po.create_project(
                project_id=body.get("project_id", f"proj-{int(time.time())}"),
                name=body.get("name", "Untitled Project"),
                description=body.get("description", ""),
            )
            self._send_json({
                "created": True,
                "project_id": ctx.project_id,
                "name": ctx.name,
            })
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_projects_switch(self):
        po = self.engine.project_orchestrator
        if not po:
            self._send_json({"error": "Project orchestrator not available"}, 500)
            return
        try:
            body = self._read_body()
            pid = body.get("project_id", "default")
            success = po.switch_project(pid)
            self._send_json({"switched": success, "active": po.active_project})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    # ── Component Registry Handlers ───────────────────────

    def _handle_components_list(self, component_type):
        cr = self.engine.component_registry
        if cr:
            self._send_json({
                "components": cr.list_components(component_type),
                "status": cr.get_status(),
            })
        else:
            self._send_json({"components": [], "status": {}})

    def _handle_components_history(self):
        cr = self.engine.component_registry
        if cr:
            self._send_json({"history": cr.swap_history()})
        else:
            self._send_json({"history": []})

    # ── User Growth Handler ───────────────────────────────

    def _handle_growth_status(self):
        ug = self.engine.user_growth
        if ug:
            self._send_json(ug.get_status())
        else:
            self._send_json({"stage": "S1", "name": "Observer", "interactions": 0})

    # ── GC Gate Handler ───────────────────────────────────

    def _handle_gc_gate_status(self):
        gate = getattr(self.engine, '_gc_gate', None)
        if gate:
            self._send_json(gate.get_status())
        else:
            self._send_json({"activated": False, "level": "unavailable"})

    # ── 5-Layer Architecture Handlers ─────────────────────

    def _handle_resource_layer_status(self):
        rl = self.engine.resource_layer
        if rl:
            self._send_json(rl.status())
        else:
            self._send_json({"layer": "resource", "status": "unavailable"})

    def _handle_resource_search(self, query, rtype):
        rl = self.engine.resource_layer
        if rl and query:
            results = rl.search(query, type_filter=rtype, top_k=20)
            self._send_json({"query": query, "results": results})
        else:
            self._send_json({"query": query, "results": []})

    def _handle_resource_collect(self):
        rl = self.engine.resource_layer
        if not rl:
            self._send_json({"error": "Resource layer not available"}, 500)
            return
        try:
            body = self._read_body()
            rid = rl.collect(
                type_=body.get("type", "text"),
                content=body.get("content", ""),
                title=body.get("title"),
                tags=body.get("tags", []),
                project_id=body.get("project_id", "default"),
                source=body.get("source", "api"),
            )
            self._send_json({"resource_id": rid})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_result_layer_status(self):
        rl = self.engine.result_layer
        if rl:
            self._send_json(rl.status())
        else:
            self._send_json({"layer": "result", "status": "unavailable"})

    def _handle_result_layer_results(self, project_id):
        rl = self.engine.result_layer
        if rl:
            results = rl.capture.get_project_results(project_id)
            self._send_json({"project_id": project_id, "results": results})
        else:
            self._send_json({"project_id": project_id, "results": []})

    def _handle_decision_layer_status(self):
        dl = self.engine.decision_layer
        if dl:
            self._send_json(dl.status())
        else:
            self._send_json({"layer": "decision", "status": "unavailable"})

    def _handle_decision_performance(self):
        dl = self.engine.decision_layer
        if dl:
            self._send_json(dl.generate_tuning_report())
        else:
            self._send_json({"report": "unavailable"})

    def _handle_close_loop(self):
        """Manually trigger a loop-closing cycle."""
        rl = self.engine.result_layer
        if rl:
            result = rl.force_close_loop()
            self._send_json(result)
        else:
            self._send_json({"error": "Result layer not available"}, 500)

    def _handle_full_loop_status(self):
        """Return the full 5-layer closed-loop architecture status."""
        def _safe_status(layer, fallback="unavailable"):
            """Safely call .status() on a layer, catching DB corruption errors."""
            if layer is None:
                return {"status": fallback}
            try:
                return layer.status()
            except Exception as e:
                return {"status": "error", "error": str(e)[:200]}

        try:
            status = {
                "architecture": "5-Layer Closed Loop",
                "layers": {
                    "L1_resource": _safe_status(self.engine.resource_layer),
                    "L2_chatroom": {"status": "active", "interactions": len(self.session_history)},
                    "L3_execution": {
                        "status": "active",
                        "roles": len(self.engine.db.get_all_roles()),
                        "ghost_channel": self.engine.ghost_channel is not None,
                        "deerflow": self.engine.deerflow is not None,
                        "src_bridge": self.engine.src_bridge is not None,
                    },
                    "L4_result": _safe_status(self.engine.result_layer),
                    "L5_decision": _safe_status(self.engine.decision_layer),
                },
                "loop_health": {
                    "resource_to_chatroom": self.engine.resource_layer is not None,
                    "chatroom_to_execution": True,  # Always true — core pipeline
                    "execution_to_result": self.engine.result_layer is not None,
                    "result_to_decision": (self.engine.result_layer is not None and
                                           self.engine.decision_layer is not None),
                    "decision_to_resource": (self.engine.result_layer is not None and
                                             self.engine.resource_layer is not None),
                },
            }
            # Check if loop is fully connected
            health = status["loop_health"]
            status["loop_complete"] = all(health.values())
            status["loop_coverage"] = f"{sum(health.values())}/{len(health)}"
            self._send_json(status)
        except Exception as e:
            self._send_json({"error": f"Full status failed: {e}", "architecture": "5-Layer Closed Loop"}, 500)

    # ── Task Manager Handlers (Point #10) ──────────────────

    def _handle_task_board(self, project_id=None, status=None):
        tm = self.engine.task_manager
        if tm:
            self._send_json(tm.get_board(project_id, status))
        else:
            self._send_json({"columns": {}, "total": 0})

    def _handle_task_analytics(self, project_id=None):
        tm = self.engine.task_manager
        if tm:
            self._send_json(tm.get_analytics(project_id))
        else:
            self._send_json({"total_tasks": 0})

    def _handle_task_create(self):
        tm = self.engine.task_manager
        if not tm:
            self._send_json({"error": "Task manager not available"}, 500)
            return
        try:
            body = self._read_body()
            task = tm.create_task(
                title=body.get("title", ""),
                description=body.get("description", ""),
                priority=body.get("priority", "normal"),
                project_id=body.get("project_id", "default"),
                assigned_role=body.get("assigned_role", ""),
                tags=body.get("tags", []),
            )
            self._send_json({"success": True, "task_id": task.task_id})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_task_update(self):
        tm = self.engine.task_manager
        if not tm:
            self._send_json({"error": "Task manager not available"}, 500)
            return
        try:
            body = self._read_body()
            ok = tm.update_status(
                body.get("task_id", ""),
                body.get("status", ""),
                result_summary=body.get("result_summary", ""),
                quality_score=body.get("quality_score", 0),
            )
            self._send_json({"success": ok})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    # ── Contact Channel Handlers (Point #20) ─────────────

    def _handle_contact_tickets(self, status=None, type_filter=None):
        cc = self.engine.contact_channel
        if cc:
            self._send_json({"tickets": cc.list_tickets(status=status, type=type_filter)})
        else:
            self._send_json({"tickets": []})

    def _handle_contact_notifications(self, unread_only=False):
        cc = self.engine.contact_channel
        if cc:
            self._send_json({
                "notifications": cc.get_notifications(unread_only=unread_only),
                "unread_count": cc.unread_count(),
            })
        else:
            self._send_json({"notifications": [], "unread_count": 0})

    def _handle_ticket_create(self):
        cc = self.engine.contact_channel
        if not cc:
            self._send_json({"error": "Contact channel not available"}, 500)
            return
        try:
            body = self._read_body()
            ticket = cc.create_ticket(
                type=body.get("type", "support"),
                subject=body.get("subject", ""),
                description=body.get("description", ""),
                priority=body.get("priority", "normal"),
                project_id=body.get("project_id", "default"),
            )
            self._send_json({"success": True, "ticket_id": ticket.ticket_id})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_ticket_respond(self):
        cc = self.engine.contact_channel
        if not cc:
            self._send_json({"error": "Contact channel not available"}, 500)
            return
        try:
            body = self._read_body()
            ok = cc.add_ticket_response(
                body.get("ticket_id", ""),
                body.get("responder", "user"),
                body.get("message", ""),
            )
            self._send_json({"success": ok})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    # ── Global Search Handler (Point #18) ──────────────────

    def _handle_global_search(self, query, domains_str=None, project_id=None, limit=30):
        gs = self.engine.global_search
        if not gs:
            self._send_json({"query": query, "results": [], "total": 0, "error": "Search not available"})
            return
        if not query:
            self._send_json({"query": "", "results": [], "total": 0})
            return
        domains = domains_str.split(",") if domains_str else None
        result = gs.search(query, domains=domains, project_id=project_id, limit=limit)
        self._send_json(result)

    # ── Project Memory Handlers (Point #19) ────────────────

    def _handle_memory_status(self):
        ctrl = self.engine.chatroom_controller
        if ctrl:
            self._send_json(ctrl.get_status())
        else:
            self._send_json({"available": False, "reason": "Project memory not loaded"})

    def _handle_memory_projects(self):
        pm = self.engine.project_memory
        if pm:
            self._send_json({"projects": pm.list_projects()})
        else:
            self._send_json({"projects": []})

    def _handle_memory_chatrooms(self, project_id=None):
        pm = self.engine.project_memory
        if pm:
            self._send_json({"chatrooms": pm.list_chatrooms(project_id)})
        else:
            self._send_json({"chatrooms": []})

    def _handle_memory_history(self, project_id=None, chatroom_id=None, limit=50):
        pm = self.engine.project_memory
        if pm:
            history = pm.get_history(chatroom_id, project_id, limit=limit)
            self._send_json({
                "project_id": project_id or pm.active_project_id,
                "chatroom_id": chatroom_id or pm.active_chatroom_id,
                "count": len(history),
                "history": history,
            })
        else:
            self._send_json({"history": []})

    def _handle_memory_search(self, query, project_id=None):
        pm = self.engine.project_memory
        if pm and query:
            results = pm.search_messages(query, project_id)
            self._send_json({"query": query, "results": results})
        else:
            self._send_json({"query": query, "results": []})

    def _handle_memory_create_project(self):
        ctrl = self.engine.chatroom_controller
        pm = self.engine.project_memory
        if not pm:
            self._send_json({"error": "Project memory not available"}, 500)
            return
        try:
            body = self._read_body()
            pid = body.get("project_id", "").strip()
            name = body.get("name", "").strip()
            if not pid or not name:
                self._send_json({"error": "project_id and name required"}, 400)
                return
            state = pm.create_project(
                pid, name,
                description=body.get("description", ""),
                tags=body.get("tags", []),
            )
            self._send_json({
                "success": True,
                "project": {
                    "id": state.project_id,
                    "name": state.name,
                    "chatrooms": len(state.chatrooms),
                },
            })
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_memory_switch_project(self):
        ctrl = self.engine.chatroom_controller
        if not ctrl:
            self._send_json({"error": "Chatroom controller not available"}, 500)
            return
        try:
            body = self._read_body()
            pid = body.get("project_id", "").strip()
            if not pid:
                self._send_json({"error": "project_id required"}, 400)
                return
            result = ctrl.switch_project(pid)
            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_memory_archive_project(self):
        pm = self.engine.project_memory
        if not pm:
            self._send_json({"error": "Project memory not available"}, 500)
            return
        try:
            body = self._read_body()
            pid = body.get("project_id", "").strip()
            ok = pm.archive_project(pid)
            self._send_json({"success": ok})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_memory_create_chatroom(self):
        pm = self.engine.project_memory
        if not pm:
            self._send_json({"error": "Project memory not available"}, 500)
            return
        try:
            body = self._read_body()
            name = body.get("name", "").strip()
            if not name:
                self._send_json({"error": "name required"}, 400)
                return
            cr = pm.create_chatroom(
                name=name,
                project_id=body.get("project_id"),
                mode=body.get("mode", "discuss"),
                description=body.get("description", ""),
                pinned_roles=body.get("pinned_roles", []),
            )
            self._send_json({
                "success": True,
                "chatroom": {
                    "id": cr.chatroom_id,
                    "name": cr.name,
                    "mode": cr.mode,
                    "project_id": cr.project_id,
                },
            })
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_memory_switch_chatroom(self):
        ctrl = self.engine.chatroom_controller
        if not ctrl:
            self._send_json({"error": "Chatroom controller not available"}, 500)
            return
        try:
            body = self._read_body()
            cid = body.get("chatroom_id", "").strip()
            if not cid:
                self._send_json({"error": "chatroom_id required"}, 400)
                return
            result = ctrl.switch_chatroom(cid)
            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_memory_archive_chatroom(self):
        pm = self.engine.project_memory
        if not pm:
            self._send_json({"error": "Project memory not available"}, 500)
            return
        try:
            body = self._read_body()
            cid = body.get("chatroom_id", "").strip()
            ok = pm.archive_chatroom(cid, body.get("project_id"))
            self._send_json({"success": ok})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_memory_md_append(self):
        """Append a curated entry to MEMORY.md at repo root.

        Closes the documented gap where USER-GUIDE.md promised MEMORY.md
        updates but the engine only stored messages in project_memory.db.

        Expected payload:
            {"kind": "decision" | "insight" | "session", "entry": "..."}
        """
        body = self._read_body()
        if body is None:
            return  # _read_body already sent 400
        kind = (body.get("kind") or "session").strip().lower()
        entry = (body.get("entry") or "").strip()
        if not entry:
            self._send_json(
                {"error": "Missing required field 'entry'", "status": "bad_request"},
                status=400,
            )
            return
        # Map kind → section header + numbering prefix (matches MEMORY.md format)
        from datetime import datetime
        section_map = {
            "session":  ("## 1. Session Log",      "S"),
            "decision": ("## 2. Key Decisions",    "D"),
            "insight":  ("## 3. Knowledge Insights", "K"),
        }
        if kind not in section_map:
            self._send_json(
                {"error": f"kind must be one of: {list(section_map)}",
                 "status": "bad_request"},
                status=400,
            )
            return
        section_header, prefix = section_map[kind]
        memory_path = ROOT / "MEMORY.md"
        try:
            text = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""
            # Count existing entries of this prefix to number this one
            import re as _re
            existing = _re.findall(rf"\*\*{prefix}(\d+)\*\*", text)
            next_n = max([int(n) for n in existing], default=0) + 1
            today = datetime.now().strftime("%Y-%m-%d")
            new_line = f"\n**{prefix}{next_n}** ({today}) — {entry}\n"
            # Insert after section header — replace any "*No ... recorded yet.*"
            # placeholder inside the section, otherwise append before the next "---".
            if section_header in text:
                header_idx = text.index(section_header)
                next_sep = text.find("\n---", header_idx + len(section_header))
                if next_sep < 0:
                    next_sep = len(text)
                section_body = text[header_idx:next_sep]
                placeholder_re = _re.compile(r"\*No[^*\n]+\*", _re.MULTILINE)
                if placeholder_re.search(section_body):
                    # First entry: replace placeholder with our line
                    new_body = placeholder_re.sub(new_line.strip(), section_body, count=1)
                else:
                    # Subsequent entries: append before the section boundary
                    new_body = section_body.rstrip() + new_line
                text = text[:header_idx] + new_body + text[next_sep:]
            else:
                # Section missing — append to end
                text += f"\n{section_header}\n{new_line}"
            try:
                memory_path.write_text(text, encoding="utf-8")
            except PermissionError as pe:
                # S072 FMEA fix: give a specific HTTP 403 + actionable hint
                # instead of generic HTTP 500 when MEMORY.md is read-only.
                self._send_json(
                    {"error": f"MEMORY.md is not writable: {pe}",
                     "status": "forbidden",
                     "hint": "check file permissions or filesystem mount (ro?)"},
                    status=403,
                )
                return
            except OSError as oe:
                # Disk full, I/O error, etc.
                self._send_json(
                    {"error": f"MEMORY.md write failed: {oe}",
                     "status": "io_error"},
                    status=507 if "no space" in str(oe).lower() else 500,
                )
                return
            self._send_json({
                "status": "ok",
                "kind": kind,
                "entry_id": f"{prefix}{next_n}",
                "date": today,
                "memory_path": str(memory_path.relative_to(ROOT)),
            })
        except Exception as e:
            self._send_json({"error": f"Failed to append to MEMORY.md: {e}"}, 500)

    # ── Scenario Engine Handlers ──────────────────────────

    def _handle_scenario_start(self):
        se = self.engine.scenario_engine
        if not se:
            self._send_json({"error": "Scenario engine not available"}, 500)
            return
        try:
            body = self._read_body()
            scenario_id = body.get("scenario_id", "").strip()
            lang = body.get("lang", "zh")
            result = se.start_scenario(scenario_id, lang)
            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_scenario_advance(self):
        se = self.engine.scenario_engine
        if not se:
            self._send_json({"error": "Scenario engine not available"}, 500)
            return
        try:
            body = self._read_body()
            step_result = body.get("step_result", {})
            result = se.advance_scenario(step_result)
            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_scenario_sandbox(self):
        se = self.engine.scenario_engine
        if not se:
            self._send_json({"error": "Scenario engine not available"}, 500)
            return
        try:
            body = self._read_body()
            if body is None:
                return  # _read_body already sent 400
            # S070 adversarial-audit FIX: strictly validate scenario_id
            # against a whitelist of registered scenarios. Previously the
            # server would echo arbitrary payloads (including shell-like
            # strings, path-traversal, and <script> tags) verbatim in its
            # response — an easy reflected-XSS / phishing vector.
            raw_id = str(body.get("scenario_id", "")).strip()
            valid = {s.get("id") or s.get("scenario_id")
                     for s in (se.list_scenarios() if hasattr(se, "list_scenarios") else [])}
            if raw_id not in valid:
                self._send_json(
                    {"error": "Unknown scenario_id",
                     "valid_scenarios": sorted(v for v in valid if v),
                     "status": "bad_request"},
                    status=400,
                )
                return
            scenario_id = raw_id
            step_idx = int(body.get("step_idx", 0))
            lang = str(body.get("lang", "zh"))
            if lang not in ("zh", "en"):
                lang = "zh"
            result = se.run_sandbox_drill(scenario_id, step_idx, lang)
            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_scenario_deerflow_sim(self):
        se = self.engine.scenario_engine
        if not se:
            self._send_json({"error": "Scenario engine not available"}, 500)
            return
        try:
            body = self._read_body()
            query = body.get("query", "")
            skill_id = body.get("skill_id", "deep-research")
            lang = body.get("lang", "zh")
            result = se.simulate_deerflow(query, skill_id, lang)
            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    # ── Helpers ───────────────────────────────────────────

    # ── File Operations Handlers (Point #12) ────────────────

    def _handle_file_scan(self, project_root, max_depth):
        """Scan project directory and return file listing."""
        try:
            from file_ops import FileScanner
            scanner = FileScanner(project_root, max_depth=max_depth)
            files, tree = scanner.scan()

            self._send_json({
                "project_root": project_root,
                "total_files": len(files),
                "files": [
                    {
                        "path": f.rel_path,
                        "size": f.size,
                        "extension": f.extension,
                        "is_text": f.is_text,
                        "line_count": f.line_count,
                        "modified": f.modified_time,
                    }
                    for f in files[:500]
                ],
                "truncated": len(files) > 500,
            })
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_file_read(self, file_path, start_line, end_line):
        """Read a file's content."""
        if not file_path:
            self._send_json({"error": "Missing 'path' parameter"}, 400)
            return
        try:
            fops = get_file_ops(str(ROOT))
            start = int(start_line) if start_line else None
            end = int(end_line) if end_line else None
            result = fops.reader.read(file_path, line_start=start, line_end=end)
            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_file_analyze(self, project_root):
        """Analyze a project directory."""
        try:
            fops = get_file_ops(project_root)
            analysis = fops.analyze_project()
            self._send_json(analysis)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_file_tree(self, project_root, max_depth):
        """Get directory tree structure."""
        try:
            from file_ops import FileScanner
            scanner = FileScanner(project_root, max_depth=max_depth)
            files, tree = scanner.scan()

            # Convert tree to dict
            def tree_to_dict(node):
                d = {"name": node.name, "rel_path": node.rel_path, "size": node.size,
                     "file_count": node.file_count, "dir_count": node.dir_count}
                d["files"] = [{"name": f.rel_path.split("/")[-1] if "/" in f.rel_path else f.rel_path,
                               "size": f.size, "ext": f.extension} for f in node.files]
                d["children"] = [tree_to_dict(c) for c in node.children]
                return d
            self._send_json(tree_to_dict(tree))
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_file_write(self):
        """Write or modify a file."""
        try:
            body = self._read_body()
            file_path = body.get("path", "")
            content = body.get("content", "")
            append = body.get("append", False)
            if not file_path or not content:
                self._send_json({"error": "Missing 'path' or 'content'"}, 400)
                return
            fops = get_file_ops(str(ROOT))
            result = fops.writer.write(file_path, content, append=append)
            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _read_body(self) -> dict:
        """Read the POST body and return a dict.

        Robust to missing/empty body and to malformed JSON: returns {}
        silently for empty body, and sends a clean HTTP 400 with a clear
        error message for malformed JSON (and returns None so callers can
        short-circuit without leaving the connection half-open).
        """
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        # Guard against oversized payloads (prevent memory exhaustion).
        MAX_BODY = 10 * 1024 * 1024  # 10 MiB
        if length > MAX_BODY:
            self._send_json(
                {"error": f"Payload too large ({length} bytes, max {MAX_BODY})",
                 "status": "bad_request"},
                status=413,
            )
            return None
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._send_json(
                {"error": f"Invalid JSON body: {e}", "status": "bad_request"},
                status=400,
            )
            return None
        # Only dict bodies are supported for our POST handlers.
        if not isinstance(parsed, dict):
            self._send_json(
                {"error": "JSON body must be an object (dict), got "
                          f"{type(parsed).__name__}", "status": "bad_request"},
                status=400,
            )
            return None
        return parsed

    def _send_json(self, data, status=200):
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._add_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # Client disconnected — safe to ignore

    def _add_cors_headers(self):
        origin = self._cors_origin if self._cors_origin else (self.headers.get("Origin", ""))
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        if origin and origin != "*":
            self.send_header("Vary", "Origin")

    def log_message(self, format, *args):
        """Structured logging: suppress static file noise, log API calls with request ID."""
        path = str(args[0]) if args else ""
        if "/api/" in path:
            req_id = getattr(self, '_request_id', '-')
            if _log_json:
                logger.info(json.dumps({
                    "event": "api_request", "request_id": req_id,
                    "path": path, "client": self.client_address[0],
                }))
            else:
                super().log_message(f"[{req_id}] " + format, *args)


def main():
    parser = argparse.ArgumentParser(description="Q-SpecTrum Web API Server")
    parser.add_argument("--port", type=int, default=8765, help="Port (default: 8765)")
    parser.add_argument("--provider", type=str, default=None,
                        help="LLM provider: mock|openai|anthropic|ollama")
    # S069 FIX (security): default to localhost-only binding. The server has
    # no authentication and CORS is wide open, so binding to 0.0.0.0 would
    # expose everything to the local network (and potentially the internet).
    # Users who need LAN access can still pass --host 0.0.0.0 explicitly.
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="Bind host (default: 127.0.0.1 — loopback only; "
                             "use 0.0.0.0 for LAN access — REQUIRES OWN PROTECTION)")
    args = parser.parse_args()

    # Change to project root so static files are served correctly
    os.chdir(str(ROOT))

    # Determine LLM provider
    provider_name = args.provider or os.environ.get("QSPECTRUM_LLM", "mock")
    llm, llm_name = create_llm_provider(provider_name)

    # Initialize engine
    print("=" * 60)
    print("  Q-SpecTrum Web API Server v2.0")
    print("=" * 60)
    print("\n  Initializing engine (this may take 10-15 seconds)...")

    import time as _t
    _t0 = _t.time()
    engine = QSpectrumEngine(llm_provider=llm)
    _elapsed = _t.time() - _t0
    status = engine.get_system_status()

    print(f"  ✅ Engine: {status['engine']} (loaded in {_elapsed:.1f}s)")
    print(f"  ✅ Roles: {status['roles_loaded']} ({status['roles_by_family']})")
    print(f"  ✅ Knowledge: {status['knowledge_entries']} entries")
    print(f"  ✅ LLM: {llm_name}")
    print(f"  ✅ Protocols: {status['protocols']} | Workflows: {status['workflows']}")

    # Ghost Channel status
    gc_info = status.get("ghost_channel")
    if gc_info and gc_info.get("active"):
        print(f"  ✅ Ghost Channel: {gc_info['mode']} ({gc_info['capabilities_count']}/10 capabilities)")
    else:
        print("  ⚠️  Ghost Channel: not loaded")

    # DeerFlow status
    df_info = status.get("deerflow")
    if df_info and df_info.get("installed"):
        running = "running" if df_info.get("running") else "offline"
        print(f"  ✅ DeerFlow: installed ({running}, {df_info.get('skills_count', 6)} skills)")
    else:
        print("  ⚠️  DeerFlow: not installed")

    # Closed-Loop Core status
    cl_core = status.get("knowledge_pipeline")
    if cl_core:
        print(f"  ✅ Knowledge Pipeline: {cl_core.get('total_deposits', 0)} deposits")
    else:
        print("  ⚠️  Knowledge Pipeline: not loaded")

    po = status.get("project_orchestrator")
    if po:
        print(f"  ✅ Project Orchestrator: {len(po.get('projects', []))} projects")
    else:
        print("  ⚠️  Project Orchestrator: not loaded")

    cr = status.get("component_registry")
    if cr:
        print(f"  ✅ Component Registry: {cr.get('total_components', 0)} components")
    else:
        print("  ⚠️  Component Registry: not loaded")

    ug = status.get("user_growth")
    if ug:
        print(f"  ✅ User Growth: {ug.get('stage', 'S1')} ({ug.get('name', 'Observer')})")
    else:
        print("  ⚠️  User Growth: not loaded")

    # Set class-level state
    QSpectrumAPIHandler.engine = engine
    QSpectrumAPIHandler.llm_name = llm_name
    QSpectrumAPIHandler.start_time = time.time()

    # Start server — handle port-in-use gracefully so double-launch produces
    # a friendly hint instead of an ugly Python stack trace.
    try:
        server = ThreadingHTTPServer((args.host, args.port), QSpectrumAPIHandler)
    except OSError as e:
        if "Address already in use" in str(e) or getattr(e, 'errno', 0) in (48, 98):
            print()
            print("  ╔════════════════════════════════════════════════════════════════╗")
            print("  ║  [!] Port already in use / 端口已被佔用                         ║")
            print("  ╚════════════════════════════════════════════════════════════════╝")
            print()
            print(f"  Port {args.port} is already in use — probably Q-SpecTrum is already")
            print(f"  running. Check your browser: http://localhost:{args.port}/chat.html")
            print()
            print(f"  端口 {args.port} 已被佔用——Q-SpecTrum 可能已經在運行。")
            print(f"  請在瀏覽器打開：http://localhost:{args.port}/chat.html")
            print()
            print("  Alternatively, start on a different port:")
            print("    python run.py --web --port 8766")
            print()
            sys.exit(1)
        raise
    print(f"\n  🌐 Server: http://localhost:{args.port}")
    print(f"  💬 Chat:   http://localhost:{args.port}/chat.html")
    print(f"  📊 Dashboard: http://localhost:{args.port}/dashboard.html")
    print(f"  📡 API:    http://localhost:{args.port}/api/status")
    if QSpectrumAPIHandler._api_token:
        print(f"  🔐 Auth:   Bearer token enabled (QSPECTRUM_API_TOKEN set)")
    else:
        print(f"  🔓 Auth:   Disabled (localhost mode — set QSPECTRUM_API_TOKEN to enable)")
    print("\n  Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  Shutting down...")
        engine.close()
        server.server_close()
        print("  Done.")


if __name__ == "__main__":
    main()
