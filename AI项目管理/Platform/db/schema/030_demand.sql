CREATE TABLE pain_points (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    pain_code VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category_code VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL DEFAULT 'medium',
    frequency_score INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE project_pain_points (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    project_id TEXT NOT NULL,
    pain_point_id TEXT NOT NULL,
    impact_score INTEGER NOT NULL DEFAULT 1,
    source_note TEXT,
    UNIQUE (project_id, pain_point_id),
    CONSTRAINT fk_ppp_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_ppp_pain FOREIGN KEY (pain_point_id) REFERENCES pain_points(id) ON DELETE CASCADE
);

CREATE TABLE demands (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    demand_code VARCHAR(100) NOT NULL UNIQUE,
    project_id TEXT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    priority VARCHAR(50) NOT NULL DEFAULT 'medium',
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_by TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_demands_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_demands_creator FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE demand_items (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    demand_id TEXT NOT NULL,
    item_code VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    acceptance_criteria TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_di_demand FOREIGN KEY (demand_id) REFERENCES demands(id) ON DELETE CASCADE
);

CREATE TABLE demand_pain_links (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    demand_id TEXT NOT NULL,
    pain_point_id TEXT NOT NULL,
    link_type VARCHAR(100) NOT NULL DEFAULT 'addresses',
    UNIQUE (demand_id, pain_point_id),
    CONSTRAINT fk_dpl_demand FOREIGN KEY (demand_id) REFERENCES demands(id) ON DELETE CASCADE,
    CONSTRAINT fk_dpl_pain FOREIGN KEY (pain_point_id) REFERENCES pain_points(id) ON DELETE CASCADE
);
