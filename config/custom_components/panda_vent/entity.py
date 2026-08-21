"""Base entity for Panda Vent."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PandaVentCoordinator


class PandaVentEntity(CoordinatorEntity[PandaVentCoordinator]):
    """Base class for Panda Vent entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator._host)},
            name="Panda Vent",
            manufacturer="Bambu Lab",
            model="Panda Vent",
            sw_version=coordinator.data.get("settings", {}).get("fw_version"),
        )
