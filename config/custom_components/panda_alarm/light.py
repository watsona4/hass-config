"""Light platform for Panda Alarm."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
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
    """LED light for Panda Alarm."""

    _attr_name = "LED"
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

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

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        rgb = self.coordinator.data.get("led", {}).get("rgb", {})
        hex_color = rgb.get("idle", "FFFFFF")
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        if not self.is_on:
            await self.coordinator.api_post("/led/toggle", {"on": True})

        if ATTR_BRIGHTNESS in kwargs:
            pct = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
            await self.coordinator.api_post("/led/brightness", {"brightness": pct})

        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            hex_color = f"{r:02X}{g:02X}{b:02X}"
            await self.coordinator.api_post(
                "/led/color", {"idle": hex_color, "printing": hex_color, "alarm": hex_color}
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/led/toggle", {"on": False})
