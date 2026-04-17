"""
rack.py — Utility closet rack architecture (T-uc-rack-architecture).

The rack is the frame that holds modular services (shelves). Each shelf
is a RackModule with a standard lifecycle: register, health check, stop.

Rack manages module registration, health monitoring, and discovery.
Modules register on startup and deregister on shutdown. The rack
provides a unified health view across all modules.

Design principles:
  - Each module is independently testable and restartable
  - Health starts simple: {"online": bool}, extensible per module
  - No direct function calls between modules — use comms channels (future)
  - Compatible with existing UC server agent registration pattern
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from .agent_base import AgentBase

log = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Registration record for a rack module."""

    name: str
    version: str
    module_type: str  # "agent", "service", "transport", etc.
    capabilities: list[str] = field(default_factory=list)
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)


class RackModule(AgentBase):
    """
    Base class for any utility closet rack module (shelf).

    Subclass and implement:
      - health() -> dict  — at minimum {"online": bool}
      - start()           — called on registration (optional)
      - stop()            — called on deregistration (optional)

    The name, version, and module_type identify the module to the rack.
    """

    def __init__(
        self,
        name: str,
        version: str = "0.1.0",
        module_type: str = "service",
        capabilities: list[str] | None = None,
        log_dir=None,
    ):
        super().__init__(log_dir=log_dir)
        self.module_name = name
        self.module_version = version
        self.module_type = module_type
        self.module_capabilities = capabilities or []

    def health(self) -> dict:
        """Return health status. Override to add module-specific fields."""
        return {"online": True}

    def start(self) -> None:
        """Called when the module is registered with the rack. Override as needed."""
        pass

    def stop(self) -> None:
        """Called when the module is deregistered. Override for cleanup."""
        pass

    def info(self) -> ModuleInfo:
        """Return registration info for this module."""
        return ModuleInfo(
            name=self.module_name,
            version=self.module_version,
            module_type=self.module_type,
            capabilities=self.module_capabilities,
        )


class Rack(AgentBase):
    """
    The rack frame — manages module registration, health, and discovery.

    Thread-safe. Modules register/deregister at any time. Health checks
    are non-blocking (each module's health() is called synchronously but
    should return quickly — heavy checks belong in background threads).
    """

    def __init__(self, log_dir=None):
        super().__init__(log_dir=log_dir)
        self._modules: dict[str, RackModule] = {}
        self._info: dict[str, ModuleInfo] = {}
        self._lock = threading.Lock()

    def register(self, module: RackModule) -> bool:
        """
        Register a module with the rack. Calls module.start().
        Returns True if newly registered, False if already present.
        """
        with self._lock:
            if module.module_name in self._modules:
                log.warning(
                    "Module %s already registered — skipping", module.module_name
                )
                return False
            self._modules[module.module_name] = module
            self._info[module.module_name] = module.info()
            log.info(
                "Rack: registered %s v%s (%s)",
                module.module_name,
                module.module_version,
                module.module_type,
            )
        module.start()
        return True

    def deregister(self, name: str) -> bool:
        """
        Deregister a module by name. Calls module.stop().
        Returns True if removed, False if not found.
        """
        with self._lock:
            module = self._modules.pop(name, None)
            self._info.pop(name, None)
        if module is None:
            return False
        module.stop()
        log.info("Rack: deregistered %s", name)
        return True

    def get(self, name: str) -> Optional[RackModule]:
        """Get a registered module by name. Returns None if not found."""
        with self._lock:
            return self._modules.get(name)

    def list_modules(self) -> list[ModuleInfo]:
        """Return info for all registered modules."""
        with self._lock:
            return list(self._info.values())

    def health(self) -> dict:
        """
        Aggregate health across all modules.
        Returns {"online": bool, "modules": {name: health_dict, ...}}.
        """
        with self._lock:
            modules = dict(self._modules)

        module_health = {}
        all_online = True
        for name, module in modules.items():
            try:
                h = module.health()
                module_health[name] = h
                if not h.get("online", False):
                    all_online = False
            except Exception as exc:
                module_health[name] = {"online": False, "error": str(exc)}
                all_online = False

        return {
            "online": all_online,
            "module_count": len(modules),
            "modules": module_health,
        }

    def heartbeat(self, name: str) -> bool:
        """Record a heartbeat from a module. Returns False if not registered."""
        with self._lock:
            info = self._info.get(name)
            if info is None:
                return False
            info.last_heartbeat = time.time()
            return True

    def stop_all(self) -> None:
        """Stop and deregister all modules. Called on UC shutdown."""
        with self._lock:
            names = list(self._modules.keys())
        for name in names:
            self.deregister(name)


# Module-level singleton — created on first import, wired into UC server.
_rack: Optional[Rack] = None
_rack_lock = threading.Lock()


def get_rack() -> Rack:
    """Return the singleton Rack instance."""
    global _rack
    if _rack is None:
        with _rack_lock:
            if _rack is None:
                _rack = Rack()
    return _rack
