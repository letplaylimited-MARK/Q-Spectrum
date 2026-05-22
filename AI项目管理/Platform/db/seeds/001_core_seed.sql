-- Core seed: users, teams, systems, agents, and identity records
-- SQLite version (converted from PostgreSQL)

INSERT OR IGNORE INTO users (username, display_name, email)
VALUES ('z', 'z', NULL);

INSERT OR IGNORE INTO teams (team_code, team_name, owner_user_id)
SELECT 'TEAM-0001', 'AI Project Platform Team', u.id
FROM users u
WHERE u.username = 'z';

INSERT OR IGNORE INTO team_members (team_id, user_id, role_code)
SELECT t.id, u.id, 'owner'
FROM teams t
JOIN users u ON u.username = 'z'
WHERE t.team_code = 'TEAM-0001';

INSERT OR IGNORE INTO systems (system_code, system_name, version, summary)
VALUES (
    'SYS-0001',
    'ai-skill-system',
    'v1.x',
    'Prompt-driven orchestration system with coordinator, skill repositories, handoff contracts, and validation loops.'
);

INSERT OR IGNORE INTO agents (agent_code, agent_name, agent_type, system_id, summary, status)
SELECT 'AGT-0001', 'AI Skill Coordinator', 'coordinator', s.id, 'Single-chat coordinator and routing role.', 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO agents (agent_code, agent_name, agent_type, system_id, summary, status)
SELECT 'AGT-0002', 'Skill 00 Navigator', 'skill', s.id, 'Intent recognition and handoff generation role.', 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO agents (agent_code, agent_name, agent_type, system_id, summary, status)
SELECT 'AGT-0003', 'Super Prompt Engineer', 'skill', s.id, 'Prompt design and pain-point translation role.', 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO agents (agent_code, agent_name, agent_type, system_id, summary, status)
SELECT 'AGT-0004', 'Skill Dev SOP Engineer', 'skill', s.id, 'Skill engineering SOP role.', 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO agents (agent_code, agent_name, agent_type, system_id, summary, status)
SELECT 'AGT-0005', 'Scout', 'skill', s.id, 'Open source and requirement scouting role.', 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO agents (agent_code, agent_name, agent_type, system_id, summary, status)
SELECT 'AGT-0006', 'Planner', 'skill', s.id, 'Implementation planning role.', 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';

INSERT OR IGNORE INTO agents (agent_code, agent_name, agent_type, system_id, summary, status)
SELECT 'AGT-0007', 'Validator', 'skill', s.id, 'Validation and release decision role.', 'active'
FROM systems s WHERE s.system_code = 'SYS-0001';
