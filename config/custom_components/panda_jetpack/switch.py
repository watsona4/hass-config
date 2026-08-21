"""Switch platform for Panda Jetpack."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
        PandaJetpackFollowPrinter(coordinator),
        PandaJetpackWarningOverride(coordinator),
    ])


class PandaJetpackFollowPrinter(PandaJetpackEntity, SwitchEntity):
    """Follow Printer Light: RGB effect auto on/off follows the bound printer."""

    _attr_name = "Follow printer light"
    _attr_icon = "mdi:printer-3d"

    def __init__(self, coordinator: PandaJetpackCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_follow_printer"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("settings", {}).get("follow", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/follow", {"follow": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/follow", {"follow": False})


class PandaJetpackWarningOverride(PandaJetpackEntity, SwitchEntity):
    """Let the red flashing warning light override the current effect on printer errors."""

    _attr_name = "Warning override"
    _attr_icon = "mdi:alert"

    def __init__(self, coordinator: PandaJetpackCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_warning_override"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("settings", {}).get("warning_override", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/warning-override", {"warning_override": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/warning-override", {"warning_override": False})
