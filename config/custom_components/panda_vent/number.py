"""Number platform for Panda Vent."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaVentCoordinator
from .entity import PandaVentEntity


def _active_simple_effect(data: dict) -> dict:
    rgb_mode = data.get("rgb_mode", {})
    idx = rgb_mode.get("current_simple_effect", 0)
    effects = rgb_mode.get("effects", [])
    if 0 <= idx < len(effects):
        return effects[idx]
    return {}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaVentCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaVentSimpleBrightness(coordinator),
        PandaVentSimpleSpeed(coordinator),
    ])


class PandaVentSimpleBrightness(PandaVentEntity, NumberEntity):
    """Brightness of the active Simple-mode effect."""

    _attr_name = "Simple brightness"
    _attr_icon = "mdi:brightness-6"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_simple_brightness"

    @property
    def native_value(self) -> float:
        return _active_simple_effect(self.coordinator.data).get("brightness", 100)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/light/simple/brightness", {"brightness": int(value)})


class PandaVentSimpleSpeed(PandaVentEntity, NumberEntity):
    """Animation speed of the active Simple-mode effect (not applicable to Static)."""

    _attr_name = "Simple speed"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_simple_speed"

    @property
    def native_value(self) -> float:
        return _active_simple_effect(self.coordinator.data).get("speed", 50)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/light/simple/speed", {"speed": int(value)})
