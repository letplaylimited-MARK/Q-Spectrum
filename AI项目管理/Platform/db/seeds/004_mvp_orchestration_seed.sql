-- MVP orchestration seed: handoff packages and validation runs
-- SQLite version (converted from PostgreSQL)

INSERT OR IGNORE INTO handoff_packages (handoff_code, project_id, from_agent_id, to_agent_id, schema_version, payload_json, raw_yaml, status)
SELECT
    'HOF-0001',
    p.id,
    a_from.id,
    a_to.id,
    '1.0',
    '{"demand_code":"DEM-0001","pain_code":"PAIN-0001","solution_code":"SOL-0001","required_output":"Implementation plan with schema, folder, import, and validation tasks"}',
    'handoff_code: HOF-0001\nfrom: AGT-0002\nto: AGT-0006\nschema_version: "1.0"\npayload:\n  demand_code: DEM-0001\n  pain_code: PAIN-0001\n  solution_code: SOL-0001\n  required_output: Implementation plan with schema, folder, import, and validation tasks',
    'active'
FROM projects p
CROSS JOIN agents a_from
CROSS JOIN agents a_to
WHERE p.project_code = 'PRJ-0001'
  AND a_from.agent_code = 'AGT-0002'
  AND a_to.agent_code = 'AGT-0006';

INSERT OR IGNORE INTO validation_runs (project_id, solution_id, validator_agent_id, status)
SELECT p.id, s.id, a.id, 'planned'
FROM projects p
CROSS JOIN solutions s
CROSS JOIN agents a
WHERE p.project_code = 'PRJ-0001'
  AND s.solution_code = 'SOL-0001'
  AND a.agent_code = 'AGT-0007'
  AND NOT EXISTS (
      SELECT 1 FROM validation_runs vr
      JOIN projects p2 ON vr.project_id = p2.id
      JOIN solutions s2 ON vr.solution_id = s2.id
      JOIN agents a2 ON vr.validator_agent_id = a2.id
      WHERE p2.project_code = 'PRJ-0001'
        AND s2.solution_code = 'SOL-0001'
        AND a2.agent_code = 'AGT-0007'
        AND vr.status = 'planned'
  );
