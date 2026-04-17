"""
agent_base.py — Base class for any agent in the utility closet ecosystem.

Extracted from IgorBase (wild_igor/igor/igor_base.py). Provides:
  - Instance naming via GC reverse-lookup (cached after first call)
  - get_name()           -> "ClassName:instance_name"
  - log property         -> lazy per-class logger with stderr fallback
  - dump()               -> __dict__ pretty-print for debugging
  - _get_caller()        -> inspect.stack() caller info
  - time_it(label)       -> context manager: logs + records elapsed time
  - record_perf()        -> write one timing entry to perf log
  - _perf_summary()      -> p50/p95/p99 per label

Design: zero required constructor args. Log directory is configurable via
constructor param (defaults to None = no file logging, just in-memory).

T-uc-base-class-extract
"""

import gc
import inspect
import logging
import sys
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Optional


class _EmergencySafeLogger:
    """
    Thin logging.Logger wrapper that falls back to sys.stderr on any logging
    infrastructure failure.

    Usage:
        from lab.utility_closet.agent_base import get_logger
        _log = get_logger(__name__)
        _log.warning("something went wrong: %s", exc)
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._logger = logging.getLogger(name)

    def _emit(self, level: str, msg: str, *args) -> None:
        try:
            getattr(self._logger, level)(msg, *args)
        except Exception:
            try:
                formatted = msg % args if args else msg
            except Exception:
                formatted = repr(msg)
            print(
                f"[STDERR-FALLBACK][{level.upper()}][{self._name}] {formatted}",
                file=sys.stderr,
            )

    def debug(self, msg: str, *args) -> None:
        self._emit("debug", msg, *args)

    def info(self, msg: str, *args) -> None:
        self._emit("info", msg, *args)

    def warning(self, msg: str, *args) -> None:
        self._emit("warning", msg, *args)

    def error(self, msg: str, *args) -> None:
        self._emit("error", msg, *args)

    def exception(self, msg: str, *args) -> None:
        try:
            self._logger.exception(msg, *args)
        except Exception:
            try:
                formatted = msg % args if args else msg
            except Exception:
                formatted = repr(msg)
            import traceback

            tb = traceback.format_exc()
            print(
                f"[STDERR-FALLBACK][EXCEPTION][{self._name}] {formatted}\n{tb}",
                file=sys.stderr,
            )


def get_logger(name: str) -> _EmergencySafeLogger:
    """
    Return an emergency-safe logger for module-level code that cannot
    inherit AgentBase.
    """
    return _EmergencySafeLogger(name)


class AgentBase:
    """Minimal diagnostic + performance base class for any UC agent."""

    # class-level logger — one per subclass, created on first .log access
    _logger: Optional[_EmergencySafeLogger] = None

    # cached instance name — set on first _get_instance_name() call
    _instance_name: Optional[str] = None

    # ── Instance naming ───────────────────────────────────────────────────────

    def _get_instance_names(self) -> list[str]:
        """
        Return all variable names that refer to this object in any live dict.
        Uses gc.get_referrers to find the first enclosing namespace dict,
        then reverse-looks up keys whose value is this instance.
        """
        referrers = gc.get_referrers(self)
        dict_of_things: dict = {}
        for item in referrers:
            if isinstance(item, dict):
                dict_of_things = item
                break
        result = [
            k for k, v in dict_of_things.items() if v is self and isinstance(k, str)
        ]
        return result if result else ["unknown"]

    def _get_instance_name(self) -> str:
        """Return the best-guess instance name. Cached after first GC lookup."""
        if self._instance_name is None:
            names = self._get_instance_names()
            self._instance_name = names[0]
        return self._instance_name

    def get_name(self) -> str:
        """Return stable identity string: 'ClassName:instance_name'."""
        return f"{self.__class__.__name__}:{self._get_instance_name()}"

    # ── Logging ───────────────────────────────────────────────────────────────

    @property
    def log(self) -> _EmergencySafeLogger:
        """
        Lazy per-class logger with emergency stderr fallback.
        Logger name is the module path so Python's logging hierarchy
        routes records to the correct area handler.
        """
        if not self.__class__._logger:
            _module = type(self).__module__ or ""
            # Strip common prefixes so names are clean
            for prefix in ("wild_igor.", "lab.utility_closet."):
                if _module.startswith(prefix):
                    _module = _module[len(prefix) :]
                    break
            _name = _module or self.__class__.__name__
            self.__class__._logger = get_logger(_name)
        return self.__class__._logger

    # ── Performance tracking ──────────────────────────────────────────────────

    def __init__(self, log_dir: Optional[Path] = None):
        if not hasattr(self, "_perf_history"):
            self._perf_history: dict[str, list[float]] = defaultdict(list)
        self._log_dir = log_dir

    def _ensure_perf_history(self) -> dict:
        """Lazy init for _perf_history — safe even if __init__ was not called."""
        if not hasattr(self, "_perf_history"):
            self._perf_history = defaultdict(list)
        return self._perf_history

    @contextmanager
    def time_it(self, label: str, log_threshold_ms: float = 0.0):
        """
        Context manager that times the block and records it.
        Logs at DEBUG level always; logs at WARNING if elapsed > log_threshold_ms.
        """
        t0 = time.monotonic()
        try:
            yield
        finally:
            elapsed_ms = (time.monotonic() - t0) * 1000
            self._ensure_perf_history()
            self.record_perf(label, elapsed_ms)
            msg = f"{self.get_name()} [{label}] {elapsed_ms:.1f}ms"
            if log_threshold_ms > 0 and elapsed_ms > log_threshold_ms:
                self.log.warning(msg)
            else:
                self.log.debug(msg)

    def record_perf(self, label: str, elapsed_ms: float) -> None:
        """
        Record one timing entry. Appends to in-memory history (last 200 per label)
        and writes to perf log file if log_dir is configured.
        """
        hist = self._ensure_perf_history()[label]
        hist.append(elapsed_ms)
        if len(hist) > 200:
            del hist[:-200]

        if self._log_dir is not None:
            try:
                self._log_dir.mkdir(parents=True, exist_ok=True)
                log_path = self._log_dir / f"perf_{self.__class__.__name__}.log"
                ts = time.strftime("%Y-%m-%dT%H:%M:%S")
                line = f"{ts}|{self.get_name()}|{label}|{elapsed_ms:.1f}ms\n"
                existing = log_path.read_text() if log_path.exists() else ""
                log_path.write_text(line + existing)
            except Exception as _e:
                logging.getLogger(__name__).warning("perf log write failed: %s", _e)

    def _perf_summary(self, label: Optional[str] = None) -> str:
        """Return p50/p95/p99 summary for all labels (or one label)."""
        labels = [label] if label else list(self._ensure_perf_history().keys())
        if not labels:
            return f"{self.get_name()}: no perf data"

        lines = [f"{self.get_name()} perf summary:"]
        for lbl in sorted(labels):
            vals = sorted(self._ensure_perf_history().get(lbl, []))
            if not vals:
                continue
            n = len(vals)
            p50 = vals[int(n * 0.50)]
            p95 = vals[min(int(n * 0.95), n - 1)]
            p99 = vals[min(int(n * 0.99), n - 1)]
            mx = vals[-1]
            lines.append(
                f"  [{lbl}] n={n} p50={p50:.0f}ms p95={p95:.0f}ms"
                f" p99={p99:.0f}ms max={mx:.0f}ms"
            )
        return "\n".join(lines)

    # ── Debugging ─────────────────────────────────────────────────────────────

    def dump(self) -> str:
        """Pretty-print __dict__ for live debugging. Values truncated at 120 chars."""
        lines = [f"=== {self.get_name()} ==="]
        for k, v in self.__dict__.items():
            s = repr(v)
            if len(s) > 120:
                s = s[:117] + "..."
            lines.append(f"  {k}: {s}")
        return "\n".join(lines)

    def _get_caller(self, depth: int = 2) -> str:
        """
        Return 'filename:lineno function' for the caller at the given stack depth.
        depth=2 -> caller of the method that called _get_caller (typical use)
        """
        try:
            frame = inspect.stack()[depth]
            filename = frame.filename.rsplit("/", 1)[-1]
            return f"{filename}:{frame.lineno} {frame.function}"
        except Exception:
            return "unknown:0 unknown"
