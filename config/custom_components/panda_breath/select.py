"""Select platform for Panda Breath."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaBreathCoordinator
from .entity import PandaBreathEntity

WORK_MODES = {1: "Auto", 2: "Manual", 3: "Custom"}
FILAMENT_MODES = {1: "PLA", 2: "ABS/PETG", 3: "Custom"}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaBreathCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaBreathWorkMode(coordinator),
        PandaBreathFilamentMode(coordinator),
    ])


class PandaBreathWorkMode(PandaBreathEntity, SelectEntity):
    """Work mode select."""

    _attr_name = "Work mode"
    _attr_icon = "mdi:cog"
    _attr_options = list(WORK_MODES.values())

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_work_mode"

    @property
    def current_option(self) -> str | None:
        mode = self.coordinator.data.get("settings", {}).get("work_mode", 1)
        return WORK_MODES.get(mode)

    async def async_select_option(self, option: str) -> None:
        for k, v in WORK_MODES.items():
            if v == option:
                await self.coordinator.api_post("/drying/work-mode", {"mode": k})
                return


class PandaBreathFilamentMode(PandaBreathEntity, SelectEntity):
    """Filament drying mode select."""

    _attr_name = "Filament mode"
    _attr_icon = "mdi:printer-3d-nozzle"
    _attr_options = list(FILAMENT_MODES.values())

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_filament_mode"

    @property
    def current_option(self) -> str | None:
        # The filament_drying_mode isn't in initial state, default to Custom (3)
        return "Custom"

    async def async_select_option(self, option: str) -> None:
        for k, v in FILAMENT_MODES.items():
            if v == option:
                await self.coordinator.api_post("/drying/filament-mode", {"mode": k})
                return
