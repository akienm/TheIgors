"""
db_shelf.py — Database proxy as a utility closet rack shelf.

Wraps the existing db_proxy (wild_igor/igor/memory/db_proxy.py) as a
RackModule with health reporting and metrics. The actual db_proxy stays
in place — this is the rack registration wrapper, not a code move.

Service calls stay direct (no comms:// overhead for high-frequency DB
reads). The shelf provides:
  - Rack module registration + health checks
  - Proxy factory access (home, local, infra)
  - Metrics exposure (latencies, errors, slow queries)
  - Future: audit trail logging to comms channel

T-uc-db-proxy-shelf
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from .rack import RackModule

log = logging.getLogger(__name__)


class DatabaseShelf(RackModule):
    """
    Rack shelf wrapper for the database proxy layer.

    Provides health() with live DB metrics and proxy factory access.
    Does NOT own the proxy instances — Cortex and other callers create
    their own via make_home_proxy/make_local_proxy. The shelf monitors
    and reports on them.
    """

    def __init__(self, log_dir=None):
        super().__init__(
            name="database",
            version="0.1.0",
            module_type="service",
            capabilities=["postgres", "query", "metrics"],
            log_dir=log_dir,
        )
        self._home_proxy = None
        self._local_proxy = None
        self._infra_proxy = None

    def start(self) -> None:
        """Initialize proxy connections on shelf registration."""
        try:
            from lab.utility_closet.db_proxy import (
                make_home_proxy,
                make_infra_proxy,
                make_local_proxy,
            )

            db_url = os.environ.get("IGOR_HOME_DB_URL")
            if db_url:
                self._home_proxy = make_home_proxy()
                self._local_proxy = make_local_proxy()
                self._infra_proxy = make_infra_proxy()
                log.info("DatabaseShelf: proxies initialized")
            else:
                log.warning("DatabaseShelf: no IGOR_HOME_DB_URL — proxies unavailable")
        except Exception as exc:
            log.error("DatabaseShelf: proxy init failed: %s", exc)

    def stop(self) -> None:
        """Clean up proxy connections."""
        self._home_proxy = None
        self._local_proxy = None
        self._infra_proxy = None

    def health(self) -> dict:
        """Return health with live DB metrics from home proxy."""
        result = {"online": False}

        if self._home_proxy is None:
            result["reason"] = "no proxy initialized"
            return result

        try:
            metrics = self._home_proxy.get_metrics()
            result["online"] = True
            result["db_url"] = metrics.get("db_url", "unknown")
            result["total_calls"] = metrics.get("total_calls", 0)
            result["error_count"] = metrics.get("error_count", 0)
            result["slow_count"] = metrics.get("slow_count", 0)
            result["latency_p50_ms"] = metrics.get("latency_p50_ms", 0)
            result["latency_p95_ms"] = metrics.get("latency_p95_ms", 0)
        except Exception as exc:
            result["reason"] = str(exc)

        return result

    @property
    def home(self):
        """Access the home (clan+infra) proxy."""
        return self._home_proxy

    @property
    def local(self):
        """Access the local (instance+clan+infra) proxy."""
        return self._local_proxy

    @property
    def infra(self):
        """Access the infra-only proxy."""
        return self._infra_proxy

    def get_metrics(self) -> dict:
        """Return combined metrics from all proxies."""
        result = {}
        for name, proxy in [
            ("home", self._home_proxy),
            ("local", self._local_proxy),
            ("infra", self._infra_proxy),
        ]:
            if proxy and hasattr(proxy, "get_metrics"):
                result[name] = proxy.get_metrics()
        return result
