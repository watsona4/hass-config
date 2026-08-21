"""Number platform for Panda Jetpack."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaJetpackCoordinator
from .entity import PandaJetpackEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaJetpackCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaJetpackBrightness(coordinator),
        PandaJetpackEffectSpeed(coordinator),
    ])


class PandaJetpackBrightness(PandaJetpackEntity, NumberEntity):
    """LED brightness control."""

    _attr_name = "Brightness"
    _attr_icon = "mdi:brightness-6"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaJetpackCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_brightness"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.get("settings", {}).get("rgb_info_brightness", 100)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/light/brightness", {"brightness": int(value)})


class PandaJetpackEffectSpeed(PandaJetpackEntity, NumberEntity):
    """Light-effect animation speed (not applicable to static-color/Warning_Hot/Fan_Speed/H2D modes)."""

    _attr_name = "Effect speed"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaJetpackCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_effect_speed"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.get("settings", {}).get("rgb_info_speed", 50)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/light/speed", {"speed": int(value)})
