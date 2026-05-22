"""
Q-SpecTrum · Minimal .env loader (zero-dependency)
==================================================
Auto-loads `.env` (if present) into `os.environ` at import time.

Design goals:
  - NO pip install required (pure stdlib).
  - Existing environment variables ALWAYS win over `.env` values
    (so shell exports stay authoritative).
  - Safe on missing / malformed files (silent no-op).
  - Ignores lines that start with "#" and blank lines.
  - Strips surrounding quotes from values.

Usage (at the top of an entry point):
    from env_loader import load_env
    load_env()
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def load_env(path: Optional[str | Path] = None, override: bool = False) -> int:
    """Load a dotenv-style file into os.environ.

    Returns the number of keys injected. Missing files return 0.
    """
    p = Path(path) if path else Path(__file__).resolve().parent / ".env"
    if not p.is_file():
        return 0
    injected = 0
    try:
        for raw in p.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip optional surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if not key:
                continue
            if not override and key in os.environ and os.environ[key] != "":
                continue
            os.environ[key] = value
            injected += 1
    except Exception:
        # Silent fallback — .env issues must never break the engine.
        return injected
    return injected


# Auto-load on import so callers just `import env_loader` or rely on
# qspectrum_engine.py pulling it in.
load_env()
