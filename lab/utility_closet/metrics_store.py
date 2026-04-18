"""
metrics_store.py — T-metrics-store

Time-series metrics accumulation in infra.metrics. Any component can
record a named metric with a numeric value. Queryable by name, time
range, and tags.

Usage:
    from lab.utility_closet.metrics_store import record_metric, query_metrics

    # Record a metric
    record_metric("memory_count", 86331)
    record_metric("session_cost_usd", 0.0042, tags={"session": "2026-04-17a"})

    # Query
    history = query_metrics("memory_count", hours=168)  # last week
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

log = logging.getLogger(__name__)

_DB_URL = os.environ.get("IGOR_HOME_DB_URL", "")


def _conn():
    import psycopg2
    import psycopg2.extras

    c = psycopg2.connect(_DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    cur = c.cursor()
    cur.execute("SET search_path TO infra, clan, instance, public")
    cur.close()
    c.commit()
    return c


def record_metric(
    name: str,
    value: float,
    tags: dict | None = None,
    instance_id: str = "",
    recorded_at: datetime | None = None,
) -> None:
    """Record a single metric datapoint."""
    if not _DB_URL:
        return
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO metrics (metric_name, metric_value, tags, recorded_at, instance_id) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                name,
                float(value),
                json.dumps(tags or {}),
                recorded_at or datetime.now(timezone.utc),
                instance_id or os.environ.get("IGOR_INSTANCE_ID", ""),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        log.warning("metrics_store record failed: %s", exc)


def query_metrics(
    name: str,
    hours: float = 24,
    limit: int = 1000,
) -> list[dict]:
    """Query metric history by name within a time window."""
    if not _DB_URL:
        return []
    try:
        conn = _conn()
        cur = conn.cursor()
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        cur.execute(
            "SELECT metric_name, metric_value, tags, recorded_at, instance_id "
            "FROM metrics "
            "WHERE metric_name = %s AND recorded_at > %s "
            "ORDER BY recorded_at DESC "
            "LIMIT %s",
            (name, since, limit),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as exc:
        log.warning("metrics_store query failed: %s", exc)
        return []


def latest_metric(name: str) -> Optional[float]:
    """Get the most recent value for a metric. Returns None if not found."""
    if not _DB_URL:
        return None
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT metric_value FROM metrics "
            "WHERE metric_name = %s "
            "ORDER BY recorded_at DESC LIMIT 1",
            (name,),
        )
        row = cur.fetchone()
        conn.close()
        return float(row["metric_value"]) if row else None
    except Exception as exc:
        log.warning("metrics_store latest failed: %s", exc)
        return None


def list_metric_names() -> list[str]:
    """List all distinct metric names."""
    if not _DB_URL:
        return []
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT metric_name FROM metrics ORDER BY metric_name")
        names = [r["metric_name"] for r in cur.fetchall()]
        conn.close()
        return names
    except Exception as exc:
        log.warning("metrics_store list failed: %s", exc)
        return []


def record_snapshot(cortex=None) -> dict:
    """Record a standard set of system metrics. Called periodically (e.g. hourly).

    Returns the recorded values as a dict.
    """
    values = {}
    if cortex:
        try:
            total = cortex.total_count()
            record_metric("memory_count", total)
            values["memory_count"] = total
        except Exception:
            pass
        try:
            counts = cortex.count_by_type()
            for mtype, count in counts.items():
                record_metric(f"memory_type_{mtype}", count)
                values[f"memory_type_{mtype}"] = count
        except Exception:
            pass
        try:
            habits = cortex.get_habits()
            record_metric("habit_count", len(habits))
            values["habit_count"] = len(habits)
        except Exception:
            pass
    return values
