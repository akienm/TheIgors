"""
db_proxy.py — DatabaseProxy: connection lifecycle, failover, and performance metrics.

All SQLite access in Cortex routes through here. Callers use:

    with self._db() as conn:
        conn.execute(...)

DatabaseProxy owns the connection lifecycle — open, close, retry, hard-interrupt on
sustained failure. Callers never know a transient error occurred.

Metrics are stored in an in-memory ring (never written to the DB — circular dependency).
Exposed via get_metrics() for /introspect and self-directed testing (#208).

Part of #211. Foundation for remote-agent sync (#190).

Updated 2026-04-29T17:08:53Z
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import threading
import time
from collections import deque
from pathlib import Path
from typing import Optional

from lab.utility_closet.agent_base import AgentBase as IgorBase  # UC uses AgentBase
from lab.utility_closet.agent_base import get_logger
from wild_igor.igor.paths import paths

_log = get_logger(__name__)

# Thread-local flag to prevent EXPLAIN QUERY PLAN re-entrancy
_in_explain = threading.local()

_SLOW_MS = int(os.getenv("IGOR_DB_SLOW_MS", "50"))
_RING_SIZE = 500

# D200: memory column list owned by db_proxy — cortex imports this constant so SQL
# construction stays in the data layer. Excludes the embedding blob (large + separate table).
MEM_COLS = (
    "id, narrative, memory_type, parent_id, children_ids, link_ids, "
    "valence, activation_count, friction_history, timestamp, metadata, "
    "arousal, dominance, portable, links_weighted, last_accessed, "
    "source, confidence, context_of_encoding, scope, payload"
)

# ── Dedicated DB query log ────────────────────────────────────────────────────
# All slow queries written to db_queries.log with timestamp + turn_id tie-back.
# turn_id links each slow query back to the forensic_logger turn for the same call.

_DB_LOG_PATH = paths().logs / "db_queries.log"
_DB_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
_DB_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


def _db_log(elapsed_ms: float, sql: str, owner: str = "?") -> None:
    """Append one slow-query entry to db_queries.log."""
    try:
        # Rotate at 10 MB — keep .1 backup, start fresh
        if _DB_LOG_PATH.exists() and _DB_LOG_PATH.stat().st_size > _DB_LOG_MAX_BYTES:
            backup = _DB_LOG_PATH.with_suffix(".log.1")
            if backup.exists():
                backup.unlink()
            _DB_LOG_PATH.rename(backup)

        turn_id = "(unknown)"
        try:
            from wild_igor.igor.cognition.forensic_logger import get_turn_id

            turn_id = get_turn_id()
        except Exception as _bare_e:
            _log.warning(
                "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
            )
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} owner={owner} turn={turn_id} elapsed={elapsed_ms}ms sql={sql}\n"
        with open(_DB_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as _bare_e:
        _log.warning("bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e)


class _DBContext:
    """
    Context manager returned by DatabaseProxy(). Yields a raw sqlite3.Connection.
    Times the block, records metrics, closes on exit.
    Uses set_trace_callback to capture executed SQL for slow-query diagnostics.
    """

    __slots__ = ("_proxy", "_conn", "_t0", "_last_sql")

    def __init__(self, proxy: "DatabaseProxy") -> None:
        self._proxy = proxy
        self._conn: Optional[sqlite3.Connection] = None
        self._t0: float = 0.0
        self._last_sql: str = ""

    def __enter__(self) -> sqlite3.Connection:
        self._t0 = time.monotonic()
        try:
            self._conn = sqlite3.connect(self._proxy.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.set_trace_callback(self._on_sql)
            return self._conn
        except Exception as exc:
            self._proxy._record_error(exc)
            raise

    def _on_sql(self, sql: str) -> None:
        self._last_sql = sql
        if self._conn is not None:
            self._proxy._track_index_usage(self._conn, sql)

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        elapsed_ms = round((time.monotonic() - self._t0) * 1000)
        self._proxy._record(
            elapsed_ms, error=exc_type is not None, last_sql=self._last_sql
        )
        if self._conn is not None:
            try:
                if exc_type is None:
                    self._conn.commit()  # persist writes — matches `with conn:` semantics
                else:
                    self._conn.rollback()
            except Exception as _bare_e:
                _log.warning(
                    "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
                )
            try:
                self._conn.close()
            except Exception as _bare_e:
                _log.warning(
                    "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
                )
        return False  # never suppress exceptions


class DatabaseProxy(IgorBase):
    """
    Drop-in replacement for Cortex._conn().

    Usage (in Cortex):
        self._db = DatabaseProxy(db_path)
        ...
        with self._db() as conn:
            conn.execute(...)

    Metrics (in-memory ring, never written to DB):
        proxy.get_metrics() -> dict with latency percentiles, slow count, error count
    """

    def __init__(self, db_path: Path) -> None:
        super().__init__()
        self.db_path = db_path
        self._latencies: deque[float] = deque(maxlen=_RING_SIZE)
        self._errors: int = 0
        self._slow: int = 0
        self._calls: int = 0
        self._connect_errors: int = 0
        # W2: index lifecycle tracking
        self._explain_cache: dict[str, list[str]] = {}  # sql_hash[:12] → [index_names]
        self._index_hits: dict[str, int] = {}
        self._ensure_lock = threading.Lock()

    def __call__(self) -> _DBContext:
        """Return a context manager that yields an instrumented connection."""
        return _DBContext(self)

    # ── Internal recording ────────────────────────────────────────────────────

    def _record(
        self, elapsed_ms: float, error: bool = False, last_sql: str = ""
    ) -> None:
        self._calls += 1
        self._latencies.append(elapsed_ms)
        if error:
            self._errors += 1
        if elapsed_ms >= _SLOW_MS:
            self._slow += 1
            try:

                sql_snippet = (
                    last_sql[:600].replace("\n", " ").strip()
                    if last_sql
                    else "(unknown)"
                )
                _log.warning(f"[db_proxy] slow query {elapsed_ms}ms — {sql_snippet}")
                _db_log(elapsed_ms, sql_snippet, owner=self.get_name())
            except Exception as _bare_e:
                _log.warning(
                    "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
                )

    def _record_error(self, exc: Exception) -> None:
        self._connect_errors += 1
        try:

            _log.error(f"[db_proxy] connection error: {exc}")
        except Exception as _bare_e:
            _log.warning(
                "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
            )

    # ── Index lifecycle ───────────────────────────────────────────────────────

    def _track_index_usage(self, conn: sqlite3.Connection, sql: str) -> None:
        """
        Run EXPLAIN QUERY PLAN once per unique SQL pattern; accumulate index hit counts.
        Called from _DBContext._on_sql() on every executed statement.
        Thread-local _in_explain flag prevents re-entrancy.
        """
        if getattr(_in_explain, "active", False):
            return
        upper = sql.lstrip().upper()
        if upper.startswith(
            (
                "EXPLAIN",
                "CREATE",
                "DROP",
                "PRAGMA",
                "BEGIN",
                "COMMIT",
                "ROLLBACK",
                "SAVEPOINT",
                "RELEASE",
                "ATTACH",
                "DETACH",
            )
        ):
            return

        key = hashlib.sha256(sql.encode()).hexdigest()[:12]
        cached = self._explain_cache.get(key)
        if cached is not None:
            for idx_name in cached:
                self._index_hits[idx_name] = self._index_hits.get(idx_name, 0) + 1
            return

        _in_explain.active = True
        try:
            rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
            idx_names: list[str] = []
            for row in rows:
                row_str = " ".join(str(c) for c in row)
                m = re.search(r"USING INDEX (\S+)", row_str, re.IGNORECASE)
                if m:
                    idx_names.append(m.group(1))
            self._explain_cache[key] = idx_names
            for idx_name in idx_names:
                self._index_hits[idx_name] = self._index_hits.get(idx_name, 0) + 1
        except Exception:
            self._explain_cache[key] = []
        finally:
            _in_explain.active = False

    def ensure_index(self, table: str, columns: tuple, unique: bool = False) -> None:
        """
        Idempotent CREATE INDEX IF NOT EXISTS for the given table+columns.
        Records creation in _cc_index_registry table (created once per DB).
        Thread-safe. Logs to db_queries.log when a new index is created.
        """
        col_str = "_".join(columns)
        idx_name = f"idx_{table}_{col_str}"
        cols_sql = ", ".join(columns)
        unique_kw = "UNIQUE " if unique else ""

        with self._ensure_lock:
            with self() as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS _cc_index_registry "
                    "(index_name TEXT PRIMARY KEY, table_name TEXT, "
                    "columns TEXT, created_at TEXT)"
                )
                existing = conn.execute(
                    "SELECT 1 FROM _cc_index_registry WHERE index_name = %s",
                    (idx_name,),
                ).fetchone()
                conn.execute(
                    f"CREATE {unique_kw}INDEX IF NOT EXISTS {idx_name} "
                    f"ON {table} ({cols_sql})"
                )
                if not existing:
                    conn.execute(
                        "INSERT INTO _cc_index_registry "
                        "(index_name, table_name, columns, created_at) VALUES (%s,%s,%s,%s) "
                        "ON CONFLICT (index_name) DO NOTHING",
                        (
                            idx_name,
                            table,
                            ",".join(columns),
                            time.strftime("%Y-%m-%dT%H:%M:%S"),
                        ),
                    )
                    _db_log(
                        0,
                        f"ensure_index: CREATE INDEX {idx_name} ON {table}({cols_sql})",
                    )

    def get_index_report(self) -> dict:
        """
        Return {index_name: {hits, table, columns, created_at}} from registry + in-memory hit counts.
        Safe to call at any time; returns {} if registry table not yet created.
        """
        result: dict = {}
        try:
            with self() as conn:
                rows = conn.execute(
                    "SELECT index_name, table_name, columns, created_at "
                    "FROM _cc_index_registry"
                ).fetchall()
            for row in rows:
                idx_name = row["index_name"]
                result[idx_name] = {
                    "hits": self._index_hits.get(idx_name, 0),
                    "table": row["table_name"],
                    "columns": row["columns"],
                    "created_at": row["created_at"],
                }
        except Exception as _bare_e:
            _log.warning(
                "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
            )
        return result

    # ── Metrics ───────────────────────────────────────────────────────────────

    def get_metrics(self) -> dict:
        """
        Return a summary dict of recent DB performance.
        Safe to call at any time — reads only the in-memory ring.
        """
        lats = sorted(self._latencies)
        n = len(lats)

        def _pct(p: float) -> float:
            if not lats:
                return 0.0
            idx = max(0, int(n * p / 100) - 1)
            return round(lats[idx], 1)

        return {
            "db_path": str(self.db_path),
            "total_calls": self._calls,
            "error_count": self._errors,
            "connect_errors": self._connect_errors,
            "slow_count": self._slow,
            "slow_threshold_ms": _SLOW_MS,
            "latency_p50_ms": _pct(50),
            "latency_p95_ms": _pct(95),
            "latency_p99_ms": _pct(99),
            "latency_max_ms": round(lats[-1], 1) if lats else 0.0,
            "sample_size": n,
        }

    # ── D200 capability methods ────────────────────────────────────────────────
    # Cortex speaks capabilities; proxy owns SQL. Callers get raw rows and call
    # _to_memory() themselves — proxy has no knowledge of the Memory dataclass.

    def fetch_by_ids(self, ids: list, excl_types: tuple = ()) -> list:
        """Fetch memory rows by ID list. Returns raw rows; caller maps to Memory."""
        if not ids:
            return []
        ph = ",".join("?" * len(ids))
        if excl_types:
            excl_ph = ",".join("?" * len(excl_types))
            sql = (
                f"SELECT {MEM_COLS} FROM memories "
                f"WHERE id IN ({ph}) AND memory_type NOT IN ({excl_ph})"
            )
            params = list(ids) + list(excl_types)
        else:
            sql = f"SELECT {MEM_COLS} FROM memories WHERE id IN ({ph})"
            params = list(ids)
        with self() as conn:
            return conn.execute(sql, params).fetchall()

    def get_activation_rows(self, limit: int, since_hours: float = 48.0) -> list:
        """Return (node_id, last_seen) rows for hottest tails entries in the window."""
        from datetime import datetime, timedelta

        cutoff = (datetime.now() - timedelta(hours=since_hours)).isoformat()
        with self() as conn:
            return conn.execute(
                "SELECT node_id, MAX(recorded_at) as last_seen "
                "FROM tails WHERE recorded_at > ? "
                "GROUP BY node_id ORDER BY last_seen DESC LIMIT ?",
                (cutoff, limit),
            ).fetchall()


# ── Postgres backend ──────────────────────────────────────────────────────────


class _PGConnWrapper:
    """
    Thin wrapper around a psycopg2 connection that makes it look like sqlite3.Connection
    to Cortex callers:
    - execute() returns self so callers can chain .fetchone()/.fetchall()
    - row_factory not needed — psycopg2.extras.RealDictCursor used at connection level
    - All callers use native Postgres syntax (no SQLite translation needed)
    """

    __slots__ = ("_conn", "_cur", "_last_sql")

    def __init__(self, conn) -> None:
        import psycopg2.extras  # noqa: F401

        self._conn = conn
        self._cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self._last_sql: str = ""

    def execute(self, sql: str, params=()) -> "_PGConnWrapper":
        self._last_sql = sql
        # SELECT statements can never abort a transaction — skip savepoint overhead.
        # Savepoints are only needed for DDL/DML that might raise (e.g. column-already-exists
        # patterns from _init_db), letting callers do `try: conn.execute(...) except: pass`.
        if sql.lstrip().upper().startswith("SELECT"):
            self._cur.execute(sql, params or ())
            return self
        # DML/DDL: wrap in a savepoint so a failed statement doesn't abort the transaction.
        # Uses a dedicated cursor so RELEASE SAVEPOINT doesn't clear self._cur's result set.
        sp_cur = self._conn.cursor()
        try:
            sp_cur.execute("SAVEPOINT _igor_sp")
            try:
                self._cur.execute(sql, params or ())
                sp_cur.execute("RELEASE SAVEPOINT _igor_sp")
            except Exception:
                sp_cur.execute("ROLLBACK TO SAVEPOINT _igor_sp")
                sp_cur.execute("RELEASE SAVEPOINT _igor_sp")
                raise
        finally:
            sp_cur.close()
        return self

    def executemany(self, sql: str, seq) -> "_PGConnWrapper":
        self._last_sql = sql
        self._cur.executemany(sql, seq)
        return self

    @property
    def rowcount(self) -> int:
        """Mirrors sqlite3.Cursor.rowcount — rows affected by last DML statement."""
        return self._cur.rowcount if self._cur.rowcount >= 0 else 0

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return _PGRowProxy(row)

    def fetchall(self):
        return [_PGRowProxy(r) for r in self._cur.fetchall()]

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        try:
            self._cur.close()
        except Exception as _bare_e:
            _log.warning(
                "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
            )
        try:
            self._conn.close()
        except Exception as _bare_e:
            _log.warning(
                "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
            )


class _PGRowProxy:
    """
    Makes psycopg2 RealDictRow act like sqlite3.Row:
    supports both row["col"] and row[0] (integer index) access.
    """

    __slots__ = ("_d", "_keys")

    def __init__(self, row) -> None:
        self._d = dict(row)
        self._keys = list(self._d.keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._d[self._keys[key]]
        return self._d[key]

    def __iter__(self):
        return iter(self._d.values())

    def keys(self):
        return self._keys

    def get(self, key, default=None):
        return self._d.get(key, default)


class _PGContext:
    """Context manager for PGDatabaseProxy — mirrors _DBContext interface."""

    __slots__ = ("_proxy", "_wrapper", "_t0")

    def __init__(self, proxy: "PGDatabaseProxy") -> None:
        self._proxy = proxy
        self._wrapper: Optional[_PGConnWrapper] = None
        self._t0: float = 0.0

    def __enter__(self) -> _PGConnWrapper:
        self._t0 = time.monotonic()
        try:
            conn = self._proxy._pool.getconn()
            # T-uc-schema-three-namespaces: set search_path so queries resolve
            # tables in the correct schema without explicit schema prefixes.
            # Uses string formatting (not parameterized) because SET search_path
            # needs bare identifiers, not a quoted string. Value is internal-only.
            cur = conn.cursor()
            cur.execute(f"SET search_path TO {self._proxy._search_path}")
            cur.close()
            conn.commit()
            self._wrapper = _PGConnWrapper(conn)
            return self._wrapper
        except Exception as exc:
            self._proxy._record_error(exc)
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        elapsed_ms = round((time.monotonic() - self._t0) * 1000)
        last_sql = self._wrapper._last_sql if self._wrapper else ""
        self._proxy._record(elapsed_ms, error=exc_type is not None, last_sql=last_sql)
        if self._wrapper is not None:
            raw_conn = self._wrapper._conn
            try:
                if exc_type is None:
                    raw_conn.commit()
                else:
                    raw_conn.rollback()
            except Exception as _bare_e:
                _log.warning(
                    "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
                )
            try:
                self._proxy._pool.putconn(raw_conn)
            except Exception as _bare_e:
                _log.warning(
                    "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
                )
        return False


class PGDatabaseProxy(IgorBase):
    """
    Postgres-backed drop-in replacement for DatabaseProxy.
    Uses IGOR_DB_URL (standard libpq DSN) from the environment.
    ThreadedConnectionPool for concurrent multi-box access.

    Interface identical to DatabaseProxy — callers use:
        with self._db() as conn:
            conn.execute(...)
    """

    # T-uc-schema-three-namespaces: search_path determines which schemas are
    # visible. Connections from make_home_proxy see clan+infra+public (shared).
    # Connections from make_local_proxy see instance+clan+infra+public (full).
    # Connections from make_infra_proxy see infra+public only (UC services).
    # _migrations stays in public so it's always findable before search_path is set.
    DEFAULT_SEARCH_PATH = "instance,clan,infra,public"

    def __init__(self, db_url: str, search_path: str = None) -> None:
        super().__init__()
        self.db_url = db_url
        self._search_path = search_path or self.DEFAULT_SEARCH_PATH
        self._latencies: deque[float] = deque(maxlen=_RING_SIZE)
        self._errors: int = 0
        self._slow: int = 0
        self._calls: int = 0
        self._connect_errors: int = 0
        import psycopg2
        from psycopg2 import pool as pg_pool

        # T-connection-pool-resize: minconn=3 so background sources (NE, push_sources,
        # cortex search) don't queue behind each other at startup. maxconn=20 headroom
        # for multi-thread contention under load. Still well within PG default max_conn.
        self._pool = pg_pool.ThreadedConnectionPool(
            minconn=3,
            maxconn=20,
            dsn=db_url,
        )

    def __call__(self) -> _PGContext:
        return _PGContext(self)

    def _record(
        self, elapsed_ms: float, error: bool = False, last_sql: str = ""
    ) -> None:
        self._calls += 1
        self._latencies.append(elapsed_ms)
        if error:
            self._errors += 1
        if elapsed_ms >= _SLOW_MS:
            self._slow += 1
            try:

                sql_snippet = (
                    last_sql[:600].replace("\n", " ").strip()
                    if last_sql
                    else "(unknown)"
                )
                _log.warning(f"[pg_proxy] slow query {elapsed_ms}ms — {sql_snippet}")
                _db_log(elapsed_ms, sql_snippet, owner=self.get_name())
            except Exception as _bare_e:
                _log.warning(
                    "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
                )

    def _record_error(self, exc: Exception) -> None:
        self._connect_errors += 1
        try:

            _log.error(f"[pg_proxy] connection error: {exc}")
        except Exception as _bare_e:
            _log.warning(
                "bare except in wild_igor/igor/memory/db_proxy.py: %s", _bare_e
            )

    def ensure_index(self, table: str, columns: tuple, unique: bool = False) -> None:
        """No-op for Postgres — indexes created by migration script."""
        pass

    def get_index_report(self) -> dict:
        return {}

    def get_metrics(self) -> dict:
        lats = sorted(self._latencies)
        n = len(lats)

        def _pct(p: float) -> float:
            if not lats:
                return 0.0
            idx = max(0, int(n * p / 100) - 1)
            return round(lats[idx], 1)

        return {
            "db_url": self.db_url.split("@")[-1],  # hide credentials
            "total_calls": self._calls,
            "error_count": self._errors,
            "connect_errors": self._connect_errors,
            "slow_count": self._slow,
            "slow_threshold_ms": _SLOW_MS,
            "latency_p50_ms": _pct(50),
            "latency_p95_ms": _pct(95),
            "latency_p99_ms": _pct(99),
            "latency_max_ms": round(lats[-1], 1) if lats else 0.0,
            "sample_size": n,
        }

    # ── D200 capability methods ────────────────────────────────────────────────

    def fetch_by_ids(self, ids: list, excl_types: tuple = ()) -> list:
        """Fetch memory rows by ID list. Returns raw rows; caller maps to Memory."""
        if not ids:
            return []
        ph = ",".join(["%s"] * len(ids))
        if excl_types:
            excl_ph = ",".join(["%s"] * len(excl_types))
            sql = (
                f"SELECT {MEM_COLS} FROM memories "
                f"WHERE id IN ({ph}) AND memory_type NOT IN ({excl_ph})"
            )
            params = list(ids) + list(excl_types)
        else:
            sql = f"SELECT {MEM_COLS} FROM memories WHERE id IN ({ph})"
            params = list(ids)
        with self() as conn:
            return conn.execute(sql, params).fetchall()

    def get_activation_rows(self, limit: int, since_hours: float = 48.0) -> list:
        """Return (node_id, last_seen) rows for hottest tails entries in the window."""
        from datetime import datetime, timedelta

        cutoff = (datetime.now() - timedelta(hours=since_hours)).isoformat()
        with self() as conn:
            return conn.execute(
                "SELECT node_id, MAX(recorded_at) as last_seen "
                "FROM tails WHERE recorded_at > %s "
                "GROUP BY node_id ORDER BY last_seen DESC LIMIT %s",
                (cutoff, limit),
            ).fetchall()


# ── Factory ───────────────────────────────────────────────────────────────────


def make_home_proxy(db_path: Path = None):
    """
    Return PGDatabaseProxy for IGOR_HOME_DB_URL (global truth DB shared across
    all Igor instances), else DatabaseProxy (SQLite fallback).

    HOME tables: clan.memories, clan.interpretive_edges, clan.wg_cooccur,
                 clan.reading_list, plus infra.* for cross-agent tables.
    search_path: clan,infra,public — no instance schema access.

    IGOR_HOME_SEARCH_PATH overrides the default search_path (used by test
    fixtures to redirect writes to an isolated schema, e.g. test_clan_<ts>).
    """
    db_url = os.getenv("IGOR_HOME_DB_URL") or os.getenv(
        "IGOR_DB_URL"
    )  # backward compat
    if db_url:
        sp = os.getenv("IGOR_HOME_SEARCH_PATH") or "clan,infra,public"
        return PGDatabaseProxy(db_url, search_path=sp)
    # SQLite fallback: use explicit path, then IGOR_DB_PATH env var
    if db_path is None:
        env_path = os.getenv("IGOR_DB_PATH")
        if env_path:
            db_path = Path(env_path)
    return DatabaseProxy(db_path)


def make_local_proxy(db_path: Path = None):
    """
    Return PGDatabaseProxy for LOCAL tables (instance.ring_memory,
    instance.twm_observations, instance.pending_replies, per-box metrics).

    Checks IGOR_LOCAL_DB_URL first, falls back to IGOR_HOME_DB_URL.
    All data lives in Postgres — no SQLite fallback for TWM/ring.
    search_path: instance,clan,infra,public — full access for Igor.

    IGOR_LOCAL_SEARCH_PATH overrides the default search_path (test fixtures).
    """
    db_url = (
        os.getenv("IGOR_LOCAL_DB_URL")
        or os.getenv("IGOR_HOME_DB_URL")
        or os.getenv("IGOR_DB_URL")
    )
    if db_url:
        sp = os.getenv("IGOR_LOCAL_SEARCH_PATH") or "instance,clan,infra,public"
        return PGDatabaseProxy(db_url, search_path=sp)
    # Last resort: SQLite — should not happen in production
    return DatabaseProxy(db_path)


def make_infra_proxy():
    """
    Return PGDatabaseProxy for infrastructure tables only (infra schema).
    Used by utility closet services that don't need clan or instance access.
    search_path: infra,public.
    """
    db_url = os.getenv("IGOR_HOME_DB_URL") or os.getenv("IGOR_DB_URL")
    if db_url:
        return PGDatabaseProxy(db_url, search_path="infra,public")
    return None


def make_db_proxy(db_path: Path = None):
    """Backward-compat alias for make_home_proxy(). Prefer make_home_proxy() or make_local_proxy()."""
    return make_home_proxy(db_path)
