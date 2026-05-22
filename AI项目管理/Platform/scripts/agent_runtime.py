"""
Q-SpecTrum Agent Runtime v1.1
================================
The glue layer that connects:
  workflow_engine → agent_modules → LLM → DB results

This is the missing link that makes Q-SpecTrum actually "think".

Architecture:
  WorkflowEngine.execute_step(step)
    → AgentRuntime.dispatch(step)
      → resolve which Agent + Module handles this step
      → build prompt from role's activation_card + step context + knowledge
      → call LLM (via src/llm/ abstraction layer)
      → write results back to DB (interaction_logs, project_agent_runs)

LLM Provider:
  Uses src/llm/ unified abstraction. Falls back to inline MockLLM if src/ unavailable.
  To switch providers: pass an LLMProvider instance to AgentRuntime(llm=provider).

Usage:
    python agent_runtime.py                    # Show system status
    python agent_runtime.py run WF-0001        # Run workflow with agent dispatch
    python agent_runtime.py chat ROLE-S01       # Chat with a specific role
    python agent_runtime.py demo               # Run a full demo cycle
"""

import json
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── LLM Provider: prefer src/llm/ abstraction, fallback to inline ───

_LLM_SOURCE = "inline"  # Track which LLM backend is active

def _try_import_src_llm():
    """Try to import LLM abstraction from src/llm/ package."""
    global _LLM_SOURCE
    try:
        # Add project root to path so src/ is importable
        project_root = Path(__file__).resolve().parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from src.llm.base import LLMRequest as SrcLLMRequest
        from src.llm.base import LLMResponse as SrcLLMResponse
        from src.llm.mock import SyncMockLLMProvider
        _LLM_SOURCE = "src/llm"
        return SrcLLMRequest, SrcLLMResponse, SyncMockLLMProvider
    except ImportError:
        return None, None, None

SrcLLMRequest, SrcLLMResponse, SrcSyncMockProvider = _try_import_src_llm()


class LLMRequest:
    """Standardized LLM request — compatible with src/llm/base.LLMRequest."""
    def __init__(self, system_prompt: str, user_message: str,
                 context: dict = None, role_id: str = "", family: str = ""):
        self.system_prompt = system_prompt
        self.user_message = user_message
        self.context = context or {}
        self.knowledge_snippets = []
        self.temperature = 0.7
        self.max_tokens = 2048
        self.role_id = role_id
        self.family = family

class LLMResponse:
    """Standardized LLM response — compatible with src/llm/base.LLMResponse."""
    def __init__(self, content: str, model: str = "mock", tokens: int = 0):
        self.content = content
        self.model = model
        self.tokens = tokens
        self.tokens_used = tokens
        self.latency_ms = 0.0
        self.finish_reason = "stop"


class _InlineMockLLM:
    """Fallback mock LLM when src/llm/ is not available."""

    def generate(self, request) -> LLMResponse:
        family = request.family
        msg = request.user_message[:200]
        ctx = getattr(request, 'context', {})
        role = request.role_id

        if family == "Trum":
            content = f"[Trum 戰略評估]\n任務: {msg}\n結論: 已完成風險與價值評估，建議推進。"
        elif family == "Spec":
            content = f"[Spec 架構審計]\n檢查項: {msg}\n結論: 符合規範，路徑合規。"
        elif family == "QCM":
            content = f"[QCM 執行]\n任務: {msg}\n結論: 基於專業知識完成分析，建議結合其他視角迭代。"
        else:
            content = f"[{role} 回應]\n任務: {msg}\n結論: 已處理。上下文: {json.dumps(ctx, ensure_ascii=False)[:100]}"
        return LLMResponse(content=content, model="inline-mock-v1", tokens=len(content))


def create_default_llm():
    """Create the best available LLM provider.

    Priority:
    1. src/llm/SyncMockLLMProvider (unified abstraction)
    2. _InlineMockLLM (standalone fallback)
    """
    if SrcSyncMockProvider is not None:
        return SrcSyncMockProvider()
    return _InlineMockLLM()


# ─── Agent Runtime Core ───

class AgentRuntime:
    """
    Connects workflow steps to agent modules and LLM execution.

    Flow:
    1. Resolve step → find responsible agent + module
    2. Load role's activation_card as system prompt
    3. Build context from workflow state + knowledge
    4. Call LLM
    5. Log interaction and return result
    """

    def __init__(self, db_path=None, llm=None):
        if db_path is None:
            db_dir = Path(__file__).parent.parent / "db"
            # Try each candidate; pick first that passes SQLite connection test.
            # Any DB may be corrupted by virtiofs, so always verify before using.
            candidates = [
                db_dir / "platform.db",
                db_dir / "platform_restored.db",
                db_dir / "platform_v4.1.db",
            ]
            for candidate in candidates:
                if candidate.exists() and candidate.stat().st_size > 0:
                    # Verify it's actually usable (not a stale virtiofs ghost)
                    # CRITICAL: use immutable URI — plain sqlite3.connect() on
                    # virtiofs-backed files zeros the file on close (the very
                    # behavior this block was meant to detect).
                    try:
                        test_uri = f"file:{Path(candidate).resolve()}?immutable=1"
                        test_conn = sqlite3.connect(test_uri, uri=True)
                        test_conn.execute("SELECT COUNT(*) FROM sqlite_master")
                        test_conn.close()
                        db_path = candidate
                        break
                    except Exception:
                        continue
            if db_path is None:
                db_path = db_dir / "platform.db"  # will error, but at expected path
        self.db_path = str(db_path)
        # Use immutable mode for virtiofs compatibility
        try:
            db_uri = f"file:{Path(self.db_path).resolve()}?immutable=1"
            self.conn = sqlite3.connect(db_uri, uri=True)
        except Exception:
            self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.llm = llm or create_default_llm()
        self._llm_source = _LLM_SOURCE

        # Cache: agent_code → {agent info + modules + role}
        self._agent_cache = {}
        self._role_cache = {}
        self._load_agents()
        self._load_roles()

    def close(self):
        self.conn.close()

    def _load_agents(self):
        """Load all agents and their modules into cache."""
        agents = self.conn.execute(
            "SELECT * FROM agents ORDER BY agent_code"
        ).fetchall()
        for a in agents:
            agent = dict(a)
            modules = self.conn.execute(
                "SELECT * FROM agent_modules WHERE agent_id = ?", (a['id'],)
            ).fetchall()
            agent['modules'] = {m['module_code']: dict(m) for m in modules}
            self._agent_cache[a['agent_code']] = agent

    def _load_roles(self):
        """Load all roles into cache."""
        roles = self.conn.execute("SELECT * FROM ai_roles").fetchall()
        for r in roles:
            self._role_cache[r['role_code']] = dict(r)

    def get_agent_for_step(self, step: dict) -> Optional[dict]:
        """Resolve which agent should handle a workflow step.

        Uses executor_type + step_name for routing (matching actual DB schema).
        """
        executor_type = step.get('executor_type', 'agent')
        step_name = step.get('step_name', '')
        name_lower = step_name.lower()

        # Strategy: match executor_type and step_name keywords to agents
        # gate/validate → Validator (AGT-0007)
        # plan/schedule/estimate/deadline → Planner (AGT-0006)
        # scout/evaluate/assess/criteria → Scout (AGT-0005)
        # sop/skill/template/deliverable → SOP Engineer (AGT-0004)
        # prompt/optim → Prompt Engineer (AGT-0003)
        # navigate/route/classify/assign → Navigator (AGT-0002)
        # default → Coordinator (AGT-0001)
        if executor_type == 'gate' or any(k in name_lower for k in ['validat', 'verif', 'approv', 'gate']):
            return self._agent_cache.get('AGT-0007')  # Validator
        elif any(k in name_lower for k in ['plan', 'pts', 'schedul', 'estimat', 'deadline', 'phase', 'critical path']):
            return self._agent_cache.get('AGT-0006')  # Planner
        elif any(k in name_lower for k in ['scout', 'evaluat', 'assess', 'criteria', 'objectiv']):
            return self._agent_cache.get('AGT-0005')  # Scout
        elif any(k in name_lower for k in ['sop', 'skill', 'template', 'deliverable', 'document']):
            return self._agent_cache.get('AGT-0004')  # SOP Engineer
        elif any(k in name_lower for k in ['prompt', 'optim']):
            return self._agent_cache.get('AGT-0003')  # Prompt Engineer
        elif any(k in name_lower for k in ['navig', 'route', 'classif', 'assign', 'executor']):
            return self._agent_cache.get('AGT-0002')  # Navigator
        else:
            return self._agent_cache.get('AGT-0001')  # Coordinator (default)

    def get_role_for_agent(self, agent: dict) -> Optional[dict]:
        """Find the ARCS role associated with an agent."""
        agent_name = agent.get('agent_name', '').lower()
        # Map agent to role family
        if 'coordinator' in agent_name:
            return self._role_cache.get('ROLE-S03')
        elif 'validator' in agent_name:
            return self._role_cache.get('ROLE-Q06')
        elif 'planner' in agent_name:
            return self._role_cache.get('ROLE-Q04')
        elif 'scout' in agent_name:
            return self._role_cache.get('ROLE-Q05')
        elif 'sop' in agent_name:
            return self._role_cache.get('ROLE-Q03')
        elif 'prompt' in agent_name:
            return self._role_cache.get('ROLE-Q02')
        elif 'navigator' in agent_name:
            return self._role_cache.get('ROLE-S02')
        return self._role_cache.get('ROLE-S01')

    def get_role_family(self, role_code: str) -> str:
        """Determine the family of a role."""
        if role_code.startswith('ROLE-Q'):
            return 'QCM'
        elif role_code.startswith('ROLE-S'):
            return 'Spec'
        else:
            return 'Trum'

    def build_prompt(self, role: dict, step: dict, wf_context: dict = None) -> str:
        """Build the system prompt for a step execution."""
        parts = []

        # 1. Role identity (from activation_card or role_name)
        card = role.get('activation_card', '')
        if card and len(card) > 100:
            # Use first 2000 chars of activation card as identity
            parts.append(card[:2000])
        else:
            parts.append(f"你是 {role.get('role_name', 'AI角色')}。{role.get('role_description', '')}")

        # 2. Current task
        parts.append(f"\n當前任務: {step.get('step_name', '未命名')}")
        parts.append(f"步驟編號: {step.get('step_code', 'N/A')}")
        parts.append(f"執行類型: {step.get('executor_type', 'agent')}")

        # 3. Workflow context
        if wf_context:
            parts.append(f"\n工作流上下文: {json.dumps(wf_context, ensure_ascii=False)[:500]}")

        return "\n".join(parts)

    def dispatch_step(self, step: dict, wf_context: dict = None) -> dict:
        """
        Execute a workflow step through the agent runtime.

        Returns:
            {agent, role, family, llm_response, log_id, status}
        """
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

        # 1. Resolve agent
        agent = self.get_agent_for_step(step)
        if not agent:
            return {"status": "error", "error": "No agent found for step"}

        # 2. Resolve role
        role = self.get_role_for_agent(agent)
        role_code = role['role_code'] if role else 'UNKNOWN'
        family = self.get_role_family(role_code)

        # 3. Build prompt
        prompt = self.build_prompt(role, step, wf_context) if role else ""

        # 4. Call LLM
        request = LLMRequest(
            system_prompt=prompt,
            user_message=step.get('step_name', ''),
            context=wf_context or {},
            role_id=role_code,
            family=family,
        )
        response = self.llm.generate(request)

        # 5. Log interaction (skip on read-only/immutable mounts)
        log_id = str(uuid.uuid4())
        try:
            self.conn.execute(
                "INSERT INTO interaction_logs VALUES (?,?,?,?,?,?,?)",
                (log_id, now, role_code, 'workflow_engine', 'step_execution',
                 'completed', json.dumps({
                     "agent": agent['agent_code'],
                     "step": step.get('step_name', ''),
                     "response_preview": response.content[:200],
                     "tokens": getattr(response, 'tokens', getattr(response, 'tokens_used', 0)),
                 }))
            )
            self.conn.commit()
        except Exception:
            pass  # Read-only mode (virtiofs immutable)

        return {
            "status": "completed",
            "agent_code": agent['agent_code'],
            "agent_name": agent['agent_name'],
            "role_code": role_code,
            "family": family,
            "response": response.content,
            "tokens": getattr(response, 'tokens', getattr(response, 'tokens_used', 0)),
            "log_id": log_id,
            "timestamp": now,
        }

    def chat_with_role(self, role_code: str, user_message: str) -> dict:
        """Direct chat with a specific role."""
        role = self._role_cache.get(role_code)
        if not role:
            return {"error": f"Role {role_code} not found"}

        family = self.get_role_family(role_code)
        card = role.get('activation_card', '')
        system_prompt = card[:2000] if len(card) > 100 else f"你是 {role['role_name']}。"

        request = LLMRequest(
            system_prompt=system_prompt,
            user_message=user_message,
            role_id=role_code,
            family=family,
        )
        response = self.llm.generate(request)

        # Log
        log_id = str(uuid.uuid4())
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        try:
            self.conn.execute(
                "INSERT INTO interaction_logs VALUES (?,?,?,?,?,?,?)",
                (log_id, now, role_code, 'user', 'chat',
                 'completed', json.dumps({
                     "user_message": user_message[:200],
                     "response_preview": response.content[:200],
                 }))
            )
            self.conn.commit()
        except Exception:
            pass  # Read-only mode (virtiofs immutable)

        return {
            "role_code": role_code,
            "role_name": role['role_name'],
            "family": family,
            "response": response.content,
            "log_id": log_id,
        }

    def run_workflow_with_agents(self, wf_code: str, dry_run: bool = False) -> dict:
        """
        Run a complete workflow with real agent dispatch.

        This is the UPGRADED version of workflow_engine.run_workflow()
        that actually invokes agents through the runtime.
        """
        try:
            from workflow_engine import WorkflowEngine
        except ImportError:
            # When run from project root instead of scripts/ directory
            script_dir = str(Path(__file__).resolve().parent)
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            from workflow_engine import WorkflowEngine
        engine = WorkflowEngine(self.db_path)
        pts = engine.get_full_pts(wf_code)
        engine.close()

        if not pts:
            return {"error": f"Workflow {wf_code} not found"}

        execution = {
            "workflow_code": wf_code,
            "workflow_name": pts["workflow_name"],
            "mode": "dry-run" if dry_run else "agent-dispatch",
            "started_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "phases": [],
            "total_steps": 0,
            "completed_steps": 0,
            "agents_invoked": set(),
            "roles_invoked": set(),
            "total_tokens": 0,
        }

        for phase in pts["phases"]:
            phase_log = {
                "phase_code": phase["phase_code"],
                "phase_name": phase["phase_name"],
                "tasks": [],
            }

            for task in phase["tasks"]:
                task_log = {
                    "task_code": task["task_code"],
                    "task_name": task["task_name"],
                    "steps": [],
                }

                for step in task["steps"]:
                    execution["total_steps"] += 1

                    if dry_run:
                        agent = self.get_agent_for_step(step)
                        role = self.get_role_for_agent(agent) if agent else None
                        task_log["steps"].append({
                            "sequence_no": step.get('sequence_no'),
                            "step_name": step.get('step_name', ''),
                            "would_dispatch_to": agent['agent_code'] if agent else 'none',
                            "role": role['role_code'] if role else 'none',
                            "status": "preview",
                        })
                    else:
                        wf_context = {
                            "workflow": wf_code,
                            "phase": phase["phase_code"],
                            "task": task["task_code"],
                        }
                        result = self.dispatch_step(step, wf_context)
                        task_log["steps"].append({
                            "sequence_no": step.get('sequence_no'),
                            "step_name": step.get('step_name', ''),
                            "agent": result.get("agent_code"),
                            "role": result.get("role_code"),
                            "family": result.get("family"),
                            "status": result.get("status"),
                            "response_preview": result.get("response", "")[:100],
                            "tokens": result.get("tokens", 0),
                        })
                        if result.get("status") == "completed":
                            execution["completed_steps"] += 1
                            execution["agents_invoked"].add(result.get("agent_code", ""))
                            execution["roles_invoked"].add(result.get("role_code", ""))
                            execution["total_tokens"] += result.get("tokens", 0)

                phase_log["tasks"].append(task_log)
            execution["phases"].append(phase_log)

        execution["ended_at"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        execution["status"] = "completed" if not dry_run else "preview"
        execution["agents_invoked"] = list(execution["agents_invoked"])
        execution["roles_invoked"] = list(execution["roles_invoked"])
        return execution

    def get_status(self) -> dict:
        """Get runtime status."""
        agents = len(self._agent_cache)
        roles = len(self._role_cache)
        total_modules = sum(len(a['modules']) for a in self._agent_cache.values())
        logs = self.conn.execute("SELECT COUNT(*) FROM interaction_logs").fetchone()[0]

        return {
            "agents": agents,
            "roles": roles,
            "modules": total_modules,
            "interaction_logs": logs,
            "llm_backend": type(self.llm).__name__,
            "llm_source": getattr(self, '_llm_source', 'unknown'),
            "db_path": self.db_path,
        }


def main():
    """CLI entry point."""
    # Support --db flag: python agent_runtime.py --db path/to/db [command ...]
    db_path = None
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == '--db':
        db_path = args[1]
        args = args[2:]
    else:
        args = args

    runtime = AgentRuntime(db_path=db_path)

    if len(args) < 1:
        print("Q-SpecTrum Agent Runtime v1.1")
        print("=" * 55)
        status = runtime.get_status()
        print(f"  Agents:  {status['agents']}")
        print(f"  Roles:   {status['roles']}")
        print(f"  Modules: {status['modules']}")
        print(f"  Logs:    {status['interaction_logs']}")
        print(f"  LLM:     {status['llm_backend']} (from {status['llm_source']})")
        print(f"  DB:      {status['db_path']}")
        print()
        print("Agents loaded:")
        for code, agent in sorted(runtime._agent_cache.items()):
            mods = list(agent['modules'].keys())
            print(f"  {code}: {agent['agent_name']} ({len(mods)} modules)")
        print()
        print("Usage:")
        print("  python agent_runtime.py run <WF-CODE>        # Run with agent dispatch")
        print("  python agent_runtime.py dry-run <WF-CODE>    # Preview agent assignments")
        print("  python agent_runtime.py chat <ROLE-CODE> <message>")
        print("  python agent_runtime.py demo                 # Full demo cycle")

    elif args[0] == 'run' and len(args) > 1:
        wf_code = args[1]
        print(f"Running {wf_code} with agent dispatch...")
        result = runtime.run_workflow_with_agents(wf_code)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args[0] == 'dry-run' and len(args) > 1:
        wf_code = args[1]
        print(f"Previewing agent assignments for {wf_code}...")
        result = runtime.run_workflow_with_agents(wf_code, dry_run=True)
        # Compact output
        for phase in result["phases"]:
            print(f"\n[{phase['phase_code']}] {phase['phase_name']}")
            for task in phase["tasks"]:
                print(f"  [{task['task_code']}] {task['task_name']}")
                for step in task["steps"]:
                    print(f"    Step {step['sequence_no']}: {step['step_name'][:40]:40s} "
                          f"→ {step['would_dispatch_to']} ({step['role']})")

    elif args[0] == 'chat' and len(args) > 2:
        role_code = args[1]
        message = " ".join(args[2:])
        result = runtime.chat_with_role(role_code, message)
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n[{result['role_name']}] ({result['family']})")
            print(f"{result['response']}")

    elif args[0] == 'demo':
        print("Q-SpecTrum Agent Runtime Demo")
        print("=" * 55)

        # 1. Show status
        status = runtime.get_status()
        print(f"\n[1] System: {status['agents']} agents, {status['roles']} roles, "
              f"{status['modules']} modules")

        # 2. Dry-run WF-0001
        print("\n[2] Dry-run WF-0001 (Coordinator Routing Flow)...")
        result = runtime.run_workflow_with_agents('WF-0001', dry_run=True)
        print(f"    Steps: {result['total_steps']}")

        # 3. Live run WF-0003
        print("\n[3] Live run WF-0003 (Planner PTS Flow)...")
        result = runtime.run_workflow_with_agents('WF-0003')
        print(f"    Completed: {result['completed_steps']}/{result['total_steps']}")
        print(f"    Agents: {result['agents_invoked']}")
        print(f"    Roles: {result['roles_invoked']}")
        print(f"    Tokens: {result['total_tokens']}")

        # 4. Chat with a role
        print("\n[4] Chat with ROLE-S03 (Coordinator)...")
        chat = runtime.chat_with_role('ROLE-S03', '請評估目前系統的整合狀態')
        print(f"    {chat['response'][:150]}")

        print("\n[5] Final status:")
        status = runtime.get_status()
        print(f"    Interaction logs: {status['interaction_logs']}")
        print("\nDemo complete!")

    runtime.close()


if __name__ == '__main__':
    main()
