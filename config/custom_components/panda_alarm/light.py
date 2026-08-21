"""Light platform for Panda Alarm."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
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
    async_add_entities([PandaAlarmLight(coordinator)])


class PandaAlarmLight(PandaAlarmEntity, LightEntity):
    """On/off + brightness control for the Panda Alarm's LED.

    Deliberately does not expose RGB color: the device has one physical LED but
    three independent mode colors (idle/printing/alarm), set once as fixed
    device configuration via POST /led/color and never changed afterwards (the
    device's own firmware picks which of the three to display based on real
    printer state). This entity used to also accept rgb_color and collapsed it
    into all three mode colors at once via the same API call -- which is
    exactly what the daytime mute/restore automation was doing every time it
    "restored" a saved color, silently erasing the distinct printing/alarm
    colors back to whatever was last saved for the LED overall. Fixed by
    dropping RGB support here entirely; there is no HA-facing color control for
    this device anymore by design.
    """

    _attr_name = "LED"
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_led"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("led", {}).get("on", False)

    @property
    def brightness(self) -> int | None:
        pct = self.coordinator.data.get("led", {}).get("brightness", 100)
        return int(pct * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if not self.is_on:
            await self.coordinator.api_post("/led/toggle", {"on": True})

        if ATTR_BRIGHTNESS in kwargs:
            pct = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
            await self.coordinator.api_post("/led/brightness", {"brightness": pct})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/led/toggle", {"on": False})
