"""
Q-SpecTrum Result Layer v1.0
==============================
Layer 4 in the 5-layer closed-loop architecture:

  [Resource Layer] → [AI Chatroom] → [Execution Layer] → **[Result Layer]** → [Decision Layer]
                                                               ↓
                                                     Aggregated results feed BACK
                                                     into Resource Layer (closes loop)

The Result Layer:
  1. Captures every execution result (role, response, quality, metadata)
  2. Aggregates results per-project for trend analysis
  3. Feeds high-quality results BACK into the Resource Layer as new resources
  4. Tracks execution history for Decision Layer tuning

This is what makes the loop a LOOP — without this layer, results are dead-ends.
"""

import hashlib
import json
import logging
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import List

logger = logging.getLogger("q-spectrum.result-layer")


def _get_writable_db(filename: str, project_dir: str = None) -> str:
    """Get a writable DB path, with fallback to /tmp."""
    if project_dir:
        path = Path(project_dir) / filename
    else:
        path = Path(__file__).parent / filename
    try:
        conn = sqlite3.connect(str(path), timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE IF NOT EXISTS _w(x)")
        conn.execute("DROP TABLE IF EXISTS _w")
        conn.commit()
        conn.close()
        return str(path)
    except Exception:
        fallback = Path(tempfile.gettempdir()) / "qspectrum_data"
        fallback.mkdir(parents=True, exist_ok=True)
        return str(fallback / filename)


class ResultCapture:
    """
    Captures and stores every execution result with full metadata.

    Every interaction that passes through QSpectrumEngine.process() gets
    recorded here with its routing info, quality signals, and response.
    """

    def __init__(self, db_path: str = None):
        self._db_path = db_path or _get_writable_db("result_layer.db")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS execution_results (
                result_id TEXT PRIMARY KEY,
                timestamp REAL,
                project_id TEXT DEFAULT 'default',
                interaction_id TEXT,
                role_code TEXT,
                family TEXT,
                user_input TEXT,
                response TEXT,
                quality_score REAL DEFAULT 0.5,
                response_time_ms REAL DEFAULT 0,
                knowledge_deposit_id TEXT,
                gc_synced INTEGER DEFAULT 0,
                deerflow_skill TEXT,
                sandbox_valid INTEGER DEFAULT 0,
                flywheel_fed INTEGER DEFAULT 0,
                reingested INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS result_aggregations (
                agg_id TEXT PRIMARY KEY,
                project_id TEXT,
                timestamp REAL,
                period TEXT,
                total_results INTEGER,
                avg_quality REAL,
                role_distribution TEXT,
                family_distribution TEXT,
                knowledge_growth REAL,
                top_roles TEXT,
                metadata TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_results_project
                ON execution_results(project_id);
            CREATE INDEX IF NOT EXISTS idx_results_role
                ON execution_results(role_code);
            CREATE INDEX IF NOT EXISTS idx_results_reingested
                ON execution_results(reingested);
        """)
        conn.commit()
        conn.close()

    def capture(self, interaction_result: dict) -> str:
        """
        Capture an execution result from QSpectrumEngine.process().
        Returns the result_id.
        """
        routing = interaction_result.get("routing", {})
        meta = interaction_result.get("metadata", {})
        gc = interaction_result.get("ghost_channel", {})
        kd = interaction_result.get("knowledge_deposit", {})
        sb = interaction_result.get("sandbox", {})
        fw = interaction_result.get("flywheel", {})

        # Generate quality score from multiple signals
        quality = self._compute_quality(interaction_result)

        result_id = f"RL-{int(time.time())}-{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"

        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            INSERT INTO execution_results
            (result_id, timestamp, project_id, interaction_id, role_code, family,
             user_input, response, quality_score, response_time_ms,
             knowledge_deposit_id, gc_synced, deerflow_skill,
             sandbox_valid, flywheel_fed, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result_id, time.time(),
            meta.get("project_id", "default"),
            f"INT-{meta.get('interaction_number', 0)}",
            routing.get("role_code", ""),
            routing.get("family", ""),
            meta.get("user_input", "")[:500],
            interaction_result.get("response", "")[:2000],
            quality,
            meta.get("elapsed_seconds", 0) * 1000,
            kd.get("deposit_id", "") if kd else "",
            1 if gc and gc.get("synced") else 0,
            (interaction_result.get("deerflow") or {}).get("skill", ""),
            1 if sb and sb.get("valid") else 0,
            1 if fw else 0,
            json.dumps({
                "llm_provider": meta.get("llm_provider", ""),
                "confidence": routing.get("confidence", 0),
                "reasoning": routing.get("reasoning", ""),
            }),
        ))
        conn.commit()
        conn.close()

        logger.info(f"Result captured: {result_id} role={routing.get('role_code')} quality={quality:.2f}")
        return result_id

    def get_unreingested(self, limit: int = 50) -> List[dict]:
        """Get results that haven't been fed back to Resource Layer yet."""
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        rows = conn.execute("""
            SELECT result_id, project_id, role_code, family, user_input,
                   response, quality_score, metadata
            FROM execution_results
            WHERE reingested = 0 AND quality_score >= 0.4
            ORDER BY quality_score DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [{
            "result_id": r[0], "project_id": r[1], "role_code": r[2],
            "family": r[3], "user_input": r[4], "response": r[5],
            "quality_score": r[6], "metadata": json.loads(r[7] or "{}"),
        } for r in rows]

    def mark_reingested(self, result_ids: List[str]):
        """Mark results as reingested into Resource Layer."""
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        for rid in result_ids:
            conn.execute(
                "UPDATE execution_results SET reingested = 1 WHERE result_id = ?",
                (rid,))
        conn.commit()
        conn.close()

    def get_project_results(self, project_id: str, limit: int = 30) -> List[dict]:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        rows = conn.execute("""
            SELECT result_id, timestamp, role_code, family, quality_score,
                   response_time_ms, gc_synced, deerflow_skill
            FROM execution_results
            WHERE project_id = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (project_id, limit)).fetchall()
        conn.close()
        return [{
            "id": r[0], "time": r[1], "role": r[2], "family": r[3],
            "quality": r[4], "latency_ms": r[5], "gc": bool(r[6]),
            "deerflow": r[7] or None,
        } for r in rows]

    def _compute_quality(self, result: dict) -> float:
        """Compute quality score from multiple signals."""
        score = 0.3  # Base
        routing = result.get("routing", {})
        response = result.get("response", "")
        gc = result.get("ghost_channel", {})
        sb = result.get("sandbox", {})

        # Response length (substantive answers)
        score += min(0.15, len(response) / 2000)
        # Routing confidence
        score += routing.get("confidence", 0) * 0.2
        # Ghost Channel verification
        if gc and gc.get("synced"):
            score += 0.15
        # Sandbox validation
        if sb and sb.get("valid"):
            score += 0.1
        # DeerFlow execution
        df = result.get("deerflow")
        if df and df.get("executed"):
            score += 0.1

        return min(1.0, score)

    def get_stats(self) -> dict:
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        total = conn.execute("SELECT COUNT(*) FROM execution_results").fetchone()[0]
        avg_q = conn.execute("SELECT AVG(quality_score) FROM execution_results").fetchone()[0]
        reingested = conn.execute("SELECT COUNT(*) FROM execution_results WHERE reingested=1").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM execution_results WHERE reingested=0").fetchone()[0]

        by_family = {}
        for row in conn.execute(
            "SELECT family, COUNT(*), AVG(quality_score) FROM execution_results GROUP BY family"
        ):
            by_family[row[0]] = {"count": row[1], "avg_quality": round(row[2] or 0, 4)}

        conn.close()
        return {
            "total_results": total,
            "avg_quality": round(avg_q or 0, 4),
            "reingested": reingested,
            "pending_reingest": pending,
            "by_family": by_family,
        }


class ResultAggregator:
    """
    Aggregates execution results per project, per period.
    Generates trend analysis and performance summaries.
    """

    def __init__(self, capture: ResultCapture):
        self._capture = capture

    def aggregate_project(self, project_id: str) -> dict:
        """Generate aggregation for a specific project."""
        conn = sqlite3.connect(self._capture._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")

        total = conn.execute(
            "SELECT COUNT(*) FROM execution_results WHERE project_id=?",
            (project_id,)).fetchone()[0]
        avg_q = conn.execute(
            "SELECT AVG(quality_score) FROM execution_results WHERE project_id=?",
            (project_id,)).fetchone()[0]
        avg_latency = conn.execute(
            "SELECT AVG(response_time_ms) FROM execution_results WHERE project_id=?",
            (project_id,)).fetchone()[0]

        # Role distribution
        roles = {}
        for row in conn.execute(
            "SELECT role_code, COUNT(*) FROM execution_results WHERE project_id=? GROUP BY role_code ORDER BY COUNT(*) DESC",
            (project_id,)
        ):
            roles[row[0]] = row[1]

        # Family distribution
        families = {}
        for row in conn.execute(
            "SELECT family, COUNT(*) FROM execution_results WHERE project_id=? GROUP BY family",
            (project_id,)
        ):
            families[row[0]] = row[1]

        # GC coverage
        gc_synced = conn.execute(
            "SELECT COUNT(*) FROM execution_results WHERE project_id=? AND gc_synced=1",
            (project_id,)).fetchone()[0]

        conn.close()

        return {
            "project_id": project_id,
            "total_results": total,
            "avg_quality": round(avg_q or 0, 4),
            "avg_latency_ms": round(avg_latency or 0, 1),
            "role_distribution": roles,
            "family_distribution": families,
            "gc_coverage": round(gc_synced / max(total, 1), 4),
            "top_roles": list(roles.keys())[:3],
        }

    def aggregate_all(self) -> dict:
        """Aggregate across all projects."""
        conn = sqlite3.connect(self._capture._db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        projects = [r[0] for r in conn.execute(
            "SELECT DISTINCT project_id FROM execution_results"
        ).fetchall()]
        conn.close()

        project_aggs = {}
        for pid in projects:
            project_aggs[pid] = self.aggregate_project(pid)

        total = sum(a["total_results"] for a in project_aggs.values())
        avg_q = sum(a["avg_quality"] * a["total_results"] for a in project_aggs.values()) / max(total, 1)

        return {
            "total_projects": len(projects),
            "total_results": total,
            "avg_quality": round(avg_q, 4),
            "projects": project_aggs,
        }


class LoopCloser:
    """
    THE CRITICAL COMPONENT — feeds execution results back into Resource Layer.

    This is what makes the closed loop a LOOP:
      Result Layer → (aggregated, quality-filtered results) → Resource Layer
      → available as context for NEXT interaction → better execution → better results

    Process:
    1. Collect unreingested results above quality threshold
    2. Transform them into resource format (type="execution_result")
    3. Feed to ResourceAPI.reingest_results()
    4. Mark as reingested
    5. Trigger Decision Layer tuning update
    """

    def __init__(self, capture: ResultCapture, resource_api=None, decision_engine=None):
        self._capture = capture
        self._resource_api = resource_api  # Set after engine init
        self._decision_engine = decision_engine  # Set after engine init
        self._total_reingested = 0
        self._loop_iterations = 0

    def set_resource_api(self, api):
        """Wire the Resource Layer API (called after engine init)."""
        self._resource_api = api

    def set_decision_engine(self, engine):
        """Wire the Decision Engine (called after engine init)."""
        self._decision_engine = engine

    def close_loop(self, batch_size: int = 20) -> dict:
        """
        Execute one loop-closing cycle:
        1. Get unreingested results
        2. Feed to Resource Layer
        3. Feed to Decision Layer
        4. Mark as processed
        """
        results = self._capture.get_unreingested(limit=batch_size)
        if not results:
            return {"processed": 0, "message": "No pending results"}

        reingested_ids = []
        resource_count = 0
        decision_count = 0

        for r in results:
            # Feed to Resource Layer
            if self._resource_api:
                try:
                    self._resource_api.collect(
                        type_="execution_result",
                        content=f"[{r['role_code']}] Q: {r['user_input'][:200]}\nA: {r['response'][:500]}",
                        title=f"Result: {r['role_code']} → {r['family']} (q={r['quality_score']:.2f})",
                        tags=[r["family"], r["role_code"], "execution_result", r["project_id"]],
                        project_id=r["project_id"],
                        source="result_layer",
                    )
                    resource_count += 1
                except Exception as e:
                    logger.warning(f"Reingest to resource failed: {e}")

            # Feed to Decision Layer
            if self._decision_engine:
                try:
                    self._decision_engine.on_result(
                        role_code=r["role_code"],
                        family=r["family"],
                        quality_score=r["quality_score"],
                        response_time_ms=r["metadata"].get("elapsed_seconds", 0) * 1000,
                        llm_window_used=r["metadata"].get("llm_provider", "mock"),
                    )
                    decision_count += 1
                except Exception as e:
                    logger.warning(f"Decision feedback failed: {e}")

            reingested_ids.append(r["result_id"])

        # Mark as processed
        if reingested_ids:
            self._capture.mark_reingested(reingested_ids)

        self._total_reingested += len(reingested_ids)
        self._loop_iterations += 1

        logger.info(
            f"Loop closed: {len(reingested_ids)} results → "
            f"{resource_count} resources, {decision_count} decisions"
        )

        return {
            "processed": len(reingested_ids),
            "resources_created": resource_count,
            "decisions_fed": decision_count,
            "total_reingested": self._total_reingested,
            "loop_iteration": self._loop_iterations,
        }

    def get_status(self) -> dict:
        stats = self._capture.get_stats()
        return {
            "total_reingested": self._total_reingested,
            "loop_iterations": self._loop_iterations,
            "pending": stats["pending_reingest"],
            "resource_api_connected": self._resource_api is not None,
            "decision_engine_connected": self._decision_engine is not None,
        }


class ResultLayer:
    """
    Unified Result Layer — the complete Layer 4 of the closed-loop architecture.

    Combines:
    - ResultCapture: Record execution results
    - ResultAggregator: Aggregate per-project trends
    - LoopCloser: Feed results back to Resource + Decision layers
    """

    def __init__(self, db_path: str = None):
        self.capture = ResultCapture(db_path=db_path)
        self.aggregator = ResultAggregator(self.capture)
        self.loop_closer = LoopCloser(self.capture)

    def on_interaction_complete(self, result: dict) -> dict:
        """
        Called after each engine.process() to record the result.
        Returns capture info + triggers loop closing if enough results accumulated.
        """
        result_id = self.capture.capture(result)

        # Auto-close loop every 5 interactions
        loop_result = None
        stats = self.capture.get_stats()
        if stats["pending_reingest"] >= 5:
            loop_result = self.loop_closer.close_loop()

        return {
            "result_id": result_id,
            "total_results": stats["total_results"] + 1,
            "loop_closed": loop_result,
        }

    def wire(self, resource_api=None, decision_engine=None):
        """Wire external layer connections after initialization."""
        if resource_api:
            self.loop_closer.set_resource_api(resource_api)
        if decision_engine:
            self.loop_closer.set_decision_engine(decision_engine)

    def force_close_loop(self) -> dict:
        """Manually trigger a loop-closing cycle."""
        return self.loop_closer.close_loop()

    def status(self) -> dict:
        return {
            "layer": "result",
            "capture": self.capture.get_stats(),
            "loop_closer": self.loop_closer.get_status(),
        }


if __name__ == "__main__":
    print("=" * 60)
    print("  Q-SpecTrum Result Layer v1.0")
    print("=" * 60)

    rl = ResultLayer()

    # Simulate capturing results
    for i, (role, fam, inp) in enumerate([
        ("ROLE-Q04", "qcm", "分析项目瓶颈"),
        ("ROLE-Q01", "qcm", "设计微服务架构"),
        ("ROLE-T03", "trum", "平台战略规划"),
        ("ROLE-S01", "spec", "数据库schema审核"),
        ("ROLE-Q02", "qcm", "研究AI最佳实践"),
    ]):
        result = {
            "routing": {"role_code": role, "family": fam, "confidence": 0.8},
            "response": f"[{role}] 对于'{inp}'的分析结果... " * 10,
            "ghost_channel": {"synced": True, "changes": 3},
            "metadata": {"interaction_number": i + 1, "elapsed_seconds": 0.15},
        }
        info = rl.on_interaction_complete(result)
        print(f"  Captured: {info['result_id']} (total: {info['total_results']})")
        if info.get("loop_closed"):
            print(f"  Loop closed: {info['loop_closed']}")

    # Aggregation
    print(f"\n  Aggregation: {rl.aggregator.aggregate_all()}")
    print(f"\n  Status: {rl.status()}")
    print("=" * 60)
