"""Number platform for Panda Sense Pro."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
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
    async_add_entities([PandaSenseProBrightness(coordinator)])


class PandaSenseProBrightness(PandaSenseProEntity, NumberEntity):
    """Normal (non-screensaver) screen brightness. The device's own UI
    offers this as a discrete dropdown rather than a free slider; step=5
    is an approximation of that option list, not device-confirmed for
    every value in range."""

    _attr_name = "Brightness"
    _attr_icon = "mdi:brightness-6"
    _attr_native_min_value = 5
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_brightness"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.get("settings", {}).get("brightness", 100)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/settings/brightness", {"brightness": int(value)})
