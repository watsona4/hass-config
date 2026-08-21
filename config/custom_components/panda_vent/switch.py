"""Switch platform for Panda Vent."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaVentCoordinator
from .entity import PandaVentEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaVentCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaVentFollowPrinter(coordinator),
        PandaVentFollowVent(coordinator),
        PandaVentWarningOverride(coordinator),
        PandaVentReverseDirection(coordinator),
    ])


class PandaVentFollowPrinter(PandaVentEntity, SwitchEntity):
    """LED effect syncs to the bound printer's own stock light."""

    _attr_name = "Follow printer light"
    _attr_icon = "mdi:printer-3d"

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_follow_printer"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("rgb_mode", {}).get("is_follow_printer", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/follow-printer", {"follow_printer": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/follow-printer", {"follow_printer": False})


class PandaVentFollowVent(PandaVentEntity, SwitchEntity):
    """LED turns on when the vent is open, off when closed. Lower priority
    than Follow Printer Light."""

    _attr_name = "Follow vent"
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_follow_vent"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("rgb_mode", {}).get("is_follow_vent", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/follow-vent", {"follow_vent": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/follow-vent", {"follow_vent": False})


class PandaVentWarningOverride(PandaVentEntity, SwitchEntity):
    """Let the red flashing warning light override the current effect on printer errors."""

    _attr_name = "Warning override"
    _attr_icon = "mdi:alert"

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_warning_override"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("rgb_mode", {}).get("warning_sw", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/warning-override", {"warning_override": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/warning-override", {"warning_override": False})


class PandaVentReverseDirection(PandaVentEntity, SwitchEntity):
    """Reverse the animation direction (Wave/Marquee/Rainbow) -- depends on
    the strip's physical mounting orientation."""

    _attr_name = "Reverse direction"
    _attr_icon = "mdi:swap-horizontal"

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_reverse_direction"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("rgb_mode", {}).get("is_reverse", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/reverse", {"reverse": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/reverse", {"reverse": False})
