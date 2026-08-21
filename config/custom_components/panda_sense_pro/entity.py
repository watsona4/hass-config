"""Base entity for Panda Sense Pro."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PandaSenseProCoordinator


class PandaSenseProEntity(CoordinatorEntity[PandaSenseProCoordinator]):
    """Base class for Panda Sense Pro entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator._host)},
            name="Panda Sense Pro",
            manufacturer="Bambu Lab",
            model="Panda Sense Pro",
            sw_version=coordinator.data.get("settings", {}).get("fw_version"),
        )
