"""Base entity for Panda Jetpack."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PandaJetpackCoordinator


class PandaJetpackEntity(CoordinatorEntity[PandaJetpackCoordinator]):
    """Base class for Panda Jetpack entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PandaJetpackCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator._host)},
            name="Panda Jetpack",
            manufacturer="Bambu Lab",
            model="Panda Jetpack",
            sw_version=coordinator.data.get("settings", {}).get("fw_version"),
        )
