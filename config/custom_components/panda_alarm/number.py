"""Number platform for Panda Alarm."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaAlarmCoordinator
from .entity import PandaAlarmEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaAlarmCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaAlarmLedBrightness(coordinator),
        PandaAlarmSoundVolume(coordinator),
        PandaAlarmPreviewProgress(coordinator),
    ])


class PandaAlarmLedBrightness(PandaAlarmEntity, NumberEntity):
    """LED brightness control."""

    _attr_name = "LED brightness"
    _attr_icon = "mdi:brightness-6"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_led_brightness"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.get("led", {}).get("brightness", 100)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/led/brightness", {"brightness": int(value)})


class PandaAlarmSoundVolume(PandaAlarmEntity, NumberEntity):
    """Sound volume control."""

    _attr_name = "Sound volume"
    _attr_icon = "mdi:volume-medium"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_sound_volume"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.get("sound", {}).get("volume", 100)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/sound/volume", {"volume": int(value)})


class PandaAlarmPreviewProgress(PandaAlarmEntity, NumberEntity):
    """Preview mode progress."""

    _attr_name = "Preview progress"
    _attr_icon = "mdi:progress-check"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_preview_progress"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.get("preview", {}).get("percent", 0)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/preview/progress", {"percent": int(value)})
