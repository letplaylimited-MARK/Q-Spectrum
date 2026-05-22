CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    username VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE teams (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    team_code VARCHAR(100) NOT NULL UNIQUE,
    team_name VARCHAR(255) NOT NULL,
    owner_user_id TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_teams_owner FOREIGN KEY (owner_user_id) REFERENCES users(id)
);

CREATE TABLE team_members (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    team_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role_code VARCHAR(100) NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (team_id, user_id),
    CONSTRAINT fk_tm_team FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    CONSTRAINT fk_tm_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
