CREATE TABLE solutions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    solution_code VARCHAR(100) NOT NULL UNIQUE,
    solution_name VARCHAR(255) NOT NULL,
    solution_type VARCHAR(100) NOT NULL,
    summary TEXT,
    maturity_level VARCHAR(50) NOT NULL DEFAULT 'draft',
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE solution_demand_links (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    solution_id TEXT NOT NULL,
    demand_id TEXT NOT NULL,
    fit_score INTEGER NOT NULL DEFAULT 3,
    UNIQUE (solution_id, demand_id),
    CONSTRAINT fk_sdl_solution FOREIGN KEY (solution_id) REFERENCES solutions(id) ON DELETE CASCADE,
    CONSTRAINT fk_sdl_demand FOREIGN KEY (demand_id) REFERENCES demands(id) ON DELETE CASCADE
);

CREATE TABLE solution_pain_links (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    solution_id TEXT NOT NULL,
    pain_point_id TEXT NOT NULL,
    fit_score INTEGER NOT NULL DEFAULT 3,
    UNIQUE (solution_id, pain_point_id),
    CONSTRAINT fk_spl_solution FOREIGN KEY (solution_id) REFERENCES solutions(id) ON DELETE CASCADE,
    CONSTRAINT fk_spl_pain FOREIGN KEY (pain_point_id) REFERENCES pain_points(id) ON DELETE CASCADE
);
