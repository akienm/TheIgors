"""
db_proxy.py — Re-export shim.

Canonical implementation lives in unseen_university.db_proxy (T-db-proxy-igor-canonical).
This shim re-exports all public names so existing imports continue to work.

Services that need make_infra_proxy() continue to import from here; the
implementation is now in unseen_university.db_proxy.
"""

from unseen_university.db_proxy import (  # noqa: F401
    DatabaseProxy,
    MEM_COLS,
    PGDatabaseProxy,
    _PGConnWrapper,
    _PGRowProxy,
    _db_log,
    make_db_proxy,
    make_dc_proxy,
    make_home_proxy,
    make_infra_proxy,
    make_local_proxy,
)
