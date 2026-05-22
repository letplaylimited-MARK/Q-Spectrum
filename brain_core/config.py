"""Brain configuration — centralized paths, env vars, and module detection."""

import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_scripts_dir() -> Path:
    return get_project_root() / "AI项目管理" / "Platform" / "scripts"


def get_db_dir() -> Path:
    return get_project_root() / "AI项目管理" / "Platform" / "db"


def find_db_path() -> Optional[Path]:
    base = get_db_dir()
    for candidate in ["platform.db", "platform_restored.db", "platform_v4.1.db"]:
        p = base / candidate
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def detect_writable_dir() -> Path:
    project_root = get_project_root()
    try:
        test_db = project_root / ".write_test.db"
        conn = sqlite3.connect(str(test_db), timeout=10, check_same_thread=False)
        conn.execute("CREATE TABLE IF NOT EXISTS _t(x)")
        conn.commit()
        conn.close()
        test_db.unlink(missing_ok=True)
        return project_root
    except Exception:
        fallback = Path(tempfile.gettempdir()) / "qspectrum_data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def detect_modules() -> dict:
    """Detect which optional modules are importable. Returns dict of module_name→bool."""
    checks = {
        "negotiation": ("negotiation_engine", "NegotiationEngine"),
        "project_memory": ("project_memory", "ProjectMemoryManager"),
        "global_search": ("global_search", "GlobalSearchEngine"),
        "role_config": ("role_config", "YAMLRoleLoader"),
        "contact": ("contact_channel", "ContactChannel"),
        "task_manager": ("task_manager", "TaskManager"),
        "scenario_engine": ("scenario_engine", "ScenarioEngineIntegration"),
    }
    result = {}
    for key, (mod_name, class_name) in checks.items():
        try:
            __import__(mod_name)
            result[key] = True
        except ImportError:
            result[key] = False
    return result


def get_llm_env() -> Optional[str]:
    return os.environ.get("QSPECTRUM_LLM") or None
