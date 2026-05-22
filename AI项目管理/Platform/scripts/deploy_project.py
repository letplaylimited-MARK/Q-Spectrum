"""
Q-SpecTrum Project Deployer v3.0
Unified replacement for create-project.py and implant_memory_and_deploy.py.

Key improvement over v2: After copying, this script also UPDATES the SQLite
database to rewrite all path references from the template root to the new
project root. This fixes the "dead copy" problem where project instances
had stale document/repository paths.

Usage:
    python deploy_project.py <project_name>
    python deploy_project.py MyNewProject
"""

import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).parent.resolve()
TEMPLATE_ROOT = SCRIPT_DIR.parent.parent  # AI项目管理/
Q_SPECTRUM_ROOT = TEMPLATE_ROOT.parent     # Q-SpecTrum(TEST)/
PROJECTS_DIR = Q_SPECTRUM_ROOT / "Projects"

# Essential directories (always copied, fast)
ESSENTIAL_DIRS = [
    "Platform", "roles", "Skills", "Maps",
]

# Full directories (copied only with --full flag; skipped in lightweight mode)
FULL_DIRS = [
    "Systems", "Scripts", "Topics", "Resources", "Operations",
    "Weekly-Logs", "QCM", "Templates", "FAQs", "Inbox", "Archive",
    "Deployments", "Exports", "Assets", "Projects", "ProjectDocs",
    "tests", "skill-install-records",
]

# Default to lightweight mode (fast on virtiofs); use --full for complete copy
LIGHTWEIGHT = "--full" not in sys.argv
COPY_DIRS = ESSENTIAL_DIRS if LIGHTWEIGHT else ESSENTIAL_DIRS + FULL_DIRS

COPY_FILES = [
    ".project_lock", "README.md", "START-HERE.md", "AGENTS.md",
]

IGNORE_PATTERNS = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo",
    "platform.db-wal", "platform.db-shm", "platform.db-journal",
    ".fuse_hidden*", ".ruff_cache", "--help",
)


def copy_template(target_root: Path):
    """Step 1: Copy template baseline to target."""
    mode = "lightweight (fast)" if LIGHTWEIGHT else "full"
    print(f"\n[1/5] Copying template baseline to: {target_root} [{mode}]")
    if LIGHTWEIGHT:
        print("  (Use --full for complete copy including QCM, Systems, etc.)")
    target_root.mkdir(parents=True, exist_ok=True)

    copied = 0
    for d in COPY_DIRS:
        src = TEMPLATE_ROOT / d
        dst = target_root / d
        if src.exists() and src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore=IGNORE_PATTERNS)
            copied += 1
    for f in COPY_FILES:
        src = TEMPLATE_ROOT / f
        dst = target_root / f
        if src.exists() and src.is_file():
            shutil.copy2(src, dst)
            copied += 1
    print(f"  Copied {copied} items")


def update_config(target_root: Path, project_name: str):
    """Step 2: Rewrite config.json with correct target path."""
    print("\n[2/5] Updating config.json...")
    config_path = target_root / "Platform" / "config.json"
    if not config_path.exists():
        print("  WARNING: config.json missing")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    config["project_id"] = f"project-{datetime.now().strftime('%Y%m%d')}-{project_name.lower()}"
    config["project_name"] = project_name
    config["root_path"] = str(target_root)
    config["q_spectrum_root"] = str(Q_SPECTRUM_ROOT)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"  Updated root_path: {target_root}")


def update_project_lock(target_root: Path, project_name: str):
    """Step 3: Rewrite .project_lock with target path."""
    print("\n[3/5] Updating .project_lock...")
    lock_path = target_root / ".project_lock"
    if not lock_path.exists():
        print("  WARNING: .project_lock missing")
        return

    with open(lock_path, "r", encoding="utf-8-sig") as f:
        lock = json.load(f)

    lock["project_id"] = f"project-{datetime.now().strftime('%Y%m%d')}-{project_name.lower()}"
    lock["project_name"] = project_name
    lock["root_path"] = str(target_root)
    lock["created_at"] = datetime.now().strftime("%Y-%m-%d")

    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(lock, f, indent=2, ensure_ascii=False)
    print("  Updated")


def update_database_paths(target_root: Path):
    """Step 4: UPDATE all path references inside the copied SQLite database.

    This is the KEY FIX missing from v2.0 scripts. Without this step,
    documents.file_path and repositories.local_path still point to the
    template's paths, making them useless in project instances.
    """
    print("\n[4/5] Updating database paths...")
    db_path = target_root / "Platform" / "db" / "platform.db"
    if not db_path.exists():
        print(f"  WARNING: Database missing: {db_path}")
        return

    # Read template root from the TEMPLATE's config (before our overwrite)
    template_root_str = str(TEMPLATE_ROOT)
    target_root_str = str(target_root)

    try:
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute("PRAGMA journal_mode=WAL")

        # Update documents.file_path
        c.execute(
            "UPDATE documents SET file_path = REPLACE(file_path, ?, ?)",
            (template_root_str, target_root_str)
        )
        doc_changes = c.rowcount
        # Also handle forward-slash variant
        c.execute(
            "UPDATE documents SET file_path = REPLACE(file_path, ?, ?)",
            (template_root_str.replace("\\", "/"), target_root_str.replace("\\", "/"))
        )

        # Update repositories.local_path
        c.execute(
            "UPDATE repositories SET local_path = REPLACE(local_path, ?, ?)",
            (template_root_str, target_root_str)
        )
        repo_changes = c.rowcount
        c.execute(
            "UPDATE repositories SET local_path = REPLACE(local_path, ?, ?)",
            (template_root_str.replace("\\", "/"), target_root_str.replace("\\", "/"))
        )

        conn.commit()
        conn.close()
        print(f"  Updated {doc_changes} document paths, {repo_changes} repository paths")

    except Exception as e:
        print(f"  ERROR updating database: {e}")


def rewrite_markdown_paths(target_root: Path):
    """Step 5: Rewrite hardcoded template paths in Markdown files."""
    print("\n[5/5] Rewriting Markdown paths...")
    template_root_str = str(TEMPLATE_ROOT).replace("\\", "\\\\")
    target_root_str = str(target_root).replace("\\", "\\\\")
    replacements = 0

    for md_file in target_root.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            original = content
            content = content.replace(template_root_str, target_root_str)
            # Also handle single-backslash variant
            content = content.replace(
                str(TEMPLATE_ROOT).replace("\\", "/"),
                str(target_root).replace("\\", "/")
            )
            if content != original:
                md_file.write_text(content, encoding="utf-8")
                replacements += 1
        except Exception:
            pass

    print(f"  Updated {replacements} Markdown files")


def main():
    print("=" * 60)
    print("Q-SpecTrum Project Deployer v3.0")
    print("=" * 60)

    if len(sys.argv) > 1:
        project_name = sys.argv[1]
    else:
        print("Usage: python deploy_project.py <project_name>")
        print("Example: python deploy_project.py MyProject")
        sys.exit(0)

    if not project_name:
        print("ERROR: Project name required")
        sys.exit(1)

    if " " in project_name:
        print("ERROR: Project name cannot contain spaces")
        sys.exit(1)

    target_root = PROJECTS_DIR / project_name
    if target_root.exists():
        print(f"ERROR: Project '{project_name}' already exists at {target_root}")
        sys.exit(1)

    print(f"\nTemplate : {TEMPLATE_ROOT}")
    print(f"Target   : {target_root}")

    copy_template(target_root)
    update_config(target_root, project_name)
    update_project_lock(target_root, project_name)
    update_database_paths(target_root)
    rewrite_markdown_paths(target_root)

    print("\n" + "=" * 60)
    print(f"SUCCESS: Project '{project_name}' deployed!")
    print("=" * 60)
    print(f"\nPath: {target_root}")
    print("\nTo activate roles:")
    print("  SPEC-001 (Architect): roles/SPEC-001_Chief_Architect.md")
    print("  SPEC-002 (Operator): roles/SPEC-002_Operations_Officer.md")
    print("  SPEC-003 (Coord):    roles/SPEC-003_Coordinator.md")


if __name__ == "__main__":
    main()
