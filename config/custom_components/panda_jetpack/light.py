"""Light platform for Panda Jetpack."""

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
from .coordinator import PandaJetpackCoordinator
from .entity import PandaJetpackEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaJetpackCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PandaJetpackLight(coordinator)])


class PandaJetpackLight(PandaJetpackEntity, LightEntity):
    """RGB status light for Panda Jetpack. Represents the currently-active
    effect mode's on/off, brightness, and color -- use the Light Effect
    select entity to change which effect mode is active."""

    _attr_name = "Light"
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, coordinator: PandaJetpackCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_light"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("settings", {}).get("on", False))

    @property
    def brightness(self) -> int | None:
        pct = self.coordinator.data.get("settings", {}).get("rgb_info_brightness", 100)
        return int(pct * 255 / 100)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        settings = self.coordinator.data.get("settings", {})
        mode = settings.get("current_mode", 0)
        modes = settings.get("list2", [])
        hex_color = "#FFFFFFFF"
        if 0 <= mode < len(modes):
            hex_color = modes[mode].get("rgb_rgba", hex_color)
        # Device reports colors as "#RRGGBBAA" (leading '#', trailing alpha).
        hex_color = hex_color.lstrip("#")
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        if not self.is_on:
            await self.coordinator.api_post("/light/toggle", {"on": True})

        if ATTR_BRIGHTNESS in kwargs:
            pct = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
            await self.coordinator.api_post("/light/brightness", {"brightness": pct})

        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            hex_color = f"{r:02X}{g:02X}{b:02X}"
            await self.coordinator.api_post("/light/color", {"rgb": hex_color})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/toggle", {"on": False})
