"""Number platform for Panda Breath."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaBreathCoordinator
from .entity import PandaBreathEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaBreathCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaBreathSetTemp(coordinator),
        PandaBreathFilterTemp(coordinator),
        PandaBreathHotbedTemp(coordinator),
        PandaBreathFilamentTemp(coordinator),
        PandaBreathFilamentTimer(coordinator),
    ])


class PandaBreathSetTemp(PandaBreathEntity, NumberEntity):
    """Main drying temperature."""

    _attr_name = "Drying temperature"
    _attr_icon = "mdi:thermometer"
    _attr_native_min_value = 0
    _attr_native_max_value = 120
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "\u00b0C"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_set_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.get("settings", {}).get("set_temp", 60)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/drying/temp", {"temp": int(value)})


class PandaBreathFilterTemp(PandaBreathEntity, NumberEntity):
    """Filter temperature threshold."""

    _attr_name = "Filter temperature"
    _attr_icon = "mdi:thermometer-low"
    _attr_native_min_value = 0
    _attr_native_max_value = 120
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "\u00b0C"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_filter_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.get("settings", {}).get("filtertemp", 30)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/drying/filter-temp", {"temp": int(value)})


class PandaBreathHotbedTemp(PandaBreathEntity, NumberEntity):
    """Hotbed temperature threshold."""

    _attr_name = "Hotbed temperature"
    _attr_icon = "mdi:thermometer-high"
    _attr_native_min_value = 0
    _attr_native_max_value = 120
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "\u00b0C"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_hotbed_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.get("settings", {}).get("hotbedtemp", 80)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/drying/hotbed-temp", {"temp": int(value)})


class PandaBreathFilamentTemp(PandaBreathEntity, NumberEntity):
    """Custom filament drying temperature."""

    _attr_name = "Filament temperature"
    _attr_icon = "mdi:thermometer-lines"
    _attr_native_min_value = 0
    _attr_native_max_value = 120
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "\u00b0C"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_filament_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.get("settings", {}).get("custom_temp", 60)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/drying/filament-temp", {"temp": int(value)})


class PandaBreathFilamentTimer(PandaBreathEntity, NumberEntity):
    """Custom filament drying timer."""

    _attr_name = "Filament timer"
    _attr_icon = "mdi:timer"
    _attr_native_min_value = 1
    _attr_native_max_value = 24
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_filament_timer"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.get("settings", {}).get("custom_timer", 12)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_post("/drying/filament-timer", {"hours": int(value)})
