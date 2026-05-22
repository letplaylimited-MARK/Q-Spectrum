CREATE TABLE documents (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    document_code VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    file_path TEXT NOT NULL,
    content_hash VARCHAR(64),
    word_count INTEGER DEFAULT 0,
    summary TEXT,
    tags_json TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (file_path)
);

CREATE TABLE document_links (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6)))),
    document_id TEXT NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id TEXT NOT NULL,
    link_role VARCHAR(100) NOT NULL,
    CONSTRAINT fk_dl_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
