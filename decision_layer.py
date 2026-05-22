"""
Q-SpecTrum Decision Tuning Layer (Layer 5)
【多组通用AI大模型窗口管理调整】(决策微调)

Manages multiple LLM provider windows, tunes routing weights based on feedback,
and provides A/B comparison capabilities for the closed-loop architecture.
"""

import json
import logging
import os
import sqlite3
import tempfile
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger("q-spectrum.decision-layer")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


@dataclass
class WindowStatus:
    """Status snapshot of an LLM window."""
    name: str
    provider_type: str
    is_available: bool
    call_count: int
    avg_latency_ms: float
    error_rate: float
    last_used: Optional[str]
    avg_quality_score: float


@dataclass
class RolePerformance:
    """Performance metrics for a specific role."""
    role_code: str
    family: str
    call_count: int
    avg_quality_score: float
    avg_response_time_ms: float
    avg_user_rating: float
    correctness_rate: float
    affinity_boost: float
    confidence_modifier: float
    last_updated: str


class LLMWindowManager:
    """
    Manages multiple named LLM provider windows with health tracking
    and automatic provider detection.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the window manager.

        Args:
            db_path: Path to SQLite database. Uses project dir, falls back to /tmp.
        """
        self.db_path = self._resolve_db_path(db_path)
        self._init_db()
        self._windows = {}
        self._active_window = None

        # Auto-register default windows
        self._auto_register_defaults()

    def _resolve_db_path(self, db_path: Optional[str]) -> str:
        """Resolve database path with fallback."""
        if db_path:
            return db_path

        # Try project directory first — test with actual SQLite write
        project_dir = Path(__file__).parent
        project_db = project_dir / "decision_layer.db"
        try:
            _tc = sqlite3.connect(str(project_db), timeout=10, check_same_thread=False)
            _tc.execute("CREATE TABLE IF NOT EXISTS _wt(x)")
            _tc.execute("INSERT INTO _wt VALUES(1)")
            _tc.commit()
            _tc.execute("DROP TABLE IF EXISTS _wt")
            _tc.commit()
            _tc.close()
            return str(project_db)
        except Exception:
            pass

        # Fall back to /tmp
        tmp_dir = Path(tempfile.gettempdir()) / "qspectrum_data"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return str(tmp_dir / "decision_layer.db")

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_windows (
                    name TEXT PRIMARY KEY,
                    provider_type TEXT NOT NULL,
                    config TEXT NOT NULL,
                    is_available INTEGER DEFAULT 1,
                    call_count INTEGER DEFAULT 0,
                    total_latency_ms REAL DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_used TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS window_quality_scores (
                    window_name TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(window_name) REFERENCES llm_windows(name)
                )
            """)
            conn.commit()

    def _auto_register_defaults(self):
        """Auto-detect and register default provider windows."""
        defaults = [
            ("mock", "mock", {"model": "mock-v1"}),
            ("ollama", "ollama", self._detect_ollama_config()),
            ("openai", "openai", self._detect_openai_config()),
            ("anthropic", "anthropic", self._detect_anthropic_config()),
        ]

        for name, ptype, config in defaults:
            if config is not None:
                self.register_window(name, ptype, config)

    def _detect_ollama_config(self) -> Optional[Dict[str, Any]]:
        """Detect Ollama availability at localhost:11434."""
        try:
            req = urllib.request.Request(
                "http://localhost:11434/api/tags",
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    logger.info("Ollama detected at localhost:11434")
                    return {"base_url": "http://localhost:11434"}
        except (urllib.error.URLError, urllib.error.HTTPError, Exception):
            pass
        return None

    def _detect_openai_config(self) -> Optional[Dict[str, Any]]:
        """Detect OpenAI availability via API key."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            logger.info("OpenAI API key detected")
            return {"api_key": api_key, "model": "gpt-4"}
        return None

    def _detect_anthropic_config(self) -> Optional[Dict[str, Any]]:
        """Detect Anthropic availability via API key."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            logger.info("Anthropic API key detected")
            return {"api_key": api_key, "model": "claude-3-opus-20240229"}
        return None

    def register_window(self, name: str, provider_type: str, config: Dict[str, Any]) -> bool:
        """
        Register a new LLM provider window.

        Args:
            name: Window identifier
            provider_type: Type of provider (mock, ollama, openai, anthropic)
            config: Provider configuration dict

        Returns:
            True if registered successfully
        """
        try:
            now = datetime.utcnow().isoformat() + "Z"
            with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO llm_windows
                    (name, provider_type, config, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, provider_type, json.dumps(config), now, now))
                conn.commit()

            self._windows[name] = {
                "provider_type": provider_type,
                "config": config,
                "is_available": True
            }
            logger.info(f"Registered window '{name}' ({provider_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to register window '{name}': {e}")
            return False

    def get_window(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get window configuration and status.

        Args:
            name: Window identifier

        Returns:
            Window info dict or None if not found
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM llm_windows WHERE name = ?",
                    (name,)
                ).fetchone()

                if not row:
                    return None

                config = json.loads(row["config"])
                call_count = row["call_count"]
                avg_latency = (
                    row["total_latency_ms"] / call_count
                    if call_count > 0 else 0
                )
                error_rate = (
                    row["error_count"] / call_count
                    if call_count > 0 else 0
                )

                # Get recent quality scores
                quality_rows = conn.execute("""
                    SELECT quality_score FROM window_quality_scores
                    WHERE window_name = ?
                    ORDER BY timestamp DESC LIMIT 10
                """, (name,)).fetchall()
                quality_scores = [r[0] for r in quality_rows]

                return {
                    "name": name,
                    "provider_type": row["provider_type"],
                    "config": config,
                    "is_available": bool(row["is_available"]),
                    "call_count": call_count,
                    "avg_latency_ms": round(avg_latency, 2),
                    "error_rate": round(error_rate, 4),
                    "last_used": row["last_used"],
                    "quality_scores": quality_scores,
                    "avg_quality_score": (
                        round(sum(quality_scores) / len(quality_scores), 3)
                        if quality_scores else 0
                    )
                }
        except Exception as e:
            logger.error(f"Failed to get window '{name}': {e}")
            return None

    def list_windows(self) -> List[WindowStatus]:
        """
        List all registered windows with health status.

        Returns:
            List of WindowStatus objects
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
                rows = conn.execute(
                    "SELECT name FROM llm_windows ORDER BY name"
                ).fetchall()

            statuses = []
            for (name,) in rows:
                window = self.get_window(name)
                if window:
                    statuses.append(WindowStatus(
                        name=window["name"],
                        provider_type=window["provider_type"],
                        is_available=window["is_available"],
                        call_count=window["call_count"],
                        avg_latency_ms=window["avg_latency_ms"],
                        error_rate=window["error_rate"],
                        last_used=window["last_used"],
                        avg_quality_score=window["avg_quality_score"]
                    ))
            return statuses
        except Exception as e:
            logger.error(f"Failed to list windows: {e}")
            return []

    def set_active(self, name: str) -> bool:
        """
        Switch the primary active window.

        Args:
            name: Window identifier

        Returns:
            True if successfully switched
        """
        window = self.get_window(name)
        if not window:
            logger.error(f"Window '{name}' not found")
            return False

        self._active_window = name
        logger.info(f"Active window switched to '{name}'")
        return True

    def get_active(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active window.

        Returns:
            Active window info or None
        """
        if not self._active_window:
            # Default to first available window
            windows = self.list_windows()
            if windows:
                self._active_window = windows[0].name

        if self._active_window:
            return self.get_window(self._active_window)
        return None

    def record_usage(
        self,
        window_name: str,
        latency_ms: float,
        quality_score: float,
        error: bool = False
    ):
        """
        Record usage metrics for a window.

        Args:
            window_name: Window identifier
            latency_ms: Response latency in milliseconds
            quality_score: Quality score (0-1)
            error: Whether an error occurred
        """
        try:
            now = datetime.utcnow().isoformat() + "Z"
            with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
                # Update aggregate stats
                if error:
                    conn.execute("""
                        UPDATE llm_windows
                        SET call_count = call_count + 1,
                            total_latency_ms = total_latency_ms + ?,
                            error_count = error_count + 1,
                            last_used = ?,
                            updated_at = ?
                        WHERE name = ?
                    """, (latency_ms, now, now, window_name))
                else:
                    conn.execute("""
                        UPDATE llm_windows
                        SET call_count = call_count + 1,
                            total_latency_ms = total_latency_ms + ?,
                            last_used = ?,
                            updated_at = ?
                        WHERE name = ?
                    """, (latency_ms, now, now, window_name))

                # Record quality score
                conn.execute("""
                    INSERT INTO window_quality_scores
                    (window_name, quality_score, timestamp)
                    VALUES (?, ?, ?)
                """, (window_name, quality_score, now))

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record usage for '{window_name}': {e}")


class RoutingTuner:
    """
    Tunes routing weights based on quality feedback from executed tasks.
    Maintains per-role performance metrics and suggests rebalancing.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the routing tuner.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = self._resolve_db_path(db_path)
        self._init_db()
        self._feedback_count = 0

    def _resolve_db_path(self, db_path: Optional[str]) -> str:
        """Resolve database path with fallback."""
        if db_path:
            return db_path

        project_dir = Path(__file__).parent
        project_db = project_dir / "decision_layer.db"
        try:
            _tc = sqlite3.connect(str(project_db), timeout=10, check_same_thread=False)
            _tc.execute("CREATE TABLE IF NOT EXISTS _wt(x)")
            _tc.execute("INSERT INTO _wt VALUES(1)")
            _tc.commit()
            _tc.execute("DROP TABLE IF EXISTS _wt")
            _tc.commit()
            _tc.close()
            return str(project_db)
        except Exception:
            pass

        tmp_dir = Path(tempfile.gettempdir()) / "qspectrum_data"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return str(tmp_dir / "decision_layer.db")

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS routing_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_code TEXT NOT NULL,
                    family TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    response_time_ms REAL NOT NULL,
                    user_rating REAL,
                    was_correct INTEGER,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS routing_weights (
                    role_code TEXT PRIMARY KEY,
                    family TEXT NOT NULL,
                    affinity_boost REAL DEFAULT 1.0,
                    confidence_modifier REAL DEFAULT 1.0,
                    sample_count INTEGER DEFAULT 0,
                    ema_quality REAL DEFAULT 0.5,
                    last_updated TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_role
                ON routing_feedback(role_code)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_family
                ON routing_feedback(family)
            """)
            conn.commit()

    def record_feedback(
        self,
        role_code: str,
        family: str,
        quality_score: float,
        response_time_ms: float,
        user_rating: Optional[float] = None,
        was_correct: Optional[bool] = None
    ) -> bool:
        """
        Record quality feedback for a role execution.

        Args:
            role_code: Code of executed role (e.g., "SEC001")
            family: Role family (trum, spec, qcm)
            quality_score: Quality score (0-1)
            response_time_ms: Response time in milliseconds
            user_rating: Optional user rating (1-5)
            was_correct: Optional correctness flag

        Returns:
            True if recorded successfully
        """
        try:
            now = datetime.utcnow().isoformat() + "Z"
            with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
                # Record feedback
                conn.execute("""
                    INSERT INTO routing_feedback
                    (role_code, family, quality_score, response_time_ms,
                     user_rating, was_correct, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    role_code, family, quality_score, response_time_ms,
                    user_rating, 1 if was_correct else (0 if was_correct is False else None),
                    now
                ))

                # Ensure routing weight entry exists
                conn.execute("""
                    INSERT OR IGNORE INTO routing_weights
                    (role_code, family, last_updated)
                    VALUES (?, ?, ?)
                """, (role_code, family, now))

                conn.commit()

            self._feedback_count += 1

            # Auto-update weights every 10 feedback entries
            if self._feedback_count % 10 == 0:
                self._update_weights()

            logger.debug(f"Recorded feedback for {role_code}: quality={quality_score:.3f}")
            return True
        except Exception as e:
            logger.error(f"Failed to record feedback for {role_code}: {e}")
            return False

    def _update_weights(self):
        """Update routing weights based on accumulated feedback."""
        try:
            with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
                conn.row_factory = sqlite3.Row

                # Get all roles with feedback
                roles = conn.execute("""
                    SELECT DISTINCT role_code, family FROM routing_feedback
                    ORDER BY role_code
                """).fetchall()

                for role in roles:
                    role_code = role["role_code"]
                    family = role["family"]

                    # Get recent feedback (last 30 days)
                    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
                    feedback = conn.execute("""
                        SELECT quality_score, response_time_ms, user_rating, was_correct
                        FROM routing_feedback
                        WHERE role_code = ? AND timestamp > ?
                        ORDER BY timestamp
                    """, (role_code, cutoff)).fetchall()

                    if not feedback:
                        continue

                    # Calculate EMA of quality scores
                    ema = 0.5  # Start from middle
                    decay = 0.95

                    for row in feedback:
                        quality = row["quality_score"]
                        ema = decay * ema + (1 - decay) * quality

                    # Calculate confidence modifier from user ratings
                    ratings = [r["user_rating"] for r in feedback if r["user_rating"]]
                    if ratings:
                        avg_rating = sum(ratings) / len(ratings)
                        confidence = avg_rating / 5.0  # Normalize to 0-1
                    else:
                        confidence = ema

                    # Affinity boost based on quality trend
                    affinity = 0.5 + (ema * 1.5)  # Range: 0.5 to 2.0

                    # Update weights
                    now = datetime.utcnow().isoformat() + "Z"
                    conn.execute("""
                        UPDATE routing_weights
                        SET affinity_boost = ?,
                            confidence_modifier = ?,
                            ema_quality = ?,
                            sample_count = ?,
                            last_updated = ?
                        WHERE role_code = ?
                    """, (
                        round(affinity, 4),
                        round(confidence, 4),
                        round(ema, 4),
                        len(feedback),
                        now,
                        role_code
                    ))

                conn.commit()

            logger.info(
                f"Updated routing weights for {len(roles)} role(s) "
                f"with feedback history (total core roles = 15; "
                f"roles without feedback yet keep default weights)"
            )
        except Exception as e:
            logger.error(f"Failed to update weights: {e}")

    def get_tuned_weights(self) -> Dict[str, Dict[str, float]]:
        """
        Get current tuned weights for all roles.

        Returns:
            Dict mapping role_code → {affinity_boost, confidence_modifier}
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("""
                    SELECT role_code, affinity_boost, confidence_modifier
                    FROM routing_weights
                """).fetchall()

            return {
                row["role_code"]: {
                    "affinity_boost": row["affinity_boost"],
                    "confidence_modifier": row["confidence_modifier"]
                }
                for row in rows
            }
        except Exception as e:
            logger.error(f"Failed to get tuned weights: {e}")
            return {}

    def get_role_performance(self, role_code: str) -> Optional[RolePerformance]:
        """
        Get detailed performance metrics for a role.

        Args:
            role_code: Role identifier

        Returns:
            RolePerformance object or None
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
                conn.row_factory = sqlite3.Row

                # Get feedback stats
                feedback_row = conn.execute("""
                    SELECT
                        COUNT(*) as count,
                        AVG(quality_score) as avg_quality,
                        AVG(response_time_ms) as avg_response,
                        AVG(user_rating) as avg_rating,
                        SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                        family
                    FROM routing_feedback
                    WHERE role_code = ?
                    GROUP BY role_code
                """, (role_code,)).fetchone()

                if not feedback_row or feedback_row["count"] == 0:
                    return None

                # Get weight info
                weight_row = conn.execute("""
                    SELECT affinity_boost, confidence_modifier, last_updated
                    FROM routing_weights
                    WHERE role_code = ?
                """, (role_code,)).fetchone()

                correctness_rate = (
                    feedback_row["correct_count"] / feedback_row["count"]
                    if feedback_row["count"] > 0 else 0
                )

                return RolePerformance(
                    role_code=role_code,
                    family=feedback_row["family"],
                    call_count=feedback_row["count"],
                    avg_quality_score=round(feedback_row["avg_quality"] or 0, 4),
                    avg_response_time_ms=round(feedback_row["avg_response"] or 0, 2),
                    avg_user_rating=round(feedback_row["avg_rating"] or 0, 2),
                    correctness_rate=round(correctness_rate, 4),
                    affinity_boost=weight_row["affinity_boost"] if weight_row else 1.0,
                    confidence_modifier=weight_row["confidence_modifier"] if weight_row else 1.0,
                    last_updated=weight_row["last_updated"] if weight_row else "unknown"
                )
        except Exception as e:
            logger.error(f"Failed to get role performance for {role_code}: {e}")
            return None

    def get_family_performance(self) -> Dict[str, Dict[str, float]]:
        """
        Get aggregated performance metrics by role family.

        Returns:
            Dict mapping family → performance metrics
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("""
                    SELECT
                        family,
                        COUNT(*) as count,
                        AVG(quality_score) as avg_quality,
                        AVG(response_time_ms) as avg_response,
                        AVG(user_rating) as avg_rating,
                        SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct_count
                    FROM routing_feedback
                    GROUP BY family
                """).fetchall()

            result = {}
            for row in rows:
                correctness = (
                    row["correct_count"] / row["count"]
                    if row["count"] > 0 else 0
                )
                result[row["family"]] = {
                    "call_count": row["count"],
                    "avg_quality_score": round(row["avg_quality"] or 0, 4),
                    "avg_response_time_ms": round(row["avg_response"] or 0, 2),
                    "avg_user_rating": round(row["avg_rating"] or 0, 2),
                    "correctness_rate": round(correctness, 4)
                }

            return result
        except Exception as e:
            logger.error(f"Failed to get family performance: {e}")
            return {}

    def suggest_rebalance(self) -> Dict[str, Any]:
        """
        Analyze performance and suggest routing weight rebalancing.

        Returns:
            Dict with suggestions and underperforming roles
        """
        try:
            suggestions = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "underperforming_roles": [],
                "high_latency_roles": [],
                "low_correctness_roles": [],
                "recommendations": []
            }

            with sqlite3.connect(self.db_path, timeout=10, check_same_thread=False) as conn:
                conn.row_factory = sqlite3.Row

                # Find underperforming roles (quality < 0.6)
                low_quality = conn.execute("""
                    SELECT role_code, family, AVG(quality_score) as avg_quality
                    FROM routing_feedback
                    WHERE timestamp > ?
                    GROUP BY role_code
                    HAVING avg_quality < 0.6
                    ORDER BY avg_quality
                """, (
                    (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
                )).fetchall()

                for row in low_quality:
                    suggestions["underperforming_roles"].append({
                        "role_code": row["role_code"],
                        "family": row["family"],
                        "avg_quality": round(row["avg_quality"], 4)
                    })

                # Find high-latency roles (> 95th percentile)
                latency_stats = conn.execute("""
                    SELECT
                        role_code, family,
                        AVG(response_time_ms) as avg_latency
                    FROM routing_feedback
                    WHERE timestamp > ?
                    GROUP BY role_code
                """, (
                    (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
                )).fetchall()

                if latency_stats:
                    latencies = [r["avg_latency"] for r in latency_stats]
                    p95 = sorted(latencies)[int(len(latencies) * 0.95)]

                    for row in latency_stats:
                        if row["avg_latency"] > p95:
                            suggestions["high_latency_roles"].append({
                                "role_code": row["role_code"],
                                "family": row["family"],
                                "avg_latency_ms": round(row["avg_latency"], 2)
                            })

                # Find low-correctness roles
                low_correct = conn.execute("""
                    SELECT
                        role_code, family,
                        COUNT(*) as total,
                        SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct
                    FROM routing_feedback
                    WHERE was_correct IS NOT NULL
                        AND timestamp > ?
                    GROUP BY role_code
                    HAVING (CAST(correct AS FLOAT) / total) < 0.7
                """, (
                    (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
                )).fetchall()

                for row in low_correct:
                    correctness = row["correct"] / row["total"]
                    suggestions["low_correctness_roles"].append({
                        "role_code": row["role_code"],
                        "family": row["family"],
                        "correctness_rate": round(correctness, 4)
                    })

            # Generate recommendations
            if suggestions["underperforming_roles"]:
                suggestions["recommendations"].append(
                    f"Review or retrain {len(suggestions['underperforming_roles'])} "
                    "underperforming roles"
                )

            if suggestions["high_latency_roles"]:
                suggestions["recommendations"].append(
                    f"Optimize {len(suggestions['high_latency_roles'])} "
                    "high-latency roles or consider routing to faster providers"
                )

            if suggestions["low_correctness_roles"]:
                suggestions["recommendations"].append(
                    f"Improve {len(suggestions['low_correctness_roles'])} "
                    "roles with low correctness rates"
                )

            return suggestions
        except Exception as e:
            logger.error(f"Failed to suggest rebalance: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(e)
            }


class DecisionEngine:
    """
    Combines LLMWindowManager and RoutingTuner to provide integrated
    decision-making for task routing and provider selection.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the decision engine.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.window_mgr = LLMWindowManager(db_path)
        self.tuner = RoutingTuner(db_path)
        self._task_type_history = defaultdict(list)

    def on_result(
        self,
        role_code: str,
        family: str,
        quality_score: float,
        response_time_ms: float,
        llm_window_used: str,
        user_rating: Optional[float] = None,
        was_correct: Optional[bool] = None
    ) -> bool:
        """
        Record the outcome of a task execution.

        Args:
            role_code: Code of executed role
            family: Role family (trum, spec, qcm)
            quality_score: Quality score (0-1)
            response_time_ms: Response time in milliseconds
            llm_window_used: Name of LLM window used
            user_rating: Optional user rating (1-5)
            was_correct: Optional correctness flag

        Returns:
            True if recorded successfully
        """
        # Record feedback in tuner
        self.tuner.record_feedback(
            role_code=role_code,
            family=family,
            quality_score=quality_score,
            response_time_ms=response_time_ms,
            user_rating=user_rating,
            was_correct=was_correct
        )

        # Record usage in window manager
        self.window_mgr.record_usage(
            window_name=llm_window_used,
            latency_ms=response_time_ms,
            quality_score=quality_score,
            error=(quality_score < 0.5)
        )

        # Track for task routing optimization
        self._task_type_history[family].append({
            "role_code": role_code,
            "quality_score": quality_score,
            "llm_window": llm_window_used,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

        return True

    def get_routing_boost(self, role_code: str) -> float:
        """
        Get affinity boost for a role (used by Secretary routing).

        Args:
            role_code: Role identifier

        Returns:
            Affinity boost factor (default 1.0)
        """
        weights = self.tuner.get_tuned_weights()
        if role_code in weights:
            return weights[role_code].get("affinity_boost", 1.0)
        return 1.0

    def get_best_llm_for_task(self, task_type: str) -> Optional[str]:
        """
        Recommend the best LLM window for a task type.

        Args:
            task_type: Task type or family (trum, spec, qcm)

        Returns:
            Recommended LLM window name or None
        """
        if task_type not in self._task_type_history:
            # Fall back to active window
            active = self.window_mgr.get_active()
            return active["name"] if active else None

        # Analyze performance for this task type
        history = self._task_type_history[task_type]
        if not history:
            active = self.window_mgr.get_active()
            return active["name"] if active else None

        # Group by window and calculate average quality
        window_scores = defaultdict(list)
        for entry in history[-50:]:  # Last 50 entries
            window_scores[entry["llm_window"]].append(
                entry["quality_score"]
            )

        # Find best performing window
        best_window = None
        best_score = -1
        for window, scores in window_scores.items():
            avg = sum(scores) / len(scores)
            if avg > best_score:
                best_score = avg
                best_window = window

        return best_window

    def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall decision layer health status.

        Returns:
            Health metrics dict
        """
        windows = self.window_mgr.list_windows()
        family_perf = self.tuner.get_family_performance()

        available_count = sum(1 for w in windows if w.is_available)
        total_count = len(windows)

        # Calculate overall quality
        all_quality = []
        for w in windows:
            if w.avg_quality_score > 0:
                all_quality.append(w.avg_quality_score)

        overall_quality = (
            sum(all_quality) / len(all_quality)
            if all_quality else 0
        )

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "windows": {
                "total": total_count,
                "available": available_count,
                "availability_rate": round(available_count / total_count, 4) if total_count > 0 else 0
            },
            "overall_quality_score": round(overall_quality, 4),
            "family_performance": family_perf,
            "active_window": (
                self.window_mgr.get_active()["name"]
                if self.window_mgr.get_active() else None
            )
        }

    def get_status(self) -> Dict[str, Any]:
        """Alias for get_system_health() for API consistency."""
        return self.get_system_health()

    def generate_tuning_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance and tuning report.

        Returns:
            Detailed report dict
        """
        report = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "system_health": self.get_system_health(),
            "windows": [],
            "role_performances": [],
            "rebalance_suggestions": self.tuner.suggest_rebalance()
        }

        # Window details
        for window in self.window_mgr.list_windows():
            report["windows"].append(asdict(window))

        # Role performances (top performers and underperformers)
        weights = self.tuner.get_tuned_weights()
        for role_code in sorted(weights.keys()):
            perf = self.tuner.get_role_performance(role_code)
            if perf:
                report["role_performances"].append(asdict(perf))

        return report

    def status(self) -> Dict[str, Any]:
        """
        Get full decision engine status.

        Returns:
            Complete status dict
        """
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "component": "decision-layer",
            "db_path": self.db_path,
            "health": self.get_system_health(),
            "active_window": (
                self.window_mgr.get_active()["name"]
                if self.window_mgr.get_active() else None
            ),
            "total_roles_tracked": len(
                self.tuner.get_tuned_weights()
            ),
            "total_feedback_recorded": sum(
                len(v) for v in self._task_type_history.values()
            )
        }


if __name__ == "__main__":
    """Test and demonstration block."""

    print("=" * 70)
    print("Q-SpecTrum Decision Tuning Layer - Test Block")
    print("=" * 70)

    # Initialize engine
    engine = DecisionEngine()
    print("\n[1] Decision Engine initialized")

    # Register a test window
    engine.window_mgr.register_window(
        "test-claude",
        "anthropic",
        {"model": "claude-3-sonnet"}
    )
    print("[2] Registered test window 'test-claude'")

    # List windows
    print("\n[3] Available LLM Windows:")
    for window in engine.window_mgr.list_windows():
        print(f"    - {window.name} ({window.provider_type}) - "
              f"Available: {window.is_available}")

    # Record some test feedback
    print("\n[4] Recording test feedback:")
    test_cases = [
        ("SEC001", "trum", 0.92, 250.5, 5.0, True),
        ("SEC001", "trum", 0.88, 270.2, 4.0, True),
        ("SEC002", "trum", 0.75, 180.1, 3.0, False),
        ("SPEC001", "spec", 0.95, 320.0, 5.0, True),
        ("SPEC002", "spec", 0.65, 150.0, 2.0, False),
        ("QCM001", "qcm", 0.85, 200.0, 4.0, True),
    ]

    for role, family, quality, latency, rating, correct in test_cases:
        engine.on_result(
            role_code=role,
            family=family,
            quality_score=quality,
            response_time_ms=latency,
            llm_window_used="test-claude",
            user_rating=rating,
            was_correct=correct
        )
        print(f"    Recorded: {role} ({family}) - quality={quality:.2f}")

    # Show status
    print("\n[5] System Status:")
    status = engine.status()
    print(f"    Active window: {status['active_window']}")
    print(f"    Roles tracked: {status['total_roles_tracked']}")
    print(f"    Feedback entries: {status['total_feedback_recorded']}")

    # Show health
    print("\n[6] System Health:")
    health = engine.get_system_health()
    print(f"    Windows available: {health['windows']['available']}/{health['windows']['total']}")
    print(f"    Overall quality: {health['overall_quality_score']:.4f}")
    print("    Family performance:")
    for family, perf in health["family_performance"].items():
        print(f"      {family}: quality={perf['avg_quality_score']:.4f}, "
              f"calls={perf['call_count']}")

    # Show role performance
    print("\n[7] Role Performance (SEC001):")
    perf = engine.tuner.get_role_performance("SEC001")
    if perf:
        print(f"    Quality: {perf.avg_quality_score:.4f}")
        print(f"    Response time: {perf.avg_response_time_ms:.2f}ms")
        print(f"    User rating: {perf.avg_user_rating:.2f}/5.0")
        print(f"    Correctness: {perf.correctness_rate:.4f}")
        print(f"    Affinity boost: {perf.affinity_boost:.4f}")

    # Show routing boost
    print("\n[8] Routing Boosts:")
    for role_code in ["SEC001", "SPEC001", "QCM001"]:
        boost = engine.get_routing_boost(role_code)
        print(f"    {role_code}: {boost:.4f}")

    # Show rebalance suggestions
    print("\n[9] Rebalance Suggestions:")
    suggestions = engine.tuner.suggest_rebalance()
    print(f"    Underperforming: {len(suggestions['underperforming_roles'])}")
    print(f"    High latency: {len(suggestions['high_latency_roles'])}")
    print(f"    Low correctness: {len(suggestions['low_correctness_roles'])}")
    for rec in suggestions["recommendations"]:
        print(f"      - {rec}")

    print("\n" + "=" * 70)
    print("Test block completed successfully")
    print("=" * 70)
