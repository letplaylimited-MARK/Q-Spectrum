import codecs
import sqlite3
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

# Dynamic path resolution: locate db/platform.db relative to script location
SQLITE_DB = Path(__file__).parent.parent / "db" / "platform.db"
MYSQL = r"C:\tools\mysql\current\bin\mysql.exe"
DB_NAME = "ai_project_platform"

def escape(s):
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"

def migrate_table(table, columns, sqlite_conn):
    cur = sqlite_conn.cursor()
    cols = ", ".join(columns)
    cur.execute(f"SELECT {cols} FROM {table}")
    rows = cur.fetchall()
    if not rows:
        print(f"  {table}: 0 rows, skipped")
        return 0

    sql_lines = []
    for row in rows:
        values = ", ".join(escape(v) for v in row)
        sql_lines.append(f"INSERT IGNORE INTO {table} ({cols}) VALUES ({values});")

    sql_text = "\n".join(sql_lines) + "\n"
    proc = subprocess.run(
        [MYSQL, "-u", "root", "--default-character-set=utf8mb4", DB_NAME],
        input=sql_text, capture_output=True, text=True, encoding="utf-8"
    )
    if proc.returncode == 0:
        print(f"  {table}: {len(rows)} rows migrated OK")
    else:
        print(f"  {table}: FAILED - {proc.stderr[:200]}")
    return len(rows)

def main():
    conn = sqlite3.connect(str(SQLITE_DB))
    total = 0

    tables = {
        "users": ["id", "username", "display_name", "email", "status", "created_at", "updated_at"],
        "teams": ["id", "team_code", "team_name", "owner_user_id", "status", "created_at", "updated_at"],
        "team_members": ["id", "team_id", "user_id", "role_code", "created_at"],
        "projects": ["id", "project_code", "project_name", "summary", "status", "priority", "owner_team_id", "created_by", "created_at", "updated_at"],
        "project_stages": ["id", "project_id", "stage_code", "stage_name", "started_at", "ended_at", "created_at", "updated_at"],
        "pain_points": ["id", "pain_code", "title", "description", "category_code", "severity", "frequency_score", "status", "created_at"],
        "project_pain_points": ["id", "project_id", "pain_point_id", "impact_score", "source_note"],
        "demands": ["id", "demand_code", "project_id", "title", "description", "source_type", "priority", "status", "created_by", "created_at", "updated_at"],
        "demand_items": ["id", "demand_id", "item_code", "title", "acceptance_criteria", "status", "created_at", "updated_at"],
        "demand_pain_links": ["id", "demand_id", "pain_point_id", "link_type"],
        "solutions": ["id", "solution_code", "solution_name", "solution_type", "summary", "maturity_level", "status", "created_at", "updated_at"],
        "solution_demand_links": ["id", "solution_id", "demand_id", "fit_score"],
        "solution_pain_links": ["id", "solution_id", "pain_point_id", "fit_score"],
        "systems": ["id", "system_code", "system_name", "version", "summary", "created_at"],
        "repositories": ["id", "system_id", "repository_code", "repository_name", "local_path", "remote_url", "status", "created_at", "updated_at"],
        "agents": ["id", "agent_code", "agent_name", "agent_type", "system_id", "summary", "status", "created_at", "updated_at"],
        "agent_versions": ["id", "agent_id", "version", "changelog", "prompt_body_md", "released_at", "created_at", "updated_at"],
        "agent_modules": ["id", "agent_id", "module_code", "module_name", "module_type", "spec_jsonb", "created_at", "updated_at"],
        "workflow_definitions": ["id", "workflow_code", "workflow_name", "workflow_type", "summary", "source_system_id", "created_at", "updated_at"],
        "project_agent_runs": ["id", "project_id", "demand_id", "agent_id", "agent_version_id", "run_status", "started_at", "ended_at", "created_by", "created_at", "updated_at"],
        "handoff_packages": ["id", "handoff_code", "project_id", "from_agent_id", "to_agent_id", "schema_version", "payload_jsonb", "raw_yaml", "status", "created_at", "updated_at"],
        "validation_runs": ["id", "project_id", "solution_id", "validator_agent_id", "status", "started_at", "ended_at"],
        "validation_defects": ["id", "validation_run_id", "defect_code", "severity", "defect_type", "title", "description", "status", "created_at", "updated_at"],
        "documents": ["id", "document_code", "title", "document_type", "file_path", "content_hash", "status", "created_at"],
        "document_links": ["id", "document_id", "entity_type", "entity_id", "link_role"],
        "release_decisions": ["id", "validation_run_id", "decision", "conditions_jsonb", "decided_at"],
    }

    print("Migrating SQLite data to MySQL...")
    for table, columns in tables.items():
        try:
            total += migrate_table(table, columns, conn)
        except Exception as e:
            print(f"  {table}: ERROR - {e}")

    conn.close()
    print(f"\nTotal rows migrated: {total}")

if __name__ == "__main__":
    main()
