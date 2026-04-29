"""
matter_shelf.py — GH-185: Matter/home automation as UC rack shelf.

RackModule for Matter protocol integration. Igor talks to Matter-compatible
devices (lights, sensors, locks, thermostats) via a local Matter controller.

Sensor state changes push to TWM via SensorTree nodes. Scheduled automations
are PROC habits that fire on calendar events or time patterns.

Architecture:
    MatterShelf (RackModule)
    ├── MatterController — protocol bridge (chip-tool or HA REST)
    ├── Device registry — discovered devices as memory nodes
    └── SensorTree integration — device states as sensor nodes

Status: Foundation only. Actual Matter protocol integration requires
hardware (Thread border router + devices). This shelf provides the
abstraction layer so everything else can be built and tested without
physical devices.
"""

from __future__ import annotations

import json
import logging
from lab.utility_closet.agent_base import get_logger
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from .agent_base import AgentBase
from .rack import RackModule

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class DeviceType(str, Enum):
    LIGHT = "light"
    SENSOR = "sensor"
    LOCK = "lock"
    THERMOSTAT = "thermostat"
    SWITCH = "switch"
    PLUG = "plug"
    UNKNOWN = "unknown"


class DeviceState(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class MatterDevice:
    """A Matter-compatible device discovered on the network."""

    device_id: str
    name: str
    device_type: DeviceType = DeviceType.UNKNOWN
    state: DeviceState = DeviceState.UNKNOWN
    location: str = ""  # room/area
    vendor: str = ""
    model: str = ""
    firmware: str = ""
    capabilities: list[str] = field(default_factory=list)
    attributes: dict = field(default_factory=dict)  # current attribute values
    last_seen: str = ""
    matter_node_id: Optional[int] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["device_type"] = self.device_type.value
        d["state"] = self.state.value
        return d


class MatterController(AgentBase):
    """
    Abstract Matter protocol controller.

    Subclasses implement the actual protocol bridge:
    - ChipToolController: direct chip-tool CLI
    - HomeAssistantController: Home Assistant REST API
    - MockController: for testing without hardware
    """

    def discover(self) -> list[MatterDevice]:
        """Discover Matter devices on the network."""
        return []

    def get_device(self, device_id: str) -> Optional[MatterDevice]:
        """Get current state of a specific device."""
        return None

    def set_attribute(self, device_id: str, attribute: str, value) -> bool:
        """Set a device attribute (e.g., brightness, on/off, temperature)."""
        return False

    def subscribe_events(self, device_id: str, callback) -> bool:
        """Subscribe to state change events for a device."""
        return False


class MockController(MatterController):
    """Mock controller for testing without physical devices."""

    def __init__(self):
        super().__init__()
        self._devices: dict[str, MatterDevice] = {}

    def add_device(self, device: MatterDevice) -> None:
        """Add a simulated device."""
        self._devices[device.device_id] = device

    def discover(self) -> list[MatterDevice]:
        return list(self._devices.values())

    def get_device(self, device_id: str) -> Optional[MatterDevice]:
        return self._devices.get(device_id)

    def set_attribute(self, device_id: str, attribute: str, value) -> bool:
        dev = self._devices.get(device_id)
        if dev is None:
            return False
        dev.attributes[attribute] = value
        return True


class MatterShelf(RackModule):
    """
    UC rack shelf for Matter/home automation.

    Provides device discovery, state management, and SensorTree integration.
    Devices are stored as FACTUAL memory nodes under SENSOR_TREE_ROOT with
    watch_type="matter_device".
    """

    name = "matter"
    version = "0.1.0"
    module_type = "automation"

    def __init__(self, controller: Optional[MatterController] = None):
        self._controller = controller or MockController()
        self._devices: dict[str, MatterDevice] = {}
        self._started = False

    def health(self) -> dict:
        return {
            "online": self._started,
            "devices": len(self._devices),
            "controller": type(self._controller).__name__,
        }

    def start(self) -> None:
        self._started = True
        logger.info("MatterShelf started with %s", type(self._controller).__name__)

    def stop(self) -> None:
        self._started = False
        logger.info("MatterShelf stopped")

    def discover_devices(self) -> list[MatterDevice]:
        """Discover and register Matter devices."""
        devices = self._controller.discover()
        for dev in devices:
            dev.last_seen = datetime.now().isoformat()
            self._devices[dev.device_id] = dev
        return devices

    def get_device(self, device_id: str) -> Optional[MatterDevice]:
        """Get a registered device by ID."""
        return self._devices.get(device_id)

    def list_devices(self) -> list[MatterDevice]:
        """List all registered devices."""
        return list(self._devices.values())

    def set_attribute(self, device_id: str, attribute: str, value) -> dict:
        """Set a device attribute. Returns result dict."""
        dev = self._devices.get(device_id)
        if dev is None:
            return {"error": f"Unknown device: {device_id}"}

        success = self._controller.set_attribute(device_id, attribute, value)
        if success:
            dev.attributes[attribute] = value
            return {
                "device_id": device_id,
                "attribute": attribute,
                "value": value,
                "success": True,
            }
        return {
            "device_id": device_id,
            "attribute": attribute,
            "success": False,
            "error": "controller rejected",
        }

    def register_as_sensors(self, cortex) -> list[dict]:
        """
        Register discovered devices as SensorTree nodes.

        Each device becomes a FACTUAL node under SENSOR_TREE_ROOT with
        watch_type="matter_device". The sensor evaluator checks device
        state via the controller.
        """
        from wild_igor.igor.cognition.sensor_tree import (
            create_sensor,
            ensure_sensor_root,
        )

        ensure_sensor_root(cortex)
        results = []

        for dev in self._devices.values():
            sensor_id = f"SENSOR_MATTER_{dev.device_id.upper()}"
            result = create_sensor(
                cortex,
                sensor_id=sensor_id,
                narrative=f"Matter device: {dev.name} ({dev.device_type.value}) in {dev.location or 'unknown'}",
                watch_type="matter_device",
                target=dev.device_id,
                condition="changed",
                check_interval_sec=60,
            )
            results.append(result)

        return results
