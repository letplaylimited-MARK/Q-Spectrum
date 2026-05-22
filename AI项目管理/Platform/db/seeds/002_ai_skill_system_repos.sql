-- Repository seed: ai-skill-system repositories
-- SQLite version (converted from PostgreSQL)

INSERT OR IGNORE INTO repositories (system_id, repository_code, repository_name, local_path, remote_url, status)
SELECT s.id, 'REP-0001', 'ai-skill-system-master', './AI项目管理/Systems/ai-skill-system', NULL, 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO repositories (system_id, repository_code, repository_name, local_path, remote_url, status)
SELECT s.id, 'REP-0002', 'skill-00-navigator', './AI项目管理/Systems/ai-skill-system/repos/skill-00-navigator', NULL, 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO repositories (system_id, repository_code, repository_name, local_path, remote_url, status)
SELECT s.id, 'REP-0003', 'super-prompt-engineer-skill', './AI项目管理/Systems/ai-skill-system/repos/super-prompt-engineer-skill', NULL, 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO repositories (system_id, repository_code, repository_name, local_path, remote_url, status)
SELECT s.id, 'REP-0004', 'skill-dev-sop-skill', './AI项目管理/Systems/ai-skill-system/repos/skill-dev-sop-skill', NULL, 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO repositories (system_id, repository_code, repository_name, local_path, remote_url, status)
SELECT s.id, 'REP-0005', 'skill-03-scout', './AI项目管理/Systems/ai-skill-system/repos/skill-03-scout', NULL, 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO repositories (system_id, repository_code, repository_name, local_path, remote_url, status)
SELECT s.id, 'REP-0006', 'skill-04-planner', './AI项目管理/Systems/ai-skill-system/repos/skill-04-planner', NULL, 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO repositories (system_id, repository_code, repository_name, local_path, remote_url, status)
SELECT s.id, 'REP-0007', 'skill-05-validator', './AI项目管理/Systems/ai-skill-system/repos/skill-05-validator', NULL, 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';
