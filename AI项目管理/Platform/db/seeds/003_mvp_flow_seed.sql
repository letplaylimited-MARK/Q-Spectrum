-- MVP flow seed: projects, pains, demands, solutions, and their links
-- SQLite version (converted from PostgreSQL)

INSERT OR IGNORE INTO projects (project_code, project_name, summary, status, priority)
VALUES ('PRJ-0001', 'AI Project Platform MVP', 'First platform foundation build.', 'active', 'high');

INSERT OR IGNORE INTO pain_points (pain_code, title, description, category_code, severity, frequency_score, status)
VALUES ('PAIN-0001', 'Multi-project information is scattered', 'The workspace lacks one structured tracking model across projects, pains, demands, and solutions.', 'workflow', 'high', 5, 'active');

INSERT OR IGNORE INTO demands (demand_code, project_id, title, description, source_type, priority, status)
SELECT 'DEM-0001', p.id, 'Unified project-demand-pain-solution tracking', 'Connect structured project operations to documents and ai-skill-system orchestration.', 'spec', 'high', 'active'
FROM projects p WHERE p.project_code = 'PRJ-0001';

INSERT OR IGNORE INTO solutions (solution_code, solution_name, solution_type, summary, maturity_level, status)
VALUES ('SOL-0001', 'AI Project Management Platform Foundation', 'platform', 'SQLite plus document-first operating model.', 'testing', 'testing');

INSERT OR IGNORE INTO project_pain_points (project_id, pain_point_id, impact_score, source_note)
SELECT p.id, pp.id, 5, 'Seeded MVP Task 6 relationship.'
FROM projects p
CROSS JOIN pain_points pp
WHERE p.project_code = 'PRJ-0001'
  AND pp.pain_code = 'PAIN-0001';

INSERT OR IGNORE INTO demand_pain_links (demand_id, pain_point_id, link_type)
SELECT d.id, pp.id, 'addresses'
FROM demands d
CROSS JOIN pain_points pp
WHERE d.demand_code = 'DEM-0001'
  AND pp.pain_code = 'PAIN-0001';

INSERT OR IGNORE INTO solution_demand_links (solution_id, demand_id, fit_score)
SELECT s.id, d.id, 5
FROM solutions s
CROSS JOIN demands d
WHERE s.solution_code = 'SOL-0001'
  AND d.demand_code = 'DEM-0001';

INSERT OR IGNORE INTO solution_pain_links (solution_id, pain_point_id, fit_score)
SELECT s.id, pp.id, 5
FROM solutions s
CROSS JOIN pain_points pp
WHERE s.solution_code = 'SOL-0001'
  AND pp.pain_code = 'PAIN-0001';
