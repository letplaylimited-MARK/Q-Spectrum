"""
Complete Platform Database Setup Script.
Builds the full SQLite schema (all tables) and seeds all MVP data.
"""
import json
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "Platform" / "db" / "platform.db"
IMPORTER = ROOT / "Platform" / "scripts" / "importers" / "import_documents.py"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def setup_schema(conn: sqlite3.Connection):
    """Create all tables matching the PostgreSQL schema design."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            display_name TEXT NOT NULL,
            email TEXT COLLATE NOCASE,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS teams (
            id TEXT PRIMARY KEY,
            team_code TEXT NOT NULL UNIQUE,
            team_name TEXT NOT NULL,
            owner_user_id TEXT REFERENCES users(id),
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS team_members (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role_code TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            UNIQUE(team_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            project_code TEXT NOT NULL UNIQUE,
            project_name TEXT NOT NULL,
            summary TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            priority TEXT NOT NULL DEFAULT 'medium',
            owner_team_id TEXT REFERENCES teams(id),
            created_by TEXT REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS project_stages (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            stage_code TEXT NOT NULL,
            stage_name TEXT NOT NULL,
            started_at TEXT,
            ended_at TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS pain_points (
            id TEXT PRIMARY KEY,
            pain_code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category_code TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'medium',
            frequency_score INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS project_pain_points (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            pain_point_id TEXT NOT NULL REFERENCES pain_points(id) ON DELETE CASCADE,
            impact_score INTEGER NOT NULL DEFAULT 1,
            source_note TEXT,
            UNIQUE(project_id, pain_point_id)
        );

        CREATE TABLE IF NOT EXISTS demands (
            id TEXT PRIMARY KEY,
            demand_code TEXT NOT NULL UNIQUE,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            source_type TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'draft',
            created_by TEXT REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS demand_items (
            id TEXT PRIMARY KEY,
            demand_id TEXT NOT NULL REFERENCES demands(id) ON DELETE CASCADE,
            item_code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            acceptance_criteria TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS demand_pain_links (
            id TEXT PRIMARY KEY,
            demand_id TEXT NOT NULL REFERENCES demands(id) ON DELETE CASCADE,
            pain_point_id TEXT NOT NULL REFERENCES pain_points(id) ON DELETE CASCADE,
            link_type TEXT NOT NULL DEFAULT 'addresses',
            UNIQUE(demand_id, pain_point_id)
        );

        CREATE TABLE IF NOT EXISTS solutions (
            id TEXT PRIMARY KEY,
            solution_code TEXT NOT NULL UNIQUE,
            solution_name TEXT NOT NULL,
            solution_type TEXT NOT NULL,
            summary TEXT,
            maturity_level TEXT NOT NULL DEFAULT 'draft',
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS solution_demand_links (
            id TEXT PRIMARY KEY,
            solution_id TEXT NOT NULL REFERENCES solutions(id) ON DELETE CASCADE,
            demand_id TEXT NOT NULL REFERENCES demands(id) ON DELETE CASCADE,
            fit_score INTEGER NOT NULL DEFAULT 3,
            UNIQUE(solution_id, demand_id)
        );

        CREATE TABLE IF NOT EXISTS solution_pain_links (
            id TEXT PRIMARY KEY,
            solution_id TEXT NOT NULL REFERENCES solutions(id) ON DELETE CASCADE,
            pain_point_id TEXT NOT NULL REFERENCES pain_points(id) ON DELETE CASCADE,
            fit_score INTEGER NOT NULL DEFAULT 3,
            UNIQUE(solution_id, pain_point_id)
        );

        CREATE TABLE IF NOT EXISTS systems (
            id TEXT PRIMARY KEY,
            system_code TEXT NOT NULL UNIQUE,
            system_name TEXT NOT NULL,
            version TEXT,
            summary TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS repositories (
            id TEXT PRIMARY KEY,
            system_id TEXT REFERENCES systems(id) ON DELETE SET NULL,
            repository_code TEXT NOT NULL UNIQUE,
            repository_name TEXT NOT NULL,
            local_path TEXT NOT NULL,
            remote_url TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            agent_code TEXT NOT NULL UNIQUE,
            agent_name TEXT NOT NULL,
            agent_type TEXT NOT NULL,
            system_id TEXT REFERENCES systems(id) ON DELETE SET NULL,
            summary TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS agent_versions (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            version TEXT NOT NULL,
            changelog TEXT,
            prompt_body_md TEXT,
            released_at TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            UNIQUE(agent_id, version)
        );

        CREATE TABLE IF NOT EXISTS agent_modules (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            module_code TEXT NOT NULL UNIQUE,
            module_name TEXT NOT NULL,
            module_type TEXT NOT NULL,
            spec_jsonb TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS agent_triggers (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            trigger_text TEXT NOT NULL,
            language_code TEXT NOT NULL DEFAULT 'en',
            is_primary INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS agent_capabilities (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            capability_code TEXT NOT NULL,
            capability_name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS workflow_definitions (
            id TEXT PRIMARY KEY,
            workflow_code TEXT NOT NULL UNIQUE,
            workflow_name TEXT NOT NULL,
            workflow_type TEXT NOT NULL,
            summary TEXT,
            source_system_id TEXT REFERENCES systems(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS workflow_phases (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL REFERENCES workflow_definitions(id) ON DELETE CASCADE,
            phase_code TEXT NOT NULL,
            phase_name TEXT NOT NULL,
            sequence_no INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS workflow_tasks (
            id TEXT PRIMARY KEY,
            phase_id TEXT NOT NULL REFERENCES workflow_phases(id) ON DELETE CASCADE,
            task_code TEXT NOT NULL,
            task_name TEXT NOT NULL,
            sequence_no INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS workflow_steps (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES workflow_tasks(id) ON DELETE CASCADE,
            step_code TEXT NOT NULL,
            step_name TEXT NOT NULL,
            executor_type TEXT NOT NULL,
            sequence_no INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS project_agent_runs (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            demand_id TEXT REFERENCES demands(id) ON DELETE SET NULL,
            agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE RESTRICT,
            agent_version_id TEXT REFERENCES agent_versions(id) ON DELETE SET NULL,
            run_status TEXT NOT NULL DEFAULT 'queued',
            started_at TEXT,
            ended_at TEXT,
            created_by TEXT REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS handoff_packages (
            id TEXT PRIMARY KEY,
            handoff_code TEXT NOT NULL UNIQUE,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            from_agent_id TEXT REFERENCES agents(id) ON DELETE SET NULL,
            to_agent_id TEXT REFERENCES agents(id) ON DELETE SET NULL,
            schema_version TEXT NOT NULL,
            payload_jsonb TEXT NOT NULL DEFAULT '{}',
            raw_yaml TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS handoff_package_links (
            id TEXT PRIMARY KEY,
            parent_handoff_id TEXT NOT NULL REFERENCES handoff_packages(id) ON DELETE CASCADE,
            child_handoff_id TEXT NOT NULL REFERENCES handoff_packages(id) ON DELETE CASCADE,
            link_type TEXT NOT NULL DEFAULT 'sequential',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS validation_runs (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            solution_id TEXT REFERENCES solutions(id) ON DELETE SET NULL,
            validator_agent_id TEXT REFERENCES agents(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'planned',
            started_at TEXT,
            ended_at TEXT
        );

        CREATE TABLE IF NOT EXISTS validation_test_cases (
            id TEXT PRIMARY KEY,
            validation_run_id TEXT NOT NULL REFERENCES validation_runs(id) ON DELETE CASCADE,
            case_code TEXT NOT NULL,
            title TEXT NOT NULL,
            input_jsonb TEXT NOT NULL DEFAULT '{}',
            expected_jsonb TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS validation_results (
            id TEXT PRIMARY KEY,
            test_case_id TEXT NOT NULL REFERENCES validation_test_cases(id) ON DELETE CASCADE,
            result_status TEXT NOT NULL,
            actual_jsonb TEXT NOT NULL DEFAULT '{}',
            score_jsonb TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS validation_defects (
            id TEXT PRIMARY KEY,
            validation_run_id TEXT NOT NULL REFERENCES validation_runs(id) ON DELETE CASCADE,
            defect_code TEXT NOT NULL UNIQUE,
            severity TEXT NOT NULL,
            defect_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS feedback_packets (
            id TEXT PRIMARY KEY,
            validation_run_id TEXT NOT NULL REFERENCES validation_runs(id) ON DELETE CASCADE,
            target_agent_id TEXT REFERENCES agents(id) ON DELETE SET NULL,
            target_version_id TEXT REFERENCES agent_versions(id) ON DELETE SET NULL,
            payload_jsonb TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS release_decisions (
            id TEXT PRIMARY KEY,
            validation_run_id TEXT NOT NULL REFERENCES validation_runs(id) ON DELETE CASCADE,
            decision TEXT NOT NULL,
            conditions_jsonb TEXT NOT NULL DEFAULT '[]',
            decided_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            document_code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            document_type TEXT NOT NULL,
            file_path TEXT NOT NULL UNIQUE,
            content_hash TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS document_links (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            link_role TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tags (
            id TEXT PRIMARY KEY,
            tag_code TEXT NOT NULL UNIQUE,
            tag_name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        );

        CREATE TABLE IF NOT EXISTS document_tags (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            tag_id TEXT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            UNIQUE(document_id, tag_id)
        );
    """)


def seed_core(conn: sqlite3.Connection):
    """Seed users, teams, systems, and agents."""
    user_id = str(uuid.uuid4())
    conn.execute("INSERT OR IGNORE INTO users (id, username, display_name, email) VALUES (?, ?, ?, ?)",
                 (user_id, 'z', 'z', None))

    team_id = str(uuid.uuid4())
    conn.execute("INSERT OR IGNORE INTO teams (id, team_code, team_name, owner_user_id) VALUES (?, ?, ?, ?)",
                 (team_id, 'TEAM-0001', 'AI Project Platform Team', user_id))

    conn.execute("INSERT OR IGNORE INTO team_members (id, team_id, user_id, role_code) VALUES (?, ?, ?, ?)",
                 (str(uuid.uuid4()), team_id, user_id, 'owner'))

    system_id = str(uuid.uuid4())
    conn.execute("INSERT OR IGNORE INTO systems (id, system_code, system_name, version, summary) VALUES (?, ?, ?, ?, ?)",
                 (system_id, 'SYS-0001', 'ai-skill-system', 'v1.x',
                  'Prompt-driven orchestration system with coordinator, skill repositories, handoff contracts, and validation loops.'))

    agents = [
        ('AGT-0001', 'AI Skill Coordinator', 'coordinator', 'Single-chat coordinator and routing role.'),
        ('AGT-0002', 'Skill 00 Navigator', 'skill', 'Intent recognition and handoff generation role.'),
        ('AGT-0003', 'Super Prompt Engineer', 'skill', 'Prompt design and pain-point translation role.'),
        ('AGT-0004', 'Skill Dev SOP Engineer', 'skill', 'Skill engineering SOP role.'),
        ('AGT-0005', 'Scout', 'skill', 'Open source and requirement scouting role.'),
        ('AGT-0006', 'Planner', 'skill', 'Implementation planning role.'),
        ('AGT-0007', 'Validator', 'skill', 'Validation and release decision role.'),
    ]
    for code, name, atype, summary in agents:
        conn.execute("INSERT OR IGNORE INTO agents (id, agent_code, agent_name, agent_type, system_id, summary, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (str(uuid.uuid4()), code, name, atype, system_id, summary, 'active'))


def seed_repos(conn: sqlite3.Connection):
    """Seed ai-skill-system repositories."""
    system = conn.execute("SELECT id FROM systems WHERE system_code = 'SYS-0001'").fetchone()
    if not system:
        return
    system_id = system[0]

    repos = [
        ('REP-0001', 'ai-skill-system-master', str(ROOT / 'Systems' / 'ai-skill-system' / 'repo' / 'ai-skill-system-master')),
        ('REP-0002', 'skill-00-navigator', str(ROOT / 'Systems' / 'ai-skill-system' / 'repos' / 'skill-00-navigator')),
        ('REP-0003', 'super-prompt-engineer-skill', str(ROOT / 'Systems' / 'ai-skill-system' / 'repos' / 'super-prompt-engineer-skill')),
        ('REP-0004', 'skill-dev-sop-skill', str(ROOT / 'Systems' / 'ai-skill-system' / 'repos' / 'skill-dev-sop-skill')),
        ('REP-0005', 'skill-03-scout', str(ROOT / 'Systems' / 'ai-skill-system' / 'repos' / 'skill-03-scout')),
        ('REP-0006', 'skill-04-planner', str(ROOT / 'Systems' / 'ai-skill-system' / 'repos' / 'skill-04-planner')),
        ('REP-0007', 'skill-05-validator', str(ROOT / 'Systems' / 'ai-skill-system' / 'repos' / 'skill-05-validator')),
    ]
    for code, name, path in repos:
        conn.execute("INSERT OR IGNORE INTO repositories (id, system_id, repository_code, repository_name, local_path, status) VALUES (?, ?, ?, ?, ?, ?)",
                     (str(uuid.uuid4()), system_id, code, name, path, 'active'))


def seed_mvp_flow(conn: sqlite3.Connection):
    """Seed the MVP business loop with relationships."""
    conn.execute("INSERT OR IGNORE INTO projects (id, project_code, project_name, summary, status, priority) VALUES (?, ?, ?, ?, ?, ?)",
                 (str(uuid.uuid4()), 'PRJ-0001', 'AI Project Platform MVP', 'First platform foundation build.', 'active', 'high'))

    conn.execute("INSERT OR IGNORE INTO pain_points (id, pain_code, title, description, category_code, severity, frequency_score, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                 (str(uuid.uuid4()), 'PAIN-0001', 'Multi-project information is scattered',
                  'The workspace lacks one structured tracking model across projects, pains, demands, and solutions.',
                  'workflow', 'high', 5, 'active'))

    project = conn.execute("SELECT id FROM projects WHERE project_code = 'PRJ-0001'").fetchone()
    if project:
        conn.execute("INSERT OR IGNORE INTO demands (id, demand_code, project_id, title, description, source_type, priority, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (str(uuid.uuid4()), 'DEM-0001', project[0],
                      'Unified project-demand-pain-solution tracking',
                      'Connect structured project operations to documents and ai-skill-system orchestration.',
                      'spec', 'high', 'active'))

    conn.execute("INSERT OR IGNORE INTO solutions (id, solution_code, solution_name, solution_type, summary, maturity_level, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (str(uuid.uuid4()), 'SOL-0001', 'AI Project Management Platform Foundation',
                  'platform', 'PostgreSQL plus document-first operating model.', 'testing', 'testing'))

    proj = conn.execute("SELECT id FROM projects WHERE project_code = 'PRJ-0001'").fetchone()
    pain = conn.execute("SELECT id FROM pain_points WHERE pain_code = 'PAIN-0001'").fetchone()
    if proj and pain:
        conn.execute("INSERT OR IGNORE INTO project_pain_points (id, project_id, pain_point_id, impact_score) VALUES (?, ?, ?, ?)",
                     (str(uuid.uuid4()), proj[0], pain[0], 5))

    dem = conn.execute("SELECT id FROM demands WHERE demand_code = 'DEM-0001'").fetchone()
    if dem and pain:
        conn.execute("INSERT OR IGNORE INTO demand_pain_links (id, demand_id, pain_point_id, link_type) VALUES (?, ?, ?, ?)",
                     (str(uuid.uuid4()), dem[0], pain[0], 'addresses'))

    sol = conn.execute("SELECT id FROM solutions WHERE solution_code = 'SOL-0001'").fetchone()
    if sol and dem:
        conn.execute("INSERT OR IGNORE INTO solution_demand_links (id, solution_id, demand_id, fit_score) VALUES (?, ?, ?, ?)",
                     (str(uuid.uuid4()), sol[0], dem[0], 5))
    if sol and pain:
        conn.execute("INSERT OR IGNORE INTO solution_pain_links (id, solution_id, pain_point_id, fit_score) VALUES (?, ?, ?, ?)",
                     (str(uuid.uuid4()), sol[0], pain[0], 5))


def seed_orchestration(conn: sqlite3.Connection):
    """Seed handoff and validation records."""
    proj = conn.execute("SELECT id FROM projects WHERE project_code = 'PRJ-0001'").fetchone()
    sol = conn.execute("SELECT id FROM solutions WHERE solution_code = 'SOL-0001'").fetchone()
    agt_nav = conn.execute("SELECT id FROM agents WHERE agent_code = 'AGT-0002'").fetchone()
    agt_plan = conn.execute("SELECT id FROM agents WHERE agent_code = 'AGT-0006'").fetchone()
    agt_val = conn.execute("SELECT id FROM agents WHERE agent_code = 'AGT-0007'").fetchone()

    payload = json.dumps({
        "demand_code": "DEM-0001",
        "pain_code": "PAIN-0001",
        "solution_code": "SOL-0001",
        "required_output": "Implementation plan with schema, folder, import, and validation tasks"
    })

    if proj and agt_nav and agt_plan:
        conn.execute("INSERT OR IGNORE INTO handoff_packages (id, handoff_code, project_id, from_agent_id, to_agent_id, schema_version, payload_jsonb, raw_yaml, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (str(uuid.uuid4()), 'HOF-0001', proj[0], agt_nav[0], agt_plan[0],
                      '1.0', payload, None, 'active'))

    if proj and sol and agt_val:
        existing = conn.execute("SELECT id FROM validation_runs WHERE project_id = ? AND solution_id = ? AND validator_agent_id = ?",
                                (proj[0], sol[0], agt_val[0])).fetchone()
        if not existing:
            conn.execute("INSERT INTO validation_runs (id, project_id, solution_id, validator_agent_id, status) VALUES (?, ?, ?, ?, ?)",
                         (str(uuid.uuid4()), proj[0], sol[0], agt_val[0], 'planned'))

    # Validation defect
    val_run = conn.execute("SELECT id FROM validation_runs LIMIT 1").fetchone()
    if val_run:
        conn.execute("INSERT OR IGNORE INTO validation_defects (id, validation_run_id, defect_code, severity, defect_type, title, description, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (str(uuid.uuid4()), val_run[0], 'BUG-0001', 'medium', 'gap',
                      'Missing document-to-entity links',
                      'The first platform version creates the document registry, but linked business entities are still incomplete for legacy Markdown content.',
                      'open'))


def seed_agent_versions(conn: sqlite3.Connection):
    """Seed agent version records."""
    agents = conn.execute("SELECT id, agent_code FROM agents").fetchall()
    for agent_id, agent_code in agents:
        conn.execute("INSERT OR IGNORE INTO agent_versions (id, agent_id, version, changelog) VALUES (?, ?, ?, ?)",
                     (str(uuid.uuid4()), agent_id, 'v1.0.0', f'Initial {agent_code} version.'))


def seed_workflows(conn: sqlite3.Connection):
    """Seed workflow definitions and phases."""
    system = conn.execute("SELECT id FROM systems WHERE system_code = 'SYS-0001'").fetchone()
    if not system:
        return
    system_id = system[0]

    workflows = [
        ('WF-0001', 'Coordinator Routing Flow', 'routing',
         'Single-chat coordinator that routes user intents to appropriate skills and generates handoff packages.',
         [
             ('PH-001', 'Intent Recognition', 1),
             ('PH-002', 'Skill Selection', 2),
             ('PH-003', 'Handoff Generation', 3),
         ]),
        ('WF-0002', 'Skill Development SOP', 'engineering',
         '10-stage SOP for developing, testing, and deploying AI skills.',
         [
             ('PH-004', 'Value Mining', 1), ('PH-005', 'Direction Decision', 2),
             ('PH-006', 'Engineering Build', 3), ('PH-007', 'Simulation Test', 4),
             ('PH-008', 'Autonomous Iteration', 5), ('PH-009', 'User Guide', 6),
             ('PH-010', 'Skill Packaging', 7), ('PH-011', 'GitHub Publish', 8),
             ('PH-012', 'Install Prompts', 9), ('PH-013', 'Global Install', 10),
         ]),
        ('WF-0003', 'Planner PTS Flow', 'planning',
         'Phase -> Task -> Step execution planning for implementation.',
         [
             ('PH-014', 'Phase Definition', 1), ('PH-015', 'Task Breakdown', 2),
             ('PH-016', 'Step Specification', 3),
         ]),
        ('WF-0004', 'Validator Feedback Loop', 'validation',
         'Validation -> defect -> feedback -> release decision cycle.',
         [
             ('PH-017', 'Validation Run', 1), ('PH-018', 'Defect Detection', 2),
             ('PH-019', 'Feedback Generation', 3), ('PH-020', 'Release Decision', 4),
         ]),
    ]

    for wf_code, wf_name, wf_type, wf_summary, phases in workflows:
        wf_id = str(uuid.uuid4())
        conn.execute("INSERT OR IGNORE INTO workflow_definitions (id, workflow_code, workflow_name, workflow_type, summary, source_system_id) VALUES (?, ?, ?, ?, ?, ?)",
                     (wf_id, wf_code, wf_name, wf_type, wf_summary, system_id))
        for ph_code, ph_name, seq in phases:
            conn.execute("INSERT OR IGNORE INTO workflow_phases (id, workflow_id, phase_code, phase_name, sequence_no) VALUES (?, ?, ?, ?, ?)",
                         (str(uuid.uuid4()), wf_id, ph_code, ph_name, seq))


def ingest_documents(conn: sqlite3.Connection):
    """Run the enhanced document importer and ingest results."""
    cmd = [sys.executable, str(IMPORTER)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"  Importer error: {result.stderr}")
        return

    data = json.loads(result.stdout)
    docs = data.get("documents", [])
    links = data.get("document_links", [])
    summary = data.get("summary", {})

    print(f"  Importer found: {summary.get('total_documents', 0)} docs, {summary.get('total_links', 0)} links")

    doc_code_to_id = {}
    for doc in docs:
        doc_id = str(uuid.uuid4())
        conn.execute("INSERT OR REPLACE INTO documents (id, document_code, title, document_type, file_path, content_hash, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (doc_id, doc["document_code"], doc["title"], doc["document_type"],
                      doc["file_path"], doc["content_hash"], doc.get("status", "active")))
        doc_code_to_id[doc["document_code"]] = doc_id

    link_count = 0
    for link in links:
        source_id = doc_code_to_id.get(link["source_document_code"])
        if source_id:
            conn.execute("INSERT OR IGNORE INTO document_links (id, document_id, entity_type, entity_id, link_role) VALUES (?, ?, ?, ?, ?)",
                         (str(uuid.uuid4()), source_id, 'document', link["target_title"], link["link_role"]))
            link_count += 1

    print(f"  -> {len(docs)} documents upserted")
    print(f"  -> {link_count} document links inserted")


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")

    print("Setting up schema...")
    setup_schema(conn)

    print("Seeding core data...")
    seed_core(conn)

    print("Seeding repositories...")
    seed_repos(conn)

    print("Seeding MVP business flow...")
    seed_mvp_flow(conn)

    print("Seeding orchestration records...")
    seed_orchestration(conn)

    print("Seeding agent versions...")
    seed_agent_versions(conn)

    print("Seeding workflows...")
    seed_workflows(conn)

    print("Ingesting documents...")
    ingest_documents(conn)

    conn.commit()

    # Verify
    print("\n=== DATABASE VERIFICATION ===")
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
        print(f"  {t[0]}: {count} rows")

    # MVP chain
    print("\n=== MVP CHAIN ===")
    chain = conn.execute("""
        SELECT p.project_code, pp.pain_code, d.demand_code, s.solution_code
        FROM projects p
        JOIN project_pain_points ppp ON p.id = ppp.project_id
        JOIN pain_points pp ON ppp.pain_point_id = pp.id
        JOIN demands d ON d.project_id = p.id
        JOIN solution_demand_links sdl ON d.id = sdl.demand_id
        JOIN solutions s ON sdl.solution_id = s.id
    """).fetchone()
    if chain:
        print(f"  {' -> '.join(chain)}")

    conn.close()
    print(f"\nDatabase created at: {DB_PATH}")


if __name__ == "__main__":
    main()
