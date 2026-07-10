"""Switch platform for Panda Breath."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
        PandaBreathDryingSwitch(coordinator),
        PandaBreathWorkOnSwitch(coordinator),
    ])


class PandaBreathDryingSwitch(PandaBreathEntity, SwitchEntity):
    """Drying on/off switch."""

    _attr_name = "Drying"
    _attr_icon = "mdi:heat-wave"

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_drying"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("settings", {}).get("isrunning", 0) == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/drying/toggle", {"on": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/drying/toggle", {"on": False})


class PandaBreathWorkOnSwitch(PandaBreathEntity, SwitchEntity):
    """Work on/off switch."""

    _attr_name = "Work on"
    _attr_icon = "mdi:power"

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_work_on"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("settings", {}).get("work_on", 0) == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/drying/work-on", {"on": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/drying/work-on", {"on": False})
