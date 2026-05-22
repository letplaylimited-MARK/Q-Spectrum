CREATE TABLE validation_runs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    project_id TEXT NOT NULL,
    solution_id TEXT,
    validator_agent_id TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'planned',
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_vr_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_vr_solution FOREIGN KEY (solution_id) REFERENCES solutions(id) ON DELETE SET NULL,
    CONSTRAINT fk_vr_validator FOREIGN KEY (validator_agent_id) REFERENCES agents(id) ON DELETE SET NULL
);

CREATE TABLE validation_defects (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    validation_run_id TEXT NOT NULL,
    defect_code VARCHAR(100) NOT NULL UNIQUE,
    severity VARCHAR(50) NOT NULL,
    defect_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_vd_run FOREIGN KEY (validation_run_id) REFERENCES validation_runs(id) ON DELETE CASCADE
);

CREATE TABLE release_decisions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    validation_run_id TEXT NOT NULL,
    decision VARCHAR(50) NOT NULL,
    conditions_json TEXT,
    decided_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rd_run FOREIGN KEY (validation_run_id) REFERENCES validation_runs(id) ON DELETE CASCADE
);
