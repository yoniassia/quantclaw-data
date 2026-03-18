"""
Database connection pool and query helpers for the pipeline.
"""
import json
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2 import pool, extras

from ..config import DB_CONFIG

logger = logging.getLogger("quantclaw.db")

_pool: Optional[pool.ThreadedConnectionPool] = None


def get_db_pool(min_conn: int = 2, max_conn: int = 10) -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        _pool = pool.ThreadedConnectionPool(min_conn, max_conn, **DB_CONFIG)
    return _pool


@contextmanager
def get_connection():
    p = get_db_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def execute_query(sql: str, params: tuple = None, fetch: bool = False) -> Optional[List[Dict]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch:
                return [dict(row) for row in cur.fetchall()]
    return None


def execute_many(sql: str, data: List[tuple]):
    with get_connection() as conn:
        with conn.cursor() as cur:
            extras.execute_batch(cur, sql, data, page_size=500)


def insert_data_points(module_id: int, points: List[Dict]):
    """Bulk insert data points using execute_values for speed."""
    if not points:
        return 0

    sql = """
        INSERT INTO data_points (ts, module_id, symbol, cadence, tier, quality_score, payload, source_hash)
        VALUES %s
        ON CONFLICT DO NOTHING
    """
    values = []
    for p in points:
        values.append((
            p["ts"],
            module_id,
            p.get("symbol"),
            p.get("cadence", "daily"),
            p.get("tier", "bronze"),
            p.get("quality_score", 0),
            json.dumps(p.get("payload", {})),
            p.get("source_hash"),
        ))

    with get_connection() as conn:
        with conn.cursor() as cur:
            extras.execute_values(cur, sql, values, page_size=500)
            return len(values)


def get_module_id(module_name: str) -> Optional[int]:
    rows = execute_query(
        "SELECT id FROM modules WHERE name = %s", (module_name,), fetch=True
    )
    return rows[0]["id"] if rows else None


def register_module(name: str, display_name: str = None, source_file: str = None,
                    cadence: str = "daily", granularity: str = "symbol",
                    tags: List[str] = None) -> int:
    """Register or update a module in the registry. Returns module_id."""
    rows = execute_query(
        """INSERT INTO modules (name, display_name, source_file, cadence, granularity)
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (name) DO UPDATE SET
               display_name = COALESCE(EXCLUDED.display_name, modules.display_name),
               source_file = COALESCE(EXCLUDED.source_file, modules.source_file),
               cadence = EXCLUDED.cadence,
               granularity = EXCLUDED.granularity,
               updated_at = NOW()
           RETURNING id""",
        (name, display_name or name, source_file, cadence, granularity),
        fetch=True,
    )
    module_id = rows[0]["id"]

    if tags:
        for tag_label in tags:
            execute_query(
                """INSERT INTO module_tags (module_id, tag_id)
                   SELECT %s, id FROM tag_definitions WHERE label = %s
                   ON CONFLICT DO NOTHING""",
                (module_id, tag_label),
            )

    return module_id


def start_pipeline_run(module_id: int, tier_target: str) -> int:
    rows = execute_query(
        """INSERT INTO pipeline_runs (module_id, tier_target, status)
           VALUES (%s, %s, 'running') RETURNING id""",
        (module_id, tier_target),
        fetch=True,
    )
    return rows[0]["id"]


def complete_pipeline_run(run_id: int, status: str, rows_in: int = 0,
                          rows_out: int = 0, rows_failed: int = 0,
                          error_message: str = None, duration_ms: int = None):
    execute_query(
        """UPDATE pipeline_runs SET
               status = %s, completed_at = NOW(), duration_ms = %s,
               rows_in = %s, rows_out = %s, rows_failed = %s,
               error_message = %s
           WHERE id = %s""",
        (status, duration_ms, rows_in, rows_out, rows_failed, error_message, run_id),
    )


def record_quality_check(run_id: int, check_type: str, passed: bool,
                         score: int = 0, details: Dict = None):
    execute_query(
        """INSERT INTO quality_checks (run_id, check_type, passed, score, details)
           VALUES (%s, %s, %s, %s, %s)""",
        (run_id, check_type, passed, score, json.dumps(details or {})),
    )


def create_alert(module_id: int, severity: str, message: str,
                 category: str = None, run_id: int = None, details: Dict = None):
    execute_query(
        """INSERT INTO alerts (module_id, run_id, severity, category, message, details)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (module_id, run_id, severity, category, message, json.dumps(details or {})),
    )
