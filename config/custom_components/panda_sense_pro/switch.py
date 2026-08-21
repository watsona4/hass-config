"""Switch platform for Panda Sense Pro."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaSenseProCoordinator
from .entity import PandaSenseProEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaSenseProCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaSenseProScreensaver(coordinator),
        PandaSenseProApAlwaysOn(coordinator),
    ])


class PandaSenseProScreensaver(PandaSenseProEntity, SwitchEntity):
    _attr_name = "Screensaver"
    _attr_icon = "mdi:monitor-screenshot"

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_screensaver"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("settings", {}).get("screensaver", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/settings/screensaver", {"on": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/settings/screensaver", {"on": False})


class PandaSenseProApAlwaysOn(PandaSenseProEntity, SwitchEntity):
    _attr_name = "Access point always on"
    _attr_icon = "mdi:access-point"

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_ap_on"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("ap", {}).get("on", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/ap/toggle", {"on": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/ap/toggle", {"on": False})
