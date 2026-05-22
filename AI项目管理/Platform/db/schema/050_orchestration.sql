CREATE TABLE systems (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    system_code VARCHAR(100) NOT NULL UNIQUE,
    system_name VARCHAR(255) NOT NULL,
    version VARCHAR(50),
    summary TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE repositories (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    system_id TEXT,
    repository_code VARCHAR(100) NOT NULL UNIQUE,
    repository_name VARCHAR(255) NOT NULL,
    local_path TEXT NOT NULL,
    remote_url TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_repos_system FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE SET NULL
);

CREATE TABLE agents (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    agent_code VARCHAR(100) NOT NULL UNIQUE,
    agent_name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    system_id TEXT,
    summary TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_agents_system FOREIGN KEY (system_id) REFERENCES systems(id) ON DELETE SET NULL
);

CREATE TABLE agent_versions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    agent_id TEXT NOT NULL,
    version VARCHAR(50) NOT NULL,
    changelog TEXT,
    prompt_body_md TEXT,
    released_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (agent_id, version),
    CONSTRAINT fk_av_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE TABLE agent_modules (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    agent_id TEXT NOT NULL,
    module_code VARCHAR(100) NOT NULL UNIQUE,
    module_name VARCHAR(255) NOT NULL,
    module_type VARCHAR(100) NOT NULL,
    spec_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_am_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE TABLE workflow_definitions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    workflow_code VARCHAR(100) NOT NULL UNIQUE,
    workflow_name VARCHAR(255) NOT NULL,
    workflow_type VARCHAR(100) NOT NULL,
    summary TEXT,
    source_system_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_wf_system FOREIGN KEY (source_system_id) REFERENCES systems(id) ON DELETE SET NULL
);

CREATE TABLE project_agent_runs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    project_id TEXT NOT NULL,
    demand_id TEXT,
    agent_id TEXT NOT NULL,
    agent_version_id TEXT,
    run_status VARCHAR(50) NOT NULL DEFAULT 'queued',
    started_at TEXT,
    ended_at TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_par_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_par_demand FOREIGN KEY (demand_id) REFERENCES demands(id) ON DELETE SET NULL,
    CONSTRAINT fk_par_agent FOREIGN KEY (agent_id) REFERENCES agents(id),
    CONSTRAINT fk_par_agentver FOREIGN KEY (agent_version_id) REFERENCES agent_versions(id) ON DELETE SET NULL,
    CONSTRAINT fk_par_creator FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE handoff_packages (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    handoff_code VARCHAR(100) NOT NULL UNIQUE,
    project_id TEXT NOT NULL,
    from_agent_id TEXT,
    to_agent_id TEXT,
    schema_version VARCHAR(50) NOT NULL,
    payload_json TEXT,
    raw_yaml TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hp_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_hp_from FOREIGN KEY (from_agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    CONSTRAINT fk_hp_to FOREIGN KEY (to_agent_id) REFERENCES agents(id) ON DELETE SET NULL
);
