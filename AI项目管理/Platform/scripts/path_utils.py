"""
PathGuard Path Utilities (v3.0 - Q-SpecTrum(TEST) Clean Migration)
===================================================================
SINGLE SOURCE OF TRUTH for all project paths.
No script should hardcode paths. Always import from this module.

v3.0 Changes:
  - Added Q-SpecTrum container root awareness (q_spectrum_root)
  - Added forbidden path checking (blocks old Users\\z paths)
  - Added get_q_spectrum_root() for container-level operations
  - All paths resolved through config.json
"""

import json
import os
import sys
from pathlib import Path

# Self-contained path resolution to find config.json
# Assumes this file is in Platform/scripts/
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
CONFIG_PATH = PROJECT_ROOT / "Platform" / "config.json"

# Forbidden path patterns (never write to these)
# Portable patterns without drive letter prefix — catches all drive letters
FORBIDDEN_PATTERNS = [
    "Users\\z\\Desktop",
    "Users/z/Desktop",
    "Users\\adminWan\\Desktop",
    "Users/adminWan/Desktop",
]


def _load_config():
    """Loads config.json. Raises error if missing."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"CRITICAL: config.json not found at {CONFIG_PATH}\n"
            "   System cannot determine project paths without this file."
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_project_root():
    """Returns the absolute project root path from config.json.

    If root_path is relative (e.g. '.'), resolves it relative to
    the config.json directory's parent (AI项目管理/).
    """
    config = _load_config()
    root = config.get("root_path", "")
    if not root:
        raise ValueError("CRITICAL: 'root_path' is empty in config.json")
    root_path = Path(root)
    if not root_path.is_absolute():
        # Resolve relative to AI项目管理/ (config.json's grandparent)
        root_path = (CONFIG_PATH.parent.parent / root).resolve()
    return str(root_path)


def get_q_spectrum_root():
    """Returns the Q-SpecTrum container root path (parent of all projects)."""
    config = _load_config()
    qs_root = config.get("q_spectrum_root", "")
    if qs_root:
        qs_path = Path(qs_root)
        if not qs_path.is_absolute():
            # Resolve relative to AI项目管理/
            qs_path = (Path(get_project_root()) / qs_root).resolve()
        return str(qs_path)
    # Fallback: derive from root_path
    root = get_project_root()
    if "AI项目管理" in root:
        return root.split("AI项目管理")[0].rstrip("\\/")
    elif "Projects" in root:
        return root.split("Projects")[0].rstrip("\\/")
    else:
        return str(Path(root).parent)


def get_db_path():
    """Returns the absolute path to the SQLite database.

    Uses db_path from config.json if available, with fallback chain.
    """
    config = _load_config()
    root = get_project_root()
    # Try primary db_path from config
    db_rel = config.get("db_path", "Platform/db/platform.db")
    db_abs = os.path.join(root, db_rel)
    if os.path.exists(db_abs):
        return db_abs
    # Try fallback list
    for fb in config.get("db_fallback", []):
        fb_abs = os.path.join(root, fb)
        if os.path.exists(fb_abs):
            return fb_abs
    # Default
    return os.path.join(root, "Platform", "db", "platform.db")


def get_scripts_path():
    """Returns the absolute path to the scripts directory."""
    root = get_project_root()
    return os.path.join(root, "Platform", "scripts")


def get_roles_path():
    """Returns the absolute path to the roles directory."""
    root = get_project_root()
    return os.path.join(root, "roles")


def get_docs_path():
    """Returns the absolute path to the docs directory."""
    root = get_project_root()
    return os.path.join(root, "docs")


def get_systems_path():
    """Returns the absolute path to the Systems directory."""
    root = get_project_root()
    return os.path.join(root, "Systems")


def get_projects_path():
    """Returns the path to the Projects directory under Q-SpecTrum root."""
    return os.path.join(get_q_spectrum_root(), "Projects")


def is_forbidden_path(path_str):
    """Check if a path contains forbidden patterns (old root directories)."""
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in str(path_str):
            return True
    return False


def assert_safe_path(path_str, context=""):
    """
    Assert that a path does not contain forbidden patterns.
    Raises ValueError if forbidden path detected.
    """
    if is_forbidden_path(path_str):
        msg = "PATHGUARD BLOCKED: Forbidden path detected"
        if context:
            msg += f" in {context}"
        msg += f"\n  Path: {path_str}"
        msg += "\n  This path belongs to the old Q-SpecTrum installation."
        msg += "\n  All paths must use the Q-SpecTrum(TEST) root."
        raise ValueError(msg)
    return True


def verify_path_guard():
    """
    PathGuard Check: Verifies that the actual script location matches config.
    Call this at the start of any critical script.
    """
    try:
        config_root = get_project_root()
        # Normalize paths for comparison
        actual_root = str(PROJECT_ROOT).replace("\\", "/").lower().strip("/")
        config_root_norm = config_root.replace("\\", "/").lower().strip("/")

        if actual_root != config_root_norm:
            print("=" * 60)
            print("PATHGUARD ALERT: Path Mismatch Detected!")
            print("=" * 60)
            print(f"   Config Path : {config_root}")
            print(f"   Actual Path : {PROJECT_ROOT}")
            print("=" * 60)
            print("   ACTION: System halted to prevent data corruption.")
            print("   Please check config.json root_path.")
            print("=" * 60)
            sys.exit(1)

        # v3.0: Also verify no forbidden paths in config
        assert_safe_path(config_root, "config.json root_path")

        return True
    except ValueError as e:
        print(f"PATHGUARD BLOCKED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"PathGuard Verification Failed: {e}")
        sys.exit(1)


def get_all_paths():
    """Returns a dictionary of all standard paths for debugging."""
    return {
        "project_root": get_project_root(),
        "q_spectrum_root": get_q_spectrum_root(),
        "db_path": get_db_path(),
        "scripts_path": get_scripts_path(),
        "roles_path": get_roles_path(),
        "docs_path": get_docs_path(),
        "systems_path": get_systems_path(),
        "projects_path": get_projects_path(),
        "config_path": str(CONFIG_PATH),
    }


if __name__ == "__main__":
    print("PathGuard v3.0 - Path Verification")
    print("=" * 50)
    try:
        verify_path_guard()
        print("PathGuard check: PASSED")
        print()
        paths = get_all_paths()
        for key, val in paths.items():
            forbidden = " [FORBIDDEN!]" if is_forbidden_path(val) else ""
            print(f"  {key}: {val}{forbidden}")
    except SystemExit:
        pass
