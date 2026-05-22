CREATE TABLE projects (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    project_code VARCHAR(100) NOT NULL UNIQUE,
    project_name VARCHAR(255) NOT NULL,
    summary TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    priority VARCHAR(50) NOT NULL DEFAULT 'medium',
    owner_team_id TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_projects_team FOREIGN KEY (owner_team_id) REFERENCES teams(id),
    CONSTRAINT fk_projects_creator FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE project_stages (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    project_id TEXT NOT NULL,
    stage_code VARCHAR(100) NOT NULL,
    stage_name VARCHAR(255) NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stages_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
