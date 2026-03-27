"""
Read-only access to eToro SAPI pipeline PostgreSQL (database etoro_sapi).

Connection: ETORO_SAPI_PG_DSN env, else same defaults as etoro-sapi-pipeline PM2
(dbname=etoro_sapi user=quant, local socket).
"""
from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

DEFAULT_DSN = os.environ.get(
    "ETORO_SAPI_PG_DSN",
    "dbname=etoro_sapi user=quant host=/var/run/postgresql",
)


def _serialize_cell(val: Any) -> Any:
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    return val


def _serialize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {k: _serialize_cell(v) for k, v in row.items()}


def _connect():
    import psycopg2
    from psycopg2.extras import RealDictCursor

    return psycopg2.connect(DEFAULT_DSN, cursor_factory=RealDictCursor)


def resolve_instrument_id(symbol_or_id: str) -> Optional[int]:
    s = str(symbol_or_id).strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT instrument_id FROM instruments WHERE UPPER(TRIM(symbol)) = UPPER(TRIM(%s)) LIMIT 1",
                (s,),
            )
            row = cur.fetchone()
            return int(row["instrument_id"]) if row else None


def fetch_instruments(symbol: str) -> Optional[Dict[str, Any]]:
    s = str(symbol).strip()
    if not s:
        return None
    with _connect() as conn:
        with conn.cursor() as cur:
            if s.isdigit():
                cur.execute("SELECT * FROM instruments WHERE instrument_id = %s", (int(s),))
            else:
                cur.execute(
                    "SELECT * FROM instruments WHERE UPPER(TRIM(symbol)) = UPPER(TRIM(%s)) LIMIT 1",
                    (s,),
                )
            row = cur.fetchone()
            return _serialize_row(dict(row)) if row else None


def fetch_instrument_prices(symbol: str, limit: int = 30) -> List[Dict[str, Any]]:
    iid = resolve_instrument_id(symbol)
    if iid is None:
        return []
    lim = max(1, min(int(limit), 500))
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM instrument_prices
                WHERE instrument_id = %s
                ORDER BY snapshot_date DESC, snapshot_hour DESC
                LIMIT %s
                """,
                (iid, lim),
            )
            return [_serialize_row(dict(r)) for r in cur.fetchall()]


def fetch_instrument_fundamentals(symbol: str, limit: int = 12) -> List[Dict[str, Any]]:
    iid = resolve_instrument_id(symbol)
    if iid is None:
        return []
    lim = max(1, min(int(limit), 120))
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM instrument_fundamentals
                WHERE instrument_id = %s
                ORDER BY snapshot_date DESC
                LIMIT %s
                """,
                (iid, lim),
            )
            return [_serialize_row(dict(r)) for r in cur.fetchall()]


def fetch_instrument_analysts(symbol: str, limit: int = 12) -> List[Dict[str, Any]]:
    iid = resolve_instrument_id(symbol)
    if iid is None:
        return []
    lim = max(1, min(int(limit), 120))
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM instrument_analysts
                WHERE instrument_id = %s
                ORDER BY snapshot_date DESC
                LIMIT %s
                """,
                (iid, lim),
            )
            return [_serialize_row(dict(r)) for r in cur.fetchall()]


def fetch_instrument_social(symbol: str, limit: int = 30) -> List[Dict[str, Any]]:
    iid = resolve_instrument_id(symbol)
    if iid is None:
        return []
    lim = max(1, min(int(limit), 500))
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM instrument_social
                WHERE instrument_id = %s
                ORDER BY snapshot_date DESC, snapshot_hour DESC
                LIMIT %s
                """,
                (iid, lim),
            )
            return [_serialize_row(dict(r)) for r in cur.fetchall()]


def fetch_instrument_esg(symbol: str, limit: int = 24) -> List[Dict[str, Any]]:
    iid = resolve_instrument_id(symbol)
    if iid is None:
        return []
    lim = max(1, min(int(limit), 120))
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM instrument_esg
                WHERE instrument_id = %s
                ORDER BY snapshot_date DESC
                LIMIT %s
                """,
                (iid, lim),
            )
            return [_serialize_row(dict(r)) for r in cur.fetchall()]


def fetch_instrument_betas(symbol: str, limit: int = 24) -> List[Dict[str, Any]]:
    iid = resolve_instrument_id(symbol)
    if iid is None:
        return []
    lim = max(1, min(int(limit), 120))
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM instrument_betas
                WHERE instrument_id = %s
                ORDER BY snapshot_date DESC
                LIMIT %s
                """,
                (iid, lim),
            )
            return [_serialize_row(dict(r)) for r in cur.fetchall()]
