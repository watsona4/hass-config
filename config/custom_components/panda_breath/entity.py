"""Base entity for Panda Breath."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PandaBreathCoordinator


class PandaBreathEntity(CoordinatorEntity[PandaBreathCoordinator]):
    """Base class for Panda Breath entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator._host)},
            name="Panda Breath",
            manufacturer="Bambu Lab",
            model="Panda Breath",
            sw_version=coordinator.data.get("settings", {}).get("fw_version"),
        )
