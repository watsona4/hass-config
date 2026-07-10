"""Base entity for Panda Alarm."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PandaAlarmCoordinator


class PandaAlarmEntity(CoordinatorEntity[PandaAlarmCoordinator]):
    """Base class for Panda Alarm entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator._host)},
            name="Panda Alarm",
            manufacturer="Bambu Lab",
            model="Panda Alarm",
            sw_version=coordinator.data.get("settings", {}).get("fw_version"),
        )
