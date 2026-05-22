"""
Q-SpecTrum Workflow Engine v1.0
================================
Reads workflow definitions from platform.db and executes them step-by-step.

Usage:
    python workflow_engine.py                    # List all workflows
    python workflow_engine.py run WF-0001        # Execute a workflow
    python workflow_engine.py status WF-0001     # Show workflow progress
    python workflow_engine.py dry-run WF-0001    # Preview without executing

Architecture:
    WorkflowEngine reads the PTS hierarchy (Phase→Task→Step) from the DB,
    creates a project_agent_run record, and walks through each step.
    Each step can invoke an agent module or record a manual checkpoint.
"""

import json
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path


class WorkflowEngine:
    """Reads and executes PTS-based workflows from platform.db."""

    def __init__(self, db_path=None):
        if db_path is None:
            try:
                from path_utils import get_db_path
                db_path = get_db_path()
            except ImportError:
                script_dir = Path(__file__).parent
                db_path = script_dir.parent / "db" / "platform.db"
        self.db_path = str(db_path)
        try:
            db_uri = f"file:{Path(self.db_path).resolve()}?immutable=1"
            self.conn = sqlite3.connect(db_uri, uri=True)
        except Exception:
            self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    # ──────────────────────────────────────────────
    # Query Methods
    # ──────────────────────────────────────────────

    def list_workflows(self):
        """List all workflow definitions."""
        rows = self.conn.execute(
            "SELECT workflow_code, workflow_name, workflow_type, summary "
            "FROM workflow_definitions ORDER BY workflow_code"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_workflow(self, wf_code):
        """Get a workflow definition by code."""
        row = self.conn.execute(
            "SELECT * FROM workflow_definitions WHERE workflow_code = ?",
            (wf_code,)
        ).fetchone()
        return dict(row) if row else None

    def get_phases(self, wf_id):
        """Get all phases for a workflow, ordered by phase_code."""
        rows = self.conn.execute(
            "SELECT * FROM workflow_phases WHERE workflow_id = ? ORDER BY phase_code",
            (wf_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_tasks(self, phase_id):
        """Get all tasks for a phase, ordered by task_code."""
        rows = self.conn.execute(
            "SELECT * FROM workflow_tasks WHERE phase_id = ? ORDER BY task_code",
            (phase_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_steps(self, task_id):
        """Get all steps for a task, ordered by sequence_no."""
        rows = self.conn.execute(
            "SELECT * FROM workflow_steps WHERE task_id = ? ORDER BY sequence_no",
            (task_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_full_pts(self, wf_code):
        """Get the complete PTS tree for a workflow."""
        wf = self.get_workflow(wf_code)
        if not wf:
            return None

        wf["phases"] = []
        for phase in self.get_phases(wf["id"]):
            phase["tasks"] = []
            for task in self.get_tasks(phase["id"]):
                task["steps"] = self.get_steps(task["id"])
                phase["tasks"].append(task)
            wf["phases"].append(phase)
        return wf

    # ──────────────────────────────────────────────
    # Execution Methods
    # ──────────────────────────────────────────────

    def create_run(self, project_id, demand_id, agent_id, agent_version_id):
        """Create a new project_agent_run record."""
        run_id = str(uuid.uuid4())
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        self.conn.execute(
            "INSERT INTO project_agent_runs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (run_id, project_id, demand_id, agent_id, agent_version_id,
             'running', now, None, 'workflow_engine', now, now)
        )
        self.conn.commit()
        return run_id

    def complete_run(self, run_id, status='completed'):
        """Mark a run as completed."""
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        self.conn.execute(
            "UPDATE project_agent_runs SET run_status=?, ended_at=?, updated_at=? WHERE id=?",
            (status, now, now, run_id)
        )
        self.conn.commit()

    def execute_step(self, step, dry_run=False):
        """Execute a single workflow step."""
        step_name = step.get('step_name', step.get('title', 'unnamed'))
        step_type = step.get('step_type', 'manual')
        instruction = step.get('instruction', '')

        result = {
            "sequence_no": step.get('sequence_no'),
            "step_name": step_name,
            "step_type": step_type,
            "status": "skipped" if dry_run else "completed",
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }

        if not dry_run:
            # In a real implementation, this would dispatch to the appropriate
            # agent module based on step_type. For now, we log the execution.
            if step_type == 'auto':
                result["note"] = f"Auto-executed: {instruction[:100]}"
            elif step_type == 'gate':
                result["note"] = f"Gate check: {instruction[:100]}"
                result["gate_passed"] = True
            else:
                result["note"] = f"Manual checkpoint: {instruction[:100]}"

        return result

    def run_workflow(self, wf_code, dry_run=False):
        """Execute a complete workflow."""
        pts = self.get_full_pts(wf_code)
        if not pts:
            return {"error": f"Workflow {wf_code} not found"}

        execution_log = {
            "workflow_code": wf_code,
            "workflow_name": pts["workflow_name"],
            "mode": "dry-run" if dry_run else "live",
            "started_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "phases": [],
            "total_steps": 0,
            "completed_steps": 0,
        }

        for phase in pts["phases"]:
            phase_log = {
                "phase_code": phase["phase_code"],
                "phase_name": phase["phase_name"],
                "tasks": []
            }

            for task in phase["tasks"]:
                task_log = {
                    "task_code": task["task_code"],
                    "task_name": task["task_name"],
                    "steps": []
                }

                for step in task["steps"]:
                    execution_log["total_steps"] += 1
                    result = self.execute_step(step, dry_run=dry_run)
                    task_log["steps"].append(result)
                    if result["status"] == "completed":
                        execution_log["completed_steps"] += 1

                phase_log["tasks"].append(task_log)
            execution_log["phases"].append(phase_log)

        execution_log["ended_at"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        execution_log["status"] = "completed" if not dry_run else "preview"
        return execution_log

    # ──────────────────────────────────────────────
    # Status Methods
    # ──────────────────────────────────────────────

    def get_run_history(self, limit=10):
        """Get recent agent run records."""
        rows = self.conn.execute(
            "SELECT * FROM project_agent_runs ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def main():
    """CLI entry point."""
    # Determine DB path from config
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

    engine = WorkflowEngine()

    if len(sys.argv) < 2:
        # List workflows
        print("Q-SpecTrum Workflow Engine v1.0")
        print("=" * 50)
        workflows = engine.list_workflows()
        for wf in workflows:
            print(f"  {wf['workflow_code']}: {wf['workflow_name']} [{wf['workflow_type']}]")
            if wf.get('summary'):
                print(f"    {wf['summary'][:80]}")
        print(f"\nTotal: {len(workflows)} workflows")
        print("\nUsage:")
        print("  python workflow_engine.py run <WF-CODE>")
        print("  python workflow_engine.py dry-run <WF-CODE>")
        print("  python workflow_engine.py status <WF-CODE>")
        print("  python workflow_engine.py history")

    elif sys.argv[1] == 'run' and len(sys.argv) > 2:
        wf_code = sys.argv[2]
        print(f"Executing {wf_code}...")
        result = engine.run_workflow(wf_code, dry_run=False)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif sys.argv[1] == 'dry-run' and len(sys.argv) > 2:
        wf_code = sys.argv[2]
        print(f"Dry-run {wf_code}...")
        result = engine.run_workflow(wf_code, dry_run=True)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif sys.argv[1] == 'status' and len(sys.argv) > 2:
        wf_code = sys.argv[2]
        pts = engine.get_full_pts(wf_code)
        if pts:
            total_steps = sum(
                len(task.get("steps", []))
                for phase in pts["phases"]
                for task in phase["tasks"]
            )
            print(f"Workflow: {pts['workflow_name']} ({wf_code})")
            print(f"Phases: {len(pts['phases'])}")
            print(f"Total steps: {total_steps}")
            for phase in pts["phases"]:
                task_count = len(phase["tasks"])
                step_count = sum(len(t.get("steps", [])) for t in phase["tasks"])
                print(f"  {phase['phase_code']}: {phase['phase_name']} ({task_count}T / {step_count}S)")
        else:
            print(f"Workflow {wf_code} not found")

    elif sys.argv[1] == 'history':
        runs = engine.get_run_history()
        for r in runs:
            print(f"  {r['run_status']:12s} | {r['started_at']} | agent={r['agent_id'][:8]}...")

    engine.close()


if __name__ == '__main__':
    main()
