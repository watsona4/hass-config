"""Light platform for Panda Vent."""

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
from .coordinator import PandaVentCoordinator
from .entity import PandaVentEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaVentCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PandaVentLight(coordinator)])


class PandaVentLight(PandaVentEntity, LightEntity):
    """RGB status light for Panda Vent. Represents Simple Mode's active
    effect on/off, brightness, and color -- use the Light Mode select to
    switch to Advance or Warning Hot mode, and Simple Effect to change
    which effect is active."""

    _attr_name = "Light"
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_light"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("rgb_mode", {}).get("light_on_off", False))

    @property
    def brightness(self) -> int | None:
        rgb_mode = self.coordinator.data.get("rgb_mode", {})
        idx = rgb_mode.get("current_simple_effect", 0)
        effects = rgb_mode.get("effects", [])
        pct = effects[idx].get("brightness", 100) if 0 <= idx < len(effects) else 100
        return int(pct * 255 / 100)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        rgb_mode = self.coordinator.data.get("rgb_mode", {})
        idx = rgb_mode.get("current_simple_effect", 0)
        effects = rgb_mode.get("effects", [])
        hex_color = effects[idx].get("color", "FFFFFF") if 0 <= idx < len(effects) else "FFFFFF"
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
            await self.coordinator.api_post("/light/simple/brightness", {"brightness": pct})

        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            hex_color = f"{r:02X}{g:02X}{b:02X}"
            await self.coordinator.api_post("/light/simple/color", {"rgb": hex_color})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/light/toggle", {"on": False})
