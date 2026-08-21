"""Base entity for Panda Branch Plus."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PandaBranchPlusCoordinator


class PandaBranchPlusEntity(CoordinatorEntity[PandaBranchPlusCoordinator]):
    """Base class for Panda Branch Plus entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PandaBranchPlusCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator._host)},
            name="Panda Branch Plus",
            manufacturer="Bambu Lab",
            model="Panda Branch Plus",
            sw_version=coordinator.data.get("settings", {}).get("fw_version"),
        )
